"""
Pramana AI — Integration Test Fixtures for API Gateway.

Uses in-memory SQLite with patched PostgreSQL column types.
"""
import json
import os
import sqlite3
import sys
import uuid
from datetime import date, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Float, String, Text, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure api-gateway app is importable
_gateway_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "services", "api-gateway")
sys.path.insert(0, os.path.abspath(_gateway_dir))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.middleware.jwt_auth import create_access_token, hash_password  # noqa: E402

# Register sqlite3 adapter for UUID so binding works
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))

# ── Stable test IDs ──
HOSPITAL_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_RS_ID = "00000000-0000-0000-0000-000000000010"
VERIFIKATOR_ID = "00000000-0000-0000-0000-000000000020"
CLAIM_LOW_ID = "00000000-0000-0000-0000-000000001001"
CLAIM_MED_ID = "00000000-0000-0000-0000-000000001002"
CLAIM_HIGH_ID = "00000000-0000-0000-0000-000000001003"

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_patched = False


def _patch_columns_for_sqlite():
    """Replace PostgreSQL-specific column types with SQLite-compatible ones."""
    global _patched
    if _patched:
        return
    for table in Base.metadata.tables.values():
        for col in table.columns:
            tn = type(col.type).__name__
            if tn == "ARRAY":
                col.type = Text()
            elif tn == "UUID":
                col.type = String(36)
            elif tn in ("JSONB", "JSON"):
                col.type = Text()
            elif tn == "Numeric":
                col.type = Float()
    _patched = True


@pytest_asyncio.fixture
async def db_engine():
    _patch_columns_for_sqlite()
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


