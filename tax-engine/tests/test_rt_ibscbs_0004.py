from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from tax_engine.engine import RuleSet, TaxEngine
from tax_engine.evaluation import ClassificationStatus, EvaluationContext, FactSet
from tax_engine.ibs_cbs_rt_0004 import RtIbsCbs0004V1
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion

CATALOG_ID = "c79f28ea-c741-42e7-a339-8016fb31cefd"
ALL_REQUIRED_FACTS = frozenset(
    {
        "product.ncm_sh",
        "product.annex_xiv_match_status",
        "normative.annex_xiv_version",
    }
)


def rule() -> RtIbsCbs0004V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0004-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0004",
            code="RT-IBSCBS-0004",
            title="Fornecimento de medicamentos relacionados no Anexo XIV da redacao original",
        ),
        version=1,
        jurisdiction="BR",
        legal_source=LegalSource(
            source_id="052c8ce0-2e4c-4422-a86f-1f6977ba2ef6",
            act_type="OFFICIAL_LEGAL_ACT",
            number="214",
            year=2025,
            issuing_authority="Presidência da República",
            device="Art. 146, caput (redação original); Anexo XIV",
            official_uri=(
                "https://www2.camara.leg.br/legin/fed/leicom/2025/"
                "leicomplementar-214-16-janeiro-2025-796905-publicacaooriginal-174141-pl.html"
            ),
            published_on=date(2025, 1, 16),
        ),
        legal_device="LC nº 214/2025, art. 146, caput (redação original); Anexo XIV",
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 1, 14),
        recorded_at=datetime(2026, 9, 7, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0004 v1",
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
    return RtIbsCbs0004V1(version, lifecycle, CATALOG_ID, "200", "200009")


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
        ruleset=RuleSet("IBSCBS-PILOT-0004-001", "1.0.0", (rule(),)),
    )


def eligible(**overrides: str) -> dict[str, str]:
    baseline = {
        "product.ncm_sh": "VERIFIED_FROM_OFFICIAL_ANNEX_XIV",
        "product.annex_xiv_match_status": "MATCHED",
        "normative.annex_xiv_version": "LC214_2025_ORIGINAL",
    }
    baseline.update(overrides)
    return baseline


def test_positive_conclusive_within_historical_window() -> None:
    evaluation = evaluate(date(2026, 1, 5), **eligible())

    assert evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    candidate = evaluation.outcome.tax_candidates[0]
    assert (candidate.cst_code, candidate.classification_code) == ("200", "200009")
    assert candidate.catalog_version_id == CATALOG_ID


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product.annex_xiv_match_status", "NOT_MATCHED"),
        ("normative.annex_xiv_version", "OTHER"),
    ],
)
def test_known_exclusions_are_unclassified(field: str, value: str) -> None:
    facts = eligible(**{field: value})

    outcome = evaluate(date(2026, 1, 5), **facts).outcome
    assert outcome.status is ClassificationStatus.UNCLASSIFIED
    assert outcome.tax_candidates == ()
    assert outcome.missing_facts == ()


@pytest.mark.parametrize("field", sorted(ALL_REQUIRED_FACTS))
def test_unknown_essential_fact_requires_validation(field: str) -> None:
    unknown_value = "" if field == "product.ncm_sh" else "UNKNOWN"
    facts = eligible(**{field: unknown_value})

    outcome = evaluate(date(2026, 1, 5), **facts).outcome

    assert outcome.status is ClassificationStatus.REQUIRES_VALIDATION
    assert outcome.missing_facts == (field,)


@pytest.mark.parametrize(
    ("operation_date", "expected"),
    [
        (date(2025, 12, 31), ClassificationStatus.UNCLASSIFIED),
        (date(2026, 1, 1), ClassificationStatus.CONCLUSIVE),
        (date(2026, 1, 13), ClassificationStatus.CONCLUSIVE),
        (date(2026, 1, 14), ClassificationStatus.UNCLASSIFIED),
        (date(2026, 6, 1), ClassificationStatus.UNCLASSIFIED),
    ],
)
def test_temporal_boundaries_of_the_historical_window(
    operation_date: date, expected: ClassificationStatus
) -> None:
    assert evaluate(operation_date, **eligible()).outcome.status is expected


def test_decision_trace_exposes_governed_basis_and_codes() -> None:
    outcome = evaluate(date(2026, 1, 5), **eligible()).outcome
    evaluation_step = next(step for step in outcome.trace if step.phase.value == "EVALUATION")
    details = dict(evaluation_step.details)

    assert details == {
        "legal_device": "LC 214/2025, art. 146, caput (redacao original); Anexo XIV",
        "rule_version": "1",
        "catalog_version_id": CATALOG_ID,
        "cst": "200",
        "cclasstrib": "200009",
    }
    assert {item.fact_name for item in evaluation_step.conditions} == ALL_REQUIRED_FACTS
