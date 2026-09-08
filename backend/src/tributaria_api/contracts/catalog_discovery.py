from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ObjectSearchResult(BaseModel):
    origin: Literal["NCM", "NBS", "PRODUCT"]
    code: str
    description: str
    level: int | None = None
    is_final: bool | None = None
    product_id: str | None = None
    internal_code: str | None = None


class TaxCandidateFamilyView(BaseModel):
    rule_codes: list[str]
    fundamento: str
    fonte: str
    versao: str
    condicoes: str


class DiscoveryResult(BaseModel):
    status: Literal["CANDIDATE_WITH_RULE", "NO_COVERAGE"]
    family: TaxCandidateFamilyView | None = None
