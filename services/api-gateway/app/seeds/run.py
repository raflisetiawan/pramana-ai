"""
Pramana AI — Seed Data Runner.

Populates the database with dummy data for development:
- 3 RS dummy
- 5 user dummy (admin, verifikator)
- 10 klaim dummy

Usage:
    python -m app.seeds.run
"""
import asyncio
import hashlib
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# ============================================================
# Fixed UUIDs for deterministic seeding (can reference in tests)
# ============================================================

# Hospital IDs
RS_SOETOMO_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
RS_SAIFUL_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
RS_HAJI_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")

# User IDs
USER_SUPERADMIN_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
USER_VERIFIKATOR1_ID = uuid.UUID("20000000-0000-0000-0000-000000000002")
USER_VERIFIKATOR2_ID = uuid.UUID("20000000-0000-0000-0000-000000000003")
USER_ADMIN_RS1_ID = uuid.UUID("20000000-0000-0000-0000-000000000004")
USER_ADMIN_RS2_ID = uuid.UUID("20000000-0000-0000-0000-000000000005")


def _hash_noka(noka: str) -> str:
    """Hash nomor kartu peserta with SHA-256."""
    return hashlib.sha256(noka.encode("utf-8")).hexdigest()


def _hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hash(password)


# ============================================================
# Seed Data Definitions
# ============================================================

HOSPITALS = [
    {
        "id": RS_SOETOMO_ID,
        "kode_rs": "0101R001",
        "nama_rs": "RSUD Dr. Soetomo",
        "tipe_rs": "A",
        "provinsi": "Jawa Timur",
        "kabupaten": "Kota Surabaya",
        "is_active": True,
    },
    {
        "id": RS_SAIFUL_ID,
        "kode_rs": "0101R002",
        "nama_rs": "RS Dr. Saiful Anwar",
        "tipe_rs": "B",
        "provinsi": "Jawa Timur",
        "kabupaten": "Kota Malang",
        "is_active": True,
    },
    {
        "id": RS_HAJI_ID,
        "kode_rs": "0101R003",
        "nama_rs": "RSU Haji Surabaya",
        "tipe_rs": "B",
        "provinsi": "Jawa Timur",
        "kabupaten": "Kota Surabaya",
        "is_active": True,
    },
]

USERS = [
    {
        "id": USER_SUPERADMIN_ID,
        "email": "admin@pramana.ai",
        "password_hash": _hash_password("admin123"),
        "role": "superadmin",
        "hospital_id": None,
        "is_active": True,
    },
    {
        "id": USER_VERIFIKATOR1_ID,
        "email": "verifikator1@bpjs.go.id",
        "password_hash": _hash_password("verif123"),
        "role": "verifikator_bpjs",
        "hospital_id": None,
        "is_active": True,
    },
    {
        "id": USER_VERIFIKATOR2_ID,
        "email": "verifikator2@bpjs.go.id",
        "password_hash": _hash_password("verif123"),
        "role": "verifikator_bpjs",
        "hospital_id": None,
        "is_active": True,
    },
    {
        "id": USER_ADMIN_RS1_ID,
        "email": "admin@rssoetomo.go.id",
        "password_hash": _hash_password("rsadmin123"),
        "role": "admin_rs",
        "hospital_id": RS_SOETOMO_ID,
        "is_active": True,
    },
    {
        "id": USER_ADMIN_RS2_ID,
        "email": "admin@rssaiful.go.id",
        "password_hash": _hash_password("rsadmin123"),
        "role": "admin_rs",
        "hospital_id": RS_SAIFUL_ID,
        "is_active": True,
    },
]

# Base date for generating claims
_base_date = date(2024, 1, 10)

