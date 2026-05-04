"""
Pramana AI — ML Engine API Schemas
=====================================

Pydantic schemas untuk request/response validation
sesuai SPEC.md bagian 5 (API Contract: /ml/score-claim).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================


class ClaimFeatures(BaseModel):
    """Fitur klaim yang dikirim untuk scoring.

    Sesuai SPEC.md bagian 5: POST /ml/score-claim request.features
    """

    total_tagihan: float = Field(..., description="Total tagihan RS dalam Rupiah")
    los: int = Field(..., ge=0, description="Length of Stay (hari)")
    diagnosa_utama: str = Field(..., description="Kode ICD-10 diagnosa utama")
    tipe_rs: str = Field(..., pattern="^[A-D]$", description="Tipe RS: A/B/C/D")
    provinsi: str = Field(default="", description="Provinsi lokasi RS")

    # Optional — akan dihitung jika tidak disediakan
    tarif_ina_cbgs: Optional[float] = Field(default=None, description="Tarif INA-CBGs")
    tagihan_per_hari: Optional[float] = Field(default=None, description="Tagihan per hari")
    rasio_terhadap_ina_cbgs: Optional[float] = Field(default=None, description="Rasio tagihan vs INA-CBGs")
    bulan_pengajuan: Optional[int] = Field(default=None, ge=1, le=12)
    hari_pengajuan_dalam_bulan: Optional[int] = Field(default=None, ge=1, le=31)
    jumlah_diagnosa_sekunder: Optional[int] = Field(default=None, ge=0)
    jumlah_prosedur: Optional[int] = Field(default=None, ge=0)
    severity_score: Optional[int] = Field(default=None, ge=1, le=5)
    diagnosa_sekunder: Optional[str] = Field(default=None, description="Kode ICD-10 sekunder, dipisah ;")
    prosedur: Optional[str] = Field(default=None, description="Kode prosedur, dipisah ;")
    tgl_pengajuan: Optional[str] = Field(default=None, description="Tanggal pengajuan (ISO 8601)")
    tgl_masuk: Optional[str] = Field(default=None, description="Tanggal masuk RS")
    tgl_pulang: Optional[str] = Field(default=None, description="Tanggal keluar RS")
    tagihan_obat_ratio: Optional[float] = Field(default=None)
    tagihan_tindakan_ratio: Optional[float] = Field(default=None)

    # Komparatif & historis (opsional, ada default)
    percentile_tagihan_per_diagnosa: Optional[float] = Field(default=None)
    percentile_los_per_diagnosa: Optional[float] = Field(default=None)
    z_score_tagihan: Optional[float] = Field(default=None)
    rs_avg_risk_score_30d: Optional[float] = Field(default=None)
    rs_pending_rate_30d: Optional[float] = Field(default=None)
    rs_total_claims_30d: Optional[int] = Field(default=None)


class ScoreClaimRequest(BaseModel):
    """Request body untuk POST /ml/score-claim.

    Sesuai SPEC.md bagian 5.
    """

    claim_id: str = Field(..., description="UUID klaim")
    features: ClaimFeatures


class BatchScoreRequest(BaseModel):
    """Request body untuk POST /ml/score-batch (bonus endpoint)."""

    claims: list[ScoreClaimRequest] = Field(..., max_length=100)


# ============================================================================
# Response Schemas
# ============================================================================


class ScoreClaimResponse(BaseModel):
    """Response body untuk POST /ml/score-claim.

    Sesuai SPEC.md bagian 5.
    """

    claim_id: str
    risk_score: float = Field(..., ge=0, le=100, description="Risk score 0-100")
    risk_level: str = Field(..., description="low | medium | high")
    shap_values: dict[str, float] = Field(
        default_factory=dict,
        description="SHAP value per fitur",
    )
    top_risk_factors: list[str] = Field(
        default_factory=list,
        description="Top 5 contributing risk factors (Bahasa Indonesia)",
    )
    model_version: str = Field(default="", description="Versi model yang dipakai")
    processing_time_ms: float = Field(default=0, description="Waktu pemrosesan (ms)")


class BatchScoreResponse(BaseModel):
    """Response body untuk POST /ml/score-batch."""

    results: list[ScoreClaimResponse]
    total_claims: int
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Response body untuk GET /ml/health."""

    status: str
    service: str
    version: str
    model_loaded: bool
    model_version: str


class ModelInfoResponse(BaseModel):
    """Response body untuk GET /ml/model-info."""

    model_version: str
    feature_count: int
    feature_names: list[str]
    metrics: dict[str, Any]
    shap_top_features: list[dict]
    risk_thresholds: dict[str, Any]
    is_loaded: bool
