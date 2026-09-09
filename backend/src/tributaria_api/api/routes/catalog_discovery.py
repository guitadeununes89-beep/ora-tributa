from __future__ import annotations

from fastapi import APIRouter, Query

from tributaria_api.api.auth_dependencies import ReadContext
from tributaria_api.api.nbs_dependencies import NbsRepositoryDep
from tributaria_api.api.ncm_dependencies import NcmRepositoryDep
from tributaria_api.api.product_dependencies import ProductRepositoryDep
from tributaria_api.application.catalog_discovery_service import resolve_discovery
from tributaria_api.application.errors import NotFoundError
from tributaria_api.contracts.catalog_discovery import (
    DiscoveryResult,
    ObjectSearchResult,
    TaxCandidateFamilyView,
)

router = APIRouter(prefix="/catalog-discovery", tags=["catalog discovery"])


@router.get("/search", response_model=list[ObjectSearchResult])
def search(
    context: ReadContext,
    ncm_repository: NcmRepositoryDep,
    nbs_repository: NbsRepositoryDep,
    products: ProductRepositoryDep,
    q: str = Query(min_length=1, max_length=200),
) -> list[ObjectSearchResult]:
    """Literal, non-ranking search across NCM, NBS and internal products.

    Returns the located object and its own catalog/registration data only -
    never a tax treatment. Missing a PUBLISHED catalog for one source (e.g.
    a fresh install before the load CLI has run) is not an error for the
    others; that source simply contributes no results.
    """
    results: list[ObjectSearchResult] = []
    try:
        for item in ncm_repository.search(context.organization_id, q):
            results.append(
                ObjectSearchResult(
                    origin="NCM",
                    code=item["code"],
                    description=item["description"],
                    level=item["level"],
                    is_final=item["is_final"],
                )
            )
    except NotFoundError:
        pass
    try:
        for item in nbs_repository.search(context.organization_id, q):
            results.append(
                ObjectSearchResult(
                    origin="NBS",
                    code=item["code"],
                    description=item["description"],
                    level=item["level"],
                )
            )
    except NotFoundError:
        pass
    for product in products.list_products(context.organization_id, q):
        results.append(
            ObjectSearchResult(
                origin="PRODUCT",
                code=product.internal_code,
                description=product.description,
                product_id=product.id,
                internal_code=product.internal_code,
            )
        )
    return results


@router.get("/candidates", response_model=DiscoveryResult)
def candidates(
    context: ReadContext,
    ncm: str | None = Query(default=None, max_length=8),
    nbs: str | None = Query(default=None, max_length=20),
) -> DiscoveryResult:
    """Fail-closed tax-candidate discovery for one NCM or NBS code.

    Always returns 200 - `NO_COVERAGE` is a normal, expected answer, never
    an error. Never invents a candidate: a code outside the governed
    registry always comes back as `NO_COVERAGE`.
    """
    del context
    family = resolve_discovery(ncm=ncm, nbs=nbs)
    if family is None:
        return DiscoveryResult(status="NO_COVERAGE")
    return DiscoveryResult(
        status="CANDIDATE_WITH_RULE",
        family=TaxCandidateFamilyView(
            rule_codes=sorted(family.rule_codes),
            fundamento=family.fundamento,
            fonte=family.fonte,
            versao=family.versao,
            condicoes=family.condicoes,
        ),
    )
