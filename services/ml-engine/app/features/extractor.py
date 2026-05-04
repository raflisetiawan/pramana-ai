"""
Pramana AI — Feature Extractor
================================

Mengekstrak fitur dari data klaim mentah menjadi format yang siap
untuk diproses oleh model ML. Sesuai dengan FEATURE_GROUPS di SPEC.md bagian 7.

Tanggung jawab:
- Menerima data klaim mentah (dict atau DataFrame)
- Menghitung fitur turunan (derived features)
- Menangani missing values (median imputation numerik, mode untuk kategori)
- Encoding: ordinal untuk tipe_rs, target encoding untuk diagnosa_utama
- Menghasilkan DataFrame dengan kolom fitur yang konsisten
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================================
# Feature Group Definitions (sesuai SPEC.md bagian 7)
# ============================================================================

FEATURE_GROUPS: dict[str, list[str]] = {
    "biaya": [
        "total_tagihan",
        "tagihan_per_hari",
        "tagihan_obat_ratio",
        "tagihan_tindakan_ratio",
        "rasio_terhadap_ina_cbgs",
    ],
    "klinis": [
        "los",
        "diagnosa_utama_encoded",
        "jumlah_diagnosa_sekunder",
        "jumlah_prosedur",
        "severity_score",
    ],
    "geografis": [
        "tipe_rs_encoded",
        "provinsi_encoded",
        "is_regional_outlier",
    ],
    "temporal": [
        "bulan_pengajuan",
        "hari_pengajuan_dalam_bulan",
        "is_end_of_month",
    ],
    "komparatif": [
        "percentile_tagihan_per_diagnosa",
        "percentile_los_per_diagnosa",
        "z_score_tagihan",
    ],
    "historis_rs": [
        "rs_avg_risk_score_30d",
        "rs_pending_rate_30d",
        "rs_total_claims_30d",
    ],
}

# All feature columns in flat list (used by preprocessor and model)
ALL_FEATURE_COLUMNS: list[str] = [
    col for group in FEATURE_GROUPS.values() for col in group
]

LABEL_COLUMN = "is_anomaly"

# ============================================================================
# Encoding Maps
# ============================================================================

# Ordinal encoding untuk tipe RS (A=4, B=3, C=2, D=1)
TIPE_RS_ENCODING: dict[str, int] = {"A": 4, "B": 3, "C": 2, "D": 1}

# ICD-10 chapter → ordinal encoding
ICD_CHAPTER_ENCODING: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5,
    "F": 6, "G": 7, "H": 8, "I": 9, "J": 10,
    "K": 11, "L": 12, "M": 13, "N": 14, "O": 15,
    "P": 16, "Q": 17, "R": 18, "S": 19, "T": 20,
}

# Regional cost index per provinsi
REGIONAL_COST_INDEX: dict[str, float] = {
    "DKI Jakarta": 1.20,
    "Jawa Barat": 1.05,
    "Jawa Tengah": 0.95,
    "DI Yogyakarta": 0.93,
    "Jawa Timur": 1.00,
    "Bali": 1.08,
    "Sumatera Utara": 1.10,
    "Sumatera Barat": 1.05,
    "Kalimantan Timur": 1.15,
    "Sulawesi Selatan": 1.05,
}

# Severity score per ICD-10 chapter (default fallback)
CHAPTER_SEVERITY: dict[str, int] = {
    "A": 2, "B": 2, "C": 5, "D": 3, "E": 2,
    "F": 2, "G": 3, "H": 1, "I": 4, "J": 3,
    "K": 3, "L": 1, "M": 1, "N": 2, "O": 2,
    "P": 4, "Q": 3, "R": 1, "S": 3, "T": 3,
}

# Target encoding: mean risk per diagnosa (learned from training data)
# This will be populated by fit_target_encoding() during training
_target_encoding_map: dict[str, float] = {}
_TARGET_ENCODING_PATH = Path(__file__).parent.parent / "saved_models" / "target_encoding.json"


# ============================================================================
# Target Encoding for diagnosa_utama
# ============================================================================


def fit_target_encoding(
    df: pd.DataFrame,
    col: str = "diagnosa_utama",
    target: str = LABEL_COLUMN,
    smoothing: float = 10.0,
) -> dict[str, float]:
    """Fit target encoding: map each diagnosa to its smoothed mean of target.

    Uses Bayesian smoothing to prevent overfitting on rare categories:
        encoding = (count * mean_category + smoothing * global_mean) / (count + smoothing)

    Args:
        df: Training DataFrame.
        col: Column to encode.
        target: Target column name.
        smoothing: Smoothing factor (higher = more regularization).

    Returns:
        Dictionary mapping category values to encoded floats.
    """
    global _target_encoding_map

    global_mean = df[target].mean()
    agg = df.groupby(col)[target].agg(["mean", "count"])
    agg["encoding"] = (
        (agg["count"] * agg["mean"] + smoothing * global_mean)
        / (agg["count"] + smoothing)
    )

    _target_encoding_map = agg["encoding"].to_dict()

    # Save to file for inference
    _TARGET_ENCODING_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_TARGET_ENCODING_PATH, "w", encoding="utf-8") as f:
        json.dump(_target_encoding_map, f, indent=2)

    logger.info(
        "Target encoding fitted for %d categories, saved to %s",
        len(_target_encoding_map),
        _TARGET_ENCODING_PATH,
    )

    return _target_encoding_map


def load_target_encoding() -> dict[str, float]:
    """Load previously fitted target encoding from disk."""
    global _target_encoding_map

    if _TARGET_ENCODING_PATH.exists():
        with open(_TARGET_ENCODING_PATH, "r", encoding="utf-8") as f:
            _target_encoding_map = json.load(f)
        logger.info("Target encoding loaded: %d categories", len(_target_encoding_map))
    else:
        logger.warning("No target encoding file found at %s", _TARGET_ENCODING_PATH)

    return _target_encoding_map


def apply_target_encoding(
    value: str, fallback: Optional[float] = None
) -> float:
    """Apply target encoding to a single diagnosa value.

    Args:
        value: ICD-10 code.
        fallback: Value to return if code not in map. Defaults to global mean.

    Returns:
        Encoded float value.
    """
    if value in _target_encoding_map:
        return _target_encoding_map[value]

    if fallback is not None:
        return fallback

    # Fallback to global mean of all known encodings
    if _target_encoding_map:
        return np.mean(list(_target_encoding_map.values()))

    return 0.5  # ultimate fallback


# ============================================================================
# Imputation Defaults (learned from training data)
# ============================================================================

# These will be populated by fit_imputation_defaults() during training
_imputation_defaults: dict[str, Any] = {}
_IMPUTATION_PATH = Path(__file__).parent.parent / "saved_models" / "imputation_defaults.json"


def fit_imputation_defaults(df: pd.DataFrame) -> dict[str, Any]:
    """Learn imputation defaults from training data.

    Strategy:
    - Numeric columns: median
    - Categorical columns: mode

    Args:
        df: Training DataFrame (with feature columns).

    Returns:
        Dictionary of column → default value.
    """
    global _imputation_defaults

    defaults = {}
    for col in ALL_FEATURE_COLUMNS:
        if col not in df.columns:
            continue

        if df[col].dtype in ("float64", "float32", "int64", "int32"):
            defaults[col] = float(df[col].median())
        else:
            mode_vals = df[col].mode()
            defaults[col] = mode_vals.iloc[0] if len(mode_vals) > 0 else 0

    _imputation_defaults = defaults

    # Save to file for inference
    _IMPUTATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_IMPUTATION_PATH, "w", encoding="utf-8") as f:
        json.dump(_imputation_defaults, f, indent=2)

    logger.info(
        "Imputation defaults fitted for %d features, saved to %s",
        len(_imputation_defaults),
        _IMPUTATION_PATH,
    )

    return _imputation_defaults


def load_imputation_defaults() -> dict[str, Any]:
    """Load previously fitted imputation defaults from disk."""
    global _imputation_defaults

    if _IMPUTATION_PATH.exists():
        with open(_IMPUTATION_PATH, "r", encoding="utf-8") as f:
            _imputation_defaults = json.load(f)
        logger.info("Imputation defaults loaded: %d features", len(_imputation_defaults))
    else:
        logger.warning("No imputation defaults file found at %s", _IMPUTATION_PATH)

    return _imputation_defaults


# ============================================================================
# Core Feature Extraction
# ============================================================================


def _derive_features_from_raw(claim: dict[str, Any]) -> dict[str, Any]:
    """Compute derived features from raw claim fields.

    This handles the case where raw claim data comes from the API
    (e.g., POST /ml/score-claim) and some features need to be calculated.

    Args:
        claim: Raw claim dict with fields like total_tagihan, los, etc.

    Returns:
        Dict with all computed features added.
    """
    features = dict(claim)

    # --- Biaya group ---
    total = features.get("total_tagihan", 0) or 0
    los = features.get("los", 1) or 1
    tarif = features.get("tarif_ina_cbgs", 1) or 1

    if "tagihan_per_hari" not in features or features["tagihan_per_hari"] is None:
        features["tagihan_per_hari"] = total / max(los, 1)

    if "rasio_terhadap_ina_cbgs" not in features or features["rasio_terhadap_ina_cbgs"] is None:
        features["rasio_terhadap_ina_cbgs"] = total / max(tarif, 1)

    if "tagihan_obat_ratio" not in features or features["tagihan_obat_ratio"] is None:
        features["tagihan_obat_ratio"] = 0.25  # default estimate

    if "tagihan_tindakan_ratio" not in features or features["tagihan_tindakan_ratio"] is None:
        features["tagihan_tindakan_ratio"] = 0.35  # default estimate

    # --- Klinis group ---
    diagnosa = features.get("diagnosa_utama", "")
    chapter = diagnosa[0] if diagnosa else ""

    if "diagnosa_utama_encoded" not in features or features["diagnosa_utama_encoded"] is None:
        features["diagnosa_utama_encoded"] = ICD_CHAPTER_ENCODING.get(chapter, 0)

    if "severity_score" not in features or features["severity_score"] is None:
        features["severity_score"] = CHAPTER_SEVERITY.get(chapter, 2)

    # Count secondary diagnoses
    sekunder = features.get("diagnosa_sekunder", "")
    if "jumlah_diagnosa_sekunder" not in features or features["jumlah_diagnosa_sekunder"] is None:
        if isinstance(sekunder, str) and sekunder:
            features["jumlah_diagnosa_sekunder"] = len(sekunder.split(";"))
        elif isinstance(sekunder, list):
            features["jumlah_diagnosa_sekunder"] = len(sekunder)
        else:
            features["jumlah_diagnosa_sekunder"] = 0

    # Count procedures
    prosedur = features.get("prosedur", "")
    if "jumlah_prosedur" not in features or features["jumlah_prosedur"] is None:
        if isinstance(prosedur, str) and prosedur:
            features["jumlah_prosedur"] = len(prosedur.split(";"))
        elif isinstance(prosedur, list):
            features["jumlah_prosedur"] = len(prosedur)
        else:
            features["jumlah_prosedur"] = 0

    # --- Geografis group ---
    tipe_rs = features.get("tipe_rs", "C")
    if "tipe_rs_encoded" not in features or features["tipe_rs_encoded"] is None:
        features["tipe_rs_encoded"] = TIPE_RS_ENCODING.get(tipe_rs, 2)

    provinsi = features.get("provinsi", "")
    if "provinsi_encoded" not in features or features["provinsi_encoded"] is None:
        features["provinsi_encoded"] = REGIONAL_COST_INDEX.get(provinsi, 1.0)

    if "is_regional_outlier" not in features or features["is_regional_outlier"] is None:
        features["is_regional_outlier"] = 0  # default, needs population data

    # --- Temporal group ---
    tgl_pengajuan = features.get("tgl_pengajuan", "")
    if tgl_pengajuan and isinstance(tgl_pengajuan, str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(tgl_pengajuan)
            if "bulan_pengajuan" not in features or features["bulan_pengajuan"] is None:
                features["bulan_pengajuan"] = dt.month
            if "hari_pengajuan_dalam_bulan" not in features or features["hari_pengajuan_dalam_bulan"] is None:
                features["hari_pengajuan_dalam_bulan"] = dt.day
            if "is_end_of_month" not in features or features["is_end_of_month"] is None:
                features["is_end_of_month"] = 1 if dt.day >= 25 else 0
        except (ValueError, TypeError):
            pass

    # Defaults for temporal if still missing
    for col, default in [
        ("bulan_pengajuan", 6),
        ("hari_pengajuan_dalam_bulan", 15),
        ("is_end_of_month", 0),
    ]:
        if col not in features or features[col] is None:
            features[col] = default

    # --- Komparatif group (defaults — need population context for real values) ---
    for col, default in [
        ("percentile_tagihan_per_diagnosa", 0.5),
        ("percentile_los_per_diagnosa", 0.5),
        ("z_score_tagihan", 0.0),
    ]:
        if col not in features or features[col] is None:
            features[col] = default

    # --- Historis RS group (defaults — need historical data for real values) ---
    for col, default in [
        ("rs_avg_risk_score_30d", 35.0),
        ("rs_pending_rate_30d", 0.15),
        ("rs_total_claims_30d", 150),
    ]:
        if col not in features or features[col] is None:
            features[col] = default

    return features


def _impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Apply imputation for missing values using learned defaults.

    Args:
        df: DataFrame with potential missing values.

    Returns:
        DataFrame with missing values filled.
    """
    defaults = _imputation_defaults if _imputation_defaults else {}

    for col in ALL_FEATURE_COLUMNS:
        if col not in df.columns:
            # Add missing columns with defaults
            df[col] = defaults.get(col, 0)
        elif df[col].isna().any():
            fill_val = defaults.get(col, 0)
            df[col] = df[col].fillna(fill_val)

    return df


