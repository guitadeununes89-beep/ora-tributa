from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError


@pytest.mark.skipif(os.getenv("POSTGRES_TESTS") != "1", reason="requires migrated PostgreSQL")
def test_postgresql_enforces_append_only_snapshots_and_rulesets() -> None:
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(
            text(
                """INSERT INTO legal_sources
                (id, source_type, number, year, issuing_authority, title, official_url,
                 publication_date, jurisdiction, notes, content_hash, is_synthetic, created_at)
                VALUES ('PG-TEST-SOURCE', 'SYNTHETIC', 'TEST', 2099, 'SYNTHETIC AUTHORITY',
                'Synthetic PostgreSQL source', 'https://example.invalid/pg-source', '2099-01-01',
                'SYNTHETIC', 'Fictitious', :hash, true, '2040-01-01T00:00:00Z')"""
            ),
            {"hash": "a" * 64},
        )
        connection.execute(
            text(
                """INSERT INTO tax_rule_identities
                (id, code, title, description, is_synthetic, created_at, created_by)
                VALUES ('PG-TEST-RULE', 'TEST-PG-RULE', 'Synthetic rule', 'Fictitious', true,
                '2040-01-01T00:00:00Z', 'author')"""
            )
        )
        connection.execute(
            text(
                """INSERT INTO tax_rule_versions
                (id, rule_identity_id, version, lifecycle_status, jurisdiction, legal_source_id,
                 legal_device, valid_from, valid_to, recorded_at, created_by, content, content_hash,
                 metadata)
                VALUES ('PG-TEST-RULE-V1', 'PG-TEST-RULE', 1, 'DRAFT', 'SYNTHETIC',
                'PG-TEST-SOURCE', 'SYNTHETIC DEVICE', '2000-01-01', '2100-01-01',
                '2040-01-01T00:00:00Z', 'author', CAST(:content AS jsonb), :hash,
                CAST('{"synthetic":"true"}' AS jsonb))"""
            ),
            {"content": '{"implementation_key":"SYNTHETIC_RULE_A_V1"}', "hash": "b" * 64},
        )
        transitions = (
            ("PG-EVENT-1", "DRAFT", "IN_REVIEW", "2040-01-02T00:00:00Z"),
            ("PG-EVENT-2", "IN_REVIEW", "APPROVED", "2040-01-03T00:00:00Z"),
            ("PG-EVENT-3", "APPROVED", "PUBLISHED", "2040-01-04T00:00:00Z"),
        )
        for event_id, old, new, occurred_at in transitions:
            connection.execute(
                text(
                    """INSERT INTO rule_lifecycle_events
                    (id, rule_version_id, from_status, to_status, occurred_at, actor_id, reason,
                     correlation_id)
                    VALUES (:id, 'PG-TEST-RULE-V1', :old, :new, :at, 'synthetic-actor',
                    'Synthetic integration test', 'pg-test')"""
                ),
                {"id": event_id, "old": old, "new": new, "at": occurred_at},
            )
            projection = {
                "IN_REVIEW": "submitted_for_review_at = :at",
                "APPROVED": "approved_at = :at, approved_by = 'reviewer'",
                "PUBLISHED": "published_at = :at, published_by = 'publisher'",
            }[new]
            connection.execute(
                text(
                    f"UPDATE tax_rule_versions SET lifecycle_status = :new, {projection} "
                    "WHERE id = 'PG-TEST-RULE-V1'"
                ),
                {"new": new, "at": occurred_at},
            )

        connection.execute(
            text(
                """INSERT INTO rulesets
                (id, name, version, status, created_at, created_by)
                VALUES ('PG-TEST-RULESET', 'Synthetic ruleset', '1', 'DRAFT',
                '2040-01-05T00:00:00Z', 'curator')"""
            )
        )
        connection.execute(
            text(
                """INSERT INTO ruleset_items (ruleset_id, rule_version_id, position)
                VALUES ('PG-TEST-RULESET', 'PG-TEST-RULE-V1', 1)"""
            )
        )
        connection.execute(
            text(
                """UPDATE rulesets SET status = 'PUBLISHED', published_at =
                '2040-01-06T00:00:00Z', published_by = 'publisher', fingerprint = :hash
                WHERE id = 'PG-TEST-RULESET'"""
            ),
            {"hash": "c" * 64},
        )

        with pytest.raises(DBAPIError), connection.begin_nested():
            connection.execute(
                text("UPDATE tax_rule_versions SET content = '{}' WHERE id = 'PG-TEST-RULE-V1'")
            )
        with pytest.raises(DBAPIError), connection.begin_nested():
            connection.execute(
                text("UPDATE rulesets SET name = 'changed' WHERE id = 'PG-TEST-RULESET'")
            )
        with pytest.raises(DBAPIError), connection.begin_nested():
            connection.execute(text("DELETE FROM rule_lifecycle_events WHERE id = 'PG-EVENT-1'"))
