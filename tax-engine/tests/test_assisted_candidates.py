from dataclasses import dataclass
from datetime import UTC, date, datetime

from tax_engine.engine import RuleSet, TaxEngine
from tax_engine.evaluation import (
    CandidateSupport,
    ClassificationStatus,
    ConditionResult,
    ConditionStatus,
    EvaluationContext,
    FactSet,
    RuleDecision,
    RuleDecisionStatus,
    TaxClassificationCandidate,
)
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, RuleVersionRef, TaxRuleIdentity, TaxRuleVersion


def at(day: int) -> datetime:
    return datetime(2039, 1, day, tzinfo=UTC)


def published_version(code: str) -> tuple[TaxRuleVersion, RuleLifecycle]:
    version = TaxRuleVersion.create(
        version_id=f"{code}-v1",
        identity=TaxRuleIdentity(f"identity-{code}", code, "Synthetic candidate rule"),
        version=1,
        jurisdiction="SYNTHETIC",
        legal_source=LegalSource(
            source_id=f"source-{code}",
            act_type="SYNTHETIC_ACT",
            number="TEST",
            year=2099,
            issuing_authority="SYNTHETIC",
            device="SYNTHETIC",
            official_uri="https://example.invalid/synthetic",
        ),
        legal_device="SYNTHETIC",
        valid_from=date(2040, 1, 1),
        valid_to=None,
        recorded_at=at(1),
        created_by="synthetic-author",
        origin="UNIT_TEST",
        content="Synthetic candidate only",
        audit_metadata=(("synthetic", "true"),),
    )
    lifecycle = (
        RuleLifecycle(version)
        .transition(
            event_id=f"{code}-review",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=at(2),
            actor_id="author",
            reason="Synthetic",
        )
        .transition(
            event_id=f"{code}-approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=at(3),
            actor_id="reviewer",
            reason="Synthetic",
        )
        .transition(
            event_id=f"{code}-publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=at(4),
            actor_id="publisher",
            reason="Synthetic",
        )
    )
    return version, lifecycle


@dataclass(frozen=True, slots=True)
class StructuredSyntheticRule:
    version: TaxRuleVersion
    lifecycle: RuleLifecycle
    cst: str
    classification: str

    def evaluate(self, facts: FactSet) -> RuleDecision:
        observed = facts.product_attributes.get("synthetic.required")
        condition = ConditionResult(
            condition_id=f"condition-{self.version.version_id}",
            description="Synthetic fixture requires a value",
            fact_name="product_attributes.synthetic.required",
            status=ConditionStatus.SATISFIED if observed == "YES" else ConditionStatus.MISSING,
            expected_value="YES",
            observed_value=observed,
        )
        reference = RuleVersionRef.from_version(self.version)
        if observed is None:
            candidate = TaxClassificationCandidate(
                catalog_version_id="SYNTHETIC-CATALOG-V1",
                cst_code=self.cst,
                classification_code=self.classification,
                rule=reference,
                support=CandidateSupport.INSUFFICIENT_FACTS,
                conditions=(condition,),
                missing_facts=("product_attributes.synthetic.required",),
                legal_sources=(self.version.legal_source,),
            )
            return RuleDecision(
                RuleDecisionStatus.REQUIRES_VALIDATION,
                tax_candidates=(candidate,),
                missing_facts=candidate.missing_facts,
                conditions=(condition,),
            )
        candidate = TaxClassificationCandidate(
            catalog_version_id="SYNTHETIC-CATALOG-V1",
            cst_code=self.cst,
            classification_code=self.classification,
            rule=reference,
            support=CandidateSupport.SUPPORTED,
            conditions=(condition,),
            legal_sources=(self.version.legal_source,),
        )
        return RuleDecision(
            RuleDecisionStatus.MATCHED,
            tax_candidates=(candidate,),
            conditions=(condition,),
        )


def rule(code: str, cst: str, classification: str) -> StructuredSyntheticRule:
    version, lifecycle = published_version(code)
    return StructuredSyntheticRule(version, lifecycle, cst, classification)


def evaluate(*rules: StructuredSyntheticRule, value: str | None = "YES"):
    attributes = {} if value is None else {"synthetic.required": value}
    return TaxEngine(engine_version="synthetic-assisted-1").evaluate(
        facts=FactSet(
            operation_date=date(2040, 1, 1),
            product_id="synthetic-product",
            product_version_id="synthetic-product-v1",
            product_attributes=attributes,
        ),
        context=EvaluationContext("evaluation", at(10), at(10), "correlation"),
        ruleset=RuleSet("synthetic-assisted", "1", rules),
    )


def test_structured_candidate_can_be_conclusive() -> None:
    result = evaluate(rule("SYN-A", "000", "000001"))
    assert result.outcome.status is ClassificationStatus.CONCLUSIVE
    assert result.outcome.tax_candidates[0].support is CandidateSupport.SUPPORTED
    assert result.outcome.tax_candidates[0].catalog_version_id == "SYNTHETIC-CATALOG-V1"


def test_distinct_structured_candidates_are_not_arbitrarily_resolved() -> None:
    result = evaluate(
        rule("SYN-A", "000", "000001"),
        rule("SYN-B", "200", "200001"),
    )
    assert result.outcome.status is ClassificationStatus.POSSIBLE_MATCHES
    assert len(result.outcome.tax_candidates) == 2
    assert result.outcome.trace[-1].outcome == "POSSIVEIS_ENQUADRAMENTOS"


def test_missing_fact_preserves_candidate_without_conclusion() -> None:
    result = evaluate(rule("SYN-A", "000", "000001"), value=None)
    assert result.outcome.status is ClassificationStatus.REQUIRES_VALIDATION
    assert result.outcome.missing_facts == ("product_attributes.synthetic.required",)
    assert result.outcome.tax_candidates[0].support is CandidateSupport.INSUFFICIENT_FACTS
