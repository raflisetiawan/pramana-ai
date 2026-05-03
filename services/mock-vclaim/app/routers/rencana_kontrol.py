"""
Pramana AI — Mock VClaim Rencana Kontrol Router.

Endpoints for managing Surat Kontrol and SPRI (Surat Perintah Rawat Inap).
Uses Redis for state management.
"""
import json
import uuid
from datetime import datetime

import redis.asyncio as redis
from fastapi import APIRouter, Depends

from app.config import mock_settings
from app.data_loader import search_dokter_by_poli, search_poli
from app.helpers import error_response, ok_response
from app.schemas.rencana_kontrol import RencanaKontrolInsertRequest, SPRIInsertRequest

router = APIRouter(prefix="/RencanaKontrol", tags=["Rencana Kontrol"])

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


@router.post("/insert")
async def insert_rencana_kontrol(request: RencanaKontrolInsertRequest, redis_client: redis.Redis = Depends(get_redis)):
    """Buat Surat Rencana Kontrol."""
    # Validasi input
    if not request.noSep or not request.kodeDokter:
        return error_response("400", "No SEP dan Dokter tidak boleh kosong")

    # Get names
    poli_name = request.poliKontrol
    polis = search_poli(request.poliKontrol)
    if polis:
        poli_name = polis[0]["nama"]
        
    dokter_name = request.kodeDokter
    dokters = search_dokter_by_poli(request.poliKontrol)
    for d in dokters:
        if d["kodeDokter"] == request.kodeDokter:
            dokter_name = d["namaDokter"]
            break

    # Generate Surat Kontrol number
    sequence = str(uuid.uuid4().int)[:4]
    no_surat = f"SRT-CTRL-{datetime.now().strftime('%Y%m%d')}-{sequence}"

    kontrol_data = {
        "noSuratKontrol": no_surat,
        "tglRencanaKontrol": request.tglRencanaKontrol,
        "poliKontrol": request.poliKontrol,
        "namaPoli": poli_name,
        "namaDokter": dokter_name
    }

    # Save to Redis
    await redis_client.set(f"kontrol:{no_surat}", json.dumps(kontrol_data), ex=86400 * 30)

    return ok_response(kontrol_data)


@router.post("/InsertSPRI")
async def insert_spri(request: SPRIInsertRequest, redis_client: redis.Redis = Depends(get_redis)):
    """Buat Surat Perintah Rawat Inap (SPRI)."""
    # Validasi input
    if not request.noKartu or not request.kodeDokter:
        return error_response("400", "No Kartu dan Dokter tidak boleh kosong")

    # Get names
    poli_name = request.poliRI
    polis = search_poli(request.poliRI)
    if polis:
        poli_name = polis[0]["nama"]
        
    dokter_name = request.kodeDokter
    dokters = search_dokter_by_poli(request.poliRI)
    for d in dokters:
        if d["kodeDokter"] == request.kodeDokter:
            dokter_name = d["namaDokter"]
            break

    # Generate SPRI number
    sequence = str(uuid.uuid4().int)[:4]
    no_spri = f"SPRI-{datetime.now().strftime('%Y%m%d')}-{sequence}"

    spri_data = {
        "noSPRI": no_spri,
        "tglRencanaRI": request.tglRencanaRI,
        "namaPoli": poli_name,
        "namaDokter": dokter_name
    }

    # Save to Redis
    await redis_client.set(f"spri:{no_spri}", json.dumps(spri_data), ex=86400 * 30)

    return ok_response(spri_data)
