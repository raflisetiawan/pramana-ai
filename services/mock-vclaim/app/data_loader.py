"""
Pramana AI — Mock VClaim Data Loader.

Loads all JSON data files into memory on startup for fast lookups.
"""
import json
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).parent / "data"

# In-memory data stores
_peserta: list[dict] = []
_icd10: list[dict] = []
_icd9: list[dict] = []
_faskes: list[dict] = []
_dokter: list[dict] = []
_poli: list[dict] = []


def _load_json(filename: str) -> list[dict]:
    """Load a JSON file from the data directory."""
    filepath = _DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_data() -> None:
    """Load all mock data into memory. Called on application startup."""
    global _peserta, _icd10, _icd9, _faskes, _dokter, _poli
    _peserta = _load_json("peserta.json")
    _icd10 = _load_json("icd10.json")
    _icd9 = _load_json("icd9.json")
    _faskes = _load_json("faskes.json")
    _dokter = _load_json("dokter.json")
    _poli = _load_json("poli.json")


def get_peserta_list() -> list[dict]:
    """Get all peserta data."""
    return _peserta


def get_peserta_by_noka(no_kartu: str) -> dict | None:
    """Find peserta by nomor kartu."""
    for p in _peserta:
        if p["noKartu"] == no_kartu:
            return p
    return None


def get_peserta_by_nik(nik: str) -> dict | None:
    """Find peserta by NIK."""
    for p in _peserta:
        if p["nik"] == nik:
            return p
    return None


def get_icd10_list() -> list[dict]:
    """Get all ICD-10 diagnosis codes."""
    return _icd10


def search_icd10(keyword: str) -> list[dict]:
    """Search ICD-10 by keyword (code or name, case-insensitive)."""
    keyword_lower = keyword.lower()
    return [
        d for d in _icd10
        if keyword_lower in d["kode"].lower() or keyword_lower in d["nama"].lower()
    ]


def get_icd9_list() -> list[dict]:
    """Get all ICD-9-CM procedure codes."""
    return _icd9


def search_icd9(keyword: str) -> list[dict]:
    """Search ICD-9-CM by keyword (code or name, case-insensitive)."""
    keyword_lower = keyword.lower()
    return [
        p for p in _icd9
        if keyword_lower in p["kode"].lower() or keyword_lower in p["nama"].lower()
    ]


def get_faskes_list() -> list[dict]:
    """Get all faskes data."""
    return _faskes


def search_faskes(tipe: str, keyword: str) -> list[dict]:
    """Search faskes by type and keyword.

    Args:
        tipe: "1" for Faskes Tingkat I, "2" for RS.
        keyword: Search keyword (code or name).
    """
    keyword_lower = keyword.lower()
    return [
        f for f in _faskes
        if f["tipe"] == tipe and (
            keyword_lower in f["kode"].lower() or keyword_lower in f["nama"].lower()
        )
    ]


def get_dokter_list() -> list[dict]:
    """Get all dokter data."""
    return _dokter


def search_dokter(keyword: str) -> list[dict]:
    """Search dokter by keyword (code, name, or specialty)."""
    keyword_lower = keyword.lower()
    return [
        d for d in _dokter
        if keyword_lower in d["kodeDokter"].lower()
        or keyword_lower in d["namaDokter"].lower()
        or keyword_lower in d["spesialistik"].lower()
    ]


def get_dokter_by_kode(kode_dokter: str) -> dict | None:
    """Find dokter by kode."""
    for d in _dokter:
        if d["kodeDokter"] == kode_dokter:
            return d
    return None


def search_dokter_by_poli(kd_poli: str) -> list[dict]:
    """Find dokter by poli code."""
    return [d for d in _dokter if d["kodePoli"] == kd_poli]


def get_poli_list() -> list[dict]:
    """Get all poli data."""
    return _poli


def search_poli(keyword: str) -> list[dict]:
    """Search poli by keyword (code or name, case-insensitive)."""
    keyword_lower = keyword.lower()
    return [
        p for p in _poli
        if keyword_lower in p["kode"].lower() or keyword_lower in p["nama"].lower()
    ]
