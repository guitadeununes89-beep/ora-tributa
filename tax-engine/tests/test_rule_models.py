from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime

import pytest
from tax_engine.rule_models import (
    LegalSource,
    TaxRuleIdentity,
    TaxRuleVersion,
    compute_content_hash,
)


def synthetic_source() -> LegalSource:
    return LegalSource(
        source_id="synthetic-source",
        act_type="SYNTHETIC_ACT",
        number="TEST-001",
        year=2099,
        issuing_authority="SYNTHETIC AUTHORITY",
        device="SYNTHETIC DEVICE",
        official_uri="https://example.invalid/source",
        published_on=date(2099, 1, 1),
        notes="Not a real legal source.",
    )


def synthetic_version() -> TaxRuleVersion:
    return TaxRuleVersion.create(
        version_id="synthetic-v1",
        identity=TaxRuleIdentity(
            identity_id="synthetic-identity",
            code="SYNTHETIC-001",
            title="Synthetic rule",
        ),
        version=1,
        jurisdiction="SYNTHETIC",
        legal_source=synthetic_source(),
        legal_device="SYNTHETIC DEVICE",
        valid_from=date(2030, 1, 1),
        valid_to=date(2040, 1, 1),
        recorded_at=datetime(2029, 1, 1, tzinfo=UTC),
        created_by="synthetic-test",
        origin="UNIT_TEST",
        content="SYNTHETIC CONTENT ONLY",
        audit_metadata=(("synthetic", "true"),),
    )


def test_rule_version_content_hash_is_verified() -> None:
    version = synthetic_version()

    assert version.content_hash == compute_content_hash(version.content)

    with pytest.raises(ValueError, match="does not match"):
        TaxRuleVersion(
            version_id=version.version_id,
            identity=version.identity,
            version=version.version,
            jurisdiction=version.jurisdiction,
            legal_source=version.legal_source,
            legal_device=version.legal_device,
            valid_from=version.valid_from,
            valid_to=version.valid_to,
            recorded_at=version.recorded_at,
            created_by=version.created_by,
            origin=version.origin,
            content="CHANGED SYNTHETIC CONTENT",
            content_hash=version.content_hash,
        )


def test_rule_version_is_immutable() -> None:
    version = synthetic_version()

    with pytest.raises(FrozenInstanceError):
        version.content = "OVERWRITE ATTEMPT"  # type: ignore[misc]


def test_valid_to_is_exclusive_and_must_follow_valid_from() -> None:
    version = synthetic_version()

    with pytest.raises(ValueError, match="later"):
        TaxRuleVersion.create(
            version_id="invalid-v1",
            identity=version.identity,
            version=1,
            jurisdiction="SYNTHETIC",
            legal_source=version.legal_source,
            legal_device="SYNTHETIC DEVICE",
            valid_from=date(2030, 1, 1),
            valid_to=date(2030, 1, 1),
            recorded_at=version.recorded_at,
            created_by="synthetic-test",
            origin="UNIT_TEST",
            content="INVALID SYNTHETIC INTERVAL",
        )
