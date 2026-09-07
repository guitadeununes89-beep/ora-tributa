from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from tax_engine.engine import RuleSet, TaxEngine
from tax_engine.evaluation import ClassificationStatus, EvaluationContext, FactSet
from tax_engine.ibs_cbs_rt_0005 import RtIbsCbs0005V1
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion

CATALOG_ID = "2295b90f-2f92-4fa4-8181-3007f02b1679"
ALL_REQUIRED_FACTS = frozenset(
    {
        "product.kind",
        "product.anvisa_registration_status",
        "buyer.health_entity_status",
        "buyer.ibs_cbs_immunity_status",
        "operation.effective_buyer_status",
        "buyer.cebas_status",
        "buyer.sus_service_requirement_status",
    }
)


def rule() -> RtIbsCbs0005V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0005-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0005",
            code="RT-IBSCBS-0005",
            title=(
                "Medicamento Anvisa adquirido por entidade de saude imune "
                "com CEBAS e prestacao de servicos ao SUS"
            ),
        ),
        version=1,
        jurisdiction="BR",
        legal_source=LegalSource(
            source_id="23302183-6c92-4b34-a26d-cd272e2c1b1e",
            act_type="OFFICIAL_LEGAL_ACT",
            number="214",
            year=2025,
            issuing_authority="Presidência da República",
            device="Art. 146, § 1º, II",
            official_uri="https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm",
            published_on=date(2025, 1, 16),
        ),
        legal_device="LC nº 214/2025, art. 146, § 1º, II; LC nº 187/2021, arts. 9º a 11",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 9, 7, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0005 v1",
    )
    lifecycle = (
        RuleLifecycle(version)
        .transition(
            event_id="review",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=datetime(2026, 9, 7, 1, tzinfo=UTC),
            actor_id="dev-curator",
            reason="test review",
        )
        .transition(
            event_id="approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=datetime(2026, 9, 7, 2, tzinfo=UTC),
            actor_id="legal-approver-guilherme-nunes",
            reason="test approval",
        )
        .transition(
            event_id="publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=datetime(2026, 9, 7, 3, tzinfo=UTC),
            actor_id="dev-publisher",
            reason="test publication",
        )
    )
    return RtIbsCbs0005V1(version, lifecycle, CATALOG_ID, "200", "200010")


def evaluate(operation_date: date, **attributes: str):
    engine = TaxEngine(engine_version="test-etapa-15")
    return engine.evaluate(
        facts=FactSet(operation_date=operation_date, product_attributes=attributes),
        context=EvaluationContext(
            evaluation_id="evaluation",
            evaluated_at=datetime(2026, 9, 8, tzinfo=UTC),
            known_at=datetime(2026, 9, 8, tzinfo=UTC),
            correlation_id="correlation",
        ),
        ruleset=RuleSet("IBSCBS-PILOT-0005-001", "1.0.0", (rule(),)),
    )


def eligible(**overrides: str) -> dict[str, str]:
    baseline = {
        "product.kind": "MEDICINE",
        "product.anvisa_registration_status": "REGISTERED",
        "buyer.health_entity_status": "HEALTH_ENTITY",
        "buyer.ibs_cbs_immunity_status": "IMMUNE",
        "operation.effective_buyer_status": "CONFIRMED",
        "buyer.cebas_status": "VALID",
        "buyer.sus_service_requirement_status": "SATISFIED",
    }
    baseline.update(overrides)
    return baseline


def test_positive_conclusive_with_all_requirements_met() -> None:
    evaluation = evaluate(date(2026, 2, 1), **eligible())

    assert evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    candidate = evaluation.outcome.tax_candidates[0]
    assert (candidate.cst_code, candidate.classification_code) == ("200", "200010")
    assert candidate.catalog_version_id == CATALOG_ID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product.kind", "OTHER"),
        ("product.anvisa_registration_status", "NOT_REGISTERED"),
        ("buyer.health_entity_status", "NOT_HEALTH_ENTITY"),
        ("buyer.ibs_cbs_immunity_status", "NOT_IMMUNE"),
        ("operation.effective_buyer_status", "NOT_CONFIRMED"),
        ("buyer.cebas_status", "INVALID"),
        ("buyer.sus_service_requirement_status", "NOT_SATISFIED"),
    ],
)
def test_known_exclusions_are_unclassified(field: str, value: str) -> None:
    facts = eligible(**{field: value})

    outcome = evaluate(date(2026, 2, 1), **facts).outcome
    assert outcome.status is ClassificationStatus.UNCLASSIFIED
    assert outcome.tax_candidates == ()
    assert outcome.missing_facts == ()


@pytest.mark.parametrize("field", sorted(ALL_REQUIRED_FACTS))
def test_unknown_essential_fact_requires_validation(field: str) -> None:
    facts = eligible(**{field: "UNKNOWN"})

    outcome = evaluate(date(2026, 2, 1), **facts).outcome

    assert outcome.status is ClassificationStatus.REQUIRES_VALIDATION
    assert outcome.missing_facts == (field,)


@pytest.mark.parametrize(
    ("operation_date", "expected"),
    [
        (date(2025, 12, 31), ClassificationStatus.UNCLASSIFIED),
        (date(2026, 1, 1), ClassificationStatus.CONCLUSIVE),
        (date(2030, 12, 31), ClassificationStatus.CONCLUSIVE),
    ],
)
def test_temporal_boundaries(operation_date: date, expected: ClassificationStatus) -> None:
    assert evaluate(operation_date, **eligible()).outcome.status is expected


def test_decision_trace_exposes_governed_basis_and_codes() -> None:
    outcome = evaluate(date(2026, 2, 1), **eligible()).outcome
    evaluation_step = next(step for step in outcome.trace if step.phase.value == "EVALUATION")
    details = dict(evaluation_step.details)

    assert details == {
        "legal_device": "LC 214/2025, art. 146, par. 1, II; LC 187/2021, arts. 9 a 11",
        "rule_version": "1",
        "catalog_version_id": CATALOG_ID,
        "cst": "200",
        "cclasstrib": "200010",
    }
    assert {item.fact_name for item in evaluation_step.conditions} == ALL_REQUIRED_FACTS
