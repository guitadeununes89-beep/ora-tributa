from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from tax_engine.engine import RuleSet, TaxEngine
from tax_engine.evaluation import ClassificationStatus, EvaluationContext, FactSet
from tax_engine.ibs_cbs_rt_0008 import RtIbsCbs0008V1
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion

CATALOG_ID = "2295b90f-2f92-4fa4-8181-3007f02b1679"
ALL_REQUIRED_FACTS = frozenset(
    {
        "operation.zfm_area_version_id",
        "seller.establishment_zfm_relation",
        "buyer.establishment_zfm_relation",
        "seller.zfm_incentivized_industry_status",
        "buyer.zfm_incentivized_industry_status",
        "product.material_good_status",
        "product.intermediate_good_status",
        "operation.delivery_area_status",
        "operation.flow_type",
        "operation.taxable_scope_status",
        "product.art_443_par1_exclusion_status",
    }
)


def rule() -> RtIbsCbs0008V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0008-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0008",
            code="RT-IBSCBS-0008",
            title="Bem intermediário entre indústrias incentivadas na ZFM",
        ),
        version=1,
        jurisdiction="BR",
        legal_source=LegalSource(
            source_id="23302183-6c92-4b34-a26d-cd272e2c1b1e",
            act_type="OFFICIAL_LEGAL_ACT",
            number="214",
            year=2025,
            issuing_authority="Presidência da República",
            device="Art. 448",
            official_uri="https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm",
            published_on=date(2025, 1, 16),
        ),
        legal_device="LC nº 214/2025, art. 448; Resolução CGIBS nº 6/2026, art. 519",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 9, 6, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0008 v3",
    )
    lifecycle = (
        RuleLifecycle(version)
        .transition(
            event_id="review",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=datetime(2026, 9, 6, 1, tzinfo=UTC),
            actor_id="dev-curator",
            reason="test review",
        )
        .transition(
            event_id="approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=datetime(2026, 9, 6, 2, tzinfo=UTC),
            actor_id="legal-approver-guilherme-nunes",
            reason="test approval",
        )
        .transition(
            event_id="publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=datetime(2026, 9, 6, 3, tzinfo=UTC),
            actor_id="dev-publisher",
            reason="test publication",
        )
    )
    return RtIbsCbs0008V1(version, lifecycle, CATALOG_ID, "200", "200023")


def evaluate(operation_date: date, **attributes: str):
    engine = TaxEngine(engine_version="test-etapa-10")
    return engine.evaluate(
        facts=FactSet(operation_date=operation_date, product_attributes=attributes),
        context=EvaluationContext(
            evaluation_id="evaluation",
            evaluated_at=datetime(2026, 9, 7, tzinfo=UTC),
            known_at=datetime(2026, 9, 7, tzinfo=UTC),
            correlation_id="correlation",
        ),
        ruleset=RuleSet("IBSCBS-ZFM-PILOT-001", "1.0.0", (rule(),)),
    )


def eligible(**overrides: str) -> dict[str, str]:
    baseline = {
        "operation.zfm_area_version_id": "GOVERNED-ZFM-VERSION",
        "seller.establishment_zfm_relation": "INSIDE",
        "buyer.establishment_zfm_relation": "INSIDE",
        "seller.zfm_incentivized_industry_status": "VALID",
        "buyer.zfm_incentivized_industry_status": "VALID",
        "product.material_good_status": "MATERIAL_GOOD",
        "product.intermediate_good_status": "INTERMEDIATE_GOOD",
        "operation.delivery_area_status": "INSIDE_ZFM",
        "operation.flow_type": "DIRECT",
        "operation.taxable_scope_status": "FULL_OPERATION",
        "product.art_443_par1_exclusion_status": "NOT_EXCLUDED",
    }
    baseline.update(overrides)
    return baseline


def test_positive_direct_flow_conclusive() -> None:
    evaluation = evaluate(date(2026, 6, 1), **eligible())

    assert evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    candidate = evaluation.outcome.tax_candidates[0]
    assert (candidate.cst_code, candidate.classification_code) == ("200", "200023")
    assert candidate.catalog_version_id == CATALOG_ID


def test_positive_toll_manufacturing_value_added_only_conclusive() -> None:
    facts = eligible(
        **{
            "operation.flow_type": "TOLL_MANUFACTURING",
            "operation.taxable_scope_status": "VALUE_ADDED_ONLY",
        }
    )

    assert evaluate(date(2026, 6, 1), **facts).outcome.status is ClassificationStatus.CONCLUSIVE


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product.art_443_par1_exclusion_status", "EXCLUDED"),
        ("operation.delivery_area_status", "OUTSIDE_ZFM"),
        ("product.intermediate_good_status", "NOT_INTERMEDIATE_GOOD"),
        ("product.material_good_status", "NOT_MATERIAL_GOOD"),
        ("seller.zfm_incentivized_industry_status", "INVALID"),
        ("buyer.zfm_incentivized_industry_status", "INVALID"),
        ("seller.establishment_zfm_relation", "OUTSIDE"),
        ("seller.establishment_zfm_relation", "BOUNDARY"),
        ("buyer.establishment_zfm_relation", "OUTSIDE"),
    ],
)
def test_known_exclusions_are_unclassified(field: str, value: str) -> None:
    facts = eligible(**{field: value})

    outcome = evaluate(date(2026, 6, 1), **facts).outcome
    assert outcome.status is ClassificationStatus.UNCLASSIFIED
    assert outcome.tax_candidates == ()
    assert outcome.missing_facts == ()


@pytest.mark.parametrize("field", sorted(ALL_REQUIRED_FACTS))
def test_unknown_essential_fact_requires_validation(field: str) -> None:
    unknown_value = "" if field == "operation.zfm_area_version_id" else "UNKNOWN"
    facts = eligible(**{field: unknown_value})

    outcome = evaluate(date(2026, 6, 1), **facts).outcome

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
    outcome = evaluate(date(2026, 6, 1), **eligible()).outcome
    evaluation_step = next(step for step in outcome.trace if step.phase.value == "EVALUATION")
    details = dict(evaluation_step.details)

    assert details == {
        "legal_device": "LC 214/2025, art. 448; Resolucao CGIBS 6/2026, art. 519",
        "rule_version": "1",
        "catalog_version_id": CATALOG_ID,
        "cst": "200",
        "cclasstrib": "200023",
    }
    assert {item.fact_name for item in evaluation_step.conditions} == ALL_REQUIRED_FACTS
