"""Add the governed tax jurisdiction area schema (ADR-0021, ADR-0024).

No real ZFM/ALC territorial data is loaded by this migration; only the governed,
bitemporal cadastro described by ADR-0024. Populating real areas is a separate,
legally-sourced governed load.

Revision ID: 0007_tax_jurisdiction_areas
Revises: 0006_first_real_tax_rule
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_tax_jurisdiction_areas"
down_revision: str | None = "0006_first_real_tax_rule"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "tax_jurisdiction_areas",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("area_type", sa.String(20), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("official_name", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "code", name="uq_jurisdiction_area_org_code"),
        sa.UniqueConstraint(
            "id", "organization_id", name="uq_jurisdiction_area_tenant_identity"
        ),
        sa.CheckConstraint("area_type IN ('ZFM','ALC')", name="ck_jurisdiction_area_type"),
    )
    op.create_table(
        "tax_jurisdiction_area_versions",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("area_id", sa.String(100), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("lifecycle_status", sa.String(30), nullable=False),
        sa.Column("legal_source_id", sa.String(100), nullable=False),
        sa.Column("legal_device", sa.String(300), nullable=False),
        sa.Column("criteria", JSON_DOCUMENT, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by", sa.String(100)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("published_by", sa.String(100)),
        sa.ForeignKeyConstraint(
            ["area_id", "organization_id"],
            ["tax_jurisdiction_areas.id", "tax_jurisdiction_areas.organization_id"],
            ondelete="RESTRICT",
            name="fk_jurisdiction_area_version_tenant",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["legal_source_id"], ["legal_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("area_id", "version", name="uq_jurisdiction_area_version"),
        sa.CheckConstraint("version > 0", name="ck_jurisdiction_area_version_positive"),
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_to > valid_from", name="ck_jurisdiction_area_validity"
        ),
        sa.CheckConstraint(
            "char_length(content_hash) = 64", name="ck_jurisdiction_area_content_hash_length"
        ),
        sa.CheckConstraint(
            "lifecycle_status IN "
            "('DRAFT','IN_REVIEW','APPROVED','PUBLISHED','REJECTED','SUPERSEDED','WITHDRAWN')",
            name="ck_jurisdiction_area_lifecycle_status",
        ),
        sa.CheckConstraint(
            "lifecycle_status NOT IN ('APPROVED','PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR approved_at IS NOT NULL AND approved_by IS NOT NULL",
            name="ck_jurisdiction_area_approval_metadata",
        ),
        sa.CheckConstraint(
            "lifecycle_status NOT IN ('PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR published_at IS NOT NULL AND published_by IS NOT NULL",
            name="ck_jurisdiction_area_publication_metadata",
        ),
    )
    op.create_index(
        "ix_jurisdiction_area_versions_bitemporal",
        "tax_jurisdiction_area_versions",
        ["valid_from", "valid_to", "recorded_at"],
    )
    op.create_table(
        "tax_jurisdiction_area_lifecycle_events",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("area_version_id", sa.String(100), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=False),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["area_version_id"], ["tax_jurisdiction_area_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_jurisdiction_area_events_version_time",
        "tax_jurisdiction_area_lifecycle_events",
        ["area_version_id", "occurred_at"],
    )

    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION protect_jurisdiction_area_version_snapshot() RETURNS trigger AS $$
            BEGIN
              IF TG_OP = 'DELETE' AND OLD.lifecycle_status <> 'DRAFT' THEN
                RAISE EXCEPTION 'non-draft jurisdiction area versions cannot be deleted';
              END IF;
              IF TG_OP = 'UPDATE' AND OLD.lifecycle_status <> 'DRAFT' AND (
                NEW.area_id IS DISTINCT FROM OLD.area_id OR
                NEW.version IS DISTINCT FROM OLD.version OR
                NEW.legal_source_id IS DISTINCT FROM OLD.legal_source_id OR
                NEW.legal_device IS DISTINCT FROM OLD.legal_device OR
                NEW.criteria IS DISTINCT FROM OLD.criteria OR
                NEW.content_hash IS DISTINCT FROM OLD.content_hash OR
                NEW.valid_from IS DISTINCT FROM OLD.valid_from OR
                NEW.valid_to IS DISTINCT FROM OLD.valid_to OR
                NEW.recorded_at IS DISTINCT FROM OLD.recorded_at OR
                NEW.created_by IS DISTINCT FROM OLD.created_by
              ) THEN
                RAISE EXCEPTION 'submitted jurisdiction area snapshots are immutable';
              END IF;
              IF TG_OP = 'UPDATE' AND OLD.lifecycle_status IN
                ('SUPERSEDED','WITHDRAWN','REJECTED') THEN
                RAISE EXCEPTION 'terminal jurisdiction area versions are immutable';
              END IF;
              IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER protect_jurisdiction_area_versions
            BEFORE UPDATE OR DELETE ON tax_jurisdiction_area_versions
            FOR EACH ROW EXECUTE FUNCTION protect_jurisdiction_area_version_snapshot();

            CREATE TRIGGER jurisdiction_area_events_append_only
            BEFORE UPDATE OR DELETE ON tax_jurisdiction_area_lifecycle_events
            FOR EACH ROW EXECUTE FUNCTION prevent_append_only_mutation();
            """
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS jurisdiction_area_events_append_only "
            "ON tax_jurisdiction_area_lifecycle_events"
        )
        op.execute(
            "DROP TRIGGER IF EXISTS protect_jurisdiction_area_versions "
            "ON tax_jurisdiction_area_versions"
        )
        op.execute("DROP FUNCTION IF EXISTS protect_jurisdiction_area_version_snapshot() CASCADE")
    op.drop_table("tax_jurisdiction_area_lifecycle_events")
    op.drop_index(
        "ix_jurisdiction_area_versions_bitemporal", table_name="tax_jurisdiction_area_versions"
    )
    op.drop_table("tax_jurisdiction_area_versions")
    op.drop_table("tax_jurisdiction_areas")