async def _seed_database(session: AsyncSession):
    """Use raw SQL to insert seed data (avoids ORM UUID type issues on SQLite)."""
    pw = hash_password("password123")

    # Hospital
    await session.execute(text(
        "INSERT INTO hospitals (id, kode_rs, nama_rs, tipe_rs, provinsi, kabupaten, is_active) "
        "VALUES (:id, :kode, :nama, :tipe, :prov, :kab, :active)"
    ), {"id": HOSPITAL_ID, "kode": "0301R001", "nama": "RSUD Dr. Soetomo Surabaya",
        "tipe": "B", "prov": "Jawa Timur", "kab": "Surabaya", "active": 1})

    # Users
    await session.execute(text(
        "INSERT INTO users (id, email, password_hash, role, hospital_id, is_active) "
        "VALUES (:id, :email, :pw, :role, :hid, :active)"
    ), {"id": ADMIN_RS_ID, "email": "admin.rs@soetomo.go.id", "pw": pw,
        "role": "admin_rs", "hid": HOSPITAL_ID, "active": 1})
    await session.execute(text(
        "INSERT INTO users (id, email, password_hash, role, hospital_id, is_active) "
        "VALUES (:id, :email, :pw, :role, :hid, :active)"
    ), {"id": VERIFIKATOR_ID, "email": "rina@bpjs.go.id", "pw": pw,
        "role": "verifikator_bpjs", "hid": None, "active": 1})

    # Claim 1: LOW risk
    await session.execute(text(
        "INSERT INTO claims (id, no_sep, rs_id, noka_hash, diagnosa_utama, los, "
        "total_tagihan, tarif_ina_cbgs, tgl_masuk, tgl_pulang, tgl_pengajuan, status) "
        "VALUES (:id, :sep, :rs, :noka, :dx, :los, :tag, :tarif, :tm, :tp, :tpj, :st)"
    ), {"id": CLAIM_LOW_ID, "sep": "0301R00120250101001", "rs": HOSPITAL_ID,
        "noka": "hash_low_001", "dx": "E11.9", "los": 3,
        "tag": 3200000, "tarif": 3400000,
        "tm": "2025-01-11", "tp": "2025-01-14", "tpj": "2025-01-14 09:00:00", "st": "pending"})

    # Claim 2: MEDIUM risk
    await session.execute(text(
        "INSERT INTO claims (id, no_sep, rs_id, noka_hash, diagnosa_utama, los, "
        "total_tagihan, tarif_ina_cbgs, tgl_masuk, tgl_pulang, tgl_pengajuan, status) "
        "VALUES (:id, :sep, :rs, :noka, :dx, :los, :tag, :tarif, :tm, :tp, :tpj, :st)"
    ), {"id": CLAIM_MED_ID, "sep": "0301R00120250101002", "rs": HOSPITAL_ID,
        "noka": "hash_med_002", "dx": "J18.9", "los": 4,
        "tag": 7800000, "tarif": 7200000,
        "tm": "2025-01-11", "tp": "2025-01-15", "tpj": "2025-01-15 10:00:00", "st": "pending"})

    # Claim 3: HIGH risk (upcoding)
    await session.execute(text(
        "INSERT INTO claims (id, no_sep, rs_id, noka_hash, diagnosa_utama, los, "
        "total_tagihan, tarif_ina_cbgs, tgl_masuk, tgl_pulang, tgl_pengajuan, status) "
        "VALUES (:id, :sep, :rs, :noka, :dx, :los, :tag, :tarif, :tm, :tp, :tpj, :st)"
    ), {"id": CLAIM_HIGH_ID, "sep": "0301R00120250101003", "rs": HOSPITAL_ID,
        "noka": "hash_high_003", "dx": "I21.0", "los": 6,
        "tag": 22400000, "tarif": 18000000,
        "tm": "2025-01-07", "tp": "2025-01-13", "tpj": "2025-01-13 11:00:00", "st": "in_review"})

    # Risk scores
    rs_data = [
        (str(uuid.uuid4()), CLAIM_LOW_ID, 18, "low",
         json.dumps({"rasio_terhadap_ina_cbgs": -0.03, "los": -0.02}),
         json.dumps(["Klaim dalam parameter normal"]), "v1.0.0"),
        (str(uuid.uuid4()), CLAIM_MED_ID, 58, "medium",
         json.dumps({"rasio_terhadap_ina_cbgs": 0.15, "tagihan_per_hari": 0.10, "los": 0.06}),
         json.dumps(["Tagihan 8% di atas tarif INA-CBGs standar"]), "v1.0.0"),
        (str(uuid.uuid4()), CLAIM_HIGH_ID, 91, "high",
         json.dumps({"rasio_terhadap_ina_cbgs": 0.35, "tagihan_per_hari": 0.22,
                      "pola_historis_rs": 0.14, "jumlah_prosedur": 0.06, "diagnosa_utama": -0.04}),
         json.dumps(["Tagihan 24% di atas tarif INA-CBGs untuk AMI",
                      "Tagihan per hari sangat tinggi dibanding RS setipe"]), "v1.0.0"),
    ]
    for rid, cid, score, level, shap, features, ver in rs_data:
        await session.execute(text(
            "INSERT INTO risk_scores (id, claim_id, score, risk_level, shap_values, top_features, model_version) "
            "VALUES (:id, :cid, :sc, :rl, :sv, :tf, :mv)"
        ), {"id": rid, "cid": cid, "sc": score, "rl": level, "sv": shap, "tf": features, "mv": ver})

    # NLP coding results
    nlp_data = [
        (str(uuid.uuid4()), CLAIM_LOW_ID, "E11.9", 0.93, None, None, 0, None),
        (str(uuid.uuid4()), CLAIM_MED_ID, "J18.9", 0.88, None, None, 0, None),
        (str(uuid.uuid4()), CLAIM_HIGH_ID, "I21.9", 0.72, None,
         json.dumps([{"code": "36.01", "confidence": 0.85}]), 1,
         json.dumps([{"field": "diagnosa_utama", "claimed": "I21.0",
                       "suggested": "I21.9", "reason": "Kode lebih spesifik"}])),
    ]
    for nid, cid, icd, conf, sec, proc, mismatch, detail in nlp_data:
        await session.execute(text(
            "INSERT INTO nlp_coding_results "
            "(id, claim_id, suggested_primary_icd, suggested_primary_conf, "
            "suggested_secondary, suggested_procedures, has_mismatch, mismatch_detail) "
            "VALUES (:id, :cid, :icd, :conf, :sec, :proc, :mm, :det)"
        ), {"id": nid, "cid": cid, "icd": icd, "conf": conf,
            "sec": sec, "proc": proc, "mm": mismatch, "det": detail})

    # Audit log
    await session.execute(text(
        "INSERT INTO audit_logs (id, claim_id, user_id, action, notes) "
        "VALUES (:id, :cid, :uid, :act, :notes)"
    ), {"id": str(uuid.uuid4()), "cid": CLAIM_HIGH_ID,
        "uid": ADMIN_RS_ID, "act": "submit", "notes": None})

    await session.commit()


@pytest_asyncio.fixture
async def seeded_db(db_engine, db_session):
    await _seed_database(db_session)
    yield db_session


@pytest_asyncio.fixture
async def client(db_engine, seeded_db):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _make_token(user_id: str, email: str, role: str) -> str:
    return create_access_token(subject=user_id, extra={"email": email, "role": role})


@pytest.fixture
def admin_rs_token():
    return _make_token(ADMIN_RS_ID, "admin.rs@soetomo.go.id", "admin_rs")


@pytest.fixture
def verifikator_token():
    return _make_token(VERIFIKATOR_ID, "rina@bpjs.go.id", "verifikator_bpjs")


@pytest.fixture
def admin_rs_headers(admin_rs_token):
    return {"Authorization": f"Bearer {admin_rs_token}"}


@pytest.fixture
def verifikator_headers(verifikator_token):
    return {"Authorization": f"Bearer {verifikator_token}"}
