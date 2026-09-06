"""Idempotent development-only seed containing no real tax content."""

from __future__ import annotations

from datetime import UTC, date, datetime
from hashlib import sha256

from tributaria_api.application.governance import GovernanceService, SegregationOfDutiesPolicy
from tributaria_api.config import get_settings
from tributaria_api.infrastructure.database.models import (
    LegalSourceRecord,
    TaxRuleIdentityRecord,
)
from tributaria_api.infrastructure.database.repositories import (
    SqlAlchemyGovernanceRepository,
)
from tributaria_api.infrastructure.database.session import get_session_factory

AT = datetime(2026, 8, 29, 12, tzinfo=UTC)


def seed() -> None:
    settings = get_settings()
    if settings.app_env.casefold() != "development":
        raise RuntimeError("Synthetic seed is restricted to APP_ENV=development")
    with get_session_factory()() as session:
        repository = SqlAlchemyGovernanceRepository(session)
        service = GovernanceService(repository, SegregationOfDutiesPolicy())
        if session.get(LegalSourceRecord, "TEST-SOURCE-001") is None:
            service.create_legal_source(
                {
                    "id": "TEST-SOURCE-001",
                    "source_type": "SYNTHETIC_TEST_ACT",
                    "number": "TEST-001",
                    "year": 2099,
                    "issuing_authority": "SYNTHETIC AUTHORITY — NOT OFFICIAL",
                    "title": "Fictitious development source",
                    "official_url": "https://example.invalid/TEST-SOURCE-001",
                    "publication_date": date(2099, 1, 1),
                    "jurisdiction": "SYNTHETIC",
                    "notes": "Fictitious data; never use as legal authority.",
                    "content_hash": sha256(b"TEST-SOURCE-001-FICTITIOUS").hexdigest(),
                    "is_synthetic": True,
                    "created_at": AT,
                    "created_by": "synthetic-seed",
                    "correlation_id": "seed-development-synthetic",
                }
            )
        for sequence, implementation in ((1, "SYNTHETIC_RULE_A_V1"), (2, "SYNTHETIC_RULE_B_V1")):
            identity_id = f"TEST-RULE-{sequence:03d}"
            if session.get(TaxRuleIdentityRecord, identity_id) is not None:
                continue
            service.create_rule_identity(
                {
                    "id": identity_id,
                    "code": identity_id,
                    "title": f"Synthetic development rule {sequence}",
                    "description": "Fictitious rule used only to validate architecture.",
                    "is_synthetic": True,
                    "created_at": AT,
                    "created_by": "synthetic-seed",
                    "correlation_id": "seed-development-synthetic",
                }
            )
            service.create_rule_version(
                {
                    "id": f"{identity_id}-V1",
                    "rule_identity_id": identity_id,
                    "version": 1,
                    "jurisdiction": "SYNTHETIC",
                    "legal_source_id": "TEST-SOURCE-001",
                    "legal_device": "SYNTHETIC DEVICE",
                    "valid_from": date(2000, 1, 1),
                    "valid_to": date(2100, 1, 1),
                    "recorded_at": AT,
                    "created_by": "synthetic-seed",
                    "content": {
                        "implementation_key": implementation,
                        "notice": "SYNTHETIC ONLY — NO TAX MEANING",
                    },
                    "metadata": {"synthetic": "true"},
                    "correlation_id": "seed-development-synthetic",
                }
            )


if __name__ == "__main__":
    seed()
