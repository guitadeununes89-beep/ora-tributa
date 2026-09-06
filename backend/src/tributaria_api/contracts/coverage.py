from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class CoverageSpecificationView(BaseModel):
    rule_id: str
    version: int
    title: str
    status: str
    legal_device: str
    effective_from: date
    effective_to: date | None
    implementation: dict[str, Any] | None


class CoverageRuleView(BaseModel):
    rule_identity_id: str
    rule_code: str
    rule_version_id: str
    version: int
    status: str
    legal_device: str
    valid_from: date
    valid_to: date | None
    content_hash: str


class CoverageItemView(BaseModel):
    cst: str
    cst_description: str | None
    cclasstrib: str
    name: str
    official_description: str
    legal_foundation: str | None
    legal_device: str | None
    official_url: str
    valid_from: date | None
    valid_to: date | None
    updated_on: date | None
    indicators: dict[str, Any]
    official_family: str
    catalog_version: str
    catalog_version_id: str
    catalog_source: dict[str, Any]
    coverage_status: str
    review_readiness: str
    foundation_identified: bool
    specifications: list[CoverageSpecificationView]
    rules: list[CoverageRuleView]
    blockers: list[str]
    coverage_caveat: str | None
    history: list[dict[str, Any]] = Field(default_factory=list)


class CoverageMetricsView(BaseModel):
    total_cclasstrib: int
    cataloged: int
    foundation_identified: int
    mapped: int
    catalog_only: int
    legal_mapping_required: int
    draft_specification: int
    ready_for_review: int
    legal_review: int
    approved: int
    implemented: int
    published: int
    blocked: int
    executable: int
    executable_percentage: str


class CoverageFamilyView(CoverageMetricsView):
    name: str


class NationalCoverageView(BaseModel):
    catalog: dict[str, Any]
    metrics: CoverageMetricsView
    families: list[CoverageFamilyView]
    items: list[CoverageItemView]
    disclaimer: str
