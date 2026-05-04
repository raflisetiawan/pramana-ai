"""
Pramana AI — Unit Test: API Endpoint Scoring (Task 2.5.2)
===========================================================

Tests untuk ML Engine API endpoints menggunakan FastAPI TestClient:
- POST /ml/score-claim dengan klaim dummy
- GET /ml/health
- GET /ml/model-info
- Edge cases: invalid input, missing fields
"""

import sys
from pathlib import Path

import pytest

# Ensure ML engine imports work
_ML_ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "services" / "ml-engine"
sys.path.insert(0, str(_ML_ENGINE_ROOT))

from fastapi.testclient import TestClient

from app.main import app


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def client():
    """Create TestClient for ML Engine API."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def normal_claim_payload() -> dict:
    """Payload klaim normal sesuai SPEC.md bagian 5."""
    return {
        "claim_id": "test-unit-001",
        "features": {
            "total_tagihan": 5_500_000,
            "los": 4,
            "diagnosa_utama": "I10",
            "tipe_rs": "B",
            "provinsi": "Jawa Timur",
            "tarif_ina_cbgs": 5_200_000,
        },
    }


@pytest.fixture
def suspicious_claim_payload() -> dict:
    """Payload klaim mencurigakan (rasio tinggi)."""
    return {
        "claim_id": "test-unit-002",
        "features": {
            "total_tagihan": 25_000_000,
            "los": 3,
            "diagnosa_utama": "I10",
            "tipe_rs": "C",
            "provinsi": "DKI Jakarta",
            "tarif_ina_cbgs": 5_200_000,
            "rasio_terhadap_ina_cbgs": 4.8,
        },
    }


@pytest.fixture
def minimal_claim_payload() -> dict:
    """Payload klaim dengan field minimal."""
    return {
        "claim_id": "test-unit-003",
        "features": {
            "total_tagihan": 3_000_000,
            "los": 2,
            "diagnosa_utama": "A09",
            "tipe_rs": "C",
        },
    }


# ============================================================================
# Tests: GET /ml/health
# ============================================================================


class TestHealthEndpoint:
    """Tests untuk GET /ml/health."""

    def test_health_returns_200(self, client):
        response = client.get("/ml/health")
        assert response.status_code == 200

    def test_health_has_required_fields(self, client):
        data = client.get("/ml/health").json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "model_loaded" in data
        assert "model_version" in data

    def test_health_service_name(self, client):
        data = client.get("/ml/health").json()
        assert data["service"] == "ml-engine"

    def test_health_model_loaded(self, client):
        data = client.get("/ml/health").json()
        assert data["model_loaded"] is True

    def test_legacy_health_endpoint(self, client):
        """Legacy /health endpoint juga harus bekerja."""
        response = client.get("/health")
        assert response.status_code == 200


# ============================================================================
# Tests: GET /ml/model-info
# ============================================================================


class TestModelInfoEndpoint:
    """Tests untuk GET /ml/model-info."""

    def test_model_info_returns_200(self, client):
        response = client.get("/ml/model-info")
        assert response.status_code == 200

    def test_model_info_has_version(self, client):
        data = client.get("/ml/model-info").json()
        assert "model_version" in data
        assert data["model_version"] == "ensemble_v1"

    def test_model_info_has_features(self, client):
        data = client.get("/ml/model-info").json()
        assert data["feature_count"] == 22
        assert len(data["feature_names"]) == 22

    def test_model_info_has_metrics(self, client):
        data = client.get("/ml/model-info").json()
        assert "metrics" in data

    def test_model_info_has_thresholds(self, client):
        data = client.get("/ml/model-info").json()
        assert "risk_thresholds" in data
        thresholds = data["risk_thresholds"]
        assert "low" in thresholds
        assert "medium" in thresholds
        assert "high" in thresholds


# ============================================================================
# Tests: POST /ml/score-claim
# ============================================================================


class TestScoreClaimEndpoint:
    """Tests untuk POST /ml/score-claim."""

    def test_score_returns_200(self, client, normal_claim_payload):
        response = client.post("/ml/score-claim", json=normal_claim_payload)
        assert response.status_code == 200

    def test_score_has_claim_id(self, client, normal_claim_payload):
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert data["claim_id"] == "test-unit-001"

    def test_score_has_risk_score(self, client, normal_claim_payload):
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert "risk_score" in data
        assert 0 <= data["risk_score"] <= 100

    def test_score_has_risk_level(self, client, normal_claim_payload):
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert data["risk_level"] in ("low", "medium", "high")

    def test_score_has_shap_values(self, client, normal_claim_payload):
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert "shap_values" in data
        assert isinstance(data["shap_values"], dict)

    def test_score_has_top_risk_factors(self, client, normal_claim_payload):
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert "top_risk_factors" in data
        assert isinstance(data["top_risk_factors"], list)
        assert len(data["top_risk_factors"]) <= 5

    def test_score_has_model_version(self, client, normal_claim_payload):
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert data["model_version"] == "ensemble_v1"

    def test_score_has_processing_time(self, client, normal_claim_payload):
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0

    def test_normal_claim_low_risk(self, client, normal_claim_payload):
        """Klaim normal harus mendapat risk score rendah."""
        data = client.post("/ml/score-claim", json=normal_claim_payload).json()
        assert data["risk_score"] < 50, f"Normal claim got high score: {data['risk_score']}"

    def test_suspicious_claim_high_risk(self, client, suspicious_claim_payload):
        """Klaim mencurigakan harus mendapat risk score tinggi."""
        data = client.post("/ml/score-claim", json=suspicious_claim_payload).json()
        assert data["risk_score"] > 50, f"Suspicious claim got low score: {data['risk_score']}"

    def test_minimal_claim_works(self, client, minimal_claim_payload):
        """Klaim dengan field minimal tetap harus berhasil."""
        response = client.post("/ml/score-claim", json=minimal_claim_payload)
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["risk_score"] <= 100

    def test_risk_factors_in_bahasa(self, client, suspicious_claim_payload):
        """Top risk factors harus dalam Bahasa Indonesia."""
        data = client.post("/ml/score-claim", json=suspicious_claim_payload).json()
        factors = data["top_risk_factors"]
        if factors:
            # Should contain Indonesian keywords
            combined = " ".join(factors).lower()
            indonesian_words = ["tagihan", "tarif", "rs", "diagnosa", "klaim",
                                "lebih", "dari", "rata", "risiko", "bulan",
                                "wilayah", "track", "score", "percentile"]
            has_indo = any(word in combined for word in indonesian_words)
            assert has_indo, f"Risk factors don't appear to be in Bahasa: {factors}"


# ============================================================================
# Tests: Invalid Input
# ============================================================================


class TestInvalidInput:
    """Tests untuk input yang tidak valid."""

    def test_missing_claim_id(self, client):
        """Request tanpa claim_id harus 422."""
        response = client.post("/ml/score-claim", json={
            "features": {"total_tagihan": 1000, "los": 1, "diagnosa_utama": "A09", "tipe_rs": "C"}
        })
        assert response.status_code == 422

    def test_missing_features(self, client):
        """Request tanpa features harus 422."""
        response = client.post("/ml/score-claim", json={"claim_id": "test"})
        assert response.status_code == 422

    def test_invalid_tipe_rs(self, client):
        """tipe_rs selain A/B/C/D harus 422."""
        response = client.post("/ml/score-claim", json={
            "claim_id": "test",
            "features": {
                "total_tagihan": 1000, "los": 1,
                "diagnosa_utama": "A09", "tipe_rs": "Z",
            }
        })
        assert response.status_code == 422

    def test_negative_los(self, client):
        """LOS negatif harus 422."""
        response = client.post("/ml/score-claim", json={
            "claim_id": "test",
            "features": {
                "total_tagihan": 1000, "los": -1,
                "diagnosa_utama": "A09", "tipe_rs": "C",
            }
        })
        assert response.status_code == 422
