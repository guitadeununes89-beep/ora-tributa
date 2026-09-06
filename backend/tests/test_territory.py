from __future__ import annotations

from tributaria_api.application.territory import (
    AreaRelation,
    NullTaxJurisdictionAreaResolver,
    TaxJurisdictionAreaResolver,
)


def test_null_resolver_never_asserts_a_territorial_determination() -> None:
    """No governed area data exists yet (ADR-0024); UNKNOWN is the only honest answer."""
    resolver: TaxJurisdictionAreaResolver = NullTaxJurisdictionAreaResolver()

    resolution = resolver.resolve(
        area_type="ZFM",
        area_version_id="any-version-id",
        evidence={"suframa_registration": "123456"},
    )

    assert resolution.relation is AreaRelation.UNKNOWN
    assert resolution.area_id is None
    assert resolution.area_version_id == "any-version-id"
    assert resolution.evidence_source == "NO_GOVERNED_AREA_DATA_LOADED"
