"""
Pramana AI — API Gateway: VClaim Proxy Router.

Task 4.4.4: POST /api/v1/vclaim/sep/create — buat SEP via Mock VClaim.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.middleware.jwt_auth import get_current_user
from app.schemas.vclaim import SEPCreateRequest, SEPCreateResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/vclaim", tags=["VClaim Proxy"])

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

# Mock VClaim credentials (from environment / settings)
_CONS_ID = "pramana"
_SECRET_KEY = "pramana_secret_dev"


def _build_vclaim_headers() -> dict[str, str]:
    """Build HMAC-SHA256 auth headers for Mock VClaim."""
    ts = str(int(time.time()))
    message = f"{_CONS_ID}&{ts}"
    signature = hmac.new(
        _SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-cons-id": _CONS_ID,
        "X-timestamp": ts,
        "X-signature": signature,
        "Content-Type": "application/json",
    }


@router.post("/sep/create", response_model=SEPCreateResponse)
async def create_sep(
    body: SEPCreateRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new SEP by proxying to the Mock VClaim service.

    Builds HMAC-SHA256 signed headers and forwards the request
    to Mock VClaim's POST /SEP/2.0/insert endpoint.
    """
    vclaim_url = f"{settings.mock_vclaim_internal_url}/SEP/2.0/insert"
    headers = _build_vclaim_headers()

    # Build VClaim payload format
    payload = {
        "request": {
            "t_sep": {
                "noKartu": body.noKartu,
                "tglSep": body.tglSep,
                "ppkPelayanan": body.ppkPelayanan,
                "jnsPelayanan": body.jnsPelayanan,
                "klsRawat": {"klsRawatHak": body.klsRawatHak},
                "noMR": body.noMR,
                "rujukan": {
                    "asalRujukan": body.asalRujukan,
                    "tglRujukan": body.tglRujukan,
                    "noRujukan": body.noRujukan,
                    "ppkRujukan": body.ppkRujukan,
                },
                "diagnosa": {"diagAwal": body.diagAwal},
                "poli": {
                    "tujuan": body.poliTujuan,
                    "eksekutif": body.poliEksekutif,
                },
                "catatan": body.catatan,
                "dpjpLayan": body.dpjpLayan,
            }
        }
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(vclaim_url, json=payload, headers=headers)

        data = response.json()
        meta = data.get("metaData", {})

        if meta.get("code") == "200":
            sep_data = data.get("response", {})
            no_sep = sep_data.get("noSep") if isinstance(sep_data, dict) else None
            logger.info("SEP created: %s for card %s", no_sep, body.noKartu)
            return SEPCreateResponse(
                success=True,
                no_sep=no_sep,
                message=meta.get("message", "SEP berhasil dibuat."),
                vclaim_response=data,
            )
        else:
            return SEPCreateResponse(
                success=False,
                no_sep=None,
                message=meta.get("message", "Gagal membuat SEP."),
                vclaim_response=data,
            )

    except httpx.ConnectError:
        logger.warning("Mock VClaim not reachable at %s", settings.mock_vclaim_internal_url)
        raise HTTPException(status_code=503, detail="Mock VClaim service tidak tersedia.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Mock VClaim timeout.")
    except Exception as exc:
        logger.error("VClaim proxy error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Gagal menghubungi VClaim: {exc}")
