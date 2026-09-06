from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class SpecificationIssueView(BaseModel):
    code: str
    path: str
    message: str


class SpecificationReadinessView(BaseModel):
    readiness: str
    rule_id: str | None
    specification_version: int | None
    title: str | None
    status: str | None
    responsible_party: str | None
    legal_source_id: str | None
    catalog_version_id: str | None
    cst: str | None
    cclasstrib: str | None
    effective_from: date | None
    effective_to: date | None
    issues: list[SpecificationIssueView]
    disclaimer: str

