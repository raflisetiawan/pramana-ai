"""
Task 4.5.2 — Three Claim Scenarios Test.

Tests 3 distinct claim risk profiles end-to-end:
1. Klaim normal (Hijau) — CHF straightforward, low risk
2. Klaim medium risk (Kuning) — tagihan sedikit tinggi
3. Klaim high risk (Merah) — tanda-tanda upcoding

Each scenario validates:
- Claim appears in list with correct risk level
- Detail shows correct risk score + SHAP values
- NLP mismatch detection is accurate
- Verifikator can take the appropriate action
"""
import pytest

from tests.integration.api_gateway.conftest import (
    CLAIM_HIGH_ID,
    CLAIM_LOW_ID,
    CLAIM_MED_ID,
)

pytestmark = pytest.mark.asyncio


class TestScenarioLowRisk:
    """Skenario 1: Klaim normal (Hijau) — CHF straightforward.

    - Diagnosa: E11.9 (DM tipe 2)
    - Tagihan: Rp 3.2jt (di bawah INA-CBGs Rp 3.4jt)
    - Risk score: 18 (LOW)
    - NLP: no mismatch
    - Expected action: Setujui
    """

    async def test_low_risk_appears_in_list(self, client, verifikator_headers):
        """Low risk claim is visible in filtered list."""
        r = await client.get(
            "/api/v1/claims",
            params={"risk_level": "low"},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["risk_level"] == "low"
        assert items[0]["risk_score"] == 18
        assert items[0]["no_sep"] == "0301R00120250101001"

    async def test_low_risk_detail(self, client, verifikator_headers):
        """Low risk detail: score < 40, no mismatch, tagihan under INA-CBGs."""
        r = await client.get(f"/api/v1/claims/{CLAIM_LOW_ID}", headers=verifikator_headers)
        assert r.status_code == 200
        d = r.json()

        # Risk assessment
        assert d["risk_score"]["score"] == 18
        assert d["risk_score"]["risk_level"] == "low"
        assert d["risk_score"]["score"] < 40  # Low threshold

        # NLP — no mismatch
        assert d["nlp_coding"]["has_mismatch"] is False
        assert d["nlp_coding"]["suggested_primary_icd"] == "E11.9"
        assert d["nlp_coding"]["suggested_primary_conf"] >= 0.75

        # Financial — tagihan <= INA-CBGs
        assert d["total_tagihan"] <= d["tarif_ina_cbgs"]

    async def test_low_risk_approve(self, client, verifikator_headers):
        """Verifikator approves low-risk claim without notes."""
        r = await client.post(
            f"/api/v1/claims/{CLAIM_LOW_ID}/approve",
            json={},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "approved"
        assert r.json()["success"] is True


class TestScenarioMediumRisk:
    """Skenario 2: Klaim medium risk (Kuning) — tagihan sedikit tinggi.

    - Diagnosa: J18.9 (Pneumonia)
    - Tagihan: Rp 7.8jt (8% di atas INA-CBGs Rp 7.2jt)
    - Risk score: 58 (MEDIUM)
    - NLP: no mismatch
    - Expected action: Return for clarification
    """

    async def test_medium_risk_appears_in_list(self, client, verifikator_headers):
        """Medium risk claim is visible in filtered list."""
        r = await client.get(
            "/api/v1/claims",
            params={"risk_level": "medium"},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["risk_level"] == "medium"
        assert items[0]["risk_score"] == 58

    async def test_medium_risk_detail(self, client, verifikator_headers):
        """Medium risk detail: score 40-70, tagihan above INA-CBGs."""
        r = await client.get(f"/api/v1/claims/{CLAIM_MED_ID}", headers=verifikator_headers)
        assert r.status_code == 200
        d = r.json()

        # Risk assessment
        assert 40 <= d["risk_score"]["score"] < 70
        assert d["risk_score"]["risk_level"] == "medium"

        # Financial — tagihan > INA-CBGs
        assert d["total_tagihan"] > d["tarif_ina_cbgs"]
        ratio = d["total_tagihan"] / d["tarif_ina_cbgs"]
        assert 1.0 < ratio < 1.15  # ~8% above

        # SHAP — rasio factor is positive (pushes risk up)
        shap = d["risk_score"]["shap_values"]
        assert shap.get("rasio_terhadap_ina_cbgs", 0) > 0

    async def test_medium_risk_return_with_notes(self, client, verifikator_headers):
        """Verifikator returns medium-risk claim to RS with notes."""
        r = await client.post(
            f"/api/v1/claims/{CLAIM_MED_ID}/return",
            json={"notes": "Tagihan sedikit di atas INA-CBGs. Mohon klarifikasi rincian biaya."},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "returned"


class TestScenarioHighRisk:
    """Skenario 3: Klaim high risk (Merah) — tanda-tanda upcoding.

    - Diagnosa diklaim: I21.0 (Acute transmural MI anterior wall)
    - Diagnosa saran AI: I21.9 (AMI unspecified — less specific)
    - Tagihan: Rp 22.4jt (24% di atas INA-CBGs Rp 18jt)
    - Risk score: 91 (HIGH)
    - NLP: MISMATCH detected (upcoding indicator)
    - Expected action: Escalate to supervisor
    """

    async def test_high_risk_appears_in_list(self, client, verifikator_headers):
        """High risk claim is visible in filtered list."""
        r = await client.get(
            "/api/v1/claims",
            params={"risk_level": "high"},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["risk_level"] == "high"
        assert items[0]["risk_score"] == 91

    async def test_high_risk_is_first_in_default_sort(self, client, verifikator_headers):
        """High risk claim appears first in default desc sort."""
        r = await client.get("/api/v1/claims", headers=verifikator_headers)
        assert r.status_code == 200
        first = r.json()["items"][0]
        assert first["risk_score"] == 91
        assert first["risk_level"] == "high"

    async def test_high_risk_detail_shows_upcoding_signals(self, client, verifikator_headers):
        """High risk detail: high score, NLP mismatch, tagihan well above INA-CBGs."""
        r = await client.get(f"/api/v1/claims/{CLAIM_HIGH_ID}", headers=verifikator_headers)
        assert r.status_code == 200
        d = r.json()

        # Risk assessment — very high
        assert d["risk_score"]["score"] >= 70
        assert d["risk_score"]["risk_level"] == "high"

        # SHAP values — multiple positive risk factors
        shap = d["risk_score"]["shap_values"]
        positive_factors = {k: v for k, v in shap.items() if v > 0}
        assert len(positive_factors) >= 3  # Multiple red flags

        # NLP mismatch — upcoding indicator
        nlp = d["nlp_coding"]
        assert nlp["has_mismatch"] is True
        assert nlp["suggested_primary_icd"] == "I21.9"  # AI suggests less specific code
        assert nlp["suggested_primary_conf"] < 0.75  # Low confidence

        # Mismatch detail present
        assert nlp["mismatch_detail"] is not None
        assert len(nlp["mismatch_detail"]) >= 1
        assert nlp["mismatch_detail"][0]["claimed"] == "I21.0"
        assert nlp["mismatch_detail"][0]["suggested"] == "I21.9"

        # Financial — significantly above INA-CBGs
        ratio = d["total_tagihan"] / d["tarif_ina_cbgs"]
        assert ratio > 1.20  # 20%+ above

        # Top risk factors present
        assert len(d["risk_score"]["top_features"]) >= 2

    async def test_high_risk_escalate(self, client, verifikator_headers):
        """Verifikator escalates high-risk claim to supervisor."""
        r = await client.post(
            f"/api/v1/claims/{CLAIM_HIGH_ID}/escalate",
            json={"notes": "Terdapat indikasi upcoding. Kode I21.0 vs saran AI I21.9. Tagihan 24% di atas INA-CBGs."},
            headers=verifikator_headers,
        )
        assert r.status_code == 200
        assert r.json()["new_status"] == "escalated"

    async def test_high_risk_escalate_without_notes_rejected(self, client, verifikator_headers):
        """Escalation without notes is rejected."""
        r = await client.post(
            f"/api/v1/claims/{CLAIM_HIGH_ID}/escalate",
            json={"notes": ""},
            headers=verifikator_headers,
        )
        assert r.status_code == 422
