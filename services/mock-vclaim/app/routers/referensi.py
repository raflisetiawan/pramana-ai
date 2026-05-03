"""
Pramana AI — Mock VClaim Referensi Router.

Endpoints for referencing ICD-10, ICD-9, Poli, Faskes, and Dokter data.
"""
from fastapi import APIRouter

from app.data_loader import (
    search_dokter_by_poli,
    search_faskes,
    search_icd9,
    search_icd10,
    search_poli,
)
from app.helpers import not_found_response, ok_response

router = APIRouter(prefix="/referensi", tags=["Referensi"])


@router.get("/diagnosa/{keyword}")
async def get_referensi_diagnosa(keyword: str):
    """Mencari referensi diagnosa (ICD-10) berdasarkan keyword kode atau nama."""
    results = search_icd10(keyword)
    if not results:
        return not_found_response("Data diagnosa tidak ditemukan")
    return ok_response({"diagnosa": results})


@router.get("/procedure/{keyword}")
async def get_referensi_procedure(keyword: str):
    """Mencari referensi prosedur (ICD-9-CM) berdasarkan keyword kode atau nama."""
    results = search_icd9(keyword)
    if not results:
        return not_found_response("Data procedure tidak ditemukan")
    return ok_response({"procedure": results})


@router.get("/poli/{keyword}")
async def get_referensi_poli(keyword: str):
    """Mencari referensi poliklinik berdasarkan keyword kode atau nama."""
    results = search_poli(keyword)
    if not results:
        return not_found_response("Data poli tidak ditemukan")
    return ok_response({"poli": results})


@router.get("/faskes/{tipe}/{keyword}")
async def get_referensi_faskes(tipe: str, keyword: str):
    """
    Mencari fasilitas kesehatan berdasarkan tipe dan keyword.

    Args:
        tipe: 1 (Faskes Tingkat I), 2 (Faskes Tingkat II / RS)
        keyword: Kode atau nama faskes
    """
    results = search_faskes(tipe, keyword)
    if not results:
        return not_found_response("Data faskes tidak ditemukan")
    return ok_response({"faskes": results})


@router.get("/dokter/pelayanan/{kdPoli}/tglPelayanan/{tgl}/Spesialis/{kdSpesialis}")
async def get_referensi_dokter(kdPoli: str, tgl: str, kdSpesialis: str):
    """
    Mencari referensi dokter DPJP berdasarkan pelayanan.
    Untuk keperluan mock, pencarian hanya disederhanakan berdasarkan poli.
    """
    # In a real VClaim, tgl and kdSpesialis are strictly validated.
    # Here we just look up by kdPoli for simplicity in the mock.
    results = search_dokter_by_poli(kdPoli)
    if not results:
        return not_found_response("Data dokter tidak ditemukan")
    return ok_response({"dokter": results})
