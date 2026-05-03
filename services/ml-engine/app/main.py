"""
Pramana AI — ML Engine Service
Risk scoring per berkas klaim (0–100) dengan XGBoost + Random Forest ensemble.
"""
from fastapi import FastAPI

app = FastAPI(
    title="Pramana AI — ML Engine",
    description="Risk scoring engine untuk deteksi anomali klaim",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ml-engine"}
