"""Harden lifecycle and ruleset invariants in PostgreSQL.

Revision ID: 0002_harden_governance
Revises: 0001_governed_tax_rules
Create Date: 2026-08-29
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_harden_governance"
down_revision: str | None = "0001_governed_tax_rules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION validate_rule_lifecycle_event() RETURNS trigger AS $$
        DECLARE current_status text;
        DECLARE recorded_time timestamptz;
        DECLARE last_event_time timestamptz;
        BEGIN
          SELECT lifecycle_status, recorded_at INTO current_status, recorded_time
            FROM tax_rule_versions WHERE id = NEW.rule_version_id FOR UPDATE;
          SELECT max(occurred_at) INTO last_event_time FROM rule_lifecycle_events
            WHERE rule_version_id = NEW.rule_version_id;
          IF current_status IS NULL OR current_status <> NEW.from_status THEN
            RAISE EXCEPTION 'lifecycle event does not continue current projection';
          END IF;
          IF NOT ((NEW.from_status = 'DRAFT' AND NEW.to_status = 'IN_REVIEW') OR
                  (NEW.from_status = 'IN_REVIEW' AND NEW.to_status IN ('APPROVED','REJECTED')) OR
                  (NEW.from_status = 'APPROVED' AND NEW.to_status = 'PUBLISHED') OR
                  (NEW.from_status = 'PUBLISHED' AND
                   NEW.to_status IN ('SUPERSEDED','WITHDRAWN'))) THEN
            RAISE EXCEPTION 'invalid lifecycle transition';
          END IF;
          IF NEW.occurred_at < recorded_time OR
             (last_event_time IS NOT NULL AND NEW.occurred_at <= last_event_time) THEN
            RAISE EXCEPTION 'lifecycle events must be chronological';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER validate_rule_events
        BEFORE INSERT ON rule_lifecycle_events
        FOR EACH ROW EXECUTE FUNCTION validate_rule_lifecycle_event();

        CREATE OR REPLACE FUNCTION protect_ruleset_snapshot() RETURNS trigger AS $$
        DECLARE current_status text;
        DECLARE target_ruleset_id text;
        DECLARE member_status text;
        BEGIN
          IF TG_TABLE_NAME = 'rulesets' THEN
            IF OLD.status = 'PUBLISHED' THEN
              RAISE EXCEPTION 'published rulesets are immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
          END IF;
          target_ruleset_id := CASE
            WHEN TG_OP = 'DELETE' THEN OLD.ruleset_id ELSE NEW.ruleset_id
          END;
          SELECT status INTO current_status FROM rulesets
            WHERE id = target_ruleset_id FOR UPDATE;
          IF current_status = 'PUBLISHED' THEN
            RAISE EXCEPTION 'published ruleset items are immutable';
          END IF;
          IF TG_OP = 'INSERT' THEN
            SELECT lifecycle_status INTO member_status FROM tax_rule_versions
              WHERE id = NEW.rule_version_id FOR UPDATE;
            IF member_status <> 'PUBLISHED' THEN
              RAISE EXCEPTION 'ruleset members must be published';
            END IF;
          END IF;
          IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS validate_rule_events ON rule_lifecycle_events")
    op.execute("DROP FUNCTION IF EXISTS validate_rule_lifecycle_event()")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION protect_ruleset_snapshot() RETURNS trigger AS $$
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
        """
    )
