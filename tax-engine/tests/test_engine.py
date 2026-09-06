from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from tax_engine.engine import RuleSet, TaxEngine
from tax_engine.evaluation import (
    ClassificationStatus,
    ConditionResult,
    ConditionStatus,
    EvaluationContext,
    FactSet,
    RuleDecision,
    RuleDecisionStatus,
)
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion


def instant(day: int) -> datetime:
    return datetime(2029, 1, day, 12, tzinfo=UTC)


def version(
    *,
    code: str,
    candidate: str,
    number: int = 1,
    valid_from: date = date(2030, 1, 1),
    valid_to: date | None = date(2040, 1, 1),
) -> TaxRuleVersion:
    return TaxRuleVersion.create(
        version_id=f"{code.lower()}-v{number}",
        identity=TaxRuleIdentity(
            identity_id=f"identity-{code.lower()}",
            code=code,
            title="Synthetic test rule",
        ),
        version=number,
        jurisdiction="SYNTHETIC",
        legal_source=LegalSource(
            source_id=f"source-{code.lower()}-v{number}",
            act_type="SYNTHETIC_ACT",
            number="TEST-000",
            year=2099,
            issuing_authority="SYNTHETIC AUTHORITY",
            device="SYNTHETIC DEVICE",
            official_uri="https://example.invalid/synthetic-source",
            notes="Fictitious test data only.",
        ),
        legal_device="SYNTHETIC DEVICE",
        valid_from=valid_from,
        valid_to=valid_to,
        recorded_at=instant(1),
        created_by="synthetic-test",
        origin="UNIT_TEST",
        content=f"SYNTHETIC ONLY: attribute x=A returns {candidate}",
        audit_metadata=(("synthetic", "true"),),
    )


def lifecycle(
    rule_version: TaxRuleVersion,
    *,
    published_on: int | None = 4,
    superseded_on: int | None = None,
) -> RuleLifecycle:
    result = RuleLifecycle(rule_version=rule_version)
    if published_on is None:
        return result
    result = (
        result.transition(
            event_id=f"{rule_version.version_id}-submit",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=instant(published_on - 2),
            actor_id="synthetic-author",
            reason="Synthetic submission",
        )
        .transition(
            event_id=f"{rule_version.version_id}-approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=instant(published_on - 1),
            actor_id="synthetic-reviewer",
            reason="Synthetic approval",
        )
        .transition(
            event_id=f"{rule_version.version_id}-publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=instant(published_on),
            actor_id="synthetic-publisher",
            reason="Synthetic publication",
        )
    )
    if superseded_on is not None:
        result = result.transition(
            event_id=f"{rule_version.version_id}-supersede",
            to_status=RuleLifecycleStatus.SUPERSEDED,
            occurred_at=instant(superseded_on),
            actor_id="synthetic-publisher",
            reason="Synthetic supersession",
            related_version=rule_version.version + 1,
        )
    return result


@dataclass(frozen=True, slots=True)
class SyntheticAttributeRule:
    version: TaxRuleVersion
    lifecycle: RuleLifecycle
    candidate: str
    required_attribute: str | None = None
    must_not_run: bool = False

    def evaluate(self, facts: FactSet) -> RuleDecision:
        if self.must_not_run:
            raise AssertionError("An ineligible rule was executed")
        observed_x = facts.product_attributes.get("x")
        condition_x = condition("x", observed_x, "A")
        if condition_x.status is ConditionStatus.MISSING:
            return RuleDecision(
                status=RuleDecisionStatus.REQUIRES_VALIDATION,
                missing_facts=("product_attributes.x",),
                conditions=(condition_x,),
            )
        if condition_x.status is ConditionStatus.NOT_SATISFIED:
            return RuleDecision(
                status=RuleDecisionStatus.NOT_MATCHED,
                conditions=(condition_x,),
            )
        conditions = [condition_x]
        if self.required_attribute is not None:
            observed_required = facts.product_attributes.get(self.required_attribute)
            required = condition(self.required_attribute, observed_required, "PRESENT")
            conditions.append(required)
            if required.status is ConditionStatus.MISSING:
                return RuleDecision(
                    status=RuleDecisionStatus.REQUIRES_VALIDATION,
                    missing_facts=(f"product_attributes.{self.required_attribute}",),
                    conditions=tuple(conditions),
                )
            if required.status is ConditionStatus.NOT_SATISFIED:
                return RuleDecision(
                    status=RuleDecisionStatus.NOT_MATCHED,
                    conditions=tuple(conditions),
                )
        return RuleDecision(
            status=RuleDecisionStatus.MATCHED,
            candidates=(self.candidate,),
            conditions=tuple(conditions),
        )


