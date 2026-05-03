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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    yield
    # Shutdown — dispose engine connections
    await engine.dispose()


app = FastAPI(
    title="Pramana AI — API Gateway",
    description="Entry point utama untuk Smart-Claim Co-Pilot",
    version="0.1.0",
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "0.1.0",
        "environment": settings.app_env,
    }
