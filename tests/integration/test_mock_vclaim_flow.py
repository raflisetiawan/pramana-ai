"""
Task 1.8.3 — Integration Test: Alur Lengkap Mock VClaim.

Full flow: cari peserta → cari rujukan → buat SEP → cek monitoring.

Task 1.8.4 — Swagger UI & Endpoint Documentation.

Verifies /docs is accessible and all endpoints are documented in OpenAPI schema.
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


def _auth_headers() -> dict:
    """Generate valid VClaim auth headers."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sig = generate_signature(
        mock_settings.vclaim_cons_id, mock_settings.vclaim_secret_key, ts
    )
    return {
        "X-cons-id": mock_settings.vclaim_cons_id,
        "X-timestamp": ts,
        "X-signature": sig,
        "Content-Type": "application/json",
    }


@pytest.fixture
def integration_client():
    """TestClient with shared fakeredis — state persists across steps."""
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


# ─────────────────────────────────────────────────────────
# Task 1.8.3 — Full Integration Flow
# ─────────────────────────────────────────────────────────


class TestFullSEPFlow:
    """Integration test: peserta → rujukan → SEP → monitoring."""

    def test_complete_sep_creation_flow(self, integration_client):
        """
        End-to-end flow simulating a real SIMRS interaction:
        1. Cari peserta by nomor kartu
        2. Cari rujukan peserta
        3. Buat SEP baru
        4. Verify SEP tersimpan (GET by noSep)
        5. Cek monitoring harian — SEP muncul di daftar
        """
        client = integration_client
        today = datetime.now().strftime("%Y-%m-%d")

        # ── Step 1: Cari Peserta ──
        headers = _auth_headers()
        r = client.get(
            f"/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/{today}",
            headers=headers,
        )
        assert r.status_code == 200
        peserta = r.json()["response"]["peserta"]
        assert peserta["noKartu"] == "0001234567890"
        assert peserta["aktif"] is True
        no_kartu = peserta["noKartu"]

        # ── Step 2: Cari Rujukan ──
        headers = _auth_headers()
        r = client.get(
            f"/vclaim/v2/Rujukan/Peserta/{no_kartu}",
            headers=headers,
        )
        assert r.status_code == 200
        rujukan = r.json()["response"]["rujukan"]
        no_rujukan = rujukan["noKunjungan"]
        assert rujukan["diagnosa"]["kode"] == "I50.0"

        # ── Step 3: Buat SEP ──
        headers = _auth_headers()
        sep_payload = {
            "noKartu": no_kartu,
            "tglSep": today,
            "ppkPelayanan": "0101R001",
            "jnsPelayanan": "2",
            "noMrLocal": "MR-TEST-001",
            "noTelp": "08123456789",
            "klsRawat": {
                "klsRawatHak": "2",
                "klsRawatNaik": "",
                "pembiayaan": "",
                "penanggungJawab": "",
            },
            "catatan": "",
            "diagAwal": "I50.0",
            "poli": "JPD",
            "poli_eks": "",
            "kodeDPJP": "DR001",
            "noRujukan": no_rujukan,
            "tujuanKunj": "0",
            "flagProcedure": "0",
            "flagKonsul": "0",
            "assesmentPel": "0",
            "kdSatuSehat": "",
            "user": "admin_rs_test",
        }
        r = client.post("/vclaim/v2/SEP/2.0/insert", json=sep_payload, headers=headers)
        assert r.status_code == 200
        assert r.json()["metaData"]["code"] == "200"

        sep = r.json()["response"]["sep"]
        no_sep = sep["noSep"]
        assert sep["noKartu"] == no_kartu
        assert sep["nama"] == "BUDI SANTOSO"
        assert sep["tglSep"] == today
        assert sep["poli"] == "JPD"
        assert sep["kdDiag"] == "I50.0"

        # ── Step 4: Verify SEP tersimpan ──
        headers = _auth_headers()
        r = client.get(f"/vclaim/v2/SEP/{no_sep}", headers=headers)
        assert r.status_code == 200
        assert r.json()["metaData"]["code"] == "200"
        stored_sep = r.json()["response"]
        assert stored_sep["noSep"] == no_sep

        # ── Step 5: Cek Monitoring ──
        headers = _auth_headers()
        r = client.get(
            f"/vclaim/v2/Monitoring/Kunjungan/Tanggal/{today}/JnsPelayanan/2",
            headers=headers,
        )
        assert r.status_code == 200
        monitoring_list = r.json()["response"]["list"]
        sep_numbers = [s["noSep"] for s in monitoring_list]
        assert no_sep in sep_numbers, f"SEP {no_sep} not found in monitoring"

    def test_sep_update_and_delete_flow(self, integration_client):
        """Test SEP lifecycle: create → update → delete."""
        client = integration_client
        today = datetime.now().strftime("%Y-%m-%d")

        # Create SEP first
        headers = _auth_headers()
        sep_payload = {
            "noKartu": "0001234567892",
            "tglSep": today,
            "ppkPelayanan": "0101R001",
            "jnsPelayanan": "2",
            "noMrLocal": "MR-TEST-002",
            "noTelp": "08123456789",
            "klsRawat": {
                "klsRawatHak": "1",
                "klsRawatNaik": "",
                "pembiayaan": "",
                "penanggungJawab": "",
            },
            "diagAwal": "I10",
            "poli": "JPD",
            "kodeDPJP": "DR001",
            "user": "admin_rs_test",
        }
        r = client.post("/vclaim/v2/SEP/2.0/insert", json=sep_payload, headers=headers)
        assert r.json()["metaData"]["code"] == "200"
        no_sep = r.json()["response"]["sep"]["noSep"]

        # Update SEP
        headers = _auth_headers()
        update_payload = {
            "noSep": no_sep,
            "klsRawat": "1",
            "noMrLocal": "MR-TEST-002-UPDATED",
            "noTelp": "08123456789",
            "diagAwal": "I50.0",
            "poli": "JPD",
            "kodeDPJP": "DR001",
            "catatan": "Updated diagnosa",
            "user": "admin_rs_test",
        }
        r = client.put("/vclaim/v2/SEP/2.0/update", json=update_payload, headers=headers)
        assert r.json()["metaData"]["code"] == "200"

        # Verify update
        headers = _auth_headers()
        r = client.get(f"/vclaim/v2/SEP/{no_sep}", headers=headers)
        updated = r.json()["response"]
        assert updated["kdDiag"] == "I50.0"
        assert updated["noMrLocal"] == "MR-TEST-002-UPDATED"

        # Delete SEP
        headers = _auth_headers()
        r = client.request(
            "DELETE",
            "/vclaim/v2/SEP/2.0/delete",
            json={"noSep": no_sep, "user": "admin_rs_test"},
            headers=headers,
        )
        assert r.json()["metaData"]["code"] == "200"

        # Verify deleted
        headers = _auth_headers()
        r = client.get(f"/vclaim/v2/SEP/{no_sep}", headers=headers)
        assert r.json()["metaData"]["code"] == "201"  # Not found

    def test_sep_validation_dpjp_required(self, integration_client):
        """SEP creation must reject empty kodeDPJP."""
        client = integration_client
        headers = _auth_headers()
        payload = {
            "noKartu": "0001234567890",
            "tglSep": datetime.now().strftime("%Y-%m-%d"),
            "ppkPelayanan": "0101R001",
            "jnsPelayanan": "2",
            "noMrLocal": "MR-001",
            "noTelp": "08123456789",
            "klsRawat": {"klsRawatHak": "2"},
            "diagAwal": "I50.0",
            "poli": "JPD",
            "kodeDPJP": "",  # Empty!
            "user": "admin_rs",
        }
        r = client.post("/vclaim/v2/SEP/2.0/insert", json=payload, headers=headers)
        assert r.json()["metaData"]["code"] == "400"
        assert "DPJP" in r.json()["metaData"]["message"]

    def test_sep_validation_future_date_rejected(self, integration_client):
        """SEP with future tglSep should be rejected."""
        client = integration_client
        headers = _auth_headers()
        payload = {
            "noKartu": "0001234567890",
            "tglSep": "2099-12-31",  # Future date
            "ppkPelayanan": "0101R001",
            "jnsPelayanan": "2",
            "noMrLocal": "MR-001",
            "noTelp": "08123456789",
            "klsRawat": {"klsRawatHak": "2"},
            "diagAwal": "I50.0",
            "poli": "JPD",
            "kodeDPJP": "DR001",
            "user": "admin_rs",
        }
        r = client.post("/vclaim/v2/SEP/2.0/insert", json=payload, headers=headers)
        assert r.json()["metaData"]["code"] == "400"

    def test_sep_inactive_peserta_rejected(self, integration_client):
        """SEP for inactive peserta should be rejected."""
        client = integration_client
        headers = _auth_headers()
        payload = {
            "noKartu": "0001234567891",  # Non-aktif
            "tglSep": datetime.now().strftime("%Y-%m-%d"),
            "ppkPelayanan": "0101R001",
            "jnsPelayanan": "2",
            "noMrLocal": "MR-001",
            "noTelp": "08123456789",
            "klsRawat": {"klsRawatHak": "3"},
            "diagAwal": "I50.0",
            "poli": "JPD",
            "kodeDPJP": "DR001",
            "user": "admin_rs",
        }
        r = client.post("/vclaim/v2/SEP/2.0/insert", json=payload, headers=headers)
        assert r.json()["metaData"]["code"] == "400"
        assert "tidak aktif" in r.json()["metaData"]["message"].lower()


