"""
Task 1.8.1 — Unit Tests: HMAC-SHA256 Signature Validator.

Tests cover three main scenarios:
- Valid signature (benar): correct credentials pass validation
- Invalid signature (salah): wrong/tampered signatures are rejected
- Expired timestamp: anti-replay protection rejects old timestamps
"""
import pytest
from datetime import datetime, timedelta

from app.auth.signature import generate_signature, validate_signature
from app.config import mock_settings


# ─────────────────────────────────────────────────────────
# Pure unit tests — validate_signature() function
# ─────────────────────────────────────────────────────────


class TestGenerateSignature:
    """Tests for the generate_signature helper."""

    def test_returns_base64_string(self):
        sig = generate_signature("id", "key", "2024-01-15 10:00:00")
        assert isinstance(sig, str)
        assert len(sig) > 0

    def test_deterministic(self):
        ts = "2024-01-15 10:00:00"
        assert generate_signature("id", "key", ts) == generate_signature("id", "key", ts)

    def test_different_inputs_differ(self):
        ts = "2024-01-15 10:00:00"
        assert generate_signature("id1", "key", ts) != generate_signature("id2", "key", ts)

    def test_different_timestamps_differ(self):
        assert (
            generate_signature("id", "key", "2024-01-15 10:00:00")
            != generate_signature("id", "key", "2024-01-15 10:00:01")
        )


class TestValidateSignatureCorrect:
    """Skenario BENAR — valid signature should pass."""

    def test_valid_current_timestamp(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature(
            mock_settings.vclaim_cons_id, mock_settings.vclaim_secret_key, ts
        )
        is_valid, msg = validate_signature(mock_settings.vclaim_cons_id, ts, sig)
        assert is_valid is True
        assert msg == ""

    def test_valid_within_tolerance(self):
        """Timestamp 2 minutes ago should still be valid (within 5min tolerance)."""
        ts = (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature(
            mock_settings.vclaim_cons_id, mock_settings.vclaim_secret_key, ts
        )
        is_valid, _ = validate_signature(mock_settings.vclaim_cons_id, ts, sig)
        assert is_valid is True


class TestValidateSignatureWrong:
    """Skenario SALAH — invalid signatures should be rejected."""

    def test_tampered_signature(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_valid, msg = validate_signature(mock_settings.vclaim_cons_id, ts, "tampered")
        assert is_valid is False
        assert "Invalid signature" in msg

    def test_wrong_cons_id(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature("wrong_id", mock_settings.vclaim_secret_key, ts)
        is_valid, msg = validate_signature("wrong_id", ts, sig)
        assert is_valid is False
        assert "Consumer ID" in msg

    def test_signature_from_different_key(self):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature(
            mock_settings.vclaim_cons_id, "completely_wrong_secret_key_here!", ts
        )
        is_valid, msg = validate_signature(mock_settings.vclaim_cons_id, ts, sig)
        assert is_valid is False
        assert "Invalid signature" in msg

    def test_invalid_timestamp_format(self):
        is_valid, msg = validate_signature(mock_settings.vclaim_cons_id, "not-valid", "sig")
        assert is_valid is False
        assert "timestamp format" in msg.lower()


class TestValidateSignatureExpired:
    """Skenario EXPIRED — anti-replay protection."""

    def test_timestamp_10min_ago_rejected(self):
        ts = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature(
            mock_settings.vclaim_cons_id, mock_settings.vclaim_secret_key, ts
        )
        is_valid, msg = validate_signature(mock_settings.vclaim_cons_id, ts, sig)
        assert is_valid is False
        assert "expired" in msg.lower() or "Timestamp" in msg

    def test_timestamp_1hour_ago_rejected(self):
        ts = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature(
            mock_settings.vclaim_cons_id, mock_settings.vclaim_secret_key, ts
        )
        is_valid, msg = validate_signature(mock_settings.vclaim_cons_id, ts, sig)
        assert is_valid is False

    def test_future_timestamp_beyond_tolerance_rejected(self):
        ts = (datetime.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature(
            mock_settings.vclaim_cons_id, mock_settings.vclaim_secret_key, ts
        )
        is_valid, msg = validate_signature(mock_settings.vclaim_cons_id, ts, sig)
        assert is_valid is False


# ─────────────────────────────────────────────────────────
# Middleware tests — through HTTP requests
# ─────────────────────────────────────────────────────────


class TestSignatureMiddleware:
    """Tests for SignatureValidatorMiddleware via the full app."""

    def test_valid_auth_passes(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["metaData"]["code"] == "200"

    def test_missing_all_headers_returns_401(self, client):
        r = client.get("/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15")
        assert r.status_code == 401
        assert "Missing required headers" in r.json()["metaData"]["message"]

    def test_wrong_signature_returns_401(self, client):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        headers = {
            "X-cons-id": mock_settings.vclaim_cons_id,
            "X-timestamp": ts,
            "X-signature": "INVALID_SIG",
        }
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15",
            headers=headers,
        )
        assert r.status_code == 401

    def test_expired_timestamp_returns_401(self, client):
        old = datetime.now() - timedelta(minutes=10)
        ts = old.strftime("%Y-%m-%d %H:%M:%S")
        sig = generate_signature(
            mock_settings.vclaim_cons_id, mock_settings.vclaim_secret_key, ts
        )
        headers = {"X-cons-id": mock_settings.vclaim_cons_id, "X-timestamp": ts, "X-signature": sig}
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15",
            headers=headers,
        )
        assert r.status_code == 401

    def test_docs_no_auth_needed(self, client):
        assert client.get("/docs").status_code == 200

    def test_health_no_auth_needed(self, client):
        assert client.get("/health").status_code == 200

    def test_mock_control_no_auth_needed(self, client):
        assert client.get("/vclaim/v2/_mock/status").status_code == 200