CLAIMS = [
    {
        "no_sep": "0101R001240110000001",
        "rs_id": RS_SOETOMO_ID,
        "noka_hash": _hash_noka("0001234567890"),
        "diagnosa_utama": "I50.0",
        "diagnosa_sekunder": ["I10", "E11.9"],
        "prosedur": ["99.04"],
        "los": 5,
        "total_tagihan": Decimal("12500000.00"),
        "tarif_ina_cbgs": Decimal("10870000.00"),
        "tgl_masuk": _base_date,
        "tgl_pulang": _base_date + timedelta(days=5),
        "tgl_pengajuan": datetime(2024, 1, 16, 10, 0, 0),
        "status": "pending",
    },
    {
        "no_sep": "0101R001240111000002",
        "rs_id": RS_SOETOMO_ID,
        "noka_hash": _hash_noka("0001234567892"),
        "diagnosa_utama": "J18.9",
        "diagnosa_sekunder": ["J44.1"],
        "prosedur": [],
        "los": 3,
        "total_tagihan": Decimal("7800000.00"),
        "tarif_ina_cbgs": Decimal("7200000.00"),
        "tgl_masuk": _base_date + timedelta(days=1),
        "tgl_pulang": _base_date + timedelta(days=4),
        "tgl_pengajuan": datetime(2024, 1, 16, 10, 30, 0),
        "status": "pending",
    },
    {
        "no_sep": "0101R002240112000003",
        "rs_id": RS_SAIFUL_ID,
        "noka_hash": _hash_noka("0001234567893"),
        "diagnosa_utama": "K35.9",
        "diagnosa_sekunder": [],
        "prosedur": ["47.09"],
        "los": 2,
        "total_tagihan": Decimal("9200000.00"),
        "tarif_ina_cbgs": Decimal("8500000.00"),
        "tgl_masuk": _base_date + timedelta(days=2),
        "tgl_pulang": _base_date + timedelta(days=4),
        "tgl_pengajuan": datetime(2024, 1, 16, 11, 0, 0),
        "status": "in_review",
    },
    {
        "no_sep": "0101R002240113000004",
        "rs_id": RS_SAIFUL_ID,
        "noka_hash": _hash_noka("0001234567890"),
        "diagnosa_utama": "I21.9",
        "diagnosa_sekunder": ["I10", "E11.9", "I50.0"],
        "prosedur": ["36.06", "88.72"],
        "los": 7,
        "total_tagihan": Decimal("45000000.00"),
        "tarif_ina_cbgs": Decimal("28500000.00"),
        "tgl_masuk": _base_date + timedelta(days=3),
        "tgl_pulang": _base_date + timedelta(days=10),
        "tgl_pengajuan": datetime(2024, 1, 21, 9, 0, 0),
        "status": "pending",
    },
    {
        "no_sep": "0101R003240114000005",
        "rs_id": RS_HAJI_ID,
        "noka_hash": _hash_noka("0001234567891"),
        "diagnosa_utama": "E11.9",
        "diagnosa_sekunder": ["I10"],
        "prosedur": [],
        "los": 1,
        "total_tagihan": Decimal("3200000.00"),
        "tarif_ina_cbgs": Decimal("3100000.00"),
        "tgl_masuk": _base_date + timedelta(days=4),
        "tgl_pulang": _base_date + timedelta(days=5),
        "tgl_pengajuan": datetime(2024, 1, 16, 14, 0, 0),
        "status": "approved",
    },
    {
        "no_sep": "0101R003240115000006",
        "rs_id": RS_HAJI_ID,
        "noka_hash": _hash_noka("0001234567892"),
        "diagnosa_utama": "N18.5",
        "diagnosa_sekunder": ["I10", "E11.9"],
        "prosedur": ["39.95"],
        "los": 1,
        "total_tagihan": Decimal("4500000.00"),
        "tarif_ina_cbgs": Decimal("4200000.00"),
        "tgl_masuk": _base_date + timedelta(days=5),
        "tgl_pulang": _base_date + timedelta(days=6),
        "tgl_pengajuan": datetime(2024, 1, 17, 8, 0, 0),
        "status": "pending",
    },
    {
        "no_sep": "0101R001240116000007",
        "rs_id": RS_SOETOMO_ID,
        "noka_hash": _hash_noka("0001234567893"),
        "diagnosa_utama": "S72.0",
        "diagnosa_sekunder": [],
        "prosedur": ["79.35"],
        "los": 10,
        "total_tagihan": Decimal("32000000.00"),
        "tarif_ina_cbgs": Decimal("25000000.00"),
        "tgl_masuk": _base_date + timedelta(days=6),
        "tgl_pulang": _base_date + timedelta(days=16),
        "tgl_pengajuan": datetime(2024, 1, 27, 10, 0, 0),
        "status": "pending",
    },
    {
        "no_sep": "0101R002240117000008",
        "rs_id": RS_SAIFUL_ID,
        "noka_hash": _hash_noka("0001234567891"),
        "diagnosa_utama": "G40.9",
        "diagnosa_sekunder": [],
        "prosedur": [],
        "los": 2,
        "total_tagihan": Decimal("5100000.00"),
        "tarif_ina_cbgs": Decimal("4800000.00"),
        "tgl_masuk": _base_date + timedelta(days=7),
        "tgl_pulang": _base_date + timedelta(days=9),
        "tgl_pengajuan": datetime(2024, 1, 20, 9, 0, 0),
        "status": "returned",
    },
    {
        "no_sep": "0101R003240118000009",
        "rs_id": RS_HAJI_ID,
        "noka_hash": _hash_noka("0001234567890"),
        "diagnosa_utama": "M54.5",
        "diagnosa_sekunder": [],
        "prosedur": [],
        "los": 1,
        "total_tagihan": Decimal("2800000.00"),
        "tarif_ina_cbgs": Decimal("2700000.00"),
        "tgl_masuk": _base_date + timedelta(days=8),
        "tgl_pulang": _base_date + timedelta(days=9),
        "tgl_pengajuan": datetime(2024, 1, 20, 10, 0, 0),
        "status": "approved",
    },
    {
        "no_sep": "0101R001240119000010",
        "rs_id": RS_SOETOMO_ID,
        "noka_hash": _hash_noka("0001234567892"),
        "diagnosa_utama": "C34.9",
        "diagnosa_sekunder": ["J18.9", "R04.2"],
        "prosedur": ["33.24", "99.04"],
        "los": 14,
        "total_tagihan": Decimal("68000000.00"),
        "tarif_ina_cbgs": Decimal("42000000.00"),
        "tgl_masuk": _base_date + timedelta(days=9),
        "tgl_pulang": _base_date + timedelta(days=23),
        "tgl_pengajuan": datetime(2024, 2, 3, 11, 0, 0),
        "status": "pending",
    },
]


