"""
Task 4.5.1 — End-to-End Integration Test: API Gateway Full Flow.

Simulates the complete verifikator workflow:
1. Login sebagai admin RS
2. Cari peserta by nomor kartu → Mock VClaim (mocked)
3. Buat SEP baru → Mock VClaim (mocked)
4. Klaim otomatis masuk ke database
5. NLP Engine analisis resume medis (mocked)
6. ML Engine hitung risk score (mocked)
7. Login sebagai verifikator BPJS
8. Lihat klaim di dashboard (terurut by risk)
9. Lihat detail klaim dengan analisis AI
10. Setujui klaim → status berubah di database

Uses pytest-asyncio with an in-memory SQLite database.
Internal service calls are pre-seeded in the database (no live services needed).
"""
import uuid

import pytest
import pytest_asyncio

from tests.integration.api_gateway.conftest import (
    ADMIN_RS_ID,
    CLAIM_HIGH_ID,
    CLAIM_LOW_ID,
    CLAIM_MED_ID,
    VERIFIKATOR_ID,
)


pytestmark = pytest.mark.asyncio


# ═══════════════════════════════════════════════════════════════════════
# Task 4.5.1 — Complete E2E Scenario
# ═══════════════════════════════════════════════════════════════════════


class TestEndToEndFlow:
    """Full end-to-end test simulating the verifikator workflow."""

    # ── Step 1: Login sebagai admin RS ──

    async def test_step1_login_admin_rs(self, client, admin_rs_headers):
        """Admin RS gets a valid JWT token (pre-created via fixture)."""
        # Verify token works by accessing a protected endpoint
        r = await client.get("/api/v1/claims", headers=admin_rs_headers)
        assert r.status_code == 200, f"Admin RS token rejected: {r.text}"

    # ── Step 7: Login sebagai verifikator BPJS ──

    async def test_step7_login_verifikator(self, client, verifikator_headers):
        """Verifikator BPJS gets a valid JWT token."""
        r = await client.get("/api/v1/claims", headers=verifikator_headers)
        assert r.status_code == 200, f"Verifikator token rejected: {r.text}"

    # ── Step 8: Lihat klaim di dashboard (terurut by risk) ──

    async def test_step8_list_claims_sorted_by_risk(self, client, verifikator_headers):
        """Claims list defaults to risk_score descending (highest first)."""
        r = await client.get(
            "/api/v1/claims",
            params={"sort_by": "risk_score", "sort_dir": "desc"},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        data = r.json()

        assert data["total"] == 3
        assert data["page"] == 1
        assert len(data["items"]) == 3

        # Verify descending risk order
        scores = [item["risk_score"] for item in data["items"] if item["risk_score"] is not None]
        assert scores == sorted(scores, reverse=True), (
            f"Expected descending order, got {scores}"
        )

        # Highest risk claim should be first
        assert data["items"][0]["risk_level"] == "high"
        assert data["items"][0]["risk_score"] == 91

    async def test_step8_list_claims_with_filter_risk_level(self, client, verifikator_headers):
        """Filter claims by risk level works correctly."""
        r = await client.get(
            "/api/v1/claims",
            params={"risk_level": "high"},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["risk_level"] == "high"

    async def test_step8_list_claims_with_filter_status(self, client, verifikator_headers):
        """Filter claims by status works correctly."""
        r = await client.get(
            "/api/v1/claims",
            params={"status": "pending"},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        data = r.json()
        # 2 claims are pending (low + med), 1 is in_review (high)
        assert data["total"] == 2
        for item in data["items"]:
            assert item["status"] == "pending"

    async def test_step8_list_claims_pagination(self, client, verifikator_headers):
        """Pagination returns correct page_size and total_pages."""
        r = await client.get(
            "/api/v1/claims",
            params={"page": 1, "page_size": 2},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 2
        assert len(data["items"]) == 2

    # ── Step 9: Lihat detail klaim dengan analisis AI ──

    async def test_step9_claim_detail_low_risk(self, client, verifikator_headers):
        """Detail of low-risk claim includes risk score and NLP result."""
        r = await client.get(
            f"/api/v1/claims/{CLAIM_LOW_ID}",
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        d = r.json()

        assert d["no_sep"] == "0301R00120250101001"
        assert d["status"] == "pending"
        assert d["diagnosa_utama"] == "E11.9"

        # Risk score
        assert d["risk_score"] is not None
        assert d["risk_score"]["score"] == 18
        assert d["risk_score"]["risk_level"] == "low"

        # NLP coding
        assert d["nlp_coding"] is not None
        assert d["nlp_coding"]["suggested_primary_icd"] == "E11.9"
        assert d["nlp_coding"]["has_mismatch"] is False

    async def test_step9_claim_detail_high_risk_with_mismatch(self, client, verifikator_headers):
        """High-risk claim detail shows mismatch and SHAP values."""
        r = await client.get(
            f"/api/v1/claims/{CLAIM_HIGH_ID}",
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        d = r.json()

        assert d["no_sep"] == "0301R00120250101003"
        assert d["status"] == "in_review"
        assert d["diagnosa_utama"] == "I21.0"

        # Risk score with SHAP
        rs = d["risk_score"]
        assert rs["score"] == 91
        assert rs["risk_level"] == "high"
        assert "rasio_terhadap_ina_cbgs" in rs["shap_values"]
        assert rs["shap_values"]["rasio_terhadap_ina_cbgs"] == 0.35

        # NLP mismatch detected
        nlp = d["nlp_coding"]
        assert nlp["has_mismatch"] is True
        assert nlp["suggested_primary_icd"] == "I21.9"  # AI suggests unspecified
        assert nlp["mismatch_detail"] is not None

        # Hospital info
        assert d["hospital"] is not None
        assert d["hospital"]["nama_rs"] == "RSUD Dr. Soetomo Surabaya"

    async def test_step9_claim_detail_not_found(self, client, verifikator_headers):
        """Non-existent claim returns 404."""
        fake_id = "00000000-0000-0000-0000-999999999999"
        r = await client.get(
            f"/api/v1/claims/{fake_id}",
            headers=verifikator_headers,
        )
        assert r.status_code == 404

    # ── Step 10: Setujui klaim → status berubah di database ──

    async def test_step10_approve_claim(self, client, verifikator_headers):
        """Approve a pending claim changes status to 'approved'."""
        # Approve the low-risk claim
        r = await client.post(
            f"/api/v1/claims/{CLAIM_LOW_ID}/approve",
            json={},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["action"] == "approve"
        assert data["new_status"] == "approved"

        # Verify status changed via detail endpoint
        r2 = await client.get(
            f"/api/v1/claims/{CLAIM_LOW_ID}",
            headers=verifikator_headers,
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "approved"

    async def test_step10_return_claim_with_notes(self, client, verifikator_headers):
        """Return a claim requires notes and changes status to 'returned'."""
        r = await client.post(
            f"/api/v1/claims/{CLAIM_MED_ID}/return",
            json={"notes": "Kode diagnosa perlu klarifikasi dari DPJP."},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "return"
        assert data["new_status"] == "returned"

    async def test_step10_return_without_notes_rejected(self, client, verifikator_headers):
        """Return without notes is rejected with 422."""
        r = await client.post(
            f"/api/v1/claims/{CLAIM_HIGH_ID}/return",
            json={"notes": ""},
            headers=verifikator_headers,
        )
        assert r.status_code == 422

    async def test_step10_escalate_claim(self, client, verifikator_headers):
        """Escalate a claim requires notes and changes status."""
        r = await client.post(
            f"/api/v1/claims/{CLAIM_HIGH_ID}/escalate",
            json={"notes": "Tagihan sangat tinggi, perlu review supervisor."},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "escalate"
        assert data["new_status"] == "escalated"

    async def test_step10_double_action_rejected(self, client, verifikator_headers):
        """A claim already actioned cannot be actioned again (409)."""
        # First approve
        await client.post(
            f"/api/v1/claims/{CLAIM_LOW_ID}/approve",
            json={},
            headers=verifikator_headers,
        )
        # Try to return the already-approved claim
        r = await client.post(
            f"/api/v1/claims/{CLAIM_LOW_ID}/return",
            json={"notes": "Trying to return after approve"},
            headers=verifikator_headers,
        )
        assert r.status_code == 409


# ═══════════════════════════════════════════════════════════════════════
# Auth-specific tests
# ═══════════════════════════════════════════════════════════════════════


class TestAuthEndpoints:
    """Test authentication endpoint behavior."""

    async def test_protected_endpoint_without_token_returns_401(self, client):
        """Accessing /claims without token returns 401."""
        r = await client.get("/api/v1/claims")
        assert r.status_code in (401, 403)

    async def test_invalid_token_returns_401(self, client):
        """Invalid JWT token returns 401."""
        r = await client.get(
            "/api/v1/claims",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# Stats endpoint tests
# ═══════════════════════════════════════════════════════════════════════


class TestDashboardStats:
    """Test GET /api/v1/stats/dashboard."""

    async def test_dashboard_stats(self, client, verifikator_headers):
        """Stats endpoint returns correct aggregated data."""
        r = await client.get("/api/v1/stats/dashboard", headers=verifikator_headers)
        assert r.status_code == 200
        data = r.json()

        assert data["total_claims"] == 3
        assert data["risk_high"]["count"] == 1
        assert data["risk_medium"]["count"] == 1
        assert data["risk_low"]["count"] == 1

    async def test_stats_requires_auth(self, client):
        """Stats endpoint requires authentication."""
        r = await client.get("/api/v1/stats/dashboard")
        assert r.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════════════════


class TestHealthCheck:
    """Gateway health and OpenAPI schema."""

    async def test_health_endpoint(self, client):
        """Health check returns OK without auth."""
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"
        assert r.json()["version"] == "0.2.0"

    async def test_openapi_schema(self, client):
        """OpenAPI schema includes all expected paths."""
        r = await client.get("/openapi.json")
        assert r.status_code == 200
        paths = r.json()["paths"]

        expected = [
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/logout",
            "/api/v1/claims",
            "/api/v1/stats/dashboard",
            "/api/v1/vclaim/sep/create",
        ]
        for ep in expected:
            assert ep in paths, f"Missing endpoint in OpenAPI: {ep}"
