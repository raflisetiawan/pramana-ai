"""
Pramana AI — NLP Coding Result Model.

Hasil NLP coding dari resume medis.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NlpCodingResult(Base):
    """Hasil ekstraksi koding ICD dari resume medis oleh NLP Engine."""

    __tablename__ = "nlp_coding_results"

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

    # Kode yang disarankan AI
    suggested_primary_icd: Mapped[str | None] = mapped_column(String(10))
    suggested_primary_conf = mapped_column(
        Numeric(4, 3)
    )  # 0.000 - 1.000

    suggested_secondary = mapped_column(JSONB)  # [{code, confidence}]
    suggested_procedures = mapped_column(JSONB)

    # Apakah sama dengan yang diklaim RS?
    has_mismatch: Mapped[bool] = mapped_column(Boolean, default=False)
    mismatch_detail = mapped_column(JSONB)

    processed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    claim = relationship(
        "Claim", back_populates="nlp_coding_result", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<NlpCodingResult claim={self.claim_id} "
            f"primary={self.suggested_primary_icd} "
            f"mismatch={self.has_mismatch}>"
        )
