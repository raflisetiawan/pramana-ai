"""
Pramana AI — Unit Test: Feature Extractor (Task 2.5.1)
=======================================================

Tests untuk app/features/extractor.py termasuk:
- Fungsi extract_features() dengan input normal
- Edge case: missing values / field kosong
- Encoding: ordinal tipe_rs, target encoding diagnosa_utama
- Derived features: tagihan_per_hari, rasio_terhadap_ina_cbgs
- Batch extraction dari DataFrame
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure ML engine imports work
_ML_ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "services" / "ml-engine"
sys.path.insert(0, str(_ML_ENGINE_ROOT))

from app.features.extractor import (
    ALL_FEATURE_COLUMNS,
    FEATURE_GROUPS,
    LABEL_COLUMN,
    ICD_CHAPTER_ENCODING,
    TIPE_RS_ENCODING,
    extract_features,
    extract_features_from_dataframe,
    fit_imputation_defaults,
    fit_target_encoding,
    load_imputation_defaults,
    load_target_encoding,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def normal_claim() -> dict:
    """Klaim normal dengan semua field lengkap."""
    return {
        "total_tagihan": 5_500_000,
        "los": 4,
        "tarif_ina_cbgs": 5_200_000,
        "diagnosa_utama": "I10",
        "diagnosa_sekunder": "E11.9;I25.0",
        "prosedur": "88.72;99.04",
        "tipe_rs": "B",
        "provinsi": "Jawa Timur",
        "tgl_pengajuan": "2024-01-15",
        "tgl_masuk": "2024-01-11",
        "tgl_pulang": "2024-01-15",
    }


@pytest.fixture
def minimal_claim() -> dict:
    """Klaim dengan hanya field wajib (missing banyak)."""
    return {
        "total_tagihan": 3_000_000,
        "los": 2,
        "diagnosa_utama": "A09",
        "tipe_rs": "C",
    }


@pytest.fixture
def claim_with_nulls() -> dict:
    """Klaim dengan field None/kosong (edge case)."""
    return {
        "total_tagihan": 7_000_000,
        "los": 0,
        "tarif_ina_cbgs": None,
        "diagnosa_utama": "I50.0",
        "diagnosa_sekunder": "",
        "prosedur": None,
        "tipe_rs": "A",
        "provinsi": "",
        "tgl_pengajuan": None,
        "bulan_pengajuan": None,
    }


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """DataFrame kecil untuk test batch extraction."""
    return pd.DataFrame([
        {
            "total_tagihan": 5_000_000, "los": 3, "tarif_ina_cbgs": 4_800_000,
            "diagnosa_utama": "I10", "tipe_rs": "B", "provinsi": "Jawa Timur",
            "is_anomaly": 0,
        },
        {
            "total_tagihan": 15_000_000, "los": 2, "tarif_ina_cbgs": 5_000_000,
            "diagnosa_utama": "I50.0", "tipe_rs": "A", "provinsi": "DKI Jakarta",
            "is_anomaly": 1,
        },
        {
            "total_tagihan": 2_500_000, "los": 5, "tarif_ina_cbgs": 3_000_000,
            "diagnosa_utama": "A09", "tipe_rs": "D", "provinsi": "Jawa Tengah",
            "is_anomaly": 0,
        },
    ])


# ============================================================================
# Tests: extract_features() — Single Claim
# ============================================================================


class TestExtractFeaturesSingle:
    """Tests untuk extract_features() dengan input dict tunggal."""

    def test_normal_claim_returns_dataframe(self, normal_claim):
        """Hasil harus berupa DataFrame dengan 1 baris."""
        result = extract_features(normal_claim)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_normal_claim_has_all_columns(self, normal_claim):
        """Semua kolom di ALL_FEATURE_COLUMNS harus ada."""
        result = extract_features(normal_claim)
        for col in ALL_FEATURE_COLUMNS:
            assert col in result.columns, f"Missing column: {col}"

    def test_column_count_matches(self, normal_claim):
        """Jumlah kolom harus tepat 22 (sesuai FEATURE_GROUPS)."""
        result = extract_features(normal_claim)
        assert result.shape[1] == len(ALL_FEATURE_COLUMNS)

    def test_all_values_numeric(self, normal_claim):
        """Semua nilai harus numerik (no strings, no NaN)."""
        result = extract_features(normal_claim)
        for col in result.columns:
            assert pd.api.types.is_numeric_dtype(result[col]), f"Non-numeric: {col}"
            assert not result[col].isna().any(), f"NaN found in: {col}"

    def test_derived_tagihan_per_hari(self, normal_claim):
        """tagihan_per_hari = total_tagihan / los."""
        result = extract_features(normal_claim)
        expected = normal_claim["total_tagihan"] / normal_claim["los"]
        assert abs(result["tagihan_per_hari"].iloc[0] - expected) < 1.0

    def test_derived_rasio_ina_cbgs(self, normal_claim):
        """rasio_terhadap_ina_cbgs = total_tagihan / tarif_ina_cbgs."""
        result = extract_features(normal_claim)
        expected = normal_claim["total_tagihan"] / normal_claim["tarif_ina_cbgs"]
        assert abs(result["rasio_terhadap_ina_cbgs"].iloc[0] - expected) < 0.01

    def test_tipe_rs_encoding(self, normal_claim):
        """tipe_rs 'B' harus di-encode jadi 3."""
        result = extract_features(normal_claim)
        assert result["tipe_rs_encoded"].iloc[0] == TIPE_RS_ENCODING["B"]

    def test_diagnosa_utama_encoding(self, normal_claim):
        """diagnosa_utama 'I10' chapter 'I' harus punya encoding."""
        result = extract_features(normal_claim)
        val = result["diagnosa_utama_encoded"].iloc[0]
        assert val > 0  # should have a non-zero encoding

    def test_jumlah_diagnosa_sekunder(self, normal_claim):
        """'E11.9;I25.0' → jumlah_diagnosa_sekunder = 2."""
        result = extract_features(normal_claim)
        assert result["jumlah_diagnosa_sekunder"].iloc[0] == 2

    def test_jumlah_prosedur(self, normal_claim):
        """'88.72;99.04' → jumlah_prosedur = 2."""
        result = extract_features(normal_claim)
        assert result["jumlah_prosedur"].iloc[0] == 2

    def test_temporal_bulan(self, normal_claim):
        """tgl_pengajuan '2024-01-15' → bulan = 1."""
        result = extract_features(normal_claim)
        assert result["bulan_pengajuan"].iloc[0] == 1

    def test_temporal_hari(self, normal_claim):
        """tgl_pengajuan '2024-01-15' → hari = 15."""
        result = extract_features(normal_claim)
        assert result["hari_pengajuan_dalam_bulan"].iloc[0] == 15

    def test_temporal_not_end_of_month(self, normal_claim):
        """Hari 15 bukan akhir bulan."""
        result = extract_features(normal_claim)
        assert result["is_end_of_month"].iloc[0] == 0


# ============================================================================
# Tests: Missing Values / Edge Cases
# ============================================================================


class TestMissingValues:
    """Tests untuk handling missing values dan edge case."""

    def test_minimal_claim_no_errors(self, minimal_claim):
        """Klaim minimal (field opsional kosong) tidak boleh error."""
        result = extract_features(minimal_claim)
        assert len(result) == 1
        assert not result.isna().any().any()

    def test_null_fields_imputed(self, claim_with_nulls):
        """Field None harus di-impute, bukan NaN."""
        result = extract_features(claim_with_nulls)
        assert not result.isna().any().any()

    def test_los_zero_no_division_error(self, claim_with_nulls):
        """LOS = 0 tidak boleh menyebabkan ZeroDivisionError."""
        result = extract_features(claim_with_nulls)
        assert np.isfinite(result["tagihan_per_hari"].iloc[0])

    def test_empty_diagnosa_sekunder(self, claim_with_nulls):
        """diagnosa_sekunder kosong → jumlah = 0."""
        result = extract_features(claim_with_nulls)
        assert result["jumlah_diagnosa_sekunder"].iloc[0] == 0

    def test_none_prosedur(self, claim_with_nulls):
        """prosedur None → jumlah = 0."""
        result = extract_features(claim_with_nulls)
        assert result["jumlah_prosedur"].iloc[0] == 0

    def test_missing_provinsi_default_index(self, claim_with_nulls):
        """Provinsi kosong → default regional index 1.0."""
        result = extract_features(claim_with_nulls)
        assert result["provinsi_encoded"].iloc[0] == 1.0

    def test_missing_tgl_pengajuan_defaults(self, claim_with_nulls):
        """tgl_pengajuan None → defaults applied."""
        result = extract_features(claim_with_nulls)
        assert result["bulan_pengajuan"].iloc[0] > 0
        assert result["hari_pengajuan_dalam_bulan"].iloc[0] > 0

    def test_empty_dict_no_crash(self):
        """Claim dict kosong (hanya required fields) tidak crash."""
        claim = {"total_tagihan": 0, "los": 0, "diagnosa_utama": "", "tipe_rs": "C"}
        result = extract_features(claim)
        assert len(result) == 1

    def test_batch_list_input(self, normal_claim, minimal_claim):
        """extract_features() menerima list of dicts."""
        result = extract_features([normal_claim, minimal_claim])
        assert len(result) == 2
        assert result.shape[1] == len(ALL_FEATURE_COLUMNS)


# ============================================================================
# Tests: Batch DataFrame Extraction
# ============================================================================


class TestDataFrameExtraction:
    """Tests untuk extract_features_from_dataframe()."""

    def test_batch_returns_correct_shape(self, sample_dataframe):
        """Hasil harus punya jumlah baris sama dan kolom = 22."""
        result = extract_features_from_dataframe(sample_dataframe, fit_encodings=True)
        assert len(result) == len(sample_dataframe)
        assert result.shape[1] == len(ALL_FEATURE_COLUMNS)

    def test_fit_encodings_creates_target_encoding(self, sample_dataframe):
        """fit_encodings=True harus membuat target encoding."""
        result = extract_features_from_dataframe(sample_dataframe, fit_encodings=True)
        # diagnosa_utama_encoded should vary across different diagnoses
        unique_vals = result["diagnosa_utama_encoded"].nunique()
        assert unique_vals >= 1

    def test_no_nan_in_output(self, sample_dataframe):
        """Output tidak boleh ada NaN."""
        result = extract_features_from_dataframe(sample_dataframe, fit_encodings=True)
        assert not result.isna().any().any()


# ============================================================================
# Tests: Feature Groups Completeness
# ============================================================================


class TestFeatureGroups:
    """Tests untuk memastikan semua FEATURE_GROUPS tercakup."""

    def test_all_groups_present(self):
        """Semua 6 group harus ada di FEATURE_GROUPS."""
        expected = ["biaya", "klinis", "geografis", "temporal", "komparatif", "historis_rs"]
        for group in expected:
            assert group in FEATURE_GROUPS, f"Missing group: {group}"

    def test_total_features_count(self):
        """Total fitur di semua group harus = 22."""
        total = sum(len(cols) for cols in FEATURE_GROUPS.values())
        assert total == 22

    def test_all_feature_columns_in_groups(self):
        """Setiap kolom di ALL_FEATURE_COLUMNS harus ada di salah satu group."""
        all_from_groups = [col for group in FEATURE_GROUPS.values() for col in group]
        for col in ALL_FEATURE_COLUMNS:
            assert col in all_from_groups, f"Column {col} not in any group"
