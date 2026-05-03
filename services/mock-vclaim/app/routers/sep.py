"""
Pramana AI — Mock VClaim SEP Router.

Endpoints for managing Surat Eligibilitas Peserta (SEP).
Uses Redis for state management (storing created SEPs).
"""
import json
import uuid
from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Request

from app.config import mock_settings
from app.data_loader import get_peserta_by_noka, search_dokter_by_poli, search_icd10, search_poli
from app.helpers import error_response, not_found_response, ok_response
from app.schemas.sep import SEPDeleteRequest, SEPInsertRequest, SEPUpdateRequest

router = APIRouter(prefix="/SEP", tags=["SEP"])

# Redis connection for SEP state management
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


@router.post("/2.0/insert")
async def insert_sep(request: SEPInsertRequest, redis_client: redis.Redis = Depends(get_redis)):
    """
    Simulasi pembuatan SEP VClaim 2.0.
    Termasuk validasi DPJP, tanggal, dan backdate.
    """
    # Validasi DPJP tidak boleh kosong
    if not request.kodeDPJP:
        return error_response("400", "DPJP tidak boleh kosong")

    # Validasi Format Tanggal
    try:
        tgl_sep = datetime.strptime(request.tglSep, "%Y-%m-%d").date()
    except ValueError:
        return error_response("400", "Format tglSep tidak valid (YYYY-MM-DD)")

    today = datetime.now().date()

    # Validasi Tanggal SEP tidak boleh lebih dari hari ini
    if tgl_sep > today:
        return error_response("400", "Tanggal SEP tidak boleh lebih dari tanggal pembuatan SEP")

    # Validasi Backdate > 1 hari harus pengajuan (simplified mock logic)
    if (today - tgl_sep) > timedelta(days=1) and request.jnsPelayanan == "2":
        return error_response("400", "SEP backdate harus mengajukan persetujuan backdate")

    # Validasi Peserta
    peserta = get_peserta_by_noka(request.noKartu)
    if not peserta:
        return error_response("400", "Peserta tidak ditemukan")
    
    if not peserta["aktif"]:
        return error_response("400", f"Peserta tidak aktif: {peserta['statusPeserta']['keterangan']}")
        
    try:
        tmt_peserta = datetime.strptime(peserta["tglMulaiAktif"], "%Y-%m-%d").date()
        if tgl_sep < tmt_peserta:
            return error_response("400", "Tanggal SEP kurang dari tanggal TMT peserta")
    except (ValueError, KeyError):
        pass

    # Simplified lookup for response names
    poli_name = request.poli
    polis = search_poli(request.poli)
    if polis:
        poli_name = polis[0]["nama"]
        
    dokter_name = request.kodeDPJP
    dokters = search_dokter_by_poli(request.poli)
    for d in dokters:
        if d["kodeDokter"] == request.kodeDPJP:
            dokter_name = d["namaDokter"]
            break
            
    diag_name = request.diagAwal
    diagnosas = search_icd10(request.diagAwal)
    if diagnosas:
        diag_name = diagnosas[0]["nama"]

    # Generate Dummy SEP Number
    # Format: PPK(8) + YYYYMMDD(8) + Sequence(6)
    sequence = str(uuid.uuid4().int)[:6]
    no_sep = f"{request.ppkPelayanan}{tgl_sep.strftime('%Y%m%d')}{sequence}"

    # Build response data
    sep_data = {
        "noSep": no_sep,
        "noKartu": request.noKartu,
        "nama": peserta["nama"],
        "tglSep": request.tglSep,
        "jnsPelayanan": request.jnsPelayanan,
        "poli": request.poli,
        "namaPoli": poli_name,
        "klsRawat": request.klsRawat.klsRawatHak,
        "namaDPJP": dokter_name,
        "noRujukan": request.noRujukan,
        "kdDiag": request.diagAwal,
        "nmDiag": diag_name,
        "statusPeserta": peserta["statusPeserta"]["kode"],
        "pjPeserta": peserta["pjPeserta"]["namaPj"],
        "hakKelas": peserta["hakKelas"]["keterangan"],
        "noMrLocal": request.noMrLocal,
        "tglTerbit": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Simpan ke Redis (State Management)
    await redis_client.set(f"sep:{no_sep}", json.dumps(sep_data), ex=86400 * 30) # Expire 30 days

    return ok_response({"sep": sep_data})


@router.get("/{noSep}")
async def get_sep(noSep: str, redis_client: redis.Redis = Depends(get_redis)):
    """Ambil data SEP by nomor."""
    sep_str = await redis_client.get(f"sep:{noSep}")
    if not sep_str:
        return not_found_response("SEP tidak ditemukan")
    
    return ok_response(json.loads(sep_str))


@router.put("/2.0/update")
async def update_sep(request: SEPUpdateRequest, redis_client: redis.Redis = Depends(get_redis)):
    """Simulasi update SEP."""
    sep_key = f"sep:{request.noSep}"
    sep_str = await redis_client.get(sep_key)
    if not sep_str:
        return error_response("400", "SEP tidak ditemukan")
        
    sep_data = json.loads(sep_str)
    
    # Update allowed fields
    sep_data["klsRawat"] = request.klsRawat
    sep_data["noMrLocal"] = request.noMrLocal
    sep_data["kdDiag"] = request.diagAwal
    sep_data["poli"] = request.poli
    
    # Update names if changed
    diagnosas = search_icd10(request.diagAwal)
    if diagnosas:
        sep_data["nmDiag"] = diagnosas[0]["nama"]
        
    polis = search_poli(request.poli)
    if polis:
        sep_data["namaPoli"] = polis[0]["nama"]

    await redis_client.set(sep_key, json.dumps(sep_data), ex=86400 * 30)
    
    return ok_response("SEP Berhasil Diupdate")


@router.delete("/2.0/delete")
async def delete_sep(request: SEPDeleteRequest, redis_client: redis.Redis = Depends(get_redis)):
    """Simulasi hapus SEP."""
    sep_key = f"sep:{request.noSep}"
    exists = await redis_client.exists(sep_key)
    
    if not exists:
        return error_response("400", "SEP tidak ditemukan")
        
    await redis_client.delete(sep_key)
    return ok_response("SEP Berhasil Dihapus")
