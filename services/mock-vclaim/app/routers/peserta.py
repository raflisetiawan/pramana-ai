"""
Pramana AI — Mock VClaim Peserta Router.

Endpoints for checking participant eligibility and data.
"""
from fastapi import APIRouter

from app.data_loader import get_peserta_by_noka
from app.helpers import not_found_response, ok_response

router = APIRouter(prefix="/Peserta", tags=["Peserta"])


@router.get("/nokartu/{noKartu}/tglSEP/{tglSEP}")
async def get_peserta_by_nokartu(noKartu: str, tglSEP: str):
    """
    Cari peserta berdasarkan nomor kartu asuransi dan tanggal SEP.

    Args:
        noKartu: 13 digit nomor kartu (contoh: 0001234567890).
        tglSEP: Tanggal rencana SEP dibuat (YYYY-MM-DD).

    Returns:
        Data peserta lengkap jika ditemukan.
        Jika peserta non-aktif, data akan ditampilkan dengan field aktif=false.
        Jika tidak ada di database mock, mengembalikan code 201 (Not Found).
    """
    peserta = get_peserta_by_noka(noKartu)

    if not peserta:
        return not_found_response("Peserta tidak ditemukan")

    # In a real system, the tglSEP would be used to check if the participant
    # was active on that specific date. For the mock, we just return the
    # current status from the static JSON data.

    return ok_response({"peserta": peserta})
