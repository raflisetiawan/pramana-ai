"""
Pramana AI — Ensemble Risk Scorer
====================================

Singleton model loader dan scoring engine.
Lazy-load model saat pertama kali dipanggil untuk efisiensi startup.
Sesuai SPEC.md: risk score 0-100, level low/medium/high.

Usage:
    scorer = RiskScorer.get_instance()
    result = scorer.score(features_df)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

_SAVED_MODELS_DIR = Path(__file__).parent.parent / "saved_models"
_ENSEMBLE_PATH = _SAVED_MODELS_DIR / "ensemble_v1.pkl"
_SCALER_PATH = _SAVED_MODELS_DIR / "standard_scaler.pkl"

# Risk level thresholds (SPEC.md bagian 7)
RISK_THRESHOLDS = {
    "low": (0, 40),
    "medium": (40, 70),
    "high": (70, 100),
}


def _classify_risk_level(score: float) -> str:
    """Classify risk score into level (low/medium/high)."""
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= score < high:
            return level
    return "high"  # score >= 100 fallback


# ============================================================================
# Singleton Risk Scorer
# ============================================================================


class RiskScorer:
    """Singleton risk scoring engine.

    Lazy-loads the trained ensemble model and preprocessor on first use.
    Thread-safe via Python's GIL for read-only inference.
    """

    _instance: Optional["RiskScorer"] = None

    def __init__(self):
        self._model = None
        self._preprocessor = None
        self._is_loaded = False
        self._model_version: str = "not_loaded"
        self._model_path: str = ""
        self._feature_names: list[str] = []

    @classmethod
    def get_instance(cls) -> "RiskScorer":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def feature_names(self) -> list[str]:
        return self._feature_names

    def load(
        self,
        model_path: Optional[Path] = None,
        scaler_path: Optional[Path] = None,
    ) -> None:
        """Load model and preprocessor from disk.

        Args:
            model_path: Path to ensemble_v1.pkl.
            scaler_path: Path to standard_scaler.pkl.
        """
        model_path = model_path or _ENSEMBLE_PATH
        scaler_path = scaler_path or _SCALER_PATH

        t0 = time.time()

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}. Run train.py first."
            )

        # Load ensemble model
        self._model = joblib.load(model_path)
        self._model_path = str(model_path)
        self._model_version = getattr(self._model, "version", "ensemble_v1")
        self._feature_names = getattr(self._model, "feature_names", [])

        # Load preprocessor
        if scaler_path.exists():
            from app.features.preprocessor import ClaimPreprocessor
            self._preprocessor = ClaimPreprocessor.load(scaler_path)
        else:
            logger.warning("Scaler not found at %s, scoring without scaling", scaler_path)

        self._is_loaded = True
        load_time = time.time() - t0

        logger.info(
            "Model loaded: version=%s, features=%d, time=%.2fs",
            self._model_version,
            len(self._feature_names),
            load_time,
        )

    def _ensure_loaded(self) -> None:
        """Lazy-load model if not yet loaded."""
        if not self._is_loaded:
            self.load()

    def score(self, features: pd.DataFrame) -> list[dict]:
        """Score one or more claims.

        Args:
            features: DataFrame with feature columns (pre-extracted).
                Can be raw (unscaled) — will be scaled automatically.

        Returns:
            List of dicts with risk_score, risk_level per claim.
        """
        self._ensure_loaded()

        t0 = time.time()

        # Scale features if preprocessor available
        if self._preprocessor is not None and self._preprocessor.is_fitted:
            X = self._preprocessor.transform(features)
        else:
            X = features

        # Get probabilities
        proba = self._model.predict_proba(X)[:, 1]

        # Convert to 0-100 risk score
        risk_scores = np.clip(proba * 100, 0, 100)

        results = []
        for i, score in enumerate(risk_scores):
            results.append({
                "risk_score": round(float(score), 2),
                "risk_level": _classify_risk_level(float(score)),
                "probability": round(float(proba[i]), 4),
            })

        elapsed_ms = (time.time() - t0) * 1000
        logger.debug("Scored %d claims in %.1fms", len(results), elapsed_ms)

        return results

    def get_model_info(self) -> dict:
        """Get model metadata for /ml/model-info endpoint."""
        self._ensure_loaded()

        metrics = getattr(self._model, "metrics", {})
        shap_imp = getattr(self._model, "shap_importance", [])

        return {
            "model_version": self._model_version,
            "model_path": self._model_path,
            "feature_count": len(self._feature_names),
            "feature_names": self._feature_names,
            "metrics": metrics,
            "shap_top_features": shap_imp[:5] if shap_imp else [],
            "risk_thresholds": RISK_THRESHOLDS,
            "is_loaded": self._is_loaded,
        }


# ============================================================================
# Ensemble Model Class
# ============================================================================


class EnsembleClassifier:
    """Weighted average ensemble of RF + XGBoost.

    Combines predictions from both models using weighted averaging
    of predicted probabilities. This class is the canonical definition
    used for pickling/unpickling the trained model.
    """

    def __init__(
        self,
        rf_model: Any = None,
        xgb_model: Any = None,
        rf_weight: float = 0.4,
        xgb_weight: float = 0.6,
        threshold: float = 0.5,
        version: str = "ensemble_v1",
    ):
        self.rf_model = rf_model
        self.xgb_model = xgb_model
        self.rf_weight = rf_weight
        self.xgb_weight = xgb_weight
        self.threshold = threshold
        self.version = version
        self.feature_names: list[str] = []
        self.metrics: Optional[dict] = None
        self.shap_importance: Optional[list] = None

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get weighted average probabilities from both models."""
        rf_prob = self.rf_model.predict_proba(X)[:, 1]
        xgb_prob = self.xgb_model.predict_proba(X)[:, 1]
        ensemble_prob = (
            self.rf_weight * rf_prob + self.xgb_weight * xgb_prob
        )
        return np.column_stack([1 - ensemble_prob, ensemble_prob])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict using the tuned threshold."""
        proba = self.predict_proba(X)[:, 1]
        return (proba >= self.threshold).astype(int)

    def score_claim(self, X: pd.DataFrame) -> np.ndarray:
        """Get risk score 0-100 for each claim."""
        proba = self.predict_proba(X)[:, 1]
        return np.clip(proba * 100, 0, 100)