async def seed_database() -> None:
    """Insert all seed data into the database."""
    from sqlalchemy import text

    engine = create_async_engine(settings.async_database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM hospitals"))
        count = result.scalar()
        if count and count > 0:
            print("⚠️  Seed data already exists. Skipping.")
            await engine.dispose()
            return

        print("🌱 Seeding database...")

        # Insert hospitals
        for h in HOSPITALS:
            await session.execute(
                text("""
                    INSERT INTO hospitals (id, kode_rs, nama_rs, tipe_rs, provinsi, kabupaten, is_active)
                    VALUES (:id, :kode_rs, :nama_rs, :tipe_rs, :provinsi, :kabupaten, :is_active)
                """),
                h,
            )
        print(f"   ✅ {len(HOSPITALS)} rumah sakit")

        # Insert users
        for u in USERS:
            await session.execute(
                text("""
                    INSERT INTO users (id, email, password_hash, role, hospital_id, is_active)
                    VALUES (:id, :email, :password_hash, :role, :hospital_id, :is_active)
                """),
                u,
            )
        print(f"   ✅ {len(USERS)} users")

        # Insert claims
        for c in CLAIMS:
            await session.execute(
                text("""
                    INSERT INTO claims (
                        no_sep, rs_id, noka_hash, diagnosa_utama, diagnosa_sekunder,
                        prosedur, los, total_tagihan, tarif_ina_cbgs,
                        tgl_masuk, tgl_pulang, tgl_pengajuan, status
                    ) VALUES (
                        :no_sep, :rs_id, :noka_hash, :diagnosa_utama, :diagnosa_sekunder,
                        :prosedur, :los, :total_tagihan, :tarif_ina_cbgs,
                        :tgl_masuk, :tgl_pulang, :tgl_pengajuan, :status
                    )
                """),
                c,
            )
        print(f"   ✅ {len(CLAIMS)} klaim")

        await session.commit()
        print("🎉 Seed data berhasil di-insert!")

    await engine.dispose()


def main() -> None:
    """Entry point for `python -m app.seeds.run`."""
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
