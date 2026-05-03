"""
Pramana AI — Hospital Model.

Data rumah sakit (FKRTL) yang terdaftar di sistem.
"""
import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Hospital(Base):
    """Data rumah sakit yang terdaftar di sistem."""

    __tablename__ = "hospitals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    kode_rs: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    nama_rs: Mapped[str | None] = mapped_column(String(200))
    tipe_rs: Mapped[str | None] = mapped_column(String(5))  # A | B | C | D
    provinsi: Mapped[str | None] = mapped_column(String(100))
    kabupaten: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="hospital", lazy="selectin")
    claims = relationship("Claim", back_populates="hospital", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Hospital {self.kode_rs} - {self.nama_rs}>"
