"""
Pramana AI — Shared Test Fixtures for Mock VClaim.

Provides TestClient with fakeredis override and auth header helpers.
"""
import pytest
from datetime import datetime

import fakeredis

from app.auth.signature import generate_signature
from app.config import mock_settings
from app.main import app
from app.routers.sep import get_redis as sep_get_redis
from app.routers.rujukan import get_redis as rujukan_get_redis
from app.routers.rencana_kontrol import get_redis as kontrol_get_redis
from app.routers.monitoring import get_redis as monitoring_get_redis


def make_auth_headers(
    cons_id: str | None = None,
    secret_key: str | None = None,
    timestamp: str | None = None,
) -> dict:
    """Generate valid VClaim authentication headers."""
    cons_id = cons_id or mock_settings.vclaim_cons_id
    secret_key = secret_key or mock_settings.vclaim_secret_key
    timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    signature = generate_signature(cons_id, secret_key, timestamp)
    return {
        "X-cons-id": cons_id,
        "X-timestamp": timestamp,
        "X-signature": signature,
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers():
    """Provide valid VClaim auth headers."""
    return make_auth_headers()


@pytest.fixture
def client():
    """Provide a FastAPI TestClient with fakeredis dependency override."""
    server = fakeredis.FakeServer()
    fake_redis_instance = fakeredis.FakeAsyncRedis(
        server=server, decode_responses=True
    )

    async def override_get_redis():
        yield fake_redis_instance

    app.dependency_overrides[sep_get_redis] = override_get_redis
    app.dependency_overrides[rujukan_get_redis] = override_get_redis
    app.dependency_overrides[kontrol_get_redis] = override_get_redis
    app.dependency_overrides[monitoring_get_redis] = override_get_redis

    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
