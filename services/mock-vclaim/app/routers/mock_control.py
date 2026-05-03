"""
Pramana AI — Mock VClaim Control Router.

Endpoints for configuring the mock behavior (errors, delays).
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.mock_state import state

router = APIRouter(prefix="/_mock", tags=["Mock Control"])


class MockConfig(BaseModel):
    error_rate: float | None = None
    response_delay_ms: int | None = None
    force_error_on_noka: list[str] | None = None
    simulate_timeout: bool | None = None


@router.post("/config")
async def update_mock_config(config: MockConfig):
    """Update mock simulation configuration."""
    state.update(config.model_dump(exclude_unset=True))
    return {"status": "success", "current_config": state.get_status()}


@router.get("/status")
async def get_mock_status():
    """Get current mock simulation configuration."""
    return state.get_status()


@router.post("/reset")
async def reset_mock_config():
    """Reset mock simulation configuration to defaults."""
    state.reset()
    return {"status": "success", "current_config": state.get_status()}
