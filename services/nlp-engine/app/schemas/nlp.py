"""Pydantic schemas for the NLP Engine API.

Defines request/response models for:
- ``POST /nlp/extract-coding``  (Task 3.4.2)
- ``POST /nlp/audit-consistency``  (Task 3.4.3)
- ``GET  /nlp/health``  (Task 3.4.4)

All schemas match the API contract in ``SPEC.md`` section 5.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------


class CodingContext(BaseModel):
    """Contextual metadata sent alongside the resume text."""

    tgl_masuk: Optional[str] = Field(None, description="Tanggal masuk (YYYY-MM-DD)")
    tgl_pulang: Optional[str] = Field(None, description="Tanggal pulang (YYYY-MM-DD)")


class ICDSuggestion(BaseModel):
    """One suggested ICD code with confidence scoring."""

    kode: str = Field(..., description="Kode ICD-10 atau ICD-9-CM")
    deskripsi: str = Field(..., description="Nama/deskripsi kode")
    confidence: float = Field(..., ge=0, le=1, description="Skor confidence 0.0–1.0")
    flagged: bool = Field(False, description="True jika confidence < threshold")
    flag_reason: str = Field("", description="Alasan flagging (kosong jika tidak di-flag)")


# ---------------------------------------------------------------------------
# POST /nlp/extract-coding
# ---------------------------------------------------------------------------


class ExtractCodingRequest(BaseModel):
    """Request body for ``POST /nlp/extract-coding``."""

    claim_id: str = Field(..., description="UUID klaim")
    resume_medis: str = Field(
        ...,
        min_length=10,
        description="Teks resume medis (plain text)",
    )
    context: Optional[CodingContext] = Field(
        None,
        description="Context tambahan (tanggal masuk/pulang)",
    )


class ExtractCodingResponse(BaseModel):
    """Response body for ``POST /nlp/extract-coding``."""

    claim_id: str
    diagnosa_utama: Optional[ICDSuggestion] = Field(
        None,
        description="Diagnosa utama yang disarankan AI",
    )
    diagnosa_sekunder: list[ICDSuggestion] = Field(
        default_factory=list,
        description="Diagnosa sekunder yang disarankan AI",
    )
    prosedur: list[ICDSuggestion] = Field(
        default_factory=list,
        description="Prosedur (ICD-9) yang disarankan AI",
    )
    has_mismatch: bool = Field(
        False,
        description="True jika ada diagnosa/prosedur yang di-flag",
    )
    processing_time_ms: int = Field(0, description="Waktu pemrosesan (ms)")


# ---------------------------------------------------------------------------
# POST /nlp/audit-consistency
# ---------------------------------------------------------------------------


class ClaimedCode(BaseModel):
    """One ICD code claimed by the hospital."""

    kode: str = Field(..., description="Kode ICD-10 atau ICD-9-CM yang diklaim RS")
    tipe: str = Field(
        "diagnosa",
        description="Tipe kode: 'diagnosa' atau 'prosedur'",
    )


class MismatchDetail(BaseModel):
    """Detail ketidaksesuaian antara kode RS dan analisis AI."""

    kode_rs: str = Field(..., description="Kode yang diklaim RS")
    kode_saran_ai: Optional[str] = Field(None, description="Kode yang disarankan AI")
    deskripsi_saran_ai: str = Field("", description="Deskripsi kode saran AI")
    confidence_ai: float = Field(0.0, description="Confidence AI untuk saran")
    alasan: str = Field(..., description="Penjelasan mismatch")
    severity: str = Field(
        "info",
        description="Tingkat severity: 'info' | 'warning' | 'critical'",
    )


class AuditConsistencyRequest(BaseModel):
    """Request body for ``POST /nlp/audit-consistency``."""

    claim_id: str = Field(..., description="UUID klaim")
    resume_medis: str = Field(
        ...,
        min_length=10,
        description="Teks resume medis (plain text)",
    )
    kode_klaim: list[ClaimedCode] = Field(
        ...,
        min_length=1,
        description="Daftar kode ICD yang diklaim RS",
    )
    context: Optional[CodingContext] = Field(None)


class AuditConsistencyResponse(BaseModel):
    """Response body for ``POST /nlp/audit-consistency``."""

    claim_id: str
    is_consistent: bool = Field(
        True,
        description="True jika semua kode RS sesuai dengan resume",
    )
    mismatch_count: int = Field(0, description="Jumlah ketidaksesuaian")
    mismatches: list[MismatchDetail] = Field(
        default_factory=list,
        description="Detail setiap ketidaksesuaian",
    )
    summary: str = Field(
        "",
        description="Ringkasan audit dalam bahasa Indonesia",
    )
    processing_time_ms: int = Field(0, description="Waktu pemrosesan (ms)")


# ---------------------------------------------------------------------------
# GET /nlp/health
# ---------------------------------------------------------------------------


class NLPHealthResponse(BaseModel):
    """Response body for ``GET /nlp/health``."""

    status: str = Field("healthy", description="Status service")
    service: str = Field("nlp-engine", description="Nama service")
    version: str = Field("0.1.0", description="Versi service")
    models_loaded: bool = Field(
        False,
        description="True jika model NLP (IndoBERT) sudah di-load",
    )
    icd_entries_count: int = Field(
        0,
        description="Jumlah entry ICD di memory",
    )
    embeddings_available: bool = Field(
        False,
        description="True jika embedding IndoBERT tersedia",
    )
