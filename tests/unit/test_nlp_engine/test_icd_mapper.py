"""Unit tests for ICD mapper — Task 3.5.2.

Covers:
- Common Indonesian diagnoses (exact alias)
- Typo handling (fuzzy matching)
- Abbreviation/singkatan handling
- Mixed Indonesian + English terms
- ICD-9 procedure search
- Master-data loading verification
- Edge cases (empty input, gibberish)
"""

from pathlib import Path
import sys

NLP_ENGINE_PATH = Path(__file__).resolve().parents[3] / "services" / "nlp-engine"
sys.path.insert(0, str(NLP_ENGINE_PATH))

import pytest  # noqa: E402

from app.pipeline.icd_mapper import COMMON_MAPPINGS, ICDMapper  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mapper() -> ICDMapper:
    """Shared mapper without embeddings for fast unit tests."""
    return ICDMapper(use_embeddings=False)


# ---------------------------------------------------------------------------
# 1. Exact alias (manual mappings)
# ---------------------------------------------------------------------------


class TestExactAliasMappings:
    """COMMON_MAPPINGS should produce top-1 hits with score >= 0.97."""

    @pytest.mark.parametrize(
        "query, expected_code",
        [
            ("gagal jantung", "I50.0"),
            ("gagal jantung kongestif", "I50.0"),
            ("hipertensi", "I10"),
            ("darah tinggi", "I10"),
            ("diabetes melitus tipe 2", "E11.9"),
            ("pneumonia", "J18.9"),
            ("gagal ginjal kronis", "N18.5"),
            ("serangan jantung", "I21.9"),
            ("stroke", "I64"),
            ("asma", "J45.9"),
            ("tb paru", "A16.2"),
            ("anemia", "D50.9"),
            ("diare", "A09"),
            ("infeksi saluran kemih", "N39.0"),
            ("low back pain", "M54.5"),
        ],
    )
    def test_manual_mapping_returns_correct_code(
        self, mapper: ICDMapper, query: str, expected_code: str
    ):
        candidates = mapper.map_diagnosis(query, top_k=3)

        assert candidates, f"No candidates returned for '{query}'"
        assert candidates[0]["kode"] == expected_code
        assert candidates[0]["score"] >= 0.97
        assert "manual" in str(candidates[0]["source"])


# ---------------------------------------------------------------------------
# 2. Typo handling (fuzzy matching)
# ---------------------------------------------------------------------------


class TestTypoHandling:
    """Common misspellings should still resolve to the correct code."""

    @pytest.mark.parametrize(
        "typo, expected_code",
        [
            ("hipertnsi", "I10"),          # missing 'e'
            ("hipertensy", "I10"),          # 'si' → 'sy'
            ("pnemonia", "J18.9"),          # missing 'eu'
            ("pneumoni", "J18.9"),          # missing final 'a'
            ("diabtes melitus", "E11.9"),   # missing 'e'
            ("gagal jantng", "I50.0"),      # missing 'u'
            ("apendisitis", "K35.9"),       # close to appendicitis
            ("hemodalisis", "39.95"),       # typo in hemodialisis
        ],
    )
    def test_typo_still_matches(
        self, mapper: ICDMapper, typo: str, expected_code: str
    ):
        system = "icd9" if "." in expected_code and expected_code[0].isdigit() else "all"
        candidates = mapper.map_diagnosis(typo, system=system, top_k=3)

        assert candidates, f"No candidates for typo '{typo}'"
        assert candidates[0]["kode"] == expected_code
        assert candidates[0]["score"] > 0.60


# ---------------------------------------------------------------------------
# 3. Abbreviation / singkatan handling
# ---------------------------------------------------------------------------


class TestAbbreviations:
    """Common clinical abbreviations should resolve correctly."""

    @pytest.mark.parametrize(
        "abbreviation, expected_code",
        [
            ("chf", "I50.0"),
            ("ckd", "N18.5"),
            ("ami", "I21.9"),
            ("dm tipe 2", "E11.9"),
            ("isk", "N39.0"),
        ],
    )
    def test_abbreviation_resolves(
        self, mapper: ICDMapper, abbreviation: str, expected_code: str
    ):
        candidates = mapper.map_diagnosis(abbreviation, top_k=3)

        assert candidates, f"No candidates for abbreviation '{abbreviation}'"
        assert candidates[0]["kode"] == expected_code
        assert candidates[0]["score"] >= 0.90


