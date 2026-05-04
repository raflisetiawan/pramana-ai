"""
Pramana AI — Generator Data Sintetis Klaim BPJS
=================================================

Script ini membangkitkan 10.000 data klaim sintetis untuk keperluan
training model ML risk scoring.

Distribusi target:
- 80% klaim "wajar" (is_anomaly = 0)
- 20% klaim "anomali" (is_anomaly = 1)

Fitur yang di-generate sesuai SPEC.md bagian 7 (FEATURE_GROUPS):
- Biaya: total_tagihan, tagihan_per_hari, tagihan_obat_ratio,
         tagihan_tindakan_ratio, rasio_terhadap_ina_cbgs
- Klinis: los, diagnosa_utama_encoded, jumlah_diagnosa_sekunder,
          jumlah_prosedur, severity_score
- Geografis: tipe_rs_encoded, provinsi_encoded, is_regional_outlier
- Temporal: bulan_pengajuan, hari_pengajuan_dalam_bulan, is_end_of_month
- Komparatif: percentile_tagihan_per_diagnosa, percentile_los_per_diagnosa,
              z_score_tagihan
- Historis RS: rs_avg_risk_score_30d, rs_pending_rate_30d, rs_total_claims_30d

Rule labeling anomali (Task 2.1.2):
1. rasio_terhadap_ina_cbgs > 1.5 → anomali
2. tagihan_per_hari > percentile_95 untuk diagnosa yang sama → anomali
3. los < 1 untuk diagnosa berat (CHF, AMI) → anomali
4. kombinasi diagnosa + prosedur yang tidak lazim → anomali

Usage:
    python -m services.ml-engine.app.data.generate_synthetic_claims
    # atau
    python services/ml-engine/app/data/generate_synthetic_claims.py
"""

import argparse
import hashlib
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure imports work regardless of how the script is invoked
_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

from diagnosa_profiles import (
    AVAILABLE_PROCEDURES,
    DIAGNOSA_PROFILES,
    HOSPITAL_PROFILES,
    ICD_CHAPTER_ENCODING,
    REGIONAL_COST_INDEX,
    UNUSUAL_PROCEDURE_MAP,
    DiagnosaProfile,
)

# ============================================================================
# Constants
# ============================================================================

TOTAL_SAMPLES = 10_000
NORMAL_RATIO = 0.80
ANOMALY_RATIO = 0.20

TIPE_RS_ENCODING = {"A": 4, "B": 3, "C": 2, "D": 1}

# Date range for synthetic claims (1 year window)
DATE_START = date(2023, 1, 1)
DATE_END = date(2023, 12, 31)

# Seed for reproducibility
RANDOM_SEED = 42


# ============================================================================
# Helper Functions
# ============================================================================


def _hash_noka(noka: str) -> str:
    """Hash nomor kartu BPJS with SHA-256 (privacy compliance)."""
    return hashlib.sha256(noka.encode("utf-8")).hexdigest()


def _random_date(start: date, end: date, rng: np.random.Generator) -> date:
    """Generate a random date between start and end."""
    delta = (end - start).days
    random_days = int(rng.integers(0, delta + 1))
    return start + timedelta(days=random_days)


def _get_tarif_for_tipe(profile: DiagnosaProfile, tipe_rs: str) -> float:
    """Get INA-CBGs tariff for a given hospital type."""
    tarif_map = {
        "A": profile.tarif_ina_cbgs_a,
        "B": profile.tarif_ina_cbgs_b,
        "C": profile.tarif_ina_cbgs_c,
        "D": profile.tarif_ina_cbgs_d,
    }
    return tarif_map.get(tipe_rs, profile.tarif_ina_cbgs_b)


def _compute_regional_index(provinsi: str) -> float:
    """Get regional cost index for a province."""
    return REGIONAL_COST_INDEX.get(provinsi, 1.0)


# ============================================================================
# Claim Generator — Normal Claims
# ============================================================================


