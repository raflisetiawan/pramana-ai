"""
Pramana AI — Risk Score Model.

Hasil risk scoring per klaim dari ML Engine.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RiskScore(Base):
    """Hasil risk scoring per klaim (0–100) dari ML Engine."""

    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id"),
        nullable=False,
        index=True,
    )

    # Score 0.00 - 100.00
    score = mapped_column(Numeric(5, 2))
    risk_level: Mapped[str | None] = mapped_column(
        String(10)
    )  # low | medium | high

    # SHAP values (JSON)
    shap_values = mapped_column(JSONB)
    top_features = mapped_column(JSONB)  # Top 5 contributing features

    model_version: Mapped[str | None] = mapped_column(String(20))
    scored_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    claim = relationship("Claim", back_populates="risk_score", lazy="selectin")

    def __repr__(self) -> str:
        return f"<RiskScore claim={self.claim_id} score={self.score} level={self.risk_level}>"