# ─────────────────────────────────────────────────────────
# Task 1.8.4 — Swagger UI & Endpoint Documentation
# ─────────────────────────────────────────────────────────


class TestSwaggerDocumentation:
    """Verify Swagger UI and OpenAPI documentation."""

    def test_swagger_ui_accessible(self, integration_client):
        """Swagger UI (/docs) must be accessible without auth."""
        r = integration_client.get("/docs")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_redoc_accessible(self, integration_client):
        """ReDoc (/redoc) must be accessible without auth."""
        r = integration_client.get("/redoc")
        assert r.status_code == 200

    def test_openapi_json_accessible(self, integration_client):
        """OpenAPI schema (/openapi.json) must be accessible."""
        r = integration_client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert "info" in schema

    def test_all_peserta_endpoints_documented(self, integration_client):
        """Peserta endpoints must appear in OpenAPI schema."""
        schema = integration_client.get("/openapi.json").json()
        paths = schema["paths"]
        assert any("/Peserta/nokartu/" in p for p in paths)

    def test_all_sep_endpoints_documented(self, integration_client):
        """SEP endpoints (insert, get, update, delete) must be documented."""
        schema = integration_client.get("/openapi.json").json()
        paths = schema["paths"]
        sep_paths = [p for p in paths if "/SEP" in p]
        assert len(sep_paths) >= 3, f"Expected >=3 SEP paths, found {sep_paths}"

    def test_all_rujukan_endpoints_documented(self, integration_client):
        """Rujukan endpoints must be documented."""
        schema = integration_client.get("/openapi.json").json()
        paths = schema["paths"]
        ruj_paths = [p for p in paths if "/Rujukan" in p]
        assert len(ruj_paths) >= 2

    def test_all_referensi_endpoints_documented(self, integration_client):
        """Referensi endpoints (diagnosa, poli, faskes, dokter, procedure)."""
        schema = integration_client.get("/openapi.json").json()
        paths = schema["paths"]
        ref_paths = [p for p in paths if "/referensi" in p]
        assert len(ref_paths) >= 4, f"Expected >=4 referensi paths, found {ref_paths}"

    def test_monitoring_endpoint_documented(self, integration_client):
        """Monitoring endpoint must be documented."""
        schema = integration_client.get("/openapi.json").json()
        paths = schema["paths"]
        assert any("/Monitoring" in p for p in paths)

    def test_mock_control_endpoints_documented(self, integration_client):
        """Mock control endpoints must be documented."""
        schema = integration_client.get("/openapi.json").json()
        paths = schema["paths"]
        mock_paths = [p for p in paths if "/_mock" in p]
        assert len(mock_paths) >= 3, f"Expected >=3 mock paths, found {mock_paths}"

    def test_rencana_kontrol_endpoints_documented(self, integration_client):
        """Rencana Kontrol + SPRI endpoints must be documented."""
        schema = integration_client.get("/openapi.json").json()
        paths = schema["paths"]
        kontrol_paths = [p for p in paths if "/RencanaKontrol" in p]
        assert len(kontrol_paths) >= 2
