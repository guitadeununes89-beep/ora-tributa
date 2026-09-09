"""Add batch tax classification tables (Etapa 23, ADR-0027).

A batch is an operational execution, not governed normative content - it
never goes through the curator/reviewer/approver/publisher lifecycle used by
rule/catalog tables (see ADR-0027, decision 11). It only needs to become
immutable once finished (COMPLETED/FAILED), mirroring the
`protect_published_{prefix}_catalog` shape from 0009 but gated on a terminal
processing state instead of a governance approval state.

Revision ID: 0010_classification_batches
Revises: 0009_ncm_nbs_catalogs
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_classification_batches"
down_revision: str | None = "0009_ncm_nbs_catalogs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "classification_batches",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_media_type", sa.String(200), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.Column("max_rows", sa.Integer(), nullable=False),
        sa.Column("ncm_catalog_version_id", sa.String(100)),
        sa.Column("nbs_catalog_version_id", sa.String(100)),
        sa.Column("taxonomy_catalog_version_id", sa.String(100)),
        sa.Column("engine_version", sa.String(100)),
        sa.Column("reprocessed_from_id", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('RECEIVED','VALIDATED','PROCESSING','COMPLETED','FAILED')",
            name="ck_classification_batch_status",
        ),
        sa.CheckConstraint("char_length(file_hash) = 64", name="ck_classification_batch_hash"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["ncm_catalog_version_id"], ["ncm_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["nbs_catalog_version_id"], ["nbs_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["taxonomy_catalog_version_id"],
            ["tax_classification_catalog_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reprocessed_from_id"], ["classification_batches.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "ix_classification_batches_org_created",
        "classification_batches",
        ["organization_id", "created_at"],
    )
    op.create_table(
        "classification_batch_rows",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("batch_id", sa.String(100), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_values", JSON_DOCUMENT, nullable=False),
        sa.Column("object_kind", sa.String(10)),
        sa.Column("internal_code", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("ncm", sa.String(8)),
        sa.Column("nbs", sa.String(20)),
        sa.Column("operation_date", sa.Date()),
        sa.Column("processing_status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("classification_status", sa.String(30)),
        sa.Column("evaluation_id", sa.String(100)),
        sa.Column("discovery_rule_codes", JSON_DOCUMENT),
        sa.Column("observations", sa.Text()),
        sa.CheckConstraint(
            "object_kind IS NULL OR object_kind IN ('GOOD','SERVICE','OTHER')",
            name="ck_classification_batch_row_object_kind",
        ),
        sa.CheckConstraint(
            "processing_status IN ('PENDING','PROCESSED','ERROR')",
            name="ck_classification_batch_row_processing_status",
        ),
        sa.CheckConstraint(
            "classification_status IS NULL OR classification_status IN "
            "('CONCLUSIVO','POSSIVEIS_ENQUADRAMENTOS','NECESSITA_VALIDACAO',"
            "'SEM_COBERTURA_NORMATIVA')",
            name="ck_classification_batch_row_classification_status",
        ),
        sa.ForeignKeyConstraint(["batch_id"], ["classification_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("batch_id", "row_number", name="uq_classification_batch_row"),
    )
    if op.get_context().dialect.name == "postgresql":
        _create_immutability_trigger()


def _create_immutability_trigger() -> None:
    op.execute(
        """
        CREATE FUNCTION protect_completed_batch() RETURNS trigger AS $$
        DECLARE batch_status text;
        BEGIN
          IF TG_TABLE_NAME = 'classification_batches' THEN
            IF OLD.status IN ('COMPLETED', 'FAILED') THEN
              RAISE EXCEPTION 'completed classification batches are immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
          END IF;
          SELECT status INTO batch_status
          FROM classification_batches
          WHERE id = CASE WHEN TG_OP = 'DELETE' THEN OLD.batch_id ELSE NEW.batch_id END;
          IF batch_status IN ('COMPLETED', 'FAILED') THEN
            RAISE EXCEPTION 'rows of a completed classification batch are immutable';
          END IF;
          IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE TRIGGER trg_protect_completed_batches "
        "BEFORE UPDATE OR DELETE ON classification_batches "
        "FOR EACH ROW EXECUTE FUNCTION protect_completed_batch()"
    )
    op.execute(
        "CREATE TRIGGER trg_protect_completed_batch_rows "
        "BEFORE INSERT OR UPDATE OR DELETE ON classification_batch_rows "
        "FOR EACH ROW EXECUTE FUNCTION protect_completed_batch()"
    )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS trg_protect_completed_batch_rows "
            "ON classification_batch_rows"
        )
        op.execute(
            "DROP TRIGGER IF EXISTS trg_protect_completed_batches ON classification_batches"
        )
        op.execute("DROP FUNCTION IF EXISTS protect_completed_batch()")
    op.drop_table("classification_batch_rows")
    op.drop_index("ix_classification_batches_org_created", table_name="classification_batches")
    op.drop_table("classification_batches")
