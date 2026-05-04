"""
Pramana AI — SHAP Explainer Wrapper
======================================

Menghitung SHAP values untuk setiap prediksi klaim,
menghasilkan top 5 contributing features dan penjelasan
teks dalam bahasa Indonesia sesuai SPEC.md bagian 5.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================================
# Risk Factor Templates (Bahasa Indonesia)
# ============================================================================

FACTOR_TEMPLATES: dict[str, str] = {
    "rasio_terhadap_ina_cbgs": "Tagihan {pct}% {direction} tarif INA-CBGs untuk diagnosa ini",
    "tagihan_per_hari": "Tagihan per hari {direction} dari RS setipe di wilayah yang sama",
    "total_tagihan": "Total tagihan {direction} dari rata-rata untuk diagnosa ini",
    "los": "Lama rawat (LOS) {direction} dari standar untuk diagnosa ini",
    "severity_score": "Severity score diagnosa {level}",
    "jumlah_prosedur": "Jumlah prosedur {direction} dari rata-rata",
    "jumlah_diagnosa_sekunder": "Jumlah diagnosa sekunder {direction} dari biasa",
    "tagihan_obat_ratio": "Rasio biaya obat {direction} dari rata-rata",
    "tagihan_tindakan_ratio": "Rasio biaya tindakan {direction} dari rata-rata",
    "rs_avg_risk_score_30d": "Track record RS menunjukkan risk score rata-rata {level}",
    "rs_pending_rate_30d": "RS memiliki tingkat klaim pending {level} dalam 30 hari terakhir",
    "rs_total_claims_30d": "Volume klaim RS dalam 30 hari terakhir {level}",
    "percentile_tagihan_per_diagnosa": "Tagihan berada di percentile {pct} dibanding RS setipe",
    "percentile_los_per_diagnosa": "LOS berada di percentile {pct} dibanding klaim serupa",
    "z_score_tagihan": "Tagihan {direction} dari rata-rata cluster RS (z-score: {val})",
    "tipe_rs_encoded": "Tipe RS {level}",
    "provinsi_encoded": "Indeks biaya regional {level}",
    "is_regional_outlier": "Tagihan merupakan outlier di wilayah ini",
    "bulan_pengajuan": "Pola pengajuan klaim pada bulan {val}",
    "hari_pengajuan_dalam_bulan": "Klaim diajukan pada hari ke-{val} bulan ini",
    "is_end_of_month": "Klaim diajukan pada akhir bulan (pola batch submission)",
    "diagnosa_utama_encoded": "Profil diagnosa utama menunjukkan risiko {level}",
}


def _generate_explanation(
    feature_name: str,
    shap_value: float,
    feature_value: float,
) -> str:
    """Generate human-readable explanation for a single feature.

    Args:
        feature_name: Name of the feature.
        shap_value: SHAP value (positive = increases risk).
        feature_value: Actual feature value.

    Returns:
        Human-readable explanation string in Bahasa Indonesia.
    """
    direction = "lebih tinggi" if shap_value > 0 else "lebih rendah"
    level = "tinggi" if shap_value > 0 else "rendah"

    template = FACTOR_TEMPLATES.get(feature_name)
    if template is None:
        return f"Fitur '{feature_name}' berkontribusi {'meningkatkan' if shap_value > 0 else 'menurunkan'} risiko"

    try:
        return template.format(
            direction=direction,
            level=level,
            pct=f"{abs(feature_value * 100):.0f}" if abs(feature_value) < 10 else f"{feature_value:.0f}",
            val=f"{feature_value:.2f}",
        )
    except (KeyError, ValueError):
        return f"Fitur '{feature_name}' berkontribusi {'meningkatkan' if shap_value > 0 else 'menurunkan'} risiko"


# ============================================================================
# ClaimExplainer
# ============================================================================


class ClaimExplainer:
    """SHAP-based claim risk explainer.

    Wraps SHAP TreeExplainer for generating per-claim explanations
    with top contributing features and human-readable text.
    """

    def __init__(self):
        self._explainer = None
        self._is_ready = False

    def initialize(self, model: Any) -> None:
        """Initialize SHAP explainer with the trained model.

        Uses the XGBoost model from the ensemble for TreeExplainer
        (faster and more accurate than KernelExplainer).

        Args:
            model: Trained ensemble model or tree-based model.
        """
        try:
            import shap

            # If ensemble, use the xgb_model for TreeExplainer
            if hasattr(model, "xgb_model"):
                base_model = model.xgb_model
            elif hasattr(model, "rf_model"):
                base_model = model.rf_model
            else:
                base_model = model

            self._explainer = shap.TreeExplainer(base_model)
            self._is_ready = True
            logger.info("SHAP explainer initialized successfully")

        except ImportError:
            logger.warning("SHAP not installed — explanations will use feature importance fallback")
            self._is_ready = False
        except Exception as e:
            logger.warning("SHAP initialization failed: %s — using fallback", e)
            self._is_ready = False

    def explain(
        self,
        features: pd.DataFrame,
        feature_names: list[str],
        top_n: int = 5,
    ) -> list[dict]:
        """Generate explanations for scored claims.

        Args:
            features: Scaled feature DataFrame (1 or more rows).
            feature_names: List of feature column names.
            top_n: Number of top contributing features to return.

        Returns:
            List of explanation dicts (one per claim), each containing:
            - shap_values: dict of feature -> SHAP value
            - top_risk_factors: list of human-readable explanations
        """
        t0 = time.time()
        results = []

        if self._is_ready and self._explainer is not None:
            results = self._explain_with_shap(features, feature_names, top_n)
        else:
            results = self._explain_fallback(features, feature_names, top_n)

        elapsed_ms = (time.time() - t0) * 1000
        logger.debug("Generated %d explanations in %.1fms", len(results), elapsed_ms)

        return results

    def _explain_with_shap(
        self,
        features: pd.DataFrame,
        feature_names: list[str],
        top_n: int,
    ) -> list[dict]:
        """Generate explanations using SHAP TreeExplainer."""
        shap_values = self._explainer.shap_values(features)

        # Handle binary classification (shap_values may be list)
        if isinstance(shap_values, list):
            shap_vals = shap_values[1]  # class 1 = anomaly
        else:
            shap_vals = shap_values

        results = []
        for i in range(len(features)):
            row_shap = shap_vals[i] if shap_vals.ndim > 1 else shap_vals
            row_features = features.iloc[i]

            # Build shap_values dict
            shap_dict = {}
            for j, name in enumerate(feature_names):
                shap_dict[name] = round(float(row_shap[j]), 4)

            # Sort by absolute SHAP value to find top contributors
            sorted_features = sorted(
                shap_dict.items(),
                key=lambda x: abs(x[1]),
                reverse=True,
            )

            # Top N risk factors with explanations
            top_factors = []
            for feat_name, shap_val in sorted_features[:top_n]:
                feat_value = float(row_features[feat_name]) if feat_name in row_features.index else 0.0
                explanation = _generate_explanation(feat_name, shap_val, feat_value)
                top_factors.append(explanation)

            results.append({
                "shap_values": shap_dict,
                "top_risk_factors": top_factors,
            })

        return results

    def _explain_fallback(
        self,
        features: pd.DataFrame,
        feature_names: list[str],
        top_n: int,
    ) -> list[dict]:
        """Fallback explanation using feature deviation from mean.

        Used when SHAP is not available. Ranks features by their
        absolute z-score (deviation from training mean).
        """
        results = []
        for i in range(len(features)):
            row = features.iloc[i]

            # Use scaled values as proxy for importance
            deviations = {}
            for name in feature_names:
                val = float(row[name]) if name in row.index else 0.0
                deviations[name] = round(val, 4)

            sorted_features = sorted(
                deviations.items(),
                key=lambda x: abs(x[1]),
                reverse=True,
            )

            top_factors = []
            for feat_name, dev_val in sorted_features[:top_n]:
                raw_val = float(row[feat_name]) if feat_name in row.index else 0.0
                explanation = _generate_explanation(feat_name, dev_val, raw_val)
                top_factors.append(explanation)

            results.append({
                "shap_values": deviations,
                "top_risk_factors": top_factors,
            })

        return results
