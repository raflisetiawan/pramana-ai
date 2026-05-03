"""
Pramana AI — Mock VClaim 2.0 Service.

Simulasi lengkap VClaim BPJS Kesehatan untuk development & testing.
Includes HMAC-SHA256 auth validation, response envelope format,
and all VClaim 2.0 endpoints with dummy data.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.signature import SignatureValidatorMiddleware
from app.data_loader import load_all_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — load data on startup."""
    load_all_data()
    print("✅ Mock VClaim data loaded into memory")
    yield


app = FastAPI(
    title="Pramana AI — Mock VClaim 2.0",
    description=(
        "Simulasi VClaim 2.0 BPJS Kesehatan untuk development. "
        "Semua data adalah data sintetis fiktif."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Signature validator middleware
app.add_middleware(SignatureValidatorMiddleware)


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "service": "mock-vclaim", "version": "0.1.0"}


# Include routers
from app.routers.peserta import router as peserta_router
from app.routers.referensi import router as referensi_router

app.include_router(peserta_router, prefix="/vclaim/v2")
app.include_router(referensi_router, prefix="/vclaim/v2")
