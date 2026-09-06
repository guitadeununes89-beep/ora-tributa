"""Add the governed IBS/CBS classification catalog.

Revision ID: 0004_ibs_cbs_taxonomy
Revises: 0003_identity_tenancy
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_ibs_cbs_taxonomy"
down_revision: str | None = "0003_identity_tenancy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.drop_constraint("ck_legal_source_synthetic_foundation", "legal_sources", type_="check")
    op.create_table(
        "tax_classification_catalogs",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "code", name="uq_tax_catalog_org_code"),
        sa.UniqueConstraint("id", "organization_id", name="uq_tax_catalog_tenant_identity"),
    )
    op.create_table(
        "tax_classification_catalog_versions",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("catalog_id", sa.String(100), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("legal_source_id", sa.String(100), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("official_title", sa.String(500), nullable=False),
        sa.Column("official_url", sa.String(1000), nullable=False),
        sa.Column("technical_document", sa.String(300), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("consulted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("artifact_file_name", sa.String(500), nullable=False),
        sa.Column("artifact_path", sa.String(1000), nullable=False),
        sa.Column("artifact_media_type", sa.String(200), nullable=False),
        sa.Column("artifact_size", sa.Integer(), nullable=False),
        sa.Column("artifact_hash", sa.String(64), nullable=False),
        sa.Column("normalized_hash", sa.String(64), nullable=False),
        sa.Column("schema_signature", sa.String(64), nullable=False),
        sa.Column("cst_count", sa.Integer(), nullable=False),
        sa.Column("cclasstrib_count", sa.Integer(), nullable=False),
        sa.Column("import_report", JSON_DOCUMENT, nullable=False),
        sa.Column("imported_by", sa.String(100), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True)),
        sa.Column("validated_by", sa.String(100)),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("submitted_by", sa.String(100)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by", sa.String(100)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("published_by", sa.String(100)),
        sa.CheckConstraint(
            "status IN ('IMPORTED','VALIDATED','IN_REVIEW','APPROVED','PUBLISHED','FAILED')",
            name="ck_tax_catalog_version_status",
        ),
        sa.CheckConstraint("char_length(artifact_hash) = 64", name="ck_tax_catalog_artifact_hash"),
        sa.CheckConstraint(
            "char_length(normalized_hash) = 64", name="ck_tax_catalog_normalized_hash"
        ),
        sa.CheckConstraint("char_length(schema_signature) = 64", name="ck_tax_catalog_schema_hash"),
        sa.ForeignKeyConstraint(
            ["catalog_id", "organization_id"],
            ["tax_classification_catalogs.id", "tax_classification_catalogs.organization_id"],
            ondelete="RESTRICT",
            name="fk_tax_catalog_version_tenant",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["legal_source_id"], ["legal_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["imported_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["validated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["submitted_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("catalog_id", "version", name="uq_tax_catalog_version"),
        sa.UniqueConstraint("catalog_id", "artifact_hash", name="uq_tax_catalog_artifact"),
    )
    op.create_index(
        "ix_tax_catalog_versions_org_status",
        "tax_classification_catalog_versions",
        ["organization_id", "status", "publication_date"],
    )
    op.create_table(
        "tax_classification_staging_rows",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("catalog_version_id", sa.String(100), nullable=False),
        sa.Column("sheet_name", sa.String(200), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_values", JSON_DOCUMENT, nullable=False),
        sa.Column("errors", JSON_DOCUMENT, nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["tax_classification_catalog_versions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "catalog_version_id", "sheet_name", "row_number", name="uq_tax_staging_row"
        ),
    )
    op.create_table(
        "ibs_cbs_csts",
        sa.Column("catalog_version_id", sa.String(100), primary_key=True),
        sa.Column("code", sa.String(3), primary_key=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("indicators", JSON_DOCUMENT, nullable=False),
        sa.CheckConstraint("char_length(code) = 3", name="ck_ibs_cbs_cst_length"),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["tax_classification_catalog_versions.id"], ondelete="RESTRICT"
        ),
    )
    op.create_table(
        "ibs_cbs_tax_classifications",
        sa.Column("catalog_version_id", sa.String(100), primary_key=True),
        sa.Column("code", sa.String(6), primary_key=True),
        sa.Column("cst_code", sa.String(3), nullable=False),
        sa.Column("cst_description", sa.Text()),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("valid_from", sa.Date()),
        sa.Column("valid_to", sa.Date()),
        sa.Column("updated_on", sa.Date()),
        sa.Column("attributes", JSON_DOCUMENT, nullable=False),
        sa.CheckConstraint("char_length(code) = 6", name="ck_cclasstrib_length"),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["tax_classification_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["catalog_version_id", "cst_code"],
            ["ibs_cbs_csts.catalog_version_id", "ibs_cbs_csts.code"],
            ondelete="RESTRICT",
            name="fk_cclasstrib_cst_version",
        ),
    )
    op.create_index(
        "ix_cclasstrib_version_cst",
        "ibs_cbs_tax_classifications",
        ["catalog_version_id", "cst_code", "code"],
    )
    op.create_table(
        "catalog_lifecycle_events",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("catalog_version_id", sa.String(100), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=False),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["tax_classification_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_catalog_events_version_time",
        "catalog_lifecycle_events",
        ["catalog_version_id", "occurred_at"],
    )

    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION protect_published_tax_catalog() RETURNS trigger AS $$
            DECLARE version_status text;
            BEGIN
              IF TG_TABLE_NAME = 'tax_classification_catalog_versions' THEN
                IF OLD.status = 'PUBLISHED' THEN
                  RAISE EXCEPTION 'published catalog versions are immutable';
                END IF;
                IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
                RETURN NEW;
              END IF;
              SELECT status INTO version_status
              FROM tax_classification_catalog_versions
              WHERE id = CASE WHEN TG_OP = 'DELETE'
                THEN OLD.catalog_version_id ELSE NEW.catalog_version_id END;
              IF version_status = 'PUBLISHED' THEN
                RAISE EXCEPTION 'published catalog contents are immutable';
              END IF;
              IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        for table in (
            "tax_classification_catalog_versions",
            "tax_classification_staging_rows",
            "ibs_cbs_csts",
            "ibs_cbs_tax_classifications",
        ):
            operations = (
                "UPDATE OR DELETE"
                if table == "tax_classification_catalog_versions"
                else "INSERT OR UPDATE OR DELETE"
            )
            op.execute(
                f"CREATE TRIGGER trg_protect_published_{table} "
                f"BEFORE {operations} ON {table} FOR EACH ROW "
                "EXECUTE FUNCTION protect_published_tax_catalog()"
            )
        op.execute(
            "CREATE TRIGGER trg_catalog_events_append_only BEFORE UPDATE OR DELETE "
            "ON catalog_lifecycle_events FOR EACH ROW "
            "EXECUTE FUNCTION prevent_append_only_mutation()"
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            "DROP TRIGGER IF EXISTS trg_catalog_events_append_only ON catalog_lifecycle_events"
        )
        for table in (
            "tax_classification_catalog_versions",
            "tax_classification_staging_rows",
            "ibs_cbs_csts",
            "ibs_cbs_tax_classifications",
        ):
            op.execute(f"DROP TRIGGER IF EXISTS trg_protect_published_{table} ON {table}")
        op.execute("DROP FUNCTION IF EXISTS protect_published_tax_catalog()")
    op.drop_table("catalog_lifecycle_events")
    op.drop_table("ibs_cbs_tax_classifications")
    op.drop_table("ibs_cbs_csts")
    op.drop_table("tax_classification_staging_rows")
    op.drop_index(
        "ix_tax_catalog_versions_org_status", table_name="tax_classification_catalog_versions"
    )
    op.drop_table("tax_classification_catalog_versions")
    op.drop_table("tax_classification_catalogs")
    op.create_check_constraint(
        "ck_legal_source_synthetic_foundation", "legal_sources", "is_synthetic"
    )
