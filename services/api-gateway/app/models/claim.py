"""
Pramana AI — Claim Model.

Data klaim yang masuk dari RS, termasuk data klinis dan finansial.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Claim(Base):
    """Klaim yang diajukan RS ke BPJS untuk diverifikasi."""

    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    no_sep: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    rs_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id"),
        nullable=True,
    )

    # Data pasien (di-hash, bukan plaintext)
    noka_hash: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # SHA-256 dari nomor kartu

    # Data klinis
    diagnosa_utama: Mapped[str | None] = mapped_column(
        String(10)
    )  # Kode ICD-10
    diagnosa_sekunder: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(10))
    )  # Array kode ICD-10
    prosedur: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(10))
    )  # Array kode ICD-9-CM
    los: Mapped[int | None] = mapped_column(Integer)  # Length of Stay (hari)

    # Data finansial
    total_tagihan = mapped_column(Numeric(15, 2))
    tarif_ina_cbgs = mapped_column(Numeric(15, 2))

    # Data waktu
    tgl_masuk: Mapped[date | None] = mapped_column(Date)
    tgl_pulang: Mapped[date | None] = mapped_column(Date)
    tgl_pengajuan: Mapped[datetime | None] = mapped_column(DateTime)

    # Status: pending | in_review | approved | rejected | returned
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    hospital = relationship("Hospital", back_populates="claims", lazy="selectin")
    risk_score = relationship(
        "RiskScore", back_populates="claim", uselist=False, lazy="selectin"
    )
    nlp_coding_result = relationship(
        "NlpCodingResult", back_populates="claim", uselist=False, lazy="selectin"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="claim", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Claim {self.no_sep} status={self.status}>"
