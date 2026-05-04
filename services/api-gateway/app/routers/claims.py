"""
Pramana AI — API Gateway: Claims Router.

Task 4.4.2: Claim endpoints.
- GET  /api/v1/claims          — list with filter + pagination
- GET  /api/v1/claims/{id}     — detail (risk score + NLP result)
- POST /api/v1/claims/{id}/approve
- POST /api/v1/claims/{id}/return
- POST /api/v1/claims/{id}/escalate
"""
from __future__ import annotations

import logging
import math
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.middleware.jwt_auth import get_current_user
from app.models.audit_log import AuditLog
from app.models.claim import Claim
from app.models.risk_score import RiskScore
from app.schemas.claims import (
    AuditLogOut,
    ClaimActionRequest,
    ClaimActionResponse,
    ClaimDetail,
    ClaimListResponse,
    ClaimSummary,
    HospitalOut,
    NlpCodingOut,
    RiskScoreOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/claims", tags=["Claims"])


def _summary(c: Claim) -> ClaimSummary:
    rs = c.risk_score
    return ClaimSummary(
        id=str(c.id),
        no_sep=c.no_sep,
        hospital_name=c.hospital.nama_rs if c.hospital else None,
        diagnosa_utama=c.diagnosa_utama,
        total_tagihan=float(c.total_tagihan) if c.total_tagihan else None,
        tarif_ina_cbgs=float(c.tarif_ina_cbgs) if c.tarif_ina_cbgs else None,
        los=c.los,
        tgl_pengajuan=c.tgl_pengajuan,
        status=c.status,
        risk_score=float(rs.score) if rs and rs.score else None,
        risk_level=rs.risk_level if rs else None,
    )


def _detail(c: Claim) -> ClaimDetail:
    hosp = None
    if c.hospital:
        hosp = HospitalOut(
            id=str(c.hospital.id), kode_rs=c.hospital.kode_rs,
            nama_rs=c.hospital.nama_rs, tipe_rs=c.hospital.tipe_rs,
        )
    import json
    def parse_json(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        return val

    risk = None
    if c.risk_score:
        r = c.risk_score
        risk = RiskScoreOut(
            score=float(r.score) if r.score else 0,
            risk_level=r.risk_level or "unknown",
            shap_values=parse_json(r.shap_values) or {},
            top_features=parse_json(r.top_features) or [],
            model_version=r.model_version or "",
            scored_at=r.scored_at,
        )
    nlp = None
    if c.nlp_coding_result:
        n = c.nlp_coding_result
        nlp = NlpCodingOut(
            suggested_primary_icd=n.suggested_primary_icd,
            suggested_primary_conf=float(n.suggested_primary_conf) if n.suggested_primary_conf else None,
            suggested_secondary=parse_json(n.suggested_secondary),
            suggested_procedures=parse_json(n.suggested_procedures),
            has_mismatch=n.has_mismatch,
            mismatch_detail=parse_json(n.mismatch_detail),
            processed_at=n.processed_at,
        )
    logs = []
    for lg in (c.audit_logs or []):
        logs.append(AuditLogOut(
            id=str(lg.id), action=lg.action, notes=lg.notes,
            user_email=lg.user.email if lg.user else None,
            user_role=lg.user.role if lg.user else None,
            created_at=lg.created_at,
        ))
    logs.sort(key=lambda x: x.created_at or datetime.min)

    return ClaimDetail(
        id=str(c.id), no_sep=c.no_sep, hospital=hosp,
        diagnosa_utama=c.diagnosa_utama,
        diagnosa_sekunder=parse_json(c.diagnosa_sekunder),
        prosedur=parse_json(c.prosedur), los=c.los,
        total_tagihan=float(c.total_tagihan) if c.total_tagihan else None,
        tarif_ina_cbgs=float(c.tarif_ina_cbgs) if c.tarif_ina_cbgs else None,
        tgl_masuk=c.tgl_masuk, tgl_pulang=c.tgl_pulang,
        tgl_pengajuan=c.tgl_pengajuan, status=c.status,
        risk_score=risk, nlp_coding=nlp, audit_logs=logs,
        created_at=c.created_at, updated_at=c.updated_at,
    )


# GET /api/v1/claims
@router.get("", response_model=ClaimListResponse)
async def list_claims(
    risk_level: Optional[str] = Query(None),
    hospital_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("risk_score"),
    sort_dir: str = Query("desc"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List claims with filter + pagination. Default sort: risk_score desc."""
    query = select(Claim).options(
        selectinload(Claim.hospital),
        selectinload(Claim.risk_score),
    )
    if status_filter:
        query = query.where(Claim.status == status_filter)
    if hospital_id:
        try:
            query = query.where(Claim.rs_id == uuid.UUID(hospital_id))
        except ValueError:
            pass
    if date_from:
        query = query.where(Claim.tgl_pengajuan >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.where(Claim.tgl_pengajuan <= datetime.combine(date_to, datetime.max.time()))
    if search:
        query = query.where(Claim.no_sep.ilike(f"%{search}%"))

    if risk_level or sort_by == "risk_score":
        query = query.outerjoin(RiskScore, RiskScore.claim_id == Claim.id)
    if risk_level:
        query = query.where(RiskScore.risk_level == risk_level)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    order_col = RiskScore.score if sort_by == "risk_score" else Claim.tgl_pengajuan
    query = query.order_by(order_col.desc().nullsfirst() if sort_dir == "desc" else order_col.asc().nullslast())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = [_summary(c) for c in result.unique().scalars().all()]

    return ClaimListResponse(
        items=items, total=total, page=page,
        page_size=page_size, total_pages=max(1, math.ceil(total / page_size)),
    )


# GET /api/v1/claims/{id}
@router.get("/{claim_id}", response_model=ClaimDetail)
async def get_claim_detail(
    claim_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full claim detail including risk score, NLP, audit trail."""
    try:
        cid_str = str(uuid.UUID(claim_id))  # validate + normalize
    except ValueError:
        raise HTTPException(400, "Claim ID format tidak valid.")

    result = await db.execute(
        select(Claim).where(cast(Claim.id, String) == cid_str).options(
            selectinload(Claim.hospital),
            selectinload(Claim.risk_score),
            selectinload(Claim.nlp_coding_result),
            selectinload(Claim.audit_logs).selectinload(AuditLog.user),
        )
    )
    claim = result.unique().scalar_one_or_none()
    if not claim:
        raise HTTPException(404, "Klaim tidak ditemukan.")
    return _detail(claim)


# Shared action logic
async def _do_action(
    claim_id: str, action: str, new_status: str,
    notes: str | None, user: dict, db: AsyncSession,
) -> ClaimActionResponse:
    try:
        cid_str = str(uuid.UUID(claim_id))  # validate + normalize
    except ValueError:
        raise HTTPException(400, "Claim ID format tidak valid.")

    result = await db.execute(select(Claim).where(cast(Claim.id, String) == cid_str))
    claim = result.scalar_one_or_none()
    if not claim:
        raise HTTPException(404, "Klaim tidak ditemukan.")
    if claim.status not in ("pending", "in_review"):
        raise HTTPException(409, f"Klaim status '{claim.status}' tidak dapat di-{action}.")

    claim.status = new_status
    uid_str = user.get("sub", str(uuid.uuid4()))
    db.add(AuditLog(claim_id=claim.id, user_id=uid_str, action=action, notes=notes))
    await db.flush()

    labels = {"approve": "disetujui", "return": "dikembalikan ke RS", "escalate": "dieskalasi"}
    return ClaimActionResponse(
        claim_id=claim_id, action=action, new_status=new_status,
        message=f"Klaim berhasil {labels.get(action, action)}.", success=True,
    )


@router.post("/{claim_id}/approve", response_model=ClaimActionResponse)
async def approve_claim(
    claim_id: str, body: ClaimActionRequest = ClaimActionRequest(),
    user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Approve claim — status → approved."""
    return await _do_action(claim_id, "approve", "approved", body.notes, user, db)


@router.post("/{claim_id}/return", response_model=ClaimActionResponse)
async def return_claim(
    claim_id: str, body: ClaimActionRequest,
    user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Return claim to RS — notes required."""
    if not body.notes or not body.notes.strip():
        raise HTTPException(422, "Catatan wajib diisi untuk mengembalikan klaim.")
    return await _do_action(claim_id, "return", "returned", body.notes, user, db)


@router.post("/{claim_id}/escalate", response_model=ClaimActionResponse)
async def escalate_claim(
    claim_id: str, body: ClaimActionRequest,
    user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    """Escalate claim to supervisor — notes required."""
    if not body.notes or not body.notes.strip():
        raise HTTPException(422, "Catatan wajib diisi untuk eskalasi klaim.")
    return await _do_action(claim_id, "escalate", "escalated", body.notes, user, db)
