"""Resolver contract for governed tax jurisdiction areas (ADR-0021, ADR-0024).

This module defines only the port: it decides nothing about which municipality
or subdivision belongs to a real ZFM/ALC area. A concrete resolver backed by
governed data is a future, separately reviewed piece of work.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Protocol


class AreaRelation(StrEnum):
    """Relation between an evidenced location and a governed area version.

    Mirrors the four allowed classification outcomes elsewhere in the platform:
    a relation is only ever asserted from evidence, never inferred by default.
    """

    INSIDE = "INSIDE"
    OUTSIDE = "OUTSIDE"
    BOUNDARY = "BOUNDARY"
    UNKNOWN = "UNKNOWN"


class TaxJurisdictionAreaResolution:
    """Outcome of resolving evidence against a governed area version."""

    __slots__ = ("area_id", "area_version_id", "evidence_source", "relation")

    def __init__(
        self,
        *,
        area_id: str | None,
        area_version_id: str | None,
        relation: AreaRelation,
        evidence_source: str,
    ) -> None:
        self.area_id = area_id
        self.area_version_id = area_version_id
        self.relation = relation
        self.evidence_source = evidence_source


class TaxJurisdictionAreaResolver(Protocol):
    """Port implemented outside tax-engine (ADR-0021, decision 3).

    Implementations receive evidence already collected elsewhere (e.g. Suframa
    habilitação records, registered establishment address) and must never
    accept raw geometry or an unversioned municipality list as ground truth.
    """

    def resolve(
        self, *, area_type: str, area_version_id: str, evidence: Mapping[str, Any]
    ) -> TaxJurisdictionAreaResolution: ...


class NullTaxJurisdictionAreaResolver:
    """Honest placeholder: no governed area data exists yet, so every lookup is UNKNOWN.

    This is not a stub to be silently relied upon in production evaluations; it
    exists so callers can wire the port today without fabricating a territorial
    determination that no governed data yet supports.
    """

    def resolve(
        self, *, area_type: str, area_version_id: str, evidence: Mapping[str, Any]
    ) -> TaxJurisdictionAreaResolution:
        return TaxJurisdictionAreaResolution(
            area_id=None,
            area_version_id=area_version_id,
            relation=AreaRelation.UNKNOWN,
            evidence_source="NO_GOVERNED_AREA_DATA_LOADED",
        )
