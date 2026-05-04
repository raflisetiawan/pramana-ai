"""
Pramana AI — Feature Preprocessor
====================================

Menangani scaling fitur numerik menggunakan StandardScaler.
Menyimpan dan memuat scaler yang sudah di-fit untuk konsistensi
antara training dan inferensi.

Tanggung jawab:
- Fit StandardScaler pada data training
- Transform fitur saat training dan inferensi
- Persist scaler ke disk (joblib) agar bisa di-load saat startup ML Engine
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .extractor import ALL_FEATURE_COLUMNS, FEATURE_GROUPS

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

_DEFAULT_SCALER_PATH = (
    Path(__file__).parent.parent / "saved_models" / "standard_scaler.pkl"
)

# Columns that should NOT be scaled (binary/ordinal with fixed meaning)
_SKIP_SCALING: set[str] = {
    "is_end_of_month",
    "is_regional_outlier",
}


# ============================================================================
# ClaimPreprocessor Class
# ============================================================================


class ClaimPreprocessor:
    """Preprocessor pipeline for claim features.

    Wraps StandardScaler with domain-specific logic:
    - Scales only numeric continuous features
    - Preserves binary features (is_end_of_month, is_regional_outlier)
    - Provides fit/transform/save/load interface
    - Tracks which columns were used during fitting

    Usage (Training):
        preprocessor = ClaimPreprocessor()
        X_train_scaled = preprocessor.fit_transform(X_train)
        preprocessor.save()

    Usage (Inference):
        preprocessor = ClaimPreprocessor.load()
        X_scaled = preprocessor.transform(X_new)
    """

    def __init__(self, scaler_path: Optional[Union[str, Path]] = None):
        """Initialize preprocessor.

        Args:
            scaler_path: Path to save/load the fitted scaler.
                Defaults to saved_models/standard_scaler.pkl.
        """
        self.scaler_path = Path(scaler_path) if scaler_path else _DEFAULT_SCALER_PATH
        self.scaler: Optional[StandardScaler] = None
        self.fitted_columns: list[str] = []
        self.scaled_columns: list[str] = []
        self._is_fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        """Check if the preprocessor has been fitted."""
        return self._is_fitted

    def _get_columns_to_scale(self, columns: list[str]) -> list[str]:
        """Determine which columns should be scaled.

        Args:
            columns: List of all feature column names.

        Returns:
            List of columns that need StandardScaler applied.
        """
        return [c for c in columns if c not in _SKIP_SCALING]

    def fit(self, X: pd.DataFrame) -> "ClaimPreprocessor":
        """Fit the scaler on training data.

        Args:
            X: Training features DataFrame with ALL_FEATURE_COLUMNS.

        Returns:
            self (for chaining).
        """
        self.fitted_columns = list(X.columns)
        self.scaled_columns = self._get_columns_to_scale(self.fitted_columns)

        self.scaler = StandardScaler()
        self.scaler.fit(X[self.scaled_columns])
        self._is_fitted = True

        logger.info(
            "Preprocessor fitted on %d columns (%d scaled, %d skipped)",
            len(self.fitted_columns),
            len(self.scaled_columns),
            len(self.fitted_columns) - len(self.scaled_columns),
        )

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform features using the fitted scaler.

        Args:
            X: Features DataFrame to transform.

        Returns:
            DataFrame with scaled numeric features and untouched binary features.

        Raises:
            RuntimeError: If preprocessor has not been fitted.
        """
        if not self._is_fitted or self.scaler is None:
            raise RuntimeError(
                "Preprocessor not fitted. Call fit() or load() first."
            )

        result = X.copy()

        # Ensure all expected columns exist
        for col in self.fitted_columns:
            if col not in result.columns:
                result[col] = 0.0
                logger.warning("Missing column '%s' filled with 0.0", col)

        # Scale continuous columns
        cols_to_scale = [c for c in self.scaled_columns if c in result.columns]
        result[cols_to_scale] = self.scaler.transform(result[cols_to_scale])

        # Reorder to match training column order
        result = result[self.fitted_columns]

        return result

    def fit_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Fit and transform in one step.

        Args:
            X: Training features DataFrame.

        Returns:
            Scaled DataFrame.
        """
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Reverse scaling to get original values back.

        Useful for interpreting SHAP values in original units.

        Args:
            X: Scaled features DataFrame.

        Returns:
            DataFrame with original scale restored.
        """
        if not self._is_fitted or self.scaler is None:
            raise RuntimeError(
                "Preprocessor not fitted. Call fit() or load() first."
            )

        result = X.copy()
        cols_to_scale = [c for c in self.scaled_columns if c in result.columns]
        result[cols_to_scale] = self.scaler.inverse_transform(
            result[cols_to_scale]
        )

        return result

    def save(self, path: Optional[Union[str, Path]] = None) -> Path:
        """Save fitted preprocessor to disk.

        Saves the scaler, fitted columns, and scaled columns together
        as a single joblib file for atomic load/save.

        Args:
            path: Optional override path. Defaults to self.scaler_path.

        Returns:
            Path where the preprocessor was saved.
        """
        save_path = Path(path) if path else self.scaler_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "scaler": self.scaler,
            "fitted_columns": self.fitted_columns,
            "scaled_columns": self.scaled_columns,
            "is_fitted": self._is_fitted,
        }

        joblib.dump(state, save_path)
        logger.info("Preprocessor saved to %s", save_path)

        return save_path

    @classmethod
    def load(cls, path: Optional[Union[str, Path]] = None) -> "ClaimPreprocessor":
        """Load a previously fitted preprocessor from disk.

        Args:
            path: Path to the saved preprocessor file.
                Defaults to saved_models/standard_scaler.pkl.

        Returns:
            Fitted ClaimPreprocessor instance.

        Raises:
            FileNotFoundError: If the scaler file doesn't exist.
        """
        load_path = Path(path) if path else _DEFAULT_SCALER_PATH

        if not load_path.exists():
            raise FileNotFoundError(
                f"Preprocessor file not found: {load_path}"
            )

        state = joblib.load(load_path)

        instance = cls(scaler_path=load_path)
        instance.scaler = state["scaler"]
        instance.fitted_columns = state["fitted_columns"]
        instance.scaled_columns = state["scaled_columns"]
        instance._is_fitted = state["is_fitted"]

        logger.info(
            "Preprocessor loaded from %s (%d columns)",
            load_path,
            len(instance.fitted_columns),
        )

        return instance

    def get_feature_stats(self) -> pd.DataFrame:
        """Get mean and scale (std) for each scaled feature.

        Useful for debugging and understanding the scaler behavior.

        Returns:
            DataFrame with columns ['feature', 'mean', 'std'].
        """
        if not self._is_fitted or self.scaler is None:
            raise RuntimeError("Preprocessor not fitted.")

        return pd.DataFrame(
            {
                "feature": self.scaled_columns,
                "mean": self.scaler.mean_,
                "std": self.scaler.scale_,
            }
        )


