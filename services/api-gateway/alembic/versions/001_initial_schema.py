"""initial_schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-05-03

Creates all 6 core tables: hospitals, users, claims, risk_scores,
nlp_coding_results, audit_logs.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- hospitals ---
    op.create_table(
        "hospitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("kode_rs", sa.String(20), unique=True, nullable=False),
        sa.Column("nama_rs", sa.String(200)),
        sa.Column("tipe_rs", sa.String(5)),
        sa.Column("provinsi", sa.String(100)),
        sa.Column("kabupaten", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
    )
    op.create_index("ix_hospitals_kode_rs", "hospitals", ["kode_rs"])

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(200), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("role", sa.String(30)),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("hospitals.id"), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- claims ---
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("no_sep", sa.String(20), unique=True, nullable=False),
        sa.Column("rs_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("hospitals.id"), nullable=True),
        sa.Column("noka_hash", sa.String(64), nullable=False),
        sa.Column("diagnosa_utama", sa.String(10)),
        sa.Column("diagnosa_sekunder", postgresql.ARRAY(sa.String(10))),
        sa.Column("prosedur", postgresql.ARRAY(sa.String(10))),
        sa.Column("los", sa.Integer()),
        sa.Column("total_tagihan", sa.Numeric(15, 2)),
        sa.Column("tarif_ina_cbgs", sa.Numeric(15, 2)),
        sa.Column("tgl_masuk", sa.Date()),
        sa.Column("tgl_pulang", sa.Date()),
        sa.Column("tgl_pengajuan", sa.DateTime()),
        sa.Column("status", sa.String(20), server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_claims_no_sep", "claims", ["no_sep"])

    # --- risk_scores ---
    op.create_table(
        "risk_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("score", sa.Numeric(5, 2)),
        sa.Column("risk_level", sa.String(10)),
        sa.Column("shap_values", postgresql.JSONB()),
        sa.Column("top_features", postgresql.JSONB()),
        sa.Column("model_version", sa.String(20)),
        sa.Column("scored_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_risk_scores_claim_id", "risk_scores", ["claim_id"])

    # --- nlp_coding_results ---
    op.create_table(
        "nlp_coding_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("suggested_primary_icd", sa.String(10)),
        sa.Column("suggested_primary_conf", sa.Numeric(4, 3)),
        sa.Column("suggested_secondary", postgresql.JSONB()),
        sa.Column("suggested_procedures", postgresql.JSONB()),
        sa.Column("has_mismatch", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("mismatch_detail", postgresql.JSONB()),
        sa.Column("processed_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_nlp_coding_results_claim_id", "nlp_coding_results", ["claim_id"])

    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(50)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_claim_id", "audit_logs", ["claim_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("nlp_coding_results")
    op.drop_table("risk_scores")
    op.drop_table("claims")
    op.drop_table("users")
    op.drop_table("hospitals")
