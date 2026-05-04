"""NLP Engine API Router — ICD Coding Extraction & Audit.

Task 3.4.2  ``POST /nlp/extract-coding``
Task 3.4.3  ``POST /nlp/audit-consistency``
Task 3.4.4  ``GET  /nlp/health``

The full pipeline:
  resume text → NER (extract entities) → ICD mapper (fuzzy + embedding)
              → confidence scorer → structured response
"""

from __future__ import annotations

import logging
import time
from typing import Literal

from fastapi import APIRouter, Request

from app.pipeline.confidence import NLP_CONFIDENCE_THRESHOLD, score_candidate
from app.pipeline.icd_mapper import ICDMapper, get_icd_mapper
from app.pipeline.ner import RuleBasedMedicalNER
from app.schemas.nlp import (
    AuditConsistencyRequest,
    AuditConsistencyResponse,
    ExtractCodingRequest,
    ExtractCodingResponse,
    ICDSuggestion,
    MismatchDetail,
    NLPHealthResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlp", tags=["NLP Engine"])


# ============================================================================
# GET /nlp/health  (Task 3.4.4)
# ============================================================================


@router.get("/health", response_model=NLPHealthResponse)
async def nlp_health(request: Request) -> NLPHealthResponse:
    """Health check with model/data status info."""
    mapper: ICDMapper = _get_mapper(request)
    return NLPHealthResponse(
        status="healthy",
        service="nlp-engine",
        version="0.1.0",
        models_loaded=mapper._model is not None,
        icd_entries_count=len(mapper.entries),
        embeddings_available=mapper._use_embeddings and bool(mapper._entry_embeddings),
    )


# ============================================================================
# POST /nlp/extract-coding  (Task 3.4.2)
# ============================================================================


@router.post("/extract-coding", response_model=ExtractCodingResponse)
async def extract_coding(
    body: ExtractCodingRequest,
    request: Request,
) -> ExtractCodingResponse:
    """Extract ICD-10/ICD-9 coding suggestions from a medical resume.

    Pipeline:
      1. NER — extract DIAGNOSA, PROSEDUR, OBAT, DURASI entities
      2. ICD Mapper — fuzzy + embedding search per entity
      3. Confidence scorer — blend fuzzy/embedding/frequency
      4. Assemble structured response
    """
    t0 = time.perf_counter()
    mapper = _get_mapper(request)
    ner = RuleBasedMedicalNER()

    # Step 1: NER
    entities = ner.extract(body.resume_medis)

    # Step 2+3: map entities → ICD candidates with confidence
    diagnoses = [e for e in entities if e.label == "DIAGNOSA"]
    procedures = [e for e in entities if e.label == "PROSEDUR"]

    # Primary diagnosis — first DIAGNOSA entity with best ICD match
    primary_suggestion: ICDSuggestion | None = None
    secondary_suggestions: list[ICDSuggestion] = []
    procedure_suggestions: list[ICDSuggestion] = []

    seen_codes: set[str] = set()

    for i, entity in enumerate(diagnoses):
        suggestion = _map_entity_to_suggestion(mapper, entity.text, system="icd10")
        if suggestion is None:
            continue
        if suggestion.kode in seen_codes:
            continue
        seen_codes.add(suggestion.kode)

        if i == 0 and primary_suggestion is None:
            primary_suggestion = suggestion
        else:
            secondary_suggestions.append(suggestion)

    for entity in procedures:
        suggestion = _map_entity_to_suggestion(mapper, entity.text, system="icd9")
        if suggestion is None:
            continue
        if suggestion.kode in seen_codes:
            continue
        seen_codes.add(suggestion.kode)
        procedure_suggestions.append(suggestion)

    # Determine if any suggestion is flagged
    has_mismatch = any(
        s.flagged
        for s in [primary_suggestion, *secondary_suggestions, *procedure_suggestions]
        if s is not None
    )

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return ExtractCodingResponse(
        claim_id=body.claim_id,
        diagnosa_utama=primary_suggestion,
        diagnosa_sekunder=secondary_suggestions,
        prosedur=procedure_suggestions,
        has_mismatch=has_mismatch,
        processing_time_ms=elapsed_ms,
    )


# ============================================================================
# POST /nlp/audit-consistency  (Task 3.4.3)
# ============================================================================


@router.post("/audit-consistency", response_model=AuditConsistencyResponse)
async def audit_consistency(
    body: AuditConsistencyRequest,
    request: Request,
) -> AuditConsistencyResponse:
    """Audit whether ICD codes claimed by a hospital match the resume.

    Pipeline:
      1. Extract coding from the resume (same pipeline as extract-coding)
      2. Compare each code claimed by the hospital with AI suggestions
      3. Identify mismatches and produce human-readable explanations
    """
    t0 = time.perf_counter()
    mapper = _get_mapper(request)
    ner = RuleBasedMedicalNER()

    # Step 1: extract entities and build AI's view of the resume
    entities = ner.extract(body.resume_medis)
    diagnoses = [e for e in entities if e.label == "DIAGNOSA"]
    procedures = [e for e in entities if e.label == "PROSEDUR"]

    # Build AI's best ICD candidates
    ai_diag_suggestions = _collect_suggestions(mapper, diagnoses, system="icd10")
    ai_proc_suggestions = _collect_suggestions(mapper, procedures, system="icd9")
    ai_diag_codes = {s.kode for s in ai_diag_suggestions}
    ai_proc_codes = {s.kode for s in ai_proc_suggestions}

    # Step 2: compare with hospital's claimed codes
    mismatches: list[MismatchDetail] = []

    for claimed in body.kode_klaim:
        if claimed.tipe == "prosedur":
            _check_claimed_code(
                claimed.kode,
                ai_proc_codes,
                ai_proc_suggestions,
                mapper,
                system="icd9",
                mismatches=mismatches,
            )
        else:
            _check_claimed_code(
                claimed.kode,
                ai_diag_codes,
                ai_diag_suggestions,
                mapper,
                system="icd10",
                mismatches=mismatches,
            )

    is_consistent = len(mismatches) == 0
    summary = _build_audit_summary(body.kode_klaim, mismatches, is_consistent)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    return AuditConsistencyResponse(
        claim_id=body.claim_id,
        is_consistent=is_consistent,
        mismatch_count=len(mismatches),
        mismatches=mismatches,
        summary=summary,
        processing_time_ms=elapsed_ms,
    )


# ============================================================================
# Internal helpers
# ============================================================================


def _get_mapper(request: Request) -> ICDMapper:
    """Retrieve the singleton ICDMapper from app state or the module cache."""
    mapper = getattr(request.app.state, "icd_mapper", None)
    if mapper is not None:
        return mapper
    return get_icd_mapper()


def _map_entity_to_suggestion(
    mapper: ICDMapper,
    entity_text: str,
    *,
    system: Literal["icd10", "icd9"],
) -> ICDSuggestion | None:
    """Map one NER entity to the best ICD suggestion with confidence scoring."""
    candidates = mapper.search(entity_text, system=system, top_k=1)
    if not candidates:
        return None

    best = candidates[0]
    scored = score_candidate(
        fuzzy_score=best.fuzzy_score,
        icd_code=best.kode,
        embedding_score=best.embedding_score,
        source=best.source,
    )

    return ICDSuggestion(
        kode=best.kode,
        deskripsi=best.nama,
        confidence=scored.confidence,
        flagged=scored.flagged,
        flag_reason=scored.flag_reason,
    )


def _collect_suggestions(
    mapper: ICDMapper,
    entities: list,
    *,
    system: Literal["icd10", "icd9"],
) -> list[ICDSuggestion]:
    """Map multiple NER entities to unique ICD suggestions."""
    suggestions: list[ICDSuggestion] = []
    seen: set[str] = set()
    for entity in entities:
        suggestion = _map_entity_to_suggestion(mapper, entity.text, system=system)
        if suggestion and suggestion.kode not in seen:
            seen.add(suggestion.kode)
            suggestions.append(suggestion)
    return suggestions


def _check_claimed_code(
    kode_rs: str,
    ai_codes: set[str],
    ai_suggestions: list[ICDSuggestion],
    mapper: ICDMapper,
    *,
    system: Literal["icd10", "icd9"],
    mismatches: list[MismatchDetail],
) -> None:
    """Check whether a code claimed by the hospital is supported by AI analysis."""
    # Case 1: exact match — the AI also found this code
    if kode_rs in ai_codes:
        return

    # Case 2: code is in master data but AI didn't extract it from the resume
    entry = mapper.entries_by_code.get(kode_rs)
    if entry is None:
        # Unknown code — not in our master data at all
        mismatches.append(
            MismatchDetail(
                kode_rs=kode_rs,
                kode_saran_ai=None,
                deskripsi_saran_ai="",
                confidence_ai=0.0,
                alasan=f"Kode {kode_rs} tidak ditemukan dalam master data ICD.",
                severity="critical",
            )
        )
        return

    # The code exists in master data but AI didn't find evidence in the resume
    best_ai = ai_suggestions[0] if ai_suggestions else None
    severity = "warning"
    alasan = (
        f"Kode {kode_rs} ({entry.nama}) diklaim RS tetapi tidak ditemukan "
        f"bukti pendukung dalam resume medis."
    )

    if best_ai:
        alasan += (
            f" AI menyarankan kode {best_ai.kode} ({best_ai.deskripsi}) "
            f"dengan confidence {best_ai.confidence:.2f}."
        )
        # If the AI's best suggestion is very different, escalate severity
        if best_ai.kode[:3] != kode_rs[:3]:
            severity = "critical"

    mismatches.append(
        MismatchDetail(
            kode_rs=kode_rs,
            kode_saran_ai=best_ai.kode if best_ai else None,
            deskripsi_saran_ai=best_ai.deskripsi if best_ai else "",
            confidence_ai=best_ai.confidence if best_ai else 0.0,
            alasan=alasan,
            severity=severity,
        )
    )


def _build_audit_summary(
    claimed_codes: list,
    mismatches: list[MismatchDetail],
    is_consistent: bool,
) -> str:
    """Build a human-readable audit summary in Indonesian."""
    total = len(claimed_codes)
    if is_consistent:
        return (
            f"Audit selesai: seluruh {total} kode yang diklaim RS "
            f"konsisten dengan resume medis."
        )

    mismatch_count = len(mismatches)
    critical_count = sum(1 for m in mismatches if m.severity == "critical")
    warning_count = sum(1 for m in mismatches if m.severity == "warning")

    parts = [
        f"Audit selesai: ditemukan {mismatch_count} ketidaksesuaian "
        f"dari {total} kode yang diklaim RS."
    ]
    if critical_count:
        parts.append(f"{critical_count} ketidaksesuaian bersifat kritis.")
    if warning_count:
        parts.append(f"{warning_count} ketidaksesuaian bersifat peringatan.")
    parts.append("Diperlukan review manual oleh verifikator.")

    return " ".join(parts)
