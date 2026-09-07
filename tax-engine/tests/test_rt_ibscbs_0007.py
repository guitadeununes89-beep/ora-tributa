from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from tax_engine.engine import RuleSet, TaxEngine
from tax_engine.evaluation import ClassificationStatus, EvaluationContext, FactSet
from tax_engine.ibs_cbs_rt_0007 import RtIbsCbs0007V1
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion

CATALOG_ID = "2295b90f-2f92-4fa4-8181-3007f02b1679"
ALL_REQUIRED_FACTS = frozenset(
    {
        "operation.zfm_area_version_id",
        "operation.origin_area_status",
        "operation.destination_area_status",
        "product.material_good_status",
        "product.industrialization_status",
        "product.origin_status",
        "buyer.establishment_area_status",
        "buyer.taxpayer_status",
        "buyer.art_442_habilitation_status",
        "buyer.tax_regime_status",
        "operation.invoice_suframa_registration_status",
        "product.art_443_par1_exclusion_status",
        "operation.zfm_entry_proof_status",
        "operation.entry_deadline_status",
    }
)


def rule() -> RtIbsCbs0007V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0007-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0007",
            code="RT-IBSCBS-0007",
            title="Bem nacional industrializado destinado a contribuinte habilitado na ZFM",
        ),
        version=1,
        jurisdiction="BR",
        legal_source=LegalSource(
            source_id="23302183-6c92-4b34-a26d-cd272e2c1b1e",
            act_type="OFFICIAL_LEGAL_ACT",
            number="214",
            year=2025,
            issuing_authority="Presidência da República",
            device="Art. 445",
            official_uri="https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm",
            published_on=date(2025, 1, 16),
        ),
        legal_device="LC nº 214/2025, art. 445; Resolução CGIBS nº 6/2026, art. 516",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 9, 6, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0007 v3",
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
    return RtIbsCbs0007V1(version, lifecycle, CATALOG_ID, "200", "200022")


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
        "operation.origin_area_status": "OUTSIDE_ZFM",
        "operation.destination_area_status": "ZFM",
        "product.material_good_status": "MATERIAL_GOOD",
        "product.industrialization_status": "INDUSTRIALIZED",
        "product.origin_status": "NATIONAL",
        "buyer.establishment_area_status": "ESTABLISHED_IN_ZFM",
        "buyer.taxpayer_status": "TAXPAYER",
        "buyer.art_442_habilitation_status": "VALID",
        "buyer.tax_regime_status": "REGULAR_IBS_CBS",
        "operation.invoice_suframa_registration_status": "PRESENT_AND_MATCHING",
        "product.art_443_par1_exclusion_status": "NOT_EXCLUDED",
        "operation.zfm_entry_proof_status": "CONFIRMED",
        "operation.entry_deadline_status": "WITHIN_120_DAYS",
    }
    baseline.update(overrides)
    return baseline


def test_positive_conclusive_within_deadline() -> None:
    evaluation = evaluate(date(2026, 6, 1), **eligible())

    assert evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    candidate = evaluation.outcome.tax_candidates[0]
    assert (candidate.cst_code, candidate.classification_code) == ("200", "200022")
    assert candidate.catalog_version_id == CATALOG_ID


def test_positive_simples_nacional_with_valid_extension() -> None:
    facts = eligible(
        **{
            "buyer.tax_regime_status": "SIMPLES_NACIONAL",
            "operation.entry_deadline_status": "VALID_EXTENSION_WITHIN_210_DAYS",
        }
    )

    assert evaluate(date(2026, 6, 1), **facts).outcome.status is ClassificationStatus.CONCLUSIVE


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("product.art_443_par1_exclusion_status", "EXCLUDED"),
        ("operation.origin_area_status", "INSIDE_ZFM"),
        ("operation.destination_area_status", "OTHER"),
        ("buyer.taxpayer_status", "NOT_TAXPAYER"),
        ("buyer.tax_regime_status", "OTHER"),
        ("operation.entry_deadline_status", "EXPIRED"),
        ("operation.zfm_entry_proof_status", "NOT_CONFIRMED_AFTER_DEADLINE"),
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


def test_entry_proof_pending_within_deadline_requires_continued_follow_up() -> None:
    facts = eligible(**{"operation.zfm_entry_proof_status": "PENDING_WITHIN_DEADLINE"})

    outcome = evaluate(date(2026, 6, 1), **facts).outcome

    assert outcome.status is ClassificationStatus.REQUIRES_VALIDATION
    assert outcome.missing_facts == ("operation.zfm_entry_proof_status",)


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
        "legal_device": "LC 214/2025, art. 445; Resolucao CGIBS 6/2026, art. 516",
        "rule_version": "1",
        "catalog_version_id": CATALOG_ID,
        "cst": "200",
        "cclasstrib": "200022",
    }
    assert {item.fact_name for item in evaluation_step.conditions} == ALL_REQUIRED_FACTS
