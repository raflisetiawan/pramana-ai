"""
Pramana AI — API Gateway: NLP Engine Integration Router
=========================================================

Task 3.4.5: Integrasi ke API Gateway — setelah klaim masuk,
otomatis panggil NLP Engine untuk ICD coding analysis.

Router ini menyediakan endpoint proxy di API Gateway yang:
1. Menerima resume medis dari frontend/RS
2. Forward ke NLP Engine untuk extract-coding / audit-consistency
3. Return structured response
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nlp", tags=["NLP Coding"])

# NLP Engine base URL (configurable via environment)
NLP_ENGINE_URL = os.getenv(
    "NLP_ENGINE_INTERNAL_URL",
    "http://nlp-engine:8002",
)

# HTTP client timeout — NLP can be slower than ML due to embedding computation
_TIMEOUT = httpx.Timeout(30.0, connect=5.0)


# ============================================================================
# Schemas (Gateway-side mirrors of NLP Engine schemas)
# ============================================================================


class CodingContext(BaseModel):
    """Contextual metadata for the resume."""

    tgl_masuk: Optional[str] = None
    tgl_pulang: Optional[str] = None


class ExtractCodingGatewayRequest(BaseModel):
    """Request: extract ICD coding from resume medis."""

    claim_id: str
    resume_medis: str = Field(..., min_length=10)
    context: Optional[CodingContext] = None


class ClaimedCode(BaseModel):
    """One ICD code claimed by the hospital."""

    kode: str
    tipe: str = "diagnosa"


class AuditConsistencyGatewayRequest(BaseModel):
    """Request: audit consistency of claimed codes vs resume."""

    claim_id: str
    resume_medis: str = Field(..., min_length=10)
    kode_klaim: list[ClaimedCode] = Field(..., min_length=1)
    context: Optional[CodingContext] = None


# ============================================================================
# Internal: Call NLP Engine
# ============================================================================


async def _call_nlp_engine(
    path: str,
    payload: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Call NLP Engine at the given path.

    Args:
        path: Endpoint path (e.g. ``/nlp/extract-coding``).
        payload: JSON request body.

    Returns:
        NLP Engine response dict or ``None`` if the service is unavailable.
    """
    url = f"{NLP_ENGINE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, json=payload)

            if response.status_code == 200:
                return response.json()

            logger.warning(
                "NLP Engine returned %d for %s: %s",
                response.status_code,
                path,
                response.text[:300],
            )
            return None

    except httpx.ConnectError:
        logger.warning("NLP Engine not reachable at %s", NLP_ENGINE_URL)
        return None
    except httpx.TimeoutException:
        logger.warning("NLP Engine timeout for %s", path)
        return None
    except Exception as exc:
        logger.error("NLP Engine call to %s failed: %s", path, exc)
        return None


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/extract-coding")
async def gateway_extract_coding(body: ExtractCodingGatewayRequest):
    """Proxy for NLP Engine's ``/nlp/extract-coding``.

    Extracts ICD-10/ICD-9 coding suggestions from medical resume text.
    Called automatically when a new claim is submitted, or on-demand by
    the frontend for re-analysis.
    """
    payload = body.model_dump(exclude_none=True)
    result = await _call_nlp_engine("/nlp/extract-coding", payload)

    if result is None:
        raise HTTPException(
            status_code=503,
            detail="NLP Engine tidak tersedia. Silakan coba lagi.",
        )
    return result


@router.post("/audit-consistency")
async def gateway_audit_consistency(body: AuditConsistencyGatewayRequest):
    """Proxy for NLP Engine's ``/nlp/audit-consistency``.

    Compares ICD codes claimed by the hospital with AI analysis of
    the medical resume. Flags any mismatches.
    """
    payload = body.model_dump(exclude_none=True)
    result = await _call_nlp_engine("/nlp/audit-consistency", payload)

    if result is None:
        raise HTTPException(
            status_code=503,
            detail="NLP Engine tidak tersedia. Silakan coba lagi.",
        )
    return result


@router.get("/health/nlp-engine")
async def check_nlp_engine_health():
    """Check NLP Engine service health from the API Gateway."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{NLP_ENGINE_URL}/nlp/health")
            if response.status_code == 200:
                return {"nlp_engine": response.json(), "reachable": True}
            return {
                "nlp_engine": None,
                "reachable": False,
                "status_code": response.status_code,
            }
    except Exception as exc:
        return {"nlp_engine": None, "reachable": False, "error": str(exc)}
