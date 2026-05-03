"""
Pramana AI — Mock VClaim Monitoring Router.

Endpoints for monitoring visits/claims.
"""
import json
from fastapi import APIRouter, Depends
import redis.asyncio as redis

from app.config import mock_settings
from app.helpers import ok_response

router = APIRouter(prefix="/Monitoring", tags=["Monitoring"])

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


@router.get("/Kunjungan/Tanggal/{tgl}/JnsPelayanan/{jnsPel}")
async def get_monitoring_kunjungan(tgl: str, jnsPel: str, redis_client: redis.Redis = Depends(get_redis)):
    """Monitoring harian SEP yang diterbitkan."""
    # In a real mock we would query all SEPs from redis
    # For now we will just scan redis for SEPs matching the criteria
    
    matching_seps = []
    
    # We use SCAN instead of KEYS to avoid blocking redis
    cursor = "0"
    while cursor != 0:
        cursor, keys = await redis_client.scan(cursor=cursor, match="sep:*", count=100)
        for key in keys:
            sep_str = await redis_client.get(key)
            if sep_str:
                sep = json.loads(sep_str)
                # Filter by date and service type
                if sep.get("tglSep") == tgl and sep.get("jnsPelayanan") == jnsPel:
                    matching_seps.append({
                        "noSep": sep["noSep"],
                        "noKartu": sep["noKartu"],
                        "nama": sep["nama"],
                        "tglSep": sep["tglSep"],
                        "poli": sep["poli"],
                        "dokter": sep["namaDPJP"],
                        "diagAwal": sep["kdDiag"],
                        "statusKlaim": "1" # Simulasi
                    })
                    
    # Limit response size for the mock
    return ok_response({"list": matching_seps[:100]})
