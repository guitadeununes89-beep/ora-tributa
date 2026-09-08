from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from pydantic import ValidationError
from tributaria_api.api.routes.unified_classification import classify_unified
from tributaria_api.application.errors import ConflictError
from tributaria_api.application.evaluations import multi_rule_evaluation_document
from tributaria_api.application.security import AuthContext, Role
from tributaria_api.contracts.unified_classification import (
    UnifiedClassificationRequest,
    UnifiedClassificationResponse,
)
from tributaria_api.main import app


def request(**overrides: object) -> UnifiedClassificationRequest:
    values: dict[str, object] = {
        "evaluation_id": "TEST-UNIFIED-EVALUATION",
        "ruleset_ids": ["IBSCBS-ZFM-0007-PILOT-001", "IBSCBS-ZFM-0008-PILOT-001"],
        "catalog_version_id": "TEST-CATALOG-DRAFT",
        "description": "Synthetic product description",
        "operation_date": date(2040, 1, 1),
        "evaluated_at": datetime(2040, 1, 2, tzinfo=UTC),
        "known_at": datetime(2040, 1, 2, tzinfo=UTC),
    }
    values.update(overrides)
    return UnifiedClassificationRequest.model_validate(values)


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


def test_unified_endpoint_is_authenticated_and_exposes_governed_result() -> None:
    operation = app.openapi()["paths"]["/api/v1/tax/ibs-cbs/classify-unified"]["post"]
    response_schema = str(operation["responses"]["200"])
    assert operation["tags"] == ["IBS/CBS unified classification"]
    assert "UnifiedClassificationResponse" in response_schema


def test_unified_classification_rejects_non_published_catalog_before_evaluation() -> None:
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
        classify_unified(
            request(),
            analyst(),
            "TEST-CORRELATION",
            cast(Any, None),
            cast(Any, None),
            taxonomy,
            cast(Any, None),
        )


def test_ruleset_ids_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="duplicates"):
        request(ruleset_ids=["IBSCBS-ZFM-0007-PILOT-001", "IBSCBS-ZFM-0007-PILOT-001"])


def test_ruleset_ids_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        request(ruleset_ids=[])


def test_unapproved_real_tax_attribute_remains_rejected() -> None:
    with pytest.raises(ValidationError, match="unsupported governed fact"):
        request(product_attributes={"product.composition": "unknown"})


def test_rt_ibscbs_0007_and_0008_facts_are_accepted_together() -> None:
    built = request(
        product_attributes={
            "operation.origin_area_status": "OUTSIDE_ZFM",
            "seller.establishment_zfm_relation": "INSIDE",
            "buyer.establishment_zfm_relation": "INSIDE",
        }
    )
    assert built.product_attributes["seller.establishment_zfm_relation"] == "INSIDE"


def test_multi_rule_document_is_serialized_with_rule_candidacies() -> None:
    rule_0007 = SimpleNamespace(
        identity_id="identity-0007",
        rule_code="RT-IBSCBS-0007",
        version_id="version-0007",
        version=3,
        content_hash="a" * 64,
    )
    rule_0008 = SimpleNamespace(
        identity_id="identity-0008",
        rule_code="RT-IBSCBS-0008",
        version_id="version-0008",
        version=3,
        content_hash="b" * 64,
    )
    outcome = SimpleNamespace(
        status=SimpleNamespace(value="CONCLUSIVO"),
        candidates=(),
        tax_candidates=(
            SimpleNamespace(
                catalog_version_id="catalog",
                cst_code="200",
                classification_code="200022",
                support=SimpleNamespace(value="SUPPORTED"),
                rule=rule_0007,
                conditions=(),
                missing_facts=(),
                legal_sources=(),
            ),
        ),
        missing_facts=(),
        evaluated_rules=(rule_0007, rule_0008),
        applicable_rules=(rule_0007,),
        satisfied_conditions=(),
        unsatisfied_conditions=(),
        legal_sources=(),
        trace=(),
    )
    evaluation = SimpleNamespace(
        evaluation_id="evaluation",
        evaluated_at=datetime(2026, 9, 8, tzinfo=UTC),
        known_at=datetime(2026, 9, 8, tzinfo=UTC),
        correlation_id="correlation",
        input_hash="c" * 64,
        engine_version="test",
        ruleset=SimpleNamespace(
            ruleset_id="COMPOSED:IBSCBS-ZFM-0007-PILOT-001+IBSCBS-ZFM-0008-PILOT-001",
            version="1.0.0-composed",
            content_hash="d" * 64,
        ),
        outcome=outcome,
    )
    candidacies = (
        SimpleNamespace(
            rule=rule_0007,
            status=SimpleNamespace(value="SUPPORTED"),
            decision=SimpleNamespace(missing_facts=()),
            unconfirmed_scope_facts=(),
        ),
        SimpleNamespace(
            rule=rule_0008,
            status=SimpleNamespace(value="SCOPE_UNCONFIRMED"),
            decision=SimpleNamespace(
                missing_facts=(
                    "seller.establishment_zfm_relation",
                    "buyer.establishment_zfm_relation",
                )
            ),
            unconfirmed_scope_facts=(
                "buyer.establishment_zfm_relation",
                "seller.establishment_zfm_relation",
            ),
        ),
    )
    result = SimpleNamespace(evaluation=evaluation, candidacies=candidacies)

    document = multi_rule_evaluation_document(cast(Any, result))
    document.update(
        {
            "product_id": None,
            "product_version_id": None,
            "catalog_version_id": "catalog",
            "official_candidates": [],
            "evaluated_ruleset_ids": [
                "IBSCBS-ZFM-0007-PILOT-001",
                "IBSCBS-ZFM-0008-PILOT-001",
            ],
        }
    )

    response = UnifiedClassificationResponse.model_validate(document)
    assert response.status.value == "CONCLUSIVO"
    assert len(response.rule_candidacies) == 2
    by_code = {item.rule_code: item for item in response.rule_candidacies}
    assert by_code["RT-IBSCBS-0007"].status == "SUPPORTED"
    assert by_code["RT-IBSCBS-0008"].status == "SCOPE_UNCONFIRMED"
    assert by_code["RT-IBSCBS-0008"].unconfirmed_scope_facts == [
        "buyer.establishment_zfm_relation",
        "seller.establishment_zfm_relation",
    ]