# ============================================================================
# Public API
# ============================================================================


def extract_features(claim: Union[dict, list[dict]]) -> pd.DataFrame:
    """Extract ML features from one or more raw claim dicts.

    This is the main entry point used by the ML Engine API endpoint
    POST /ml/score-claim. It handles:
    1. Computing derived features from raw data
    2. Applying encoding (ordinal for tipe_rs, target for diagnosa_utama)
    3. Imputing missing values
    4. Returning a DataFrame with exactly ALL_FEATURE_COLUMNS

    Args:
        claim: A single claim dict or list of claim dicts.
            Expected raw fields: total_tagihan, los, tarif_ina_cbgs,
            diagnosa_utama, tipe_rs, provinsi, tgl_pengajuan, etc.

    Returns:
        pd.DataFrame with columns matching ALL_FEATURE_COLUMNS.
        One row per input claim.
    """
    if isinstance(claim, dict):
        claims = [claim]
    else:
        claims = claim

    # Step 1: Derive features from raw data
    processed = [_derive_features_from_raw(c) for c in claims]
    df = pd.DataFrame(processed)

    # Step 2: Apply target encoding for diagnosa_utama (replaces chapter encoding)
    if _target_encoding_map and "diagnosa_utama" in df.columns:
        df["diagnosa_utama_encoded"] = df["diagnosa_utama"].apply(
            apply_target_encoding
        )

    # Step 3: Impute missing values
    df = _impute_missing(df)

    # Step 4: Select only feature columns in the correct order
    result = df[ALL_FEATURE_COLUMNS].copy()

    # Ensure all columns are numeric
    for col in result.columns:
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0)

    return result


