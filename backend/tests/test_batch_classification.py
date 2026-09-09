"""Unit coverage for the batch row orchestrator (Etapa 23, ADR-0027).

Everything here runs without Postgres: it exercises identification,
discovery routing and ruleset resolution purely against mocked
repositories (`SimpleNamespace`, same style as `test_catalog_discovery.py`).
The one path this file cannot cover without a live database - a full
`evaluate_many()` producing CONCLUSIVO/POSSIVEIS_ENQUADRAMENTOS/
NECESSITA_VALIDACAO against the real RT-IBSCBS-0004/0005 rules - is covered
by `test_batch_classification_integration.py` instead.
"""

from datetime import date
from types import SimpleNamespace
from typing import Any, cast

from tributaria_api.application.batch_classification import (
    expand_row_result,
    process_batch_row,
    resolve_ruleset_ids_for_rule_codes,
)
from tributaria_api.application.errors import NotFoundError


def _row(**overrides: Any) -> Any:
    defaults: dict[str, Any] = {
        "ncm": None,
        "nbs": None,
        "description": None,
        "object_kind": None,
        "internal_code": None,
        "operation_date": date(2026, 1, 5),
        "raw_values": {},
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _ncm_repository(
    *, found_codes: set[str] = frozenset(), search_results: list[dict] | None = None
) -> Any:
    def get_code(organization_id: str, code: str) -> dict[str, Any]:
        if code not in found_codes:
            raise NotFoundError("NCM code not found")
        return {"code": code}

    return cast(
        Any,
        SimpleNamespace(
            get_code=get_code,
            search=lambda organization_id, q: search_results or [],
        ),
    )


def _nbs_repository(
    *, found_codes: set[str] = frozenset(), search_results: list[dict] | None = None
) -> Any:
    def get_code(organization_id: str, code: str) -> dict[str, Any]:
        if code not in found_codes:
            raise NotFoundError("NBS code not found")
        return {"code": code}

    return cast(
        Any,
        SimpleNamespace(
            get_code=get_code,
            search=lambda organization_id, q: search_results or [],
        ),
    )


def _products(records: list[Any] | None = None) -> Any:
    return cast(Any, SimpleNamespace(list_products=lambda organization_id, q: records or []))


def _governance_repository(rule_versions: list[dict[str, Any]] | None = None) -> Any:
    return cast(Any, SimpleNamespace(list_rule_versions=lambda: rule_versions or []))


def test_invalid_ncm_format_is_an_error_before_touching_discovery() -> None:
    outcome = process_batch_row(
        _row(ncm="ABC"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(),
        nbs_repository=_nbs_repository(),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "ERROR"
    assert outcome.classification_status is None
    assert "formato inválido" in (outcome.error_message or "")


def test_ncm_not_in_published_catalog_is_an_error() -> None:
    outcome = process_batch_row(
        _row(ncm="30019010"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(found_codes=set()),
        nbs_repository=_nbs_repository(),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "ERROR"
    assert "não encontrado" in (outcome.error_message or "")


def test_description_with_no_catalog_match_is_an_error() -> None:
    outcome = process_batch_row(
        _row(description="produto inexistente"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(search_results=[]),
        nbs_repository=_nbs_repository(search_results=[]),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "ERROR"
    assert "sem correspondência" in (outcome.error_message or "")


def test_ambiguous_description_is_an_error_not_a_guess() -> None:
    outcome = process_batch_row(
        _row(description="construção"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(search_results=[{"code": "68101100"}]),
        nbs_repository=_nbs_repository(search_results=[{"code": "1.0101.11.00"}]),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "ERROR"
    assert "ambígua" in (outcome.error_message or "")


def test_row_without_any_identifier_is_an_error() -> None:
    outcome = process_batch_row(
        _row(),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(),
        nbs_repository=_nbs_repository(),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "ERROR"
    assert "identificar o objeto" in (outcome.error_message or "")


def test_missing_operation_date_is_an_error_after_identification_succeeds() -> None:
    outcome = process_batch_row(
        _row(ncm="30019010", operation_date=None),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(found_codes={"30019010"}),
        nbs_repository=_nbs_repository(),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "ERROR"
    assert "Data da operação" in (outcome.error_message or "")


def test_ncm_outside_chapter_30_has_no_governed_coverage() -> None:
    outcome = process_batch_row(
        _row(ncm="01012100"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(found_codes={"01012100"}),
        nbs_repository=_nbs_repository(),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "PROCESSED"
    assert outcome.classification_status == "SEM_COBERTURA_NORMATIVA"
    assert outcome.evaluation_id is None
    assert "sem cobertura normativa" in (outcome.observations or "")


def test_candidate_family_without_queryable_ruleset_is_necessita_validacao() -> None:
    outcome = process_batch_row(
        _row(ncm="30019010"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(found_codes={"30019010"}),
        nbs_repository=_nbs_repository(),
        products=_products(),
        governance_repository=_governance_repository(rule_versions=[]),
    )

    assert outcome.processing_status == "PROCESSED"
    assert outcome.classification_status == "NECESSITA_VALIDACAO"
    assert outcome.discovery_rule_codes == ("RT-IBSCBS-0004", "RT-IBSCBS-0005")
    assert "pendência de publicação" in (outcome.observations or "")


def test_internal_code_resolves_via_product_ncm() -> None:
    product = SimpleNamespace(internal_code="SKU-1", ncm="30019010")

    outcome = process_batch_row(
        _row(internal_code="SKU-1"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(found_codes={"30019010"}),
        nbs_repository=_nbs_repository(),
        products=_products([product]),
        governance_repository=_governance_repository(rule_versions=[]),
    )

    # Reached discovery (governed for chapter 30), proving the NCM was
    # resolved from the product record rather than erroring out early.
    assert outcome.classification_status == "NECESSITA_VALIDACAO"


def test_internal_code_not_found_is_an_error() -> None:
    outcome = process_batch_row(
        _row(internal_code="SKU-UNKNOWN"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(),
        nbs_repository=_nbs_repository(),
        products=_products([]),
        governance_repository=_governance_repository(),
    )

    assert outcome.processing_status == "ERROR"
    assert "cadastro de produtos" in (outcome.error_message or "")


def test_object_kind_service_only_searches_nbs() -> None:
    outcome = process_batch_row(
        _row(description="serviço de construção", object_kind="SERVICE"),
        organization_id="org",
        correlation_id="corr",
        engine_version="test",
        taxonomy_catalog_version_id="catalog-1",
        ncm_repository=_ncm_repository(search_results=[{"code": "68101100"}]),
        nbs_repository=_nbs_repository(search_results=[]),
        products=_products(),
        governance_repository=_governance_repository(),
    )

    # NCM had a hit but object_kind=SERVICE means it was never consulted;
    # NBS had zero hits, so the row is a no-match error, not an ambiguity.
    assert outcome.processing_status == "ERROR"
    assert "sem correspondência" in (outcome.error_message or "")


def test_resolve_ruleset_ids_skips_rule_without_queryable_ruleset() -> None:
    repository = _governance_repository(
        rule_versions=[
            {
                "identity_code": "RT-IBSCBS-0004",
                "lifecycle_status": "PUBLISHED",
                "queryable_rulesets": ["IBSCBS-PILOT-0004-001"],
            },
            {
                "identity_code": "RT-IBSCBS-0005",
                "lifecycle_status": "PUBLISHED",
                "queryable_rulesets": [],
            },
        ]
    )

    ruleset_ids = resolve_ruleset_ids_for_rule_codes(
        repository, ["RT-IBSCBS-0004", "RT-IBSCBS-0005"]
    )

    assert ruleset_ids == ["IBSCBS-PILOT-0004-001"]


def test_resolve_ruleset_ids_ignores_non_published_versions() -> None:
    repository = _governance_repository(
        rule_versions=[
            {
                "identity_code": "RT-IBSCBS-0004",
                "lifecycle_status": "DRAFT",
                "queryable_rulesets": ["IBSCBS-PILOT-0004-DRAFT"],
            }
        ]
    )

    ruleset_ids = resolve_ruleset_ids_for_rule_codes(repository, ["RT-IBSCBS-0004"])

    assert ruleset_ids == []


def test_expand_row_result_without_evaluation_returns_empty_defaults() -> None:
    row = SimpleNamespace(evaluation_id=None)

    result = expand_row_result(row, governance_repository=cast(Any, SimpleNamespace()))

    assert result == {
        "cst": None,
        "cclasstrib": None,
        "tratamento": None,
        "fundamento_legal": [],
        "regra": None,
        "fatos_faltantes": [],
        "decision_trace": [],
    }


def test_expand_row_result_reads_from_the_real_evaluation_document() -> None:
    row = SimpleNamespace(evaluation_id="eval-1")
    governance_repository = cast(
        Any,
        SimpleNamespace(
            get_evaluation=lambda evaluation_id: {
                "outcome": {
                    "missing_facts": ["buyer.health_entity_status"],
                    "tax_candidates": [
                        {
                            "cst": "200",
                            "cclasstrib": "200009",
                            "rule": {"rule_code": "RT-IBSCBS-0004", "version": "1.0.0"},
                            "legal_references": [{"act_type": "LEI", "number": "214"}],
                        }
                    ],
                }
            }
        ),
    )

    result = expand_row_result(row, governance_repository=governance_repository)

    assert result["cst"] == "200"
    assert result["cclasstrib"] == "200009"
    assert result["tratamento"] == "CST 200 / cClassTrib 200009"
    assert result["regra"] == {"rule_code": "RT-IBSCBS-0004", "version": "1.0.0"}
    assert result["fatos_faltantes"] == ["buyer.health_entity_status"]


def test_expand_row_result_coerces_an_integer_rule_version_to_string() -> None:
    row = SimpleNamespace(evaluation_id="eval-2")
    governance_repository = cast(
        Any,
        SimpleNamespace(
            get_evaluation=lambda evaluation_id: {
                "outcome": {
                    "missing_facts": [],
                    "tax_candidates": [
                        {
                            "cst": "200",
                            "cclasstrib": "200009",
                            "rule": {"rule_code": "RT-IBSCBS-0004", "version": 1},
                            "legal_references": [],
                        }
                    ],
                }
            }
        ),
    )

    result = expand_row_result(row, governance_repository=governance_repository)

    assert result["regra"] == {"rule_code": "RT-IBSCBS-0004", "version": "1"}