def generate_normal_claim(
    rng: np.random.Generator,
    hospital: dict,
    profile: DiagnosaProfile,
    claim_date: date,
) -> dict:
    """Generate a single normal (non-anomalous) claim.

    Normal claims have:
    - rasio_terhadap_ina_cbgs between 0.7 and 1.3
    - tagihan_per_hari within normal range for the diagnosa
    - LOS consistent with diagnosa severity
    - Procedures consistent with diagnosa
    """
    tipe_rs = hospital["tipe_rs"]
    provinsi = hospital["provinsi"]
    regional_idx = _compute_regional_index(provinsi)

    # --- LOS ---
    los = max(
        profile.los_min,
        min(
            profile.los_max,
            int(rng.normal(profile.los_mean, profile.los_std)),
        ),
    )

    # --- Tarif INA-CBGs ---
    tarif_ina_cbgs = _get_tarif_for_tipe(profile, tipe_rs) * regional_idx
    # Add some natural variation (±10%)
    tarif_ina_cbgs *= rng.uniform(0.90, 1.10)

    # --- Total tagihan (normal: within 0.7-1.3 of INA-CBGs) ---
    rasio = rng.uniform(0.75, 1.30)
    total_tagihan = tarif_ina_cbgs * rasio

    # --- Breakdown biaya ---
    tagihan_obat_ratio = rng.uniform(0.15, 0.40)
    tagihan_tindakan_ratio = rng.uniform(0.20, 0.50)
    # Ensure ratios don't exceed 1.0
    remaining = 1.0 - tagihan_obat_ratio - tagihan_tindakan_ratio
    if remaining < 0.10:
        tagihan_obat_ratio = 0.25
        tagihan_tindakan_ratio = 0.35

    # --- Derived features ---
    tagihan_per_hari = total_tagihan / max(los, 1)
    rasio_terhadap_ina_cbgs = total_tagihan / max(tarif_ina_cbgs, 1)

    # --- Diagnosa sekunder ---
    num_secondary = rng.choice([0, 1, 2, 3], p=[0.15, 0.35, 0.35, 0.15])
    secondary_codes = []
    if num_secondary > 0 and profile.common_secondary:
        secondary_codes = list(
            rng.choice(
                profile.common_secondary,
                size=min(num_secondary, len(profile.common_secondary)),
                replace=False,
            )
        )

    # --- Prosedur (lazim/sesuai) ---
    if profile.common_procedures:
        num_proc = rng.choice(
            [0, 1, 2], p=[0.20, 0.50, 0.30]
        )
        procedures = list(
            rng.choice(
                profile.common_procedures,
                size=min(num_proc, len(profile.common_procedures)),
                replace=False,
            )
        )
    else:
        procedures = []

    # --- Temporal features ---
    bulan_pengajuan = claim_date.month
    hari_pengajuan = claim_date.day
    is_end_of_month = 1 if hari_pengajuan >= 25 else 0

    return {
        "claim_id": str(uuid.uuid4()),
        "no_sep": f"SEP{claim_date.strftime('%Y%m%d')}{rng.integers(100000, 999999)}",
        "noka_hash": _hash_noka(f"000{rng.integers(1000000000, 9999999999)}"),
        "kode_rs": hospital["kode_rs"],
        "nama_rs": hospital["nama_rs"],
        "tipe_rs": tipe_rs,
        "provinsi": provinsi,
        "kabupaten": hospital["kabupaten"],
        "diagnosa_utama": profile.kode,
        "diagnosa_sekunder": ";".join(secondary_codes),
        "prosedur": ";".join(procedures),
        "los": los,
        "total_tagihan": round(total_tagihan, 2),
        "tarif_ina_cbgs": round(tarif_ina_cbgs, 2),
        "tagihan_per_hari": round(tagihan_per_hari, 2),
        "tagihan_obat_ratio": round(tagihan_obat_ratio, 4),
        "tagihan_tindakan_ratio": round(tagihan_tindakan_ratio, 4),
        "rasio_terhadap_ina_cbgs": round(rasio_terhadap_ina_cbgs, 4),
        "diagnosa_utama_encoded": ICD_CHAPTER_ENCODING.get(profile.chapter, 0),
        "jumlah_diagnosa_sekunder": len(secondary_codes),
        "jumlah_prosedur": len(procedures),
        "severity_score": profile.severity_score,
        "tipe_rs_encoded": TIPE_RS_ENCODING[tipe_rs],
        "provinsi_encoded": round(regional_idx, 4),
        "bulan_pengajuan": bulan_pengajuan,
        "hari_pengajuan_dalam_bulan": hari_pengajuan,
        "is_end_of_month": is_end_of_month,
        "tgl_masuk": (claim_date - timedelta(days=los)).isoformat(),
        "tgl_pulang": claim_date.isoformat(),
        "tgl_pengajuan": claim_date.isoformat(),
        "anomaly_reason": "",
        "is_anomaly": 0,
    }


