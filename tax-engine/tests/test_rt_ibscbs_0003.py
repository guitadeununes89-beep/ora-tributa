from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from tax_engine.engine import RuleSet, TaxEngine
from tax_engine.evaluation import ClassificationStatus, EvaluationContext, FactSet
from tax_engine.ibs_cbs_rt_0003 import RtIbsCbs0003V1
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion

CATALOG_ID = "2295b90f-2f92-4fa4-8181-3007f02b1679"


def rule() -> RtIbsCbs0003V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0003-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0003",
            code="RT-IBSCBS-0003",
            title="Medicamento adquirido por ente público elegível",
        ),
        version=1,
        jurisdiction="BR",
        legal_source=LegalSource(
            source_id="23302183-6c92-4b34-a26d-cd272e2c1b1e",
            act_type="OFFICIAL_LEGAL_ACT",
            number="214",
            year=2025,
            issuing_authority="Presidência da República",
            device="Art. 146, § 1º, I",
            official_uri="https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm",
            published_on=date(2025, 1, 16),
        ),
        legal_device="LC nº 214/2025, art. 146, § 1º, I",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 8, 31, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0003 v2",
    )
    lifecycle = (
        RuleLifecycle(version)
        .transition(
            event_id="review",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=datetime(2026, 8, 31, 1, tzinfo=UTC),
            actor_id="dev-curator",
            reason="test review",
        )
        .transition(
            event_id="approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=datetime(2026, 8, 31, 2, tzinfo=UTC),
            actor_id="legal-approver-guilherme-nunes",
            reason="test approval",
        )
        .transition(
            event_id="publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=datetime(2026, 8, 31, 3, tzinfo=UTC),
            actor_id="dev-publisher",
            reason="test publication",
        )
    )
    return RtIbsCbs0003V1(version, lifecycle, CATALOG_ID, "200", "200010")


def evaluate(operation_date: date, **attributes: str):
    engine = TaxEngine(engine_version="test-7c")
    return engine.evaluate(
        facts=FactSet(operation_date=operation_date, product_attributes=attributes),
        context=EvaluationContext(
            evaluation_id="evaluation",
            evaluated_at=datetime(2026, 9, 1, tzinfo=UTC),
            known_at=datetime(2026, 9, 1, tzinfo=UTC),
            correlation_id="correlation",
        ),
        ruleset=RuleSet("IBSCBS-PILOT-001", "1.0.0", (rule(),)),
    )


def eligible(legal_nature: str) -> dict[str, str]:
    return {
        "product.kind": "MEDICINE",
        "product.anvisa_registration_status": "REGISTERED",
        "buyer.legal_nature": legal_nature,
        "operation.buyer_is_acquirer": "YES",
    }


@pytest.mark.parametrize(
    "legal_nature",
    ["DIRECT_PUBLIC_ADMINISTRATION_BODY", "AUTARCHY", "PUBLIC_FOUNDATION"],
)
def test_positive_public_buyers_are_conclusive(legal_nature: str) -> None:
    evaluation = evaluate(date(2026, 1, 1), **eligible(legal_nature))

    assert evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    candidate = evaluation.outcome.tax_candidates[0]
    assert (candidate.cst_code, candidate.classification_code) == ("200", "200010")
    assert candidate.catalog_version_id == CATALOG_ID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("buyer.legal_nature", "PUBLIC_COMPANY"),
        ("buyer.legal_nature", "MIXED_CAPITAL_COMPANY"),
        ("buyer.legal_nature", "PRIVATE_ENTITY"),
        ("product.anvisa_registration_status", "NOT_REGISTERED"),
    ],
)
def test_known_exclusions_are_unclassified(field: str, value: str) -> None:
    facts = eligible("AUTARCHY")
    facts[field] = value

    assert evaluate(date(2026, 6, 1), **facts).outcome.status is ClassificationStatus.UNCLASSIFIED


@pytest.mark.parametrize(
    "field",
    [
        "buyer.legal_nature",
        "operation.buyer_is_acquirer",
        "product.anvisa_registration_status",
    ],
)
def test_unknown_essential_fact_requires_validation(field: str) -> None:
    facts = eligible("PUBLIC_FOUNDATION")
    facts[field] = "UNKNOWN"
    outcome = evaluate(date(2026, 6, 1), **facts).outcome

    assert outcome.status is ClassificationStatus.REQUIRES_VALIDATION
    assert field in outcome.missing_facts


@pytest.mark.parametrize(
    "operation_date",
    [date(2026, 1, 1), date(2026, 1, 13), date(2026, 1, 14), date(2030, 12, 31)],
)
def test_temporal_boundaries_from_2026_are_valid(operation_date: date) -> None:
    assert (
        evaluate(operation_date, **eligible("AUTARCHY")).outcome.status
        is ClassificationStatus.CONCLUSIVE
    )


def test_decision_trace_exposes_governed_basis_and_codes() -> None:
    outcome = evaluate(date(2026, 1, 14), **eligible("AUTARCHY")).outcome
    evaluation_step = next(step for step in outcome.trace if step.phase.value == "EVALUATION")
    details = dict(evaluation_step.details)

    assert details == {
        "legal_device": "LC 214/2025, art. 146, § 1º, I",
        "rule_version": "1",
        "catalog_version_id": CATALOG_ID,
        "cst": "200",
        "cclasstrib": "200010",
    }
    assert {item.fact_name for item in evaluation_step.conditions} == {
        "product.kind",
        "product.anvisa_registration_status",
        "buyer.legal_nature",
        "operation.buyer_is_acquirer",
    }
