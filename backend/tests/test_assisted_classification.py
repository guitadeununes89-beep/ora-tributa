from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from pydantic import ValidationError
from tax_engine.evaluation import FactSet
from tributaria_api.api.routes.assisted_classification import classify
from tributaria_api.application.errors import ConflictError
from tributaria_api.application.evaluations import evaluation_document
from tributaria_api.application.security import AuthContext, Role
from tributaria_api.contracts.assisted_classification import (
    AssistedClassificationRequest,
    AssistedClassificationResponse,
)
from tributaria_api.main import app


def request(**overrides: object) -> AssistedClassificationRequest:
    values: dict[str, object] = {
        "evaluation_id": "TEST-ASSISTED-EVALUATION",
        "ruleset_id": "TEST-RULESET",
        "catalog_version_id": "TEST-CATALOG-DRAFT",
        "description": "Synthetic product description",
        "operation_date": date(2040, 1, 1),
        "evaluated_at": datetime(2040, 1, 2, tzinfo=UTC),
        "known_at": datetime(2040, 1, 2, tzinfo=UTC),
    }
    values.update(overrides)
    return AssistedClassificationRequest.model_validate(values)


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


def test_assisted_endpoint_is_authenticated_and_exposes_governed_result() -> None:
    operation = app.openapi()["paths"]["/api/v1/tax/ibs-cbs/classify"]["post"]
    response_schema = str(operation["responses"]["200"])
    assert operation["tags"] == ["IBS/CBS assisted classification"]
    assert "AssistedClassificationResponse" in response_schema
    assert "/api/v1/tax/ibs-cbs/evaluations/{evaluation_id}/review" in app.openapi()["paths"]


def test_assisted_classification_rejects_non_published_catalog_before_evaluation() -> None:
    taxonomy = cast(
        Any,
        SimpleNamespace(
            get_version=lambda organization_id, version_id: SimpleNamespace(
                id=version_id,
                organization_id=organization_id,
                status="DRAFT",
            )
        ),
    )
    with pytest.raises(ConflictError, match="PUBLISHED catalog"):
        classify(
            request(),
            analyst(),
            "TEST-CORRELATION",
            cast(Any, None),
            cast(Any, None),
            taxonomy,
            cast(Any, None),
        )


def test_unapproved_real_tax_attribute_remains_rejected() -> None:
    with pytest.raises(ValidationError, match="unsupported governed fact"):
        request(product_attributes={"product.composition": "unknown"})


def test_rt_ibscbs_0007_facts_are_accepted() -> None:
    built = request(
        product_attributes={
            "operation.zfm_area_version_id": "TJA-ZFM-V1",
            "operation.origin_area_status": "OUTSIDE_ZFM",
            "buyer.art_442_habilitation_status": "VALID",
            "operation.zfm_entry_proof_status": "PENDING_WITHIN_DEADLINE",
        }
    )
    assert built.product_attributes["operation.origin_area_status"] == "OUTSIDE_ZFM"


def test_rt_ibscbs_0008_facts_are_accepted() -> None:
    built = request(
        product_attributes={
            "seller.establishment_zfm_relation": "INSIDE",
            "buyer.establishment_zfm_relation": "BOUNDARY",
            "operation.flow_type": "TOLL_MANUFACTURING",
            "operation.taxable_scope_status": "VALUE_ADDED_ONLY",
        }
    )
    assert built.product_attributes["seller.establishment_zfm_relation"] == "INSIDE"


def test_zfm_fact_still_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError, match="unsupported governed fact"):
        request(product_attributes={"operation.origin_area_status": "SOMEWHERE_ELSE"})


def test_product_version_participates_in_factset_hash() -> None:
    first = FactSet(
        operation_date=date(2040, 1, 1),
        product_id="product",
        product_version_id="product-v1",
    )
    second = FactSet(
        operation_date=date(2040, 1, 1),
        product_id="product",
        product_version_id="product-v2",
    )
    assert first.canonical_payload() != second.canonical_payload()


def test_candidate_legal_reference_is_serialized_as_auditable_object() -> None:
    source = SimpleNamespace(
        source_id="source",
        act_type="OFFICIAL_LEGAL_ACT",
        number="214",
        year=2025,
        issuing_authority="Presidência da República",
        device="Art. 146, § 1º, I",
        official_uri="https://example.invalid/official-source",
        published_on=date(2025, 1, 16),
        notes=None,
        integrity_hash="a" * 64,
    )
    rule = SimpleNamespace(
        identity_id="identity",
        rule_code="RT-IBSCBS-0003",
        version_id="version",
        version=1,
        content_hash="b" * 64,
    )
    outcome = SimpleNamespace(
        status=SimpleNamespace(value="CONCLUSIVO"),
        candidates=(),
        tax_candidates=(
            SimpleNamespace(
                catalog_version_id="catalog",
                cst_code="200",
                classification_code="200010",
                support=SimpleNamespace(value="SUPPORTED"),
                rule=rule,
                conditions=(),
                missing_facts=(),
                legal_sources=(source,),
            ),
        ),
        missing_facts=(),
        evaluated_rules=(rule,),
        applicable_rules=(rule,),
        satisfied_conditions=(),
        unsatisfied_conditions=(),
        legal_sources=(source,),
        trace=(),
    )
    evaluation = SimpleNamespace(
        evaluation_id="evaluation",
        evaluated_at=datetime(2026, 8, 31, tzinfo=UTC),
        known_at=datetime(2026, 8, 31, tzinfo=UTC),
        correlation_id="correlation",
        input_hash="c" * 64,
        engine_version="test",
        ruleset=SimpleNamespace(ruleset_id="ruleset", version="1", content_hash="d" * 64),
        outcome=outcome,
    )

    document = evaluation_document(cast(Any, evaluation))
    document.update(
        {
            "product_id": None,
            "product_version_id": None,
            "catalog_version_id": "catalog",
            "official_candidates": [],
        }
    )

    response = AssistedClassificationResponse.model_validate(document)
    assert response.tax_candidates[0].legal_references[0].source_id == "source"