# ============================================================================
# Claim Generator — Anomalous Claims
# ============================================================================


def generate_anomaly_claim(
    rng: np.random.Generator,
    hospital: dict,
    profile: DiagnosaProfile,
    claim_date: date,
    anomaly_type: str,
) -> dict:
    """Generate a single anomalous claim.

    Anomaly types:
    - "high_ratio": rasio_terhadap_ina_cbgs > 1.5
    - "high_per_day": tagihan_per_hari > p95
    - "short_los": LOS < 1 hari untuk diagnosa berat
    - "unusual_procedure": prosedur tidak lazim untuk diagnosa
    """
    # Start with a normal claim, then inject anomaly
    claim = generate_normal_claim(rng, hospital, profile, claim_date)
    claim["is_anomaly"] = 1

    if anomaly_type == "high_ratio":
        # rasio_terhadap_ina_cbgs > 1.5 (biasanya 1.5 - 3.0)
        rasio = rng.uniform(1.55, 3.0)
        claim["total_tagihan"] = round(
            claim["tarif_ina_cbgs"] * rasio, 2
        )
        claim["rasio_terhadap_ina_cbgs"] = round(rasio, 4)
        claim["tagihan_per_hari"] = round(
            claim["total_tagihan"] / max(claim["los"], 1), 2
        )
        claim["anomaly_reason"] = "high_ratio"

    elif anomaly_type == "high_per_day":
        # Inflate tagihan per hari jauh di atas normal
        # Normal tagihan_per_hari ~ tarif / los
        normal_per_day = claim["tarif_ina_cbgs"] / max(profile.los_mean, 1)
        inflated_per_day = normal_per_day * rng.uniform(2.5, 5.0)
        claim["tagihan_per_hari"] = round(inflated_per_day, 2)
        claim["total_tagihan"] = round(
            inflated_per_day * max(claim["los"], 1), 2
        )
        claim["rasio_terhadap_ina_cbgs"] = round(
            claim["total_tagihan"] / max(claim["tarif_ina_cbgs"], 1), 4
        )
        claim["anomaly_reason"] = "high_per_day"

    elif anomaly_type == "short_los":
        # LOS < 1 hari (0 hari) untuk diagnosa berat
        claim["los"] = 0
        claim["tagihan_per_hari"] = claim["total_tagihan"]  # all in 1 day
        # Keep total tagihan roughly normal to make it trickier
        claim["tgl_masuk"] = claim["tgl_pulang"]
        claim["anomaly_reason"] = "short_los_severe"

    elif anomaly_type == "unusual_procedure":
        # Prosedur tidak lazim untuk diagnosa ini
        unusual_procs = UNUSUAL_PROCEDURE_MAP.get(profile.kode, [])
        if unusual_procs:
            num_unusual = rng.choice([1, 2], p=[0.7, 0.3])
            chosen_unusual = list(
                rng.choice(
                    unusual_procs,
                    size=min(num_unusual, len(unusual_procs)),
                    replace=False,
                )
            )
            # Combine with normal procedures
            existing = claim["prosedur"].split(";") if claim["prosedur"] else []
            all_procs = existing + chosen_unusual
            claim["prosedur"] = ";".join(all_procs)
            claim["jumlah_prosedur"] = len(all_procs)
            # Unusual procedures also tend to inflate costs
            cost_inflation = rng.uniform(1.2, 1.8)
            claim["total_tagihan"] = round(
                claim["total_tagihan"] * cost_inflation, 2
            )
            claim["tagihan_per_hari"] = round(
                claim["total_tagihan"] / max(claim["los"], 1), 2
            )
            claim["rasio_terhadap_ina_cbgs"] = round(
                claim["total_tagihan"] / max(claim["tarif_ina_cbgs"], 1), 4
            )
            claim["tagihan_tindakan_ratio"] = round(
                rng.uniform(0.45, 0.70), 4
            )
        claim["anomaly_reason"] = "unusual_procedure"

    return claim