def condition(name: str, observed: str | None, expected: str) -> ConditionResult:
    if observed is None:
        status = ConditionStatus.MISSING
    elif observed == expected:
        status = ConditionStatus.SATISFIED
    else:
        status = ConditionStatus.NOT_SATISFIED
    return ConditionResult(
        condition_id=f"condition-{name}",
        description=f"Synthetic {name} equals {expected}",
        fact_name=f"product_attributes.{name}",
        status=status,
        expected_value=expected,
        observed_value=observed,
    )


def context(*, known_day: int = 5, evaluation_id: str = "eval-1") -> EvaluationContext:
    return EvaluationContext(
        evaluation_id=evaluation_id,
        evaluated_at=instant(10),
        known_at=instant(known_day),
        correlation_id="corr-synthetic",
    )


def facts(*, operation_date: date = date(2030, 1, 1), **attributes: str) -> FactSet:
    return FactSet(operation_date=operation_date, product_attributes=attributes)


def evaluate(*rules: SyntheticAttributeRule, fact_set: FactSet | None = None, known_day: int = 5):
    return TaxEngine(engine_version="test-engine-1").evaluate(
        facts=fact_set or facts(x="A"),
        context=context(known_day=known_day),
        ruleset=RuleSet(ruleset_id="synthetic-tests", version="1", rules=rules),
    )


