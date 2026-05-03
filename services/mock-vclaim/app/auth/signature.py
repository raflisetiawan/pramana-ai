"""
Pramana AI — HMAC-SHA256 Signature Validator.

Validates VClaim 2.0 authentication headers:
- X-cons-id: Consumer ID
- X-timestamp: Request timestamp (YYYY-MM-DD HH:MM:SS)
- X-signature: HMAC-SHA256(cons_id&timestamp, secret_key) base64-encoded

Anti-replay: rejects timestamps older than 5 minutes.
"""
import base64
import hashlib
import hmac
from datetime import datetime, timedelta

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import mock_settings
from app.helpers import error_response


def generate_signature(cons_id: str, secret_key: str, timestamp: str) -> str:
    """Generate HMAC-SHA256 signature for VClaim authentication.

    Args:
        cons_id: Consumer ID.
        secret_key: Secret key for HMAC.
        timestamp: Timestamp string (YYYY-MM-DD HH:MM:SS).

    Returns:
        Base64-encoded HMAC-SHA256 signature.
    """
    message = f"{cons_id}&{timestamp}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(signature).decode("utf-8")


def validate_signature(cons_id: str, timestamp: str, signature: str) -> tuple[bool, str]:
    """Validate HMAC-SHA256 signature from request headers.

    Args:
        cons_id: Consumer ID from X-cons-id header.
        timestamp: Timestamp from X-timestamp header.
        signature: Signature from X-signature header.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Validate cons_id
    if cons_id != mock_settings.vclaim_cons_id:
        return False, "Invalid Consumer ID"

    # Validate timestamp format and anti-replay
    try:
        ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False, "Invalid timestamp format. Expected: YYYY-MM-DD HH:MM:SS"

    now = datetime.now()
    tolerance = timedelta(seconds=mock_settings.signature_timestamp_tolerance)

    if abs(now - ts) > tolerance:
        return False, "Timestamp expired. Request must be within 5 minutes."

    # Validate signature
    expected = generate_signature(
        cons_id=cons_id,
        secret_key=mock_settings.vclaim_secret_key,
        timestamp=timestamp,
    )

    if not hmac.compare_digest(signature, expected):
        return False, "Invalid signature"

    return True, ""


class SignatureValidatorMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that validates VClaim HMAC-SHA256 signatures.

    Skips validation for:
    - /docs, /redoc, /openapi.json (Swagger UI)
    - /health (health check)
    - /_mock/* (mock control endpoints)
    """

    SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/health"}

    async def dispatch(self, request: Request, call_next):
        """Process request through signature validation."""
        path = request.url.path

        # Skip auth for docs, health, and mock control endpoints
        if path in self.SKIP_PATHS or path.startswith("/vclaim/v2/_mock"):
            return await call_next(request)

        # Extract headers
        cons_id = request.headers.get("X-cons-id", "")
        timestamp = request.headers.get("X-timestamp", "")
        signature = request.headers.get("X-signature", "")

        # Check all required headers are present
        if not all([cons_id, timestamp, signature]):
            return JSONResponse(
                status_code=401,
                content=error_response(
                    "401",
                    "Unauthorized - Missing required headers (X-cons-id, X-timestamp, X-signature)",
                ),
            )

        # Validate signature
        is_valid, error_msg = validate_signature(cons_id, timestamp, signature)
        if not is_valid:
            return JSONResponse(
                status_code=401,
                content=error_response("401", f"Unauthorized - {error_msg}"),
            )

        return await call_next(request)
