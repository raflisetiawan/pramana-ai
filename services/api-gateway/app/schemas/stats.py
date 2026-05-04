"""
Pramana AI — Dashboard Stats Pydantic Schemas.

Response model for GET /api/v1/stats/dashboard.
"""
from pydantic import BaseModel


class RiskDistribution(BaseModel):
    """Count and percentage per risk level."""

    count: int
    percentage: float


class DashboardStats(BaseModel):
    """Aggregated stats for the dashboard header."""

    total_claims: int
    pending_verification: int
    processed_today: int

    risk_high: RiskDistribution
    risk_medium: RiskDistribution
    risk_low: RiskDistribution

    high_risk_delta: int = 0  # compared to yesterday
