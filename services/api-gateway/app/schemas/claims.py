"""
Pramana AI — Claims Pydantic Schemas.

Request/response models for claim endpoints.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Sub-models
# ============================================================================


class RiskScoreOut(BaseModel):
    """Risk score data embedded in claim detail."""

    score: float
    risk_level: str  # low | medium | high
    shap_values: dict[str, float] = Field(default_factory=dict)
    top_features: list[str] = Field(default_factory=list)
    model_version: str = ""
    scored_at: datetime | None = None


class NlpCodingOut(BaseModel):
    """NLP coding result embedded in claim detail."""

    suggested_primary_icd: str | None = None
    suggested_primary_conf: float | None = None
    suggested_secondary: Any = None
    suggested_procedures: Any = None
    has_mismatch: bool = False
    mismatch_detail: Any = None
    processed_at: datetime | None = None


class AuditLogOut(BaseModel):
    """One audit log entry."""

    id: str
    action: str | None
    notes: str | None = None
    user_email: str | None = None
    user_role: str | None = None
    created_at: datetime | None = None


class HospitalOut(BaseModel):
    """Hospital summary."""

    id: str
    kode_rs: str
    nama_rs: str | None
    tipe_rs: str | None


# ============================================================================
# List / summary
# ============================================================================


class ClaimSummary(BaseModel):
    """One row in the claims list table."""

    id: str
    no_sep: str
    hospital_name: str | None = None
    diagnosa_utama: str | None = None
    total_tagihan: float | None = None
    tarif_ina_cbgs: float | None = None
    los: int | None = None
    tgl_pengajuan: datetime | None = None
    status: str
    risk_score: float | None = None
    risk_level: str | None = None


class ClaimListResponse(BaseModel):
    """Paginated list of claims."""

    items: list[ClaimSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Detail
# ============================================================================


class ClaimDetail(BaseModel):
    """Full claim detail including risk score + NLP result."""

    id: str
    no_sep: str
    hospital: HospitalOut | None = None

    # Clinical
    diagnosa_utama: str | None = None
    diagnosa_sekunder: list[str] | None = None
    prosedur: list[str] | None = None
    los: int | None = None

    # Financial
    total_tagihan: float | None = None
    tarif_ina_cbgs: float | None = None

    # Dates
    tgl_masuk: date | None = None
    tgl_pulang: date | None = None
    tgl_pengajuan: datetime | None = None

    # Status
    status: str

    # AI analysis
    risk_score: RiskScoreOut | None = None
    nlp_coding: NlpCodingOut | None = None

    # Audit history
    audit_logs: list[AuditLogOut] = Field(default_factory=list)

    created_at: datetime | None = None
    updated_at: datetime | None = None


# ============================================================================
# Actions
# ============================================================================


class ClaimActionRequest(BaseModel):
    """Request body for approve / return / escalate."""

    notes: str | None = Field(None, max_length=2000)


class ClaimActionResponse(BaseModel):
    """Response after a claim action."""

    claim_id: str
    action: str
    new_status: str
    message: str
    success: bool = True
