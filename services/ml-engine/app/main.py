"""
Pramana AI — ML Engine Service
=================================

FastAPI application untuk risk scoring klaim BPJS.
Menyediakan endpoint sesuai SPEC.md bagian 5:

- POST /ml/score-claim   — scoring single claim
- POST /ml/score-batch   — scoring batch claims (bonus)
- GET  /ml/health        — health check + model version
- GET  /ml/model-info    — info model yang sedang dipakai
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.features.extractor import (
    ALL_FEATURE_COLUMNS,
    extract_features,
    load_imputation_defaults,
    load_target_encoding,
)
from app.models.explainer import ClaimExplainer
from app.models.risk_scorer import RiskScorer
from app.schemas import (
    BatchScoreRequest,
    BatchScoreResponse,
    HealthResponse,
    ModelInfoResponse,
    ScoreClaimRequest,
    ScoreClaimResponse,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ============================================================================
# Global singletons
# ============================================================================

_scorer: RiskScorer = RiskScorer.get_instance()
_explainer: ClaimExplainer = ClaimExplainer()

APP_VERSION = "1.0.0"


# ============================================================================
# Lifespan (startup / shutdown)
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — load model on startup."""
    # --- Startup ---
    logger.info("ML Engine starting up...")

    try:
        # Load encoding/imputation artifacts
        load_target_encoding()
        load_imputation_defaults()
        logger.info("Feature encoding artifacts loaded")

        # Load model (lazy load — will load on first request if fails here)
        _scorer.load()
        logger.info("Model loaded: %s", _scorer.model_version)

        # Initialize SHAP explainer
        if _scorer.is_loaded and _scorer._model is not None:
            _explainer.initialize(_scorer._model)
            logger.info("SHAP explainer initialized")

    except FileNotFoundError as e:
        logger.warning("Model not found during startup: %s", e)
        logger.warning("Model will be loaded lazily on first request")
    except Exception as e:
        logger.error("Startup error: %s", e)

    yield

    # --- Shutdown ---
    logger.info("ML Engine shutting down...")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Pramana AI — ML Engine",
    description=(
        "Risk scoring engine untuk deteksi anomali klaim BPJS. "
        "Menggunakan ensemble model (Random Forest + XGBoost) "
        "dengan SHAP-based explanations."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/ml/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint + model version.

    Task 2.4.4: GET /ml/health — health check + model version.
    """
    return HealthResponse(
        status="healthy" if _scorer.is_loaded else "degraded",
        service="ml-engine",
        version=APP_VERSION,
        model_loaded=_scorer.is_loaded,
        model_version=_scorer.model_version,
    )


@app.get("/ml/model-info", response_model=ModelInfoResponse, tags=["Model"])
async def model_info():
    """Info model yang sedang dipakai.

    Task 2.4.5: GET /ml/model-info — info model yang sedang dipakai.
    """
    try:
        info = _scorer.get_model_info()
        return ModelInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")


@app.post("/ml/score-claim", response_model=ScoreClaimResponse, tags=["Scoring"])
async def score_claim(request: ScoreClaimRequest):
    """Score a single claim for risk.

    Task 2.4.3: POST /ml/score-claim — sesuai contract di SPEC.md bagian 5.

    Pipeline:
    1. Extract features dari input
    2. Run inference (ensemble model)
    3. Hitung SHAP values
    4. Return risk score + top 5 contributing features
    """
    t0 = time.time()

    try:
        # Step 1: Extract features
        claim_dict = request.features.model_dump(exclude_none=True)
        features_df = extract_features(claim_dict)

        # Step 2: Score
        score_results = _scorer.score(features_df)

        if not score_results:
            raise HTTPException(status_code=500, detail="Scoring failed: empty result")

        result = score_results[0]

        # Step 3: SHAP explanation
        explanation = {"shap_values": {}, "top_risk_factors": []}

        if _scorer.is_loaded and _scorer._preprocessor is not None:
            scaled = _scorer._preprocessor.transform(features_df)
            explanations = _explainer.explain(
                scaled, list(features_df.columns), top_n=5
            )
            if explanations:
                explanation = explanations[0]

        elapsed_ms = (time.time() - t0) * 1000

        return ScoreClaimResponse(
            claim_id=request.claim_id,
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            shap_values=explanation.get("shap_values", {}),
            top_risk_factors=explanation.get("top_risk_factors", []),
            model_version=_scorer.model_version,
            processing_time_ms=round(elapsed_ms, 1),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Scoring error for claim %s: %s", request.claim_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")


@app.post("/ml/score-batch", response_model=BatchScoreResponse, tags=["Scoring"])
async def score_batch(request: BatchScoreRequest):
    """Score multiple claims in a single request.

    Bonus endpoint for batch processing. Max 100 claims per request.
    """
    t0 = time.time()

    results = []
    for claim_req in request.claims:
        try:
            single_result = await score_claim(claim_req)
            results.append(single_result)
        except HTTPException as e:
            # Include error result instead of failing entire batch
            results.append(
                ScoreClaimResponse(
                    claim_id=claim_req.claim_id,
                    risk_score=0,
                    risk_level="unknown",
                    shap_values={},
                    top_risk_factors=[f"Error: {e.detail}"],
                    model_version=_scorer.model_version,
                    processing_time_ms=0,
                )
            )

    elapsed_ms = (time.time() - t0) * 1000

    return BatchScoreResponse(
        results=results,
        total_claims=len(results),
        processing_time_ms=round(elapsed_ms, 1),
    )


# ============================================================================
# Legacy health endpoint (backward compatibility)
# ============================================================================


@app.get("/health", tags=["Health"])
async def legacy_health():
    """Legacy health check (backward compat with docker-compose)."""
    return {
        "status": "healthy",
        "service": "ml-engine",
        "version": APP_VERSION,
        "model_loaded": _scorer.is_loaded,
    }
