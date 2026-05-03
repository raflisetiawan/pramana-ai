"""
Pramana AI — Mock VClaim Rujukan Router.

Endpoints for checking and creating Rujukan (Referrals).
Uses Redis for state management.
"""
import json
import uuid
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import APIRouter, Depends

from app.config import mock_settings
from app.data_loader import get_peserta_by_noka, search_faskes, search_icd10, search_poli
from app.helpers import error_response, not_found_response, ok_response
from app.schemas.rujukan import RujukanInsertRequest

router = APIRouter(prefix="/Rujukan", tags=["Rujukan"])

# Redis connection
async def get_redis():
    """Get redis connection pool."""
    redis_client = redis.Redis(
        host=mock_settings.redis_host,
        port=mock_settings.redis_port,
        password=mock_settings.redis_password,
        db=0,
        decode_responses=True
    )
    try:
        yield redis_client
    finally:
        await redis_client.aclose()


@router.get("/Peserta/{noKartu}")
async def get_rujukan_by_noka(noKartu: str, redis_client: redis.Redis = Depends(get_redis)):
    """Ambil rujukan aktif berdasarkan nomor kartu."""
    peserta = get_peserta_by_noka(noKartu)
    if not peserta:
        return not_found_response("Peserta tidak ditemukan")
        
    # In a real mock we could generate a deterministic rujukan from the card number
    # For now we will check if any custom rujukan has been saved to redis for this noka
    # or return a standard dummy active rujukan
    
    # Return dummy active rujukan
    tgl_kunjungan = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    tgl_akhir = (datetime.now() + timedelta(days=80)).strftime("%Y-%m-%d")
    
    rujukan_data = {
        "noKunjungan": f"1501001001{datetime.now().strftime('%Y%m%d')}000001",
        "tglKunjungan": tgl_kunjungan,
        "ppkAsal": {
            "kode": "150100100",
            "nama": "Puskesmas Tegalsari"
        },
        "ppkTujuan": {
            "kode": "0101R001",
            "nama": "RSUD Dr. Soetomo"
        },
        "diagnosa": {
            "kode": "I50.0",
            "nama": "Congestive Heart Failure"
        },
        "poliRujukan": {
            "kode": "JPD",
            "nama": "Jantung dan Pembuluh Darah"
        },
        "tglAkhirBerlaku": tgl_akhir,
        "jnsPelayanan": "2",
        "masaBerlaku": 90
    }
    
    return ok_response({"rujukan": rujukan_data})


@router.get("/{noRujukan}")
async def get_rujukan_by_nomor(noRujukan: str, redis_client: redis.Redis = Depends(get_redis)):
    """Ambil rujukan berdasarkan nomor rujukan."""
    ruj_str = await redis_client.get(f"rujukan:{noRujukan}")
    if not ruj_str:
        return not_found_response("Rujukan tidak ditemukan")
    
    return ok_response({"rujukan": json.loads(ruj_str)})


@router.post("/2.0/insert")
async def insert_rujukan(request: RujukanInsertRequest, redis_client: redis.Redis = Depends(get_redis)):
    """Simulasi pembuatan rujukan antar RS."""
    # Lookup names
    diag_name = request.diagRujukan
    diagnosas = search_icd10(request.diagRujukan)
    if diagnosas:
        diag_name = diagnosas[0]["nama"]
        
    poli_name = request.poliRujukan
    polis = search_poli(request.poliRujukan)
    if polis:
        poli_name = polis[0]["nama"]
        
    ppk_name = request.ppkRujukan
    faskes = search_faskes("2", request.ppkRujukan)  # Asumsi rujuk ke RS
    if faskes:
        ppk_name = faskes[0]["nama"]

    # Generate dummy rujukan number
    sequence = str(uuid.uuid4().int)[:6]
    no_rujukan = f"{request.ppkRujukan}{datetime.now().strftime('%Y%m%d')}{sequence}"
    tgl_akhir = (datetime.strptime(request.tglRujukan, "%Y-%m-%d") + timedelta(days=90)).strftime("%Y-%m-%d")

    rujukan_data = {
        "noKunjungan": no_rujukan,
        "tglKunjungan": request.tglRujukan,
        "ppkAsal": {
            "kode": "0101R001", # Asumsi dari RS Soetomo
            "nama": "RSUD Dr. Soetomo"
        },
        "ppkTujuan": {
            "kode": request.ppkRujukan,
            "nama": ppk_name
        },
        "diagnosa": {
            "kode": request.diagRujukan,
            "nama": diag_name
        },
        "poliRujukan": {
            "kode": request.poliRujukan,
            "nama": poli_name
        },
        "tglAkhirBerlaku": tgl_akhir,
        "jnsPelayanan": "2",
        "masaBerlaku": 90
    }

    # Save to redis
    await redis_client.set(f"rujukan:{no_rujukan}", json.dumps(rujukan_data), ex=86400 * 90)

    return ok_response({"rujukan": rujukan_data})