# ---------------------------------------------------------------------------
# 4. Mixed Indonesian + English terms
# ---------------------------------------------------------------------------


class TestMixedLanguage:
    """Both Indonesian and English terms should map correctly."""

    @pytest.mark.parametrize(
        "term, expected_code",
        [
            ("congestive heart failure", "I50.0"),
            ("chronic kidney disease", "N18.5"),
            ("fraktur femur", "S72.0"),
            ("tuberkulosis paru", "A16.2"),
            ("cuci darah", "39.95"),
            ("operasi sesar", "74.1"),
            ("usg jantung", "88.72"),
        ],
    )
    def test_bilingual_terms(
        self, mapper: ICDMapper, term: str, expected_code: str
    ):
        system = "icd9" if term in ("cuci darah", "operasi sesar", "usg jantung") else "all"
        candidates = mapper.map_diagnosis(term, system=system, top_k=3)

        assert candidates, f"No candidates for '{term}'"
        assert candidates[0]["kode"] == expected_code


# ---------------------------------------------------------------------------
# 5. ICD-9 procedure search
# ---------------------------------------------------------------------------


class TestICD9ProcedureSearch:
    """ICD-9 procedure codes should be searchable."""

    @pytest.mark.parametrize(
        "procedure, expected_code",
        [
            ("hemodialisis", "39.95"),
            ("transfusi darah", "99.04"),
            ("echocardiography", "88.72"),
            ("appendectomy", "47.09"),
            ("sectio caesarea", "74.1"),
            ("pemasangan stent", "36.07"),
            ("orif femur", "79.35"),
            ("ventilasi mekanik", "96.71"),
            ("intubasi", "96.04"),
        ],
    )
    def test_icd9_procedure_search(
        self, mapper: ICDMapper, procedure: str, expected_code: str
    ):
        candidates = mapper.map_diagnosis(procedure, system="icd9", top_k=3)

        assert candidates, f"No ICD-9 candidates for '{procedure}'"
        assert candidates[0]["kode"] == expected_code
        assert candidates[0]["system"] == "icd9"


# ---------------------------------------------------------------------------
# 6. Master data loading
# ---------------------------------------------------------------------------


class TestMasterDataLoading:
    """ICD-10 and ICD-9 master data must be loaded into memory at startup."""

    def test_entries_loaded(self, mapper: ICDMapper):
        assert len(mapper.entries) >= 60

    def test_entries_by_code_lookup(self, mapper: ICDMapper):
        assert "E11.9" in mapper.entries_by_code
        assert mapper.entries_by_code["E11.9"].nama.startswith("Type 2 Diabetes")

    def test_icd10_entries_present(self, mapper: ICDMapper):
        icd10 = [e for e in mapper.entries if e.system == "icd10"]
        assert len(icd10) >= 40

    def test_icd9_entries_present(self, mapper: ICDMapper):
        icd9 = [e for e in mapper.entries if e.system == "icd9"]
        assert len(icd9) >= 10

    def test_common_mappings_are_attached_as_aliases(self, mapper: ICDMapper):
        entry_i50 = mapper.entries_by_code["I50.0"]
        assert "gagal jantung" in entry_i50.aliases


# ---------------------------------------------------------------------------
# 7. Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Boundary and degenerate inputs."""

    def test_empty_string_returns_empty(self, mapper: ICDMapper):
        assert mapper.map_diagnosis("") == []

    def test_whitespace_only_returns_empty(self, mapper: ICDMapper):
        assert mapper.map_diagnosis("   ") == []

    def test_gibberish_returns_candidates_with_low_score(self, mapper: ICDMapper):
        candidates = mapper.map_diagnosis("xyzqwert", top_k=3)
        # May or may not return candidates; if it does, scores should be low
        for c in candidates:
            assert c["score"] < 0.90

    def test_top_k_limits_output(self, mapper: ICDMapper):
        candidates = mapper.map_diagnosis("heart", top_k=2)
        assert len(candidates) <= 2

    def test_system_filter_icd10_excludes_icd9(self, mapper: ICDMapper):
        candidates = mapper.map_diagnosis("hemodialisis", system="icd10", top_k=5)
        for c in candidates:
            assert c["system"] == "icd10"

    def test_system_filter_icd9_excludes_icd10(self, mapper: ICDMapper):
        candidates = mapper.map_diagnosis("heart failure", system="icd9", top_k=5)
        for c in candidates:
            assert c["system"] == "icd9"