def rule(
    *,
    code: str,
    candidate: str,
    number: int = 1,
    valid_from: date = date(2030, 1, 1),
    valid_to: date | None = date(2040, 1, 1),
    published_on: int | None = 4,
    superseded_on: int | None = None,
    required_attribute: str | None = None,
    must_not_run: bool = False,
) -> SyntheticAttributeRule:
    rule_version = version(
        code=code,
        candidate=candidate,
        number=number,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    return SyntheticAttributeRule(
        version=rule_version,
        lifecycle=lifecycle(
            rule_version,
            published_on=published_on,
            superseded_on=superseded_on,
        ),
        candidate=candidate,
        required_attribute=required_attribute,
        must_not_run=must_not_run,
    )


def test_conclusive_result() -> None:
    result = evaluate(rule(code="SYN-A", candidate="SYNTHETIC-Y"))

    assert result.outcome.status is ClassificationStatus.CONCLUSIVE
    assert result.outcome.candidates == ("SYNTHETIC-Y",)
    assert len(result.outcome.applicable_rules) == 1


def test_multiple_possible_matches_are_not_arbitrarily_reduced() -> None:
    result = evaluate(
        rule(code="SYN-A", candidate="SYNTHETIC-Y"),
        rule(code="SYN-B", candidate="SYNTHETIC-Z"),
    )

    assert result.outcome.status is ClassificationStatus.POSSIBLE_MATCHES
    assert result.outcome.candidates == ("SYNTHETIC-Y", "SYNTHETIC-Z")


def test_missing_required_fact_needs_validation() -> None:
    result = evaluate(
        rule(
            code="SYN-A",
            candidate="SYNTHETIC-Y",
            required_attribute="z",
        )
    )

    assert result.outcome.status is ClassificationStatus.REQUIRES_VALIDATION
    assert result.outcome.missing_facts == ("product_attributes.z",)


def test_no_rule_found() -> None:
    result = evaluate(
        rule(code="SYN-A", candidate="SYNTHETIC-Y"),
        fact_set=facts(x="NOT-A"),
    )

    assert result.outcome.status is ClassificationStatus.UNCLASSIFIED
    assert result.outcome.candidates == ()


def test_legal_validity_start_is_inclusive_and_end_is_exclusive() -> None:
    synthetic_rule = rule(code="SYN-A", candidate="SYNTHETIC-Y")

    at_start = evaluate(synthetic_rule, fact_set=facts(operation_date=date(2030, 1, 1), x="A"))
    at_end = evaluate(synthetic_rule, fact_set=facts(operation_date=date(2040, 1, 1), x="A"))
    before_start = evaluate(
        synthetic_rule,
        fact_set=facts(operation_date=date(2029, 12, 31), x="A"),
    )

    assert at_start.outcome.status is ClassificationStatus.CONCLUSIVE
    assert at_end.outcome.status is ClassificationStatus.UNCLASSIFIED
    assert before_start.outcome.status is ClassificationStatus.UNCLASSIFIED


def test_non_published_and_superseded_rules_are_not_executed() -> None:
    draft = rule(
        code="SYN-DRAFT",
        candidate="NEVER",
        published_on=None,
        must_not_run=True,
    )
    review_version = version(code="SYN-REVIEW", candidate="NEVER")
    review_lifecycle = RuleLifecycle(rule_version=review_version).transition(
        event_id="review-submit",
        to_status=RuleLifecycleStatus.IN_REVIEW,
        occurred_at=instant(2),
        actor_id="synthetic-author",
        reason="Synthetic submission",
    )
    review = SyntheticAttributeRule(
        review_version,
        review_lifecycle,
        "NEVER",
        must_not_run=True,
    )
    approved_version = version(code="SYN-APPROVED", candidate="NEVER")
    approved_lifecycle = (
        RuleLifecycle(rule_version=approved_version)
        .transition(
            event_id="approved-submit",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=instant(2),
            actor_id="synthetic-author",
            reason="Synthetic submission",
        )
        .transition(
            event_id="approved-approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=instant(3),
            actor_id="synthetic-reviewer",
            reason="Synthetic approval",
        )
    )
    approved = SyntheticAttributeRule(
        approved_version,
        approved_lifecycle,
        "NEVER",
        must_not_run=True,
    )
    superseded = rule(
        code="SYN-SUPERSEDED",
        candidate="NEVER",
        superseded_on=5,
        must_not_run=True,
    )

    result = evaluate(draft, review, approved, superseded, known_day=5)

    assert result.outcome.status is ClassificationStatus.UNCLASSIFIED
    assert result.outcome.evaluated_rules == ()


def test_historical_evaluation_uses_version_known_at_execution_time() -> None:

    old_version = version(code="SYN-HISTORY", candidate="OLD", number=1)
    new_version = version(code="SYN-HISTORY", candidate="NEW", number=2)
    old_rule = SyntheticAttributeRule(
        old_version,
        lifecycle(old_version, published_on=4, superseded_on=7),
        "OLD",
    )
    new_rule = SyntheticAttributeRule(new_version, lifecycle(new_version, published_on=7), "NEW")
    ruleset = RuleSet(ruleset_id="synthetic-history", version="1", rules=(old_rule, new_rule))
    engine = TaxEngine(engine_version="test-engine-1")

    historical = engine.evaluate(facts=facts(x="A"), context=context(known_day=6), ruleset=ruleset)
    current = engine.evaluate(facts=facts(x="A"), context=context(known_day=8), ruleset=ruleset)

    assert historical.outcome.candidates == ("OLD",)
    assert current.outcome.candidates == ("NEW",)


def test_ruleset_fingerprint_is_stable_when_lifecycle_history_grows() -> None:
    rule_version = version(code="SYN-HASH", candidate="SYNTHETIC-Y")
    draft_rule = SyntheticAttributeRule(
        rule_version,
        RuleLifecycle(rule_version=rule_version),
        "SYNTHETIC-Y",
    )
    published_rule = SyntheticAttributeRule(
        rule_version,
        lifecycle(rule_version),
        "SYNTHETIC-Y",
    )

    draft_ruleset = RuleSet(ruleset_id="synthetic-hash", version="1", rules=(draft_rule,))
    published_ruleset = RuleSet(
        ruleset_id="synthetic-hash",
        version="1",
        rules=(published_rule,),
    )

    assert draft_ruleset.content_hash == published_ruleset.content_hash


def test_same_inputs_engine_and_ruleset_are_deterministic() -> None:
    synthetic_rule = rule(code="SYN-A", candidate="SYNTHETIC-Y")
    ruleset = RuleSet(ruleset_id="synthetic-tests", version="1", rules=(synthetic_rule,))
    engine = TaxEngine(engine_version="test-engine-1")
    fact_set = facts(x="A")
    evaluation_context = context()

    first = engine.evaluate(facts=fact_set, context=evaluation_context, ruleset=ruleset)
    second = engine.evaluate(facts=fact_set, context=evaluation_context, ruleset=ruleset)

    assert first == second
    assert first.input_hash == second.input_hash
    assert first.ruleset.content_hash == second.ruleset.content_hash
