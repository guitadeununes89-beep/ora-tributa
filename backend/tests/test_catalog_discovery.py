from types import SimpleNamespace
from typing import Any, cast

from tributaria_api.api.routes.catalog_discovery import candidates, search
from tributaria_api.application.errors import NotFoundError
from tributaria_api.application.security import AuthContext, Role
from tributaria_api.main import app


def analyst() -> AuthContext:
    return AuthContext(
        session_id="session",
        user_id="user",
        email="analyst@example.invalid",
        display_name="Synthetic analyst",
        organization_id="org",
        organization_name="Synthetic organization",
        membership_id="membership",
        role=Role.ANALYST,
    )


def test_discovery_endpoints_are_authenticated_and_exposed() -> None:
    schema = app.openapi()["paths"]
    assert "/api/v1/catalog-discovery/search" in schema
    assert "/api/v1/catalog-discovery/candidates" in schema
    assert schema["/api/v1/catalog-discovery/search"]["get"]["tags"] == ["catalog discovery"]


def test_search_combines_ncm_nbs_and_product_results() -> None:
    ncm_repo = cast(
        Any,
        SimpleNamespace(
            search=lambda org, q: [
                {"code": "30012010", "description": "De fígado", "level": 8, "is_final": True}
            ]
        ),
    )
    nbs_repo = cast(
        Any,
        SimpleNamespace(
            search=lambda org, q: [
                {"code": "1.01", "description": "Serviços de construção", "level": 2}
            ]
        ),
    )
    products = cast(
        Any,
        SimpleNamespace(
            list_products=lambda org, q: [
                SimpleNamespace(id="prod-1", internal_code="SKU-1", description="Produto teste")
            ]
        ),
    )

    result = search(analyst(), ncm_repo, nbs_repo, products, q="teste")

    origins = {item.origin for item in result}
    assert origins == {"NCM", "NBS", "PRODUCT"}
    ncm_item = next(item for item in result if item.origin == "NCM")
    assert ncm_item.code == "30012010"
    assert ncm_item.is_final is True
    product_item = next(item for item in result if item.origin == "PRODUCT")
    assert product_item.product_id == "prod-1"


def test_search_tolerates_a_catalog_with_no_published_version() -> None:
    def raise_not_found(org: str, q: str) -> list[Any]:
        raise NotFoundError("Published NCM catalog version not found")

    ncm_repo = cast(Any, SimpleNamespace(search=raise_not_found))
    nbs_repo = cast(Any, SimpleNamespace(search=lambda org, q: []))
    products = cast(Any, SimpleNamespace(list_products=lambda org, q: []))

    result = search(analyst(), ncm_repo, nbs_repo, products, q="anything")

    assert result == []


def test_candidates_returns_candidate_with_rule_for_ncm_chapter_30() -> None:
    result = candidates(analyst(), ncm="30012010", nbs=None)

    assert result.status == "CANDIDATE_WITH_RULE"
    assert result.family is not None
    assert result.family.rule_codes == ["RT-IBSCBS-0004", "RT-IBSCBS-0005"]


def test_candidates_returns_no_coverage_outside_chapter_30() -> None:
    result = candidates(analyst(), ncm="01012100", nbs=None)

    assert result.status == "NO_COVERAGE"
    assert result.family is None


def test_candidates_returns_no_coverage_for_any_nbs_code() -> None:
    result = candidates(analyst(), ncm=None, nbs="1.0101.11.00")

    assert result.status == "NO_COVERAGE"
    assert result.family is None


def test_candidates_returns_no_coverage_when_neither_code_is_given() -> None:
    result = candidates(analyst(), ncm=None, nbs=None)

    assert result.status == "NO_COVERAGE"
