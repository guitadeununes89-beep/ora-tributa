"""Read-only exposure of governed territorial areas (ADR-0021, ADR-0024).

Returns already-approved, already-published TaxJurisdictionAreaVersion data
as-is. This is reference information for a human to read while filling a
consultation form (or, in the future, a triage hint) - never an automatic
determination of whether a given establishment is inside a governed area.
"""

from __future__ import annotations

from fastapi import APIRouter

from tributaria_api.api.auth_dependencies import ReadContext
from tributaria_api.api.territory_dependencies import TerritoryRepositoryDep
from tributaria_api.contracts.territory import TerritorialAreaView

router = APIRouter(prefix="/territory", tags=["governed territorial areas"])


@router.get("/areas", response_model=list[TerritorialAreaView])
def list_areas(
    context: ReadContext, repository: TerritoryRepositoryDep
) -> list[dict[str, object]]:
    return repository.list_published_areas(context.organization_id)