# ============================================================================
# Convenience Functions
# ============================================================================


def build_training_pipeline(
    csv_path: Union[str, Path],
    scaler_path: Optional[Union[str, Path]] = None,
) -> tuple[pd.DataFrame, pd.Series, "ClaimPreprocessor"]:
    """End-to-end pipeline: load CSV → extract features → fit & scale.

    This is a convenience function for training scripts and notebooks.

    Args:
        csv_path: Path to synthetic_claims.csv.
        scaler_path: Optional path to save the fitted scaler.

    Returns:
        Tuple of (X_scaled, y, preprocessor).
    """
    from .extractor import extract_features_from_dataframe, LABEL_COLUMN

    # Load data
    df = pd.read_csv(csv_path)
    logger.info("Loaded %d claims from %s", len(df), csv_path)

    # Extract features (with fitting encodings)
    X = extract_features_from_dataframe(df, fit_encodings=True)
    y = df[LABEL_COLUMN].copy() if LABEL_COLUMN in df.columns else None

    # Fit and transform
    preprocessor = ClaimPreprocessor(scaler_path=scaler_path)
    X_scaled = preprocessor.fit_transform(X)
    preprocessor.save()

    logger.info(
        "Training pipeline complete: %d samples, %d features",
        len(X_scaled),
        len(X_scaled.columns),
    )

    return X_scaled, y, preprocessor
