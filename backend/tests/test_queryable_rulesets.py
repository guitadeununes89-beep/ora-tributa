from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository


@pytest.mark.skipif(os.getenv("POSTGRES_TESTS") != "1", reason="requires migrated PostgreSQL")
def test_queryable_rulesets_excludes_published_rulesets_that_bundle_other_rules() -> None:
    """Reproduces the exact shape of the Etapa 11 bug (CLAUDE_STATUS.md): a rule can be
    PUBLISHED and still belong to a PUBLISHED ruleset that bundles another, mutually
    exclusive rule. That bundled ruleset must never be reported as queryable for either
    rule - only the single-rule ruleset should."""
    engine = create_engine(os.environ["DATABASE_URL"])
    with Session(engine) as session:
        session.execute(
            text(
                """INSERT INTO legal_sources
                (id, source_type, number, year, issuing_authority, title, official_url,
                 publication_date, jurisdiction, notes, content_hash, is_synthetic, created_at)
                VALUES ('PG-TEST-QR-SOURCE', 'SYNTHETIC', 'TEST', 2099, 'SYNTHETIC AUTHORITY',
                'Synthetic queryable-rulesets source', 'https://example.invalid/pg-qr-source',
                '2099-01-01', 'SYNTHETIC', 'Fictitious', :hash, true, '2040-01-01T00:00:00Z')"""
            ),
            {"hash": "a" * 64},
        )
        session.execute(
            text(
                """INSERT INTO tax_rule_identities
                (id, code, title, description, is_synthetic, created_at, created_by)
                VALUES ('PG-TEST-QR-IDENTITY-1', 'TEST-QR-RULE-1', 'Synthetic rule 1',
                'Fictitious', true, '2040-01-01T00:00:00Z', 'author')"""
            )
        )
        session.execute(
            text(
                """INSERT INTO tax_rule_identities
                (id, code, title, description, is_synthetic, created_at, created_by)
                VALUES ('PG-TEST-QR-IDENTITY-2', 'TEST-QR-RULE-2', 'Synthetic rule 2',
                'Fictitious', true, '2040-01-01T00:00:00Z', 'author')"""
            )
        )
        for version_id, identity_id, key in (
            ("PG-TEST-QR-VERSION-1", "PG-TEST-QR-IDENTITY-1", "SYNTHETIC_RULE_A_V1"),
            ("PG-TEST-QR-VERSION-2", "PG-TEST-QR-IDENTITY-2", "SYNTHETIC_RULE_B_V1"),
        ):
            session.execute(
                text(
                    """INSERT INTO tax_rule_versions
                    (id, rule_identity_id, version, lifecycle_status, jurisdiction,
                     legal_source_id, legal_device, valid_from, valid_to, recorded_at,
                     created_by, approved_at, approved_by, published_at, published_by,
                     content, content_hash, metadata)
                    VALUES (:id, :identity_id, 1, 'PUBLISHED', 'SYNTHETIC', 'PG-TEST-QR-SOURCE',
                    'SYNTHETIC DEVICE', '2000-01-01', '2100-01-01', '2040-01-01T00:00:00Z',
                    'author', '2040-01-02T00:00:00Z', 'reviewer', '2040-01-03T00:00:00Z',
                    'publisher', CAST(:content AS jsonb), :hash, CAST('{}' AS jsonb))"""
                ),
                {
                    "id": version_id,
                    "identity_id": identity_id,
                    "content": f'{{"implementation_key":"{key}"}}',
                    "hash": ("b" if key.endswith("A_V1") else "c") * 64,
                },
            )
        session.execute(
            text(
                """INSERT INTO rulesets (id, name, version, status, created_at, created_by)
                VALUES ('PG-TEST-QR-RULESET-SINGLE', 'Synthetic single-rule ruleset', '1',
                'DRAFT', '2040-01-04T00:00:00Z', 'curator')"""
            )
        )
        session.execute(
            text(
                """INSERT INTO rulesets (id, name, version, status, created_at, created_by)
                VALUES ('PG-TEST-QR-RULESET-BUNDLED', 'Synthetic bundled ruleset', '1',
                'DRAFT', '2040-01-04T00:00:00Z', 'curator')"""
            )
        )
        session.execute(
            text(
                """INSERT INTO ruleset_items (ruleset_id, rule_version_id, position)
                VALUES ('PG-TEST-QR-RULESET-SINGLE', 'PG-TEST-QR-VERSION-1', 1)"""
            )
        )
        session.execute(
            text(
                """INSERT INTO ruleset_items (ruleset_id, rule_version_id, position)
                VALUES ('PG-TEST-QR-RULESET-BUNDLED', 'PG-TEST-QR-VERSION-1', 1),
                ('PG-TEST-QR-RULESET-BUNDLED', 'PG-TEST-QR-VERSION-2', 2)"""
            )
        )
        session.execute(
            text(
                """UPDATE rulesets SET status = 'PUBLISHED',
                published_at = '2040-01-05T00:00:00Z', published_by = 'publisher',
                fingerprint = :hash WHERE id = :id"""
            ),
            [
                {"id": "PG-TEST-QR-RULESET-SINGLE", "hash": "d" * 64},
                {"id": "PG-TEST-QR-RULESET-BUNDLED", "hash": "e" * 64},
            ],
        )
        session.commit()

        repository = SqlAlchemyGovernanceRepository(session)
        versions = {item["id"]: item for item in repository.list_rule_versions()}

        assert versions["PG-TEST-QR-VERSION-1"]["queryable_rulesets"] == [
            "PG-TEST-QR-RULESET-SINGLE"
        ]
        assert versions["PG-TEST-QR-VERSION-2"]["queryable_rulesets"] == []
