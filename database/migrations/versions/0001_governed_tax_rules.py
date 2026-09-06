"""Create governed synthetic tax-rule catalog.

Revision ID: 0001_governed_tax_rules
Revises: None
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_governed_tax_rules"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "legal_sources",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("number", sa.String(100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("issuing_authority", sa.String(200), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("official_url", sa.String(500), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("char_length(content_hash) = 64", name="ck_legal_source_hash_length"),
        sa.CheckConstraint("is_synthetic", name="ck_legal_source_synthetic_foundation"),
    )
    op.create_table(
        "tax_rule_identities",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.CheckConstraint("is_synthetic", name="ck_rule_identity_synthetic_foundation"),
    )
    op.create_table(
        "tax_rule_versions",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "rule_identity_id",
            sa.String(100),
            sa.ForeignKey("tax_rule_identities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("lifecycle_status", sa.String(30), nullable=False),
        sa.Column("jurisdiction", sa.String(100), nullable=False),
        sa.Column(
            "legal_source_id",
            sa.String(100),
            sa.ForeignKey("legal_sources.id", ondelete="RESTRICT"),
        ),
        sa.Column("legal_device", sa.String(300), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_for_review_at", sa.DateTime(timezone=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("approved_by", sa.String(100)),
        sa.Column("published_by", sa.String(100)),
        sa.Column("content", JSONB, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
        sa.UniqueConstraint("rule_identity_id", "version", name="uq_rule_identity_version"),
        sa.CheckConstraint("version > 0", name="ck_rule_version_positive"),
        sa.CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="ck_rule_validity"),
        sa.CheckConstraint("char_length(content_hash) = 64", name="ck_rule_content_hash_length"),
        sa.CheckConstraint(
            "lifecycle_status IN "
            "('DRAFT','IN_REVIEW','APPROVED','PUBLISHED','REJECTED','SUPERSEDED','WITHDRAWN')",
            name="ck_rule_lifecycle_status",
        ),
        sa.CheckConstraint(
            "lifecycle_status NOT IN ('APPROVED','PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR approved_at IS NOT NULL AND approved_by IS NOT NULL",
            name="ck_rule_approval_metadata",
        ),
        sa.CheckConstraint(
            "lifecycle_status NOT IN ('PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR published_at IS NOT NULL AND published_by IS NOT NULL "
            "AND legal_source_id IS NOT NULL AND legal_device <> ''",
            name="ck_rule_publication_metadata",
        ),
    )
    op.create_index(
        "ix_rule_versions_bitemporal",
        "tax_rule_versions",
        ["valid_from", "valid_to", "recorded_at"],
    )
    op.create_table(
        "rule_lifecycle_events",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "rule_version_id",
            sa.String(100),
            sa.ForeignKey("tax_rule_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(30), nullable=False),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("related_version", sa.Integer()),
        sa.Column("correlation_id", sa.String(100), nullable=False),
    )
    op.create_index(
        "ix_rule_events_version_time",
        "rule_lifecycle_events",
        ["rule_version_id", "occurred_at"],
    )
    op.create_table(
        "rulesets",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("published_by", sa.String(100)),
        sa.Column("fingerprint", sa.String(64), unique=True),
        sa.CheckConstraint("status IN ('DRAFT','PUBLISHED')", name="ck_ruleset_status"),
        sa.CheckConstraint(
            "status <> 'PUBLISHED' OR published_at IS NOT NULL AND published_by IS NOT NULL "
            "AND fingerprint IS NOT NULL",
            name="ck_ruleset_publication_metadata",
        ),
    )
    op.create_table(
        "ruleset_items",
        sa.Column(
            "ruleset_id",
            sa.String(100),
            sa.ForeignKey("rulesets.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "rule_version_id",
            sa.String(100),
            sa.ForeignKey("tax_rule_versions.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("ruleset_id", "position", name="uq_ruleset_position"),
    )
    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("known_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("operation_date", sa.Date(), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("engine_version", sa.String(100), nullable=False),
        sa.Column(
            "ruleset_id",
            sa.String(100),
            sa.ForeignKey("rulesets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ruleset_fingerprint", sa.String(64), nullable=False),
        sa.Column("input_facts", JSONB, nullable=False),
        sa.Column("outcome", JSONB, nullable=False),
        sa.Column("decision_trace", JSONB, nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.Column(
            "reproduced_from_id",
            sa.String(100),
            sa.ForeignKey("evaluations.id", ondelete="RESTRICT"),
        ),
        sa.CheckConstraint("char_length(input_hash) = 64", name="ck_evaluation_input_hash"),
        sa.CheckConstraint(
            "char_length(ruleset_fingerprint) = 64", name="ck_evaluation_ruleset_hash"
        ),
    )
    op.create_index("ix_evaluations_ruleset_time", "evaluations", ["ruleset_id", "evaluated_at"])
    op.create_table(
        "evaluation_rule_versions",
        sa.Column(
            "evaluation_id",
            sa.String(100),
            sa.ForeignKey("evaluations.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "rule_version_id",
            sa.String(100),
            sa.ForeignKey("tax_rule_versions.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("evaluation_id", "position", name="uq_evaluation_position"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.String(100), nullable=False),
        sa.Column("origin", sa.String(100), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.Column("metadata", JSONB, nullable=False),
    )
    op.create_index(
        "ix_audit_entity_time", "audit_events", ["entity_type", "entity_id", "occurred_at"]
    )
    _create_immutability_triggers()


def _create_immutability_triggers() -> None:
    op.execute(
        """
        CREATE FUNCTION prevent_append_only_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER rule_events_append_only
        BEFORE UPDATE OR DELETE ON rule_lifecycle_events
        FOR EACH ROW EXECUTE FUNCTION prevent_append_only_mutation();

        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION prevent_append_only_mutation();

        CREATE FUNCTION protect_rule_version_snapshot() RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'DELETE' AND OLD.lifecycle_status <> 'DRAFT' THEN
            RAISE EXCEPTION 'non-draft rule versions cannot be deleted';
          END IF;
          IF TG_OP = 'UPDATE' AND OLD.lifecycle_status <> 'DRAFT' AND (
            NEW.rule_identity_id IS DISTINCT FROM OLD.rule_identity_id OR
            NEW.version IS DISTINCT FROM OLD.version OR
            NEW.jurisdiction IS DISTINCT FROM OLD.jurisdiction OR
            NEW.legal_source_id IS DISTINCT FROM OLD.legal_source_id OR
            NEW.legal_device IS DISTINCT FROM OLD.legal_device OR
            NEW.valid_from IS DISTINCT FROM OLD.valid_from OR
            NEW.valid_to IS DISTINCT FROM OLD.valid_to OR
            NEW.recorded_at IS DISTINCT FROM OLD.recorded_at OR
            NEW.created_by IS DISTINCT FROM OLD.created_by OR
            NEW.content IS DISTINCT FROM OLD.content OR
            NEW.content_hash IS DISTINCT FROM OLD.content_hash OR
            NEW.metadata IS DISTINCT FROM OLD.metadata
          ) THEN
            RAISE EXCEPTION 'submitted rule snapshots are immutable';
          END IF;
          IF TG_OP = 'UPDATE' AND OLD.lifecycle_status IN ('SUPERSEDED','WITHDRAWN','REJECTED') THEN
            RAISE EXCEPTION 'terminal rule versions are immutable';
          END IF;
          IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER protect_rule_versions
        BEFORE UPDATE OR DELETE ON tax_rule_versions
        FOR EACH ROW EXECUTE FUNCTION protect_rule_version_snapshot();

        CREATE FUNCTION protect_ruleset_snapshot() RETURNS trigger AS $$
        DECLARE current_status text;
        BEGIN
          IF TG_TABLE_NAME = 'rulesets' THEN
            IF OLD.status = 'PUBLISHED' THEN
              RAISE EXCEPTION 'published rulesets are immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
          RETURN NEW;
          END IF;
          SELECT status INTO current_status FROM rulesets
            WHERE id = CASE WHEN TG_OP = 'DELETE' THEN OLD.ruleset_id ELSE NEW.ruleset_id END;
          IF current_status = 'PUBLISHED' THEN
            RAISE EXCEPTION 'published ruleset items are immutable';
          END IF;
          IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER protect_rulesets
        BEFORE UPDATE OR DELETE ON rulesets
        FOR EACH ROW EXECUTE FUNCTION protect_ruleset_snapshot();

        CREATE TRIGGER protect_ruleset_items
        BEFORE INSERT OR UPDATE OR DELETE ON ruleset_items
        FOR EACH ROW EXECUTE FUNCTION protect_ruleset_snapshot();
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS protect_ruleset_snapshot() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS protect_rule_version_snapshot() CASCADE")
    op.execute("DROP FUNCTION IF EXISTS prevent_append_only_mutation() CASCADE")
    op.drop_table("audit_events")
    op.drop_table("evaluation_rule_versions")
    op.drop_table("evaluations")
    op.drop_table("ruleset_items")
    op.drop_table("rulesets")
    op.drop_table("rule_lifecycle_events")
    op.drop_table("tax_rule_versions")
    op.drop_table("tax_rule_identities")
    op.drop_table("legal_sources")
