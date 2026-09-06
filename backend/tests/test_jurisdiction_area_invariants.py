from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError


@pytest.mark.skipif(os.getenv("POSTGRES_TESTS") != "1", reason="requires migrated PostgreSQL")
def test_postgresql_enforces_immutable_published_jurisdiction_area_versions() -> None:
    """ADR-0021/ADR-0024 schema invariants: no real ZFM/ALC content is asserted here."""
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(
            text(
                """INSERT INTO organizations (id, name, slug, status, created_at, updated_at)
                VALUES ('PG-TEST-JURISDICTION-ORG', 'Synthetic Org', 'pg-test-jurisdiction-org',
                'ACTIVE', '2040-01-01T00:00:00Z', '2040-01-01T00:00:00Z')"""
            )
        )
        connection.execute(
            text(
                """INSERT INTO users (id, email, display_name, status, created_at)
                VALUES ('PG-TEST-JURISDICTION-USER', 'pg-test-jurisdiction@example.invalid',
                'Synthetic User', 'ACTIVE', '2040-01-01T00:00:00Z')"""
            )
        )
        connection.execute(
            text(
                """INSERT INTO legal_sources
                (id, source_type, number, year, issuing_authority, title, official_url,
                 publication_date, jurisdiction, notes, content_hash, is_synthetic, created_at)
                VALUES ('PG-TEST-JURISDICTION-SOURCE', 'SYNTHETIC', 'TEST', 2099,
                'SYNTHETIC AUTHORITY', 'Synthetic PostgreSQL source',
                'https://example.invalid/pg-jurisdiction-source', '2099-01-01', 'SYNTHETIC',
                'Fictitious', :hash, true, '2040-01-01T00:00:00Z')"""
            ),
            {"hash": "d" * 64},
        )
        connection.execute(
            text(
                """INSERT INTO tax_jurisdiction_areas
                (id, organization_id, area_type, code, official_name, created_at, created_by)
                VALUES ('PG-TEST-AREA', 'PG-TEST-JURISDICTION-ORG', 'ZFM', 'SYNTHETIC-AREA',
                'Synthetic area', '2040-01-01T00:00:00Z', 'PG-TEST-JURISDICTION-USER')"""
            )
        )
        connection.execute(
            text(
                """INSERT INTO tax_jurisdiction_area_versions
                (id, area_id, organization_id, version, lifecycle_status, legal_source_id,
                 legal_device, criteria, content_hash, valid_from, valid_to, recorded_at,
                 created_by)
                VALUES ('PG-TEST-AREA-V1', 'PG-TEST-AREA', 'PG-TEST-JURISDICTION-ORG', 1, 'DRAFT',
                'PG-TEST-JURISDICTION-SOURCE', 'SYNTHETIC DEVICE',
                CAST(:criteria AS jsonb), :hash, '2000-01-01', '2100-01-01',
                '2040-01-01T00:00:00Z', 'PG-TEST-JURISDICTION-USER')"""
            ),
            {"criteria": '{"synthetic":"true"}', "hash": "e" * 64},
        )

        transitions = (
            ("PG-JURISDICTION-EVENT-1", "DRAFT", "IN_REVIEW", "2040-01-02T00:00:00Z"),
            ("PG-JURISDICTION-EVENT-2", "IN_REVIEW", "APPROVED", "2040-01-03T00:00:00Z"),
            ("PG-JURISDICTION-EVENT-3", "APPROVED", "PUBLISHED", "2040-01-04T00:00:00Z"),
        )
        for event_id, old, new, occurred_at in transitions:
            connection.execute(
                text(
                    """INSERT INTO tax_jurisdiction_area_lifecycle_events
                    (id, area_version_id, from_status, to_status, occurred_at, actor_id, reason,
                     correlation_id)
                    VALUES (:id, 'PG-TEST-AREA-V1', :old, :new, :at,
                    'PG-TEST-JURISDICTION-USER', 'Synthetic integration test',
                    'pg-jurisdiction-test')"""
                ),
                {"id": event_id, "old": old, "new": new, "at": occurred_at},
            )
            projection = {
                "IN_REVIEW": "",
                "APPROVED": (
                    ", approved_at = :at, approved_by = 'PG-TEST-JURISDICTION-USER'"
                ),
                "PUBLISHED": (
                    ", published_at = :at, published_by = 'PG-TEST-JURISDICTION-USER'"
                ),
            }[new]
            connection.execute(
                text(
                    f"UPDATE tax_jurisdiction_area_versions SET lifecycle_status = :new"
                    f"{projection} WHERE id = 'PG-TEST-AREA-V1'"
                ),
                {"new": new, "at": occurred_at},
            )

        with pytest.raises(DBAPIError), connection.begin_nested():
            connection.execute(
                text(
                    "UPDATE tax_jurisdiction_area_versions SET criteria = '{}' "
                    "WHERE id = 'PG-TEST-AREA-V1'"
                )
            )
        with pytest.raises(DBAPIError), connection.begin_nested():
            connection.execute(
                text("DELETE FROM tax_jurisdiction_area_versions WHERE id = 'PG-TEST-AREA-V1'")
            )
        with pytest.raises(DBAPIError), connection.begin_nested():
            connection.execute(
                text(
                    "DELETE FROM tax_jurisdiction_area_lifecycle_events "
                    "WHERE id = 'PG-JURISDICTION-EVENT-1'"
                )
            )
