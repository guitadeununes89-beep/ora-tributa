"""Add the governed NCM and NBS classification catalogs (Etapa 22).

Mirrors 0004_ibs_cbs_taxonomy.py's shape exactly, as two independent catalog
families (NCM codes and NBS codes have different validity/hierarchy rules
and no shared parent table is warranted - see docs/adr for the reasoning).

Revision ID: 0009_ncm_nbs_catalogs
Revises: 0008_composed_evaluations
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_ncm_nbs_catalogs"
down_revision: str | None = "0008_composed_evaluations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _create_catalog_family(prefix: str, *, code_length: int) -> None:
    op.create_table(
        f"{prefix}_catalogs",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "code", name=f"uq_{prefix}_catalog_org_code"),
        sa.UniqueConstraint("id", "organization_id", name=f"uq_{prefix}_catalog_tenant_identity"),
    )
    op.create_table(
        f"{prefix}_catalog_versions",
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
        sa.Column("code_count", sa.Integer(), nullable=False),
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
            name=f"ck_{prefix}_catalog_version_status",
        ),
        sa.CheckConstraint(
            "char_length(artifact_hash) = 64", name=f"ck_{prefix}_catalog_artifact_hash"
        ),
        sa.CheckConstraint(
            "char_length(normalized_hash) = 64", name=f"ck_{prefix}_catalog_normalized_hash"
        ),
        sa.ForeignKeyConstraint(
            ["catalog_id", "organization_id"],
            [f"{prefix}_catalogs.id", f"{prefix}_catalogs.organization_id"],
            ondelete="RESTRICT",
            name=f"fk_{prefix}_catalog_version_tenant",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["legal_source_id"], ["legal_sources.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["imported_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["validated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["submitted_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("catalog_id", "version", name=f"uq_{prefix}_catalog_version"),
        sa.UniqueConstraint("catalog_id", "artifact_hash", name=f"uq_{prefix}_catalog_artifact"),
    )
    op.create_index(
        f"ix_{prefix}_catalog_versions_org_status",
        f"{prefix}_catalog_versions",
        ["organization_id", "status", "publication_date"],
    )
    op.create_table(
        f"{prefix}_staging_rows",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("catalog_version_id", sa.String(100), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw_values", JSON_DOCUMENT, nullable=False),
        sa.Column("errors", JSON_DOCUMENT, nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], [f"{prefix}_catalog_versions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "catalog_version_id", "row_number", name=f"uq_{prefix}_staging_row"
        ),
    )
    code_columns = [
        sa.Column("catalog_version_id", sa.String(100), primary_key=True),
        sa.Column("code", sa.String(code_length), primary_key=True),
        sa.Column("level", sa.Integer(), nullable=False),
    ]
    if prefix == "ncm":
        code_columns += [
            sa.Column("is_final", sa.Boolean(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("valid_from", sa.Date()),
            sa.Column("valid_to", sa.Date()),
            sa.Column("legal_act", sa.String(200)),
        ]
    else:
        code_columns.append(sa.Column("description", sa.Text(), nullable=False))
    op.create_table(
        f"{prefix}_codes",
        *code_columns,
        sa.CheckConstraint(
            f"char_length(code) BETWEEN 2 AND {code_length}", name=f"ck_{prefix}_code_length"
        ),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], [f"{prefix}_catalog_versions.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        f"ix_{prefix}_codes_description",
        f"{prefix}_codes",
        ["catalog_version_id", "description"],
    )
    op.create_table(
        f"{prefix}_catalog_lifecycle_events",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("catalog_version_id", sa.String(100), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=False),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], [f"{prefix}_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        f"ix_{prefix}_catalog_events_version_time",
        f"{prefix}_catalog_lifecycle_events",
        ["catalog_version_id", "occurred_at"],
    )


def _create_immutability_triggers(prefix: str) -> None:
    op.execute(
        f"""
        CREATE FUNCTION protect_published_{prefix}_catalog() RETURNS trigger AS $$
        DECLARE version_status text;
        BEGIN
          IF TG_TABLE_NAME = '{prefix}_catalog_versions' THEN
            IF OLD.status = 'PUBLISHED' THEN
              RAISE EXCEPTION 'published {prefix} catalog versions are immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
          END IF;
          SELECT status INTO version_status
          FROM {prefix}_catalog_versions
          WHERE id = CASE WHEN TG_OP = 'DELETE'
            THEN OLD.catalog_version_id ELSE NEW.catalog_version_id END;
          IF version_status = 'PUBLISHED' THEN
            RAISE EXCEPTION 'published {prefix} catalog contents are immutable';
          END IF;
          IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in (
        f"{prefix}_catalog_versions",
        f"{prefix}_staging_rows",
        f"{prefix}_codes",
    ):
        operations = (
            "UPDATE OR DELETE" if table.endswith("_versions") else "INSERT OR UPDATE OR DELETE"
        )
        op.execute(
            f"CREATE TRIGGER trg_protect_published_{table} "
            f"BEFORE {operations} ON {table} FOR EACH ROW "
            f"EXECUTE FUNCTION protect_published_{prefix}_catalog()"
        )
    op.execute(
        f"CREATE TRIGGER trg_{prefix}_catalog_events_append_only BEFORE UPDATE OR DELETE "
        f"ON {prefix}_catalog_lifecycle_events FOR EACH ROW "
        "EXECUTE FUNCTION prevent_append_only_mutation()"
    )


def upgrade() -> None:
    _create_catalog_family("ncm", code_length=8)
    _create_catalog_family("nbs", code_length=20)
    if op.get_context().dialect.name == "postgresql":
        _create_immutability_triggers("ncm")
        _create_immutability_triggers("nbs")


def _drop_catalog_family(prefix: str) -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            f"DROP TRIGGER IF EXISTS trg_{prefix}_catalog_events_append_only "
            f"ON {prefix}_catalog_lifecycle_events"
        )
        for table in (f"{prefix}_catalog_versions", f"{prefix}_staging_rows", f"{prefix}_codes"):
            op.execute(f"DROP TRIGGER IF EXISTS trg_protect_published_{table} ON {table}")
        op.execute(f"DROP FUNCTION IF EXISTS protect_published_{prefix}_catalog()")
    op.drop_table(f"{prefix}_catalog_lifecycle_events")
    op.drop_index(f"ix_{prefix}_codes_description", table_name=f"{prefix}_codes")
    op.drop_table(f"{prefix}_codes")
    op.drop_table(f"{prefix}_staging_rows")
    op.drop_index(
        f"ix_{prefix}_catalog_versions_org_status", table_name=f"{prefix}_catalog_versions"
    )
    op.drop_table(f"{prefix}_catalog_versions")
    op.drop_table(f"{prefix}_catalogs")


def downgrade() -> None:
    _drop_catalog_family("nbs")
    _drop_catalog_family("ncm")
