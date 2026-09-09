"""Shared NCM-vs-NBS discovery selection (Etapa 22/23).

Extracted out of `api/routes/catalog_discovery.py` so the batch classification
processor (Etapa 23) reuses the exact same selection rule the
`GET /catalog-discovery/candidates` endpoint already uses, instead of a
second, possibly-diverging copy of the same two-line decision.
"""

from __future__ import annotations

from tax_engine.tax_candidate_discovery import (
    TaxCandidateFamily,
    discover_by_nbs,
    discover_by_ncm,
)


def resolve_discovery(*, ncm: str | None, nbs: str | None) -> TaxCandidateFamily | None:
    if ncm:
        return discover_by_ncm(ncm)
    if nbs:
        return discover_by_nbs(nbs)
    return None
