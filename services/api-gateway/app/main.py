"""
Pramana AI — API Gateway Service.

Entry point utama seluruh request dari frontend.
Routing ke service yang sesuai, authentication, rate limiting, logging.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine

# --- Routers ---
from app.routers.auth import router as auth_router
from app.routers.claims import router as claims_router
from app.routers.stats import router as stats_router
from app.routers.vclaim_proxy import router as vclaim_router
from app.routers.ml_scoring import router as ml_scoring_router
from app.routers.nlp_coding import router as nlp_coding_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    yield
    # Shutdown — dispose engine connections
    await engine.dispose()


app = FastAPI(
    title="Pramana AI — API Gateway",
    description=(
        "Entry point utama untuk Smart-Claim Co-Pilot.\n\n"
        "**Auth** — JWT login, refresh, logout\n\n"
        "**Claims** — List, detail, approve, return, escalate\n\n"
        "**Stats** — Dashboard aggregation\n\n"
        "**VClaim** — SEP creation proxy\n\n"
        "**ML/NLP** — AI engine integration"
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Task 4.4.1: Auth endpoints ---
app.include_router(auth_router)

# --- Task 4.4.2: Claim endpoints ---
app.include_router(claims_router)

# --- Task 4.4.3: Stats endpoint ---
app.include_router(stats_router)

# --- Task 4.4.4: VClaim proxy ---
app.include_router(vclaim_router)

# --- Existing ML/NLP integration routers ---
app.include_router(ml_scoring_router)
app.include_router(nlp_coding_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "0.2.0",
        "environment": settings.app_env,
    }