def extract_features_from_dataframe(
    df: pd.DataFrame,
    fit_encodings: bool = False,
) -> pd.DataFrame:
    """Extract features from a full DataFrame (e.g., training CSV).

    Unlike extract_features() which works on raw dicts from the API,
    this operates on a DataFrame that may already have pre-computed columns
    (e.g., from the synthetic data generator).

    Args:
        df: Input DataFrame (from synthetic_claims.csv or similar).
        fit_encodings: If True, fit target encoding and imputation defaults
            from this data (use during training). If False, use previously
            fitted values (use during inference).

    Returns:
        Tuple of (features_df, labels_series) if LABEL_COLUMN exists,
        otherwise just features_df.
    """
    work_df = df.copy()

    # Fit or load target encoding
    if fit_encodings and LABEL_COLUMN in work_df.columns:
        if "diagnosa_utama" in work_df.columns:
            fit_target_encoding(work_df, "diagnosa_utama", LABEL_COLUMN)
            work_df["diagnosa_utama_encoded"] = work_df["diagnosa_utama"].apply(
                apply_target_encoding
            )
    elif not _target_encoding_map:
        load_target_encoding()
        if _target_encoding_map and "diagnosa_utama" in work_df.columns:
            work_df["diagnosa_utama_encoded"] = work_df["diagnosa_utama"].apply(
                apply_target_encoding
            )

    # Ensure all feature columns exist with derived values
    for col in ALL_FEATURE_COLUMNS:
        if col not in work_df.columns:
            work_df[col] = 0

    # Fit or load imputation defaults
    if fit_encodings:
        fit_imputation_defaults(work_df[ALL_FEATURE_COLUMNS])
    elif not _imputation_defaults:
        load_imputation_defaults()

    # Apply imputation
    work_df = _impute_missing(work_df)

    # Select feature columns
    features = work_df[ALL_FEATURE_COLUMNS].copy()

    # Ensure numeric
    for col in features.columns:
        features[col] = pd.to_numeric(features[col], errors="coerce").fillna(0)

    return features
