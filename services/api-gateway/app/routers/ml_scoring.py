"""
Pramana AI — API Gateway: ML Engine Integration Router
=========================================================

Task 2.4.6: Integrasi ke API Gateway — setelah klaim masuk,
otomatis panggil ML Engine untuk risk scoring.

Router ini menyediakan endpoint proxy di API Gateway yang:
1. Menerima klaim baru dari frontend/RS
2. Forward ke ML Engine untuk scoring otomatis
3. Return combined response (claim data + risk score)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["ML Scoring"])

# ML Engine base URL (configurable via environment)
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "http://ml-engine:8002")

# HTTP client timeout
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


# ============================================================================
# Schemas
# ============================================================================


class ClaimSubmission(BaseModel):
    """Request: klaim baru dari RS."""

    no_sep: str
    diagnosa_utama: str
    diagnosa_sekunder: Optional[str] = None
    prosedur: Optional[str] = None
    los: int
    total_tagihan: float
    tarif_ina_cbgs: Optional[float] = None
    tipe_rs: str = "C"
    provinsi: str = ""
    tgl_masuk: Optional[str] = None
    tgl_pulang: Optional[str] = None
    tgl_pengajuan: Optional[str] = None


class RiskScoreResult(BaseModel):
    """Risk score result dari ML Engine."""

    risk_score: float = 0
    risk_level: str = "unknown"
    top_risk_factors: list[str] = Field(default_factory=list)
    model_version: str = ""


class ClaimWithRiskResponse(BaseModel):
    """Response: data klaim + risk scoring."""

    claim_id: str
    no_sep: str
    status: str = "pending"
    risk_scoring: Optional[RiskScoreResult] = None
    ml_engine_available: bool = True


# ============================================================================
# Internal: Call ML Engine
# ============================================================================


async def _call_ml_engine(claim_id: str, features: dict) -> Optional[dict]:
    """Call ML Engine's /ml/score-claim endpoint.

    Args:
        claim_id: UUID of the claim.
        features: Claim features dict.

    Returns:
        ML Engine response dict or None if service unavailable.
    """
    payload = {
        "claim_id": claim_id,
        "features": features,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{ML_ENGINE_URL}/ml/score-claim",
                json=payload,
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    "ML Engine returned %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return None

    except httpx.ConnectError:
        logger.warning("ML Engine not reachable at %s", ML_ENGINE_URL)
        return None
    except httpx.TimeoutException:
        logger.warning("ML Engine timeout for claim %s", claim_id)
        return None
    except Exception as e:
        logger.error("ML Engine call failed: %s", e)
        return None


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/submit", response_model=ClaimWithRiskResponse)
async def submit_claim(claim: ClaimSubmission):
    """Submit klaim baru dan otomatis dapatkan risk scoring.

    Flow:
    1. Simpan klaim ke database (TODO: implement DB persistence)
    2. Panggil ML Engine untuk scoring otomatis
    3. Return gabungan data klaim + risk score

    Task 2.4.6: setelah klaim masuk, otomatis panggil ML Engine.
    """
    import uuid

    claim_id = str(uuid.uuid4())

    # Build features for ML Engine
    features = claim.model_dump(exclude_none=True)

    # Call ML Engine
    ml_result = await _call_ml_engine(claim_id, features)

    # Build response
    risk_scoring = None
    ml_available = True

    if ml_result:
        risk_scoring = RiskScoreResult(
            risk_score=ml_result.get("risk_score", 0),
            risk_level=ml_result.get("risk_level", "unknown"),
            top_risk_factors=ml_result.get("top_risk_factors", []),
            model_version=ml_result.get("model_version", ""),
        )
    else:
        ml_available = False

    return ClaimWithRiskResponse(
        claim_id=claim_id,
        no_sep=claim.no_sep,
        status="pending",
        risk_scoring=risk_scoring,
        ml_engine_available=ml_available,
    )


@router.get("/health/ml-engine")
async def check_ml_engine_health():
    """Check ML Engine service health dari API Gateway."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{ML_ENGINE_URL}/ml/health")
            if response.status_code == 200:
                return {"ml_engine": response.json(), "reachable": True}
            return {"ml_engine": None, "reachable": False, "status_code": response.status_code}
    except Exception as e:
        return {"ml_engine": None, "reachable": False, "error": str(e)}
