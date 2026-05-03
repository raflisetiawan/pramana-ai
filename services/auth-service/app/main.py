"""
Pramana AI — Auth Service
JWT issuance, user management, RBAC.
"""
from fastapi import FastAPI

app = FastAPI(
    title="Pramana AI — Auth Service",
    description="Authentication & authorization service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth-service"}
