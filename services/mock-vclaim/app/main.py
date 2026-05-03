"""
Pramana AI — Mock VClaim 2.0 Service
Simulasi lengkap VClaim BPJS Kesehatan untuk development & testing.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Pramana AI — Mock VClaim 2.0",
    description="Simulasi VClaim 2.0 BPJS Kesehatan untuk development",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mock-vclaim"}
