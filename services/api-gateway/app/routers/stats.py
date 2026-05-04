"""
Pramana AI — API Gateway: Stats Router.

Task 4.4.3: GET /api/v1/stats/dashboard
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.jwt_auth import get_current_user
from app.models.claim import Claim
from app.models.risk_score import RiskScore
from app.schemas.stats import DashboardStats, RiskDistribution

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/stats", tags=["Statistics"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated statistics for the dashboard header cards.

    Returns total claims, counts per risk level (with percentages),
    pending verification count, and processed today count.
    """
    # Total claims
    total_q = await db.execute(select(func.count(Claim.id)))
    total = total_q.scalar() or 0

    # Risk level counts via join
    risk_q = await db.execute(
        select(RiskScore.risk_level, func.count(RiskScore.id))
        .group_by(RiskScore.risk_level)
    )
    risk_counts: dict[str, int] = {}
    for level, cnt in risk_q.all():
        if level:
            risk_counts[level] = cnt

    high = risk_counts.get("high", 0)
    medium = risk_counts.get("medium", 0)
    low = risk_counts.get("low", 0)

    def pct(n: int) -> float:
        return round(n / total * 100, 1) if total else 0.0

    # Pending (pending + in_review)
    pending_q = await db.execute(
        select(func.count(Claim.id)).where(Claim.status.in_(["pending", "in_review"]))
    )
    pending = pending_q.scalar() or 0

    # Processed today (approved or returned today)
    from datetime import date, datetime
    today_start = datetime.combine(date.today(), datetime.min.time())
    processed_q = await db.execute(
        select(func.count(Claim.id)).where(
            Claim.status.in_(["approved", "returned"]),
            Claim.updated_at >= today_start,
        )
    )
    processed = processed_q.scalar() or 0

    return DashboardStats(
        total_claims=total,
        pending_verification=pending,
        processed_today=processed,
        risk_high=RiskDistribution(count=high, percentage=pct(high)),
        risk_medium=RiskDistribution(count=medium, percentage=pct(medium)),
        risk_low=RiskDistribution(count=low, percentage=pct(low)),
        high_risk_delta=0,
    )
