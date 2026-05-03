"""
Pramana AI — NLP Engine Service
NER pada resume medis, mapping teks → ICD-10/ICD-9, confidence scoring.
"""
from fastapi import FastAPI

app = FastAPI(
    title="Pramana AI — NLP Engine",
    description="NLP pipeline untuk ekstraksi koding ICD dari resume medis",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nlp-engine"}