# ============================================================================
# RS Historical Features Generator
# ============================================================================


def add_hospital_historical_features(
    df: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    """Add hospital-level historical features (historis_rs group).

    These simulate the RS track record over the past 30 days:
    - rs_avg_risk_score_30d
    - rs_pending_rate_30d
    - rs_total_claims_30d
    """
    # Generate base historical stats per RS
    rs_stats = {}
    for hospital in HOSPITAL_PROFILES:
        kode = hospital["kode_rs"]
        rs_stats[kode] = {
            "rs_avg_risk_score_30d": round(rng.uniform(15, 55), 2),
            "rs_pending_rate_30d": round(rng.uniform(0.05, 0.30), 4),
            "rs_total_claims_30d": int(rng.integers(50, 400)),
        }

    df["rs_avg_risk_score_30d"] = df["kode_rs"].map(
        lambda k: rs_stats.get(k, {}).get("rs_avg_risk_score_30d", 30.0)
    )
    df["rs_pending_rate_30d"] = df["kode_rs"].map(
        lambda k: rs_stats.get(k, {}).get("rs_pending_rate_30d", 0.15)
    )
    df["rs_total_claims_30d"] = df["kode_rs"].map(
        lambda k: rs_stats.get(k, {}).get("rs_total_claims_30d", 150)
    )

    # Anomalous RS: slightly higher avg risk score and pending rate
    anomaly_mask = df["is_anomaly"] == 1
    # Add noise so it's not a perfect signal
    df.loc[anomaly_mask, "rs_avg_risk_score_30d"] += rng.uniform(
        5, 15, size=anomaly_mask.sum()
    )
    df.loc[anomaly_mask, "rs_pending_rate_30d"] += rng.uniform(
        0.05, 0.12, size=anomaly_mask.sum()
    )

    return df


# ============================================================================
# Comparative Features Generator
# ============================================================================


def add_comparative_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add comparative features (komparatif group).

    Computed relative to other claims with the same diagnosa and RS type:
    - percentile_tagihan_per_diagnosa
    - percentile_los_per_diagnosa
    - z_score_tagihan
    """
    # Percentile of tagihan within same diagnosa + RS type group
    df["percentile_tagihan_per_diagnosa"] = df.groupby(
        ["diagnosa_utama", "tipe_rs"]
    )["total_tagihan"].rank(pct=True)

    # Percentile of LOS within same diagnosa group
    df["percentile_los_per_diagnosa"] = df.groupby("diagnosa_utama")[
        "los"
    ].rank(pct=True)

    # Z-score of tagihan within same RS type
    group_stats = df.groupby("tipe_rs")["total_tagihan"].agg(["mean", "std"])
    df = df.merge(
        group_stats, left_on="tipe_rs", right_index=True, how="left"
    )
    df["z_score_tagihan"] = (df["total_tagihan"] - df["mean"]) / df[
        "std"
    ].replace(0, 1)
    df.drop(columns=["mean", "std"], inplace=True)

    # Regional outlier: is tagihan > 2 std above regional mean?
    regional_stats = df.groupby("provinsi")["total_tagihan"].agg(
        ["mean", "std"]
    )
    df = df.merge(
        regional_stats,
        left_on="provinsi",
        right_index=True,
        how="left",
        suffixes=("", "_regional"),
    )
    df["is_regional_outlier"] = (
        (df["total_tagihan"] > df["mean"] + 2 * df["std"]).astype(int)
    )
    df.drop(columns=["mean", "std"], inplace=True)

    # Round numeric columns
    for col in [
        "percentile_tagihan_per_diagnosa",
        "percentile_los_per_diagnosa",
        "z_score_tagihan",
    ]:
        df[col] = df[col].round(4)

    return df


# ============================================================================
# Main Generator
# ============================================================================


def generate_dataset(
    n_samples: int = TOTAL_SAMPLES,
    seed: int = RANDOM_SEED,
    anomaly_ratio: float = ANOMALY_RATIO,
) -> pd.DataFrame:
    """Generate the full synthetic claims dataset.

    Args:
        n_samples: Total number of claims to generate.
        seed: Random seed for reproducibility.
        anomaly_ratio: Fraction of anomalous claims (default 0.20).

    Returns:
        DataFrame with all features as specified in SPEC.md section 7.
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    n_anomaly = int(n_samples * anomaly_ratio)
    n_normal = n_samples - n_anomaly

    # Build weighted diagnosa selection
    diag_codes = list(DIAGNOSA_PROFILES.keys())
    diag_weights = np.array(
        [DIAGNOSA_PROFILES[k].frequency_weight for k in diag_codes]
    )
    diag_weights = diag_weights / diag_weights.sum()

    # Anomaly types and their weights
    anomaly_types = ["high_ratio", "high_per_day", "short_los", "unusual_procedure"]
    anomaly_weights = np.array([0.35, 0.25, 0.15, 0.25])

    claims: list[dict] = []

    print(f"Generating {n_normal} normal claims...")
    for i in range(n_normal):
        hospital = rng.choice(HOSPITAL_PROFILES)
        diag_code = rng.choice(diag_codes, p=diag_weights)
        profile = DIAGNOSA_PROFILES[diag_code]
        claim_date = _random_date(DATE_START, DATE_END, rng)
        claim = generate_normal_claim(rng, hospital, profile, claim_date)
        claims.append(claim)

        if (i + 1) % 2000 == 0:
            print(f"  ... {i + 1}/{n_normal} normal claims generated")

    print(f"Generating {n_anomaly} anomaly claims...")
    for i in range(n_anomaly):
        hospital = rng.choice(HOSPITAL_PROFILES)
        diag_code = rng.choice(diag_codes, p=diag_weights)
        profile = DIAGNOSA_PROFILES[diag_code]
        claim_date = _random_date(DATE_START, DATE_END, rng)

        # Select anomaly type
        atype = rng.choice(anomaly_types, p=anomaly_weights)

        # "short_los" only applicable to severe diagnosa
        if atype == "short_los" and not profile.is_severe:
            atype = "high_ratio"  # fallback

        # "unusual_procedure" needs mapping to exist
        if atype == "unusual_procedure" and profile.kode not in UNUSUAL_PROCEDURE_MAP:
            atype = "high_ratio"  # fallback

        claim = generate_anomaly_claim(rng, hospital, profile, claim_date, atype)
        claims.append(claim)

        if (i + 1) % 500 == 0:
            print(f"  ... {i + 1}/{n_anomaly} anomaly claims generated")

    # Build DataFrame
    df = pd.DataFrame(claims)

    # Shuffle to mix normal and anomaly claims
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    print("Adding hospital historical features...")
    df = add_hospital_historical_features(df, rng)

    print("Adding comparative features...")
    df = add_comparative_features(df)

    # Reorder columns for clarity
    column_order = [
        # Identifiers
        "claim_id",
        "no_sep",
        "noka_hash",
        "kode_rs",
        "nama_rs",
        # Raw data
        "diagnosa_utama",
        "diagnosa_sekunder",
        "prosedur",
        "tgl_masuk",
        "tgl_pulang",
        "tgl_pengajuan",
        # FEATURE_GROUPS — biaya
        "total_tagihan",
        "tarif_ina_cbgs",
        "tagihan_per_hari",
        "tagihan_obat_ratio",
        "tagihan_tindakan_ratio",
        "rasio_terhadap_ina_cbgs",
        # FEATURE_GROUPS — klinis
        "los",
        "diagnosa_utama_encoded",
        "jumlah_diagnosa_sekunder",
        "jumlah_prosedur",
        "severity_score",
        # FEATURE_GROUPS — geografis
        "tipe_rs",
        "tipe_rs_encoded",
        "provinsi",
        "provinsi_encoded",
        "is_regional_outlier",
        # FEATURE_GROUPS — temporal
        "bulan_pengajuan",
        "hari_pengajuan_dalam_bulan",
        "is_end_of_month",
        # FEATURE_GROUPS — komparatif
        "percentile_tagihan_per_diagnosa",
        "percentile_los_per_diagnosa",
        "z_score_tagihan",
        # FEATURE_GROUPS — historis_rs
        "rs_avg_risk_score_30d",
        "rs_pending_rate_30d",
        "rs_total_claims_30d",
        # Label
        "is_anomaly",
        "anomaly_reason",
    ]

    # Keep only columns that exist
    column_order = [c for c in column_order if c in df.columns]
    df = df[column_order]

    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print a summary of the generated dataset."""
    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Total samples:     {len(df):,}")
    print(f"Normal claims:     {(df['is_anomaly'] == 0).sum():,} "
          f"({(df['is_anomaly'] == 0).mean():.1%})")
    print(f"Anomaly claims:    {(df['is_anomaly'] == 1).sum():,} "
          f"({(df['is_anomaly'] == 1).mean():.1%})")
    print(f"Features:          {len(df.columns)}")
    print()

    print("--- Anomaly Breakdown ---")
    if "anomaly_reason" in df.columns:
        anomaly_df = df[df["is_anomaly"] == 1]
        print(anomaly_df["anomaly_reason"].value_counts().to_string())
    print()

    print("--- Diagnosa Distribution (Top 10) ---")
    print(df["diagnosa_utama"].value_counts().head(10).to_string())
    print()

    print("--- RS Type Distribution ---")
    print(df["tipe_rs"].value_counts().sort_index().to_string())
    print()

    print("--- Key Statistics ---")
    stats_cols = [
        "total_tagihan",
        "tagihan_per_hari",
        "rasio_terhadap_ina_cbgs",
        "los",
        "severity_score",
    ]
    print(df[stats_cols].describe().round(2).to_string())
    print()

    # Compare normal vs anomaly
    print("--- Normal vs Anomaly (Mean) ---")
    comparison = df.groupby("is_anomaly")[stats_cols].mean().round(2)
    comparison.index = comparison.index.map({0: "Normal", 1: "Anomaly"})
    print(comparison.to_string())
    print("=" * 60)


# ============================================================================
# Entry Point
# ============================================================================


def main() -> None:
    """Generate synthetic claims and save to CSV."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic BPJS claims for ML training"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=TOTAL_SAMPLES,
        help=f"Total number of samples to generate (default: {TOTAL_SAMPLES})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: tests/fixtures/synthetic_claims.csv)",
    )
    parser.add_argument(
        "--anomaly-ratio",
        type=float,
        default=ANOMALY_RATIO,
        help=f"Fraction of anomalous claims (default: {ANOMALY_RATIO})",
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Default: project_root/tests/fixtures/synthetic_claims.csv
        project_root = _THIS_DIR.parent.parent.parent.parent
        output_path = project_root / "tests" / "fixtures" / "synthetic_claims.csv"

    # Generate dataset
    print(f"[*] Generating {args.samples:,} synthetic claims (seed={args.seed})...")
    print(f"    Anomaly ratio: {args.anomaly_ratio:.0%}")
    print()

    df = generate_dataset(
        n_samples=args.samples,
        seed=args.seed,
        anomaly_ratio=args.anomaly_ratio,
    )

    # Print summary
    print_summary(df)

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n[OK] Dataset saved to: {output_path}")
    print(f"     File size: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    main()
