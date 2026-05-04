"""
Pramana AI - NLP Engine Service
NER pada resume medis, mapping teks -> ICD-10/ICD-9, confidence scoring.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.pipeline.icd_mapper import warmup_icd_mapper
from app.routers.nlp import router as nlp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load shared NLP resources once when the service starts."""
    app.state.icd_mapper = warmup_icd_mapper()
    yield


app = FastAPI(
    title="Pramana AI - NLP Engine",
    description="NLP pipeline untuk ekstraksi koding ICD dari resume medis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Routers ---
app.include_router(nlp_router)


@app.get("/health")
async def health_check():
    """Root-level health check (backward compatible)."""
    return {"status": "healthy", "service": "nlp-engine"}
