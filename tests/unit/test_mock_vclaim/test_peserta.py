"""
Task 1.8.2 — Unit Tests: Semua Endpoint Peserta (5 Skenario).

Scenarios from MOCK_API_SPEC.md section 4:
1. 0001234567890 → Peserta aktif, kelas II
2. 0001234567891 → Peserta non-aktif (premi tunggak)
3. 0001234567892 → Peserta aktif, kelas I
4. 0001234567893 → Peserta aktif, kelas III
5. 9999999999999 → Nomor kartu tidak ditemukan
"""
import pytest


class TestPesertaAktifKelasII:
    """Skenario 1: Peserta aktif kelas II — BUDI SANTOSO."""

    def test_returns_200(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["metaData"]["code"] == "200"

    def test_peserta_data_correct(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        peserta = r.json()["response"]["peserta"]
        assert peserta["noKartu"] == "0001234567890"
        assert peserta["nama"] == "BUDI SANTOSO"
        assert peserta["aktif"] is True
        assert peserta["hakKelas"]["kode"] == "2"
        assert peserta["hakKelas"]["keterangan"] == "KELAS II"
        assert peserta["statusPeserta"]["keterangan"] == "AKTIF"


class TestPesertaNonAktif:
    """Skenario 2: Peserta non-aktif (premi tunggak) — SITI RAHAYU."""

    def test_returns_200_with_inactive_status(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567891/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["metaData"]["code"] == "200"

    def test_peserta_is_inactive(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567891/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        peserta = r.json()["response"]["peserta"]
        assert peserta["noKartu"] == "0001234567891"
        assert peserta["nama"] == "SITI RAHAYU"
        assert peserta["aktif"] is False
        assert "NON AKTIF" in peserta["statusPeserta"]["keterangan"]
        assert peserta["hakKelas"]["kode"] == "3"


class TestPesertaAktifKelasI:
    """Skenario 3: Peserta aktif kelas I — HENDRA WIJAYA."""

    def test_returns_200(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567892/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_peserta_data_correct(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567892/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        peserta = r.json()["response"]["peserta"]
        assert peserta["noKartu"] == "0001234567892"
        assert peserta["nama"] == "HENDRA WIJAYA"
        assert peserta["aktif"] is True
        assert peserta["hakKelas"]["kode"] == "1"
        assert peserta["hakKelas"]["keterangan"] == "KELAS I"


class TestPesertaAktifKelasIII:
    """Skenario 4: Peserta aktif kelas III — DEWI KUSUMA."""

    def test_returns_200(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567893/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        assert r.status_code == 200

    def test_peserta_data_correct(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567893/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        peserta = r.json()["response"]["peserta"]
        assert peserta["noKartu"] == "0001234567893"
        assert peserta["nama"] == "DEWI KUSUMA"
        assert peserta["aktif"] is True
        assert peserta["hakKelas"]["kode"] == "3"
        assert peserta["hakKelas"]["keterangan"] == "KELAS III"


class TestPesertaTidakDitemukan:
    """Skenario 5: Nomor kartu tidak ditemukan."""

    def test_returns_201_not_found(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/9999999999999/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        assert r.status_code == 200  # HTTP 200, VClaim code 201
        data = r.json()
        assert data["metaData"]["code"] == "201"
        assert data["response"] is None

    def test_not_found_message(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/9999999999999/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        assert "tidak ditemukan" in r.json()["metaData"]["message"].lower()


class TestPesertaResponseEnvelope:
    """Validate VClaim 2.0 response envelope format."""

    def test_envelope_has_metadata(self, client, auth_headers):
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        data = r.json()
        assert "metaData" in data
        assert "code" in data["metaData"]
        assert "message" in data["metaData"]
        assert "response" in data

    def test_peserta_has_required_fields(self, client, auth_headers):
        """Peserta response must contain all required fields per MOCK_API_SPEC."""
        r = client.get(
            "/vclaim/v2/Peserta/nokartu/0001234567890/tglSEP/2024-01-15",
            headers=auth_headers,
        )
        peserta = r.json()["response"]["peserta"]
        required_fields = [
            "noKartu", "nik", "nama", "pisa", "tglLahir",
            "aktif", "statusPeserta", "hakKelas", "jenisPeserta", "pjPeserta",
        ]
        for field in required_fields:
            assert field in peserta, f"Missing required field: {field}"
