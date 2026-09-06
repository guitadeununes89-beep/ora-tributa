from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from tax_engine.engine import DeterministicRule, RuleSet, TaxEngine
from tax_engine.evaluation import (
    ConditionResult,
    ConditionStatus,
    FactSet,
    RuleDecision,
    RuleDecisionStatus,
)
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion

_RECORDED_AT = datetime(2025, 1, 1, tzinfo=UTC)


def _synthetic_source(source_id: str) -> LegalSource:
    return LegalSource(
        source_id=source_id,
        act_type="SYNTHETIC_TEST_ACT",
        number="TEST-000",
        year=2099,
        issuing_authority="SYNTHETIC AUTHORITY — NOT A LEGAL SOURCE",
        device="SYNTHETIC DEVICE",
        official_uri="https://example.invalid/synthetic-tax-rule",
        published_on=date(2099, 1, 1),
        notes="Fictitious source used exclusively to validate software architecture.",
    )


def _published_lifecycle(version: TaxRuleVersion, prefix: str) -> RuleLifecycle:
    return (
        RuleLifecycle(rule_version=version)
        .transition(
            event_id=f"{prefix}-submit",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=datetime(2025, 1, 2, tzinfo=UTC),
            actor_id="synthetic-author",
            reason="Synthetic rule submitted for architectural testing",
        )
        .transition(
            event_id=f"{prefix}-approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=datetime(2025, 1, 3, tzinfo=UTC),
            actor_id="synthetic-reviewer",
            reason="Synthetic rule approved for architectural testing",
        )
        .transition(
            event_id=f"{prefix}-publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=datetime(2025, 1, 4, tzinfo=UTC),
            actor_id="synthetic-publisher",
            reason="Synthetic rule published in experimental in-memory ruleset",
        )
    )


def _version(*, code: str, version_id: str, content: str, source_id: str) -> TaxRuleVersion:
    return TaxRuleVersion.create(
        version_id=version_id,
        identity=TaxRuleIdentity(
            identity_id=f"identity-{code.lower()}",
            code=code,
            title="Synthetic rule — not tax legislation",
        ),
        version=1,
        jurisdiction="SYNTHETIC",
        legal_source=_synthetic_source(source_id),
        legal_device="SYNTHETIC DEVICE",
        valid_from=date(2000, 1, 1),
        valid_to=date(2100, 1, 1),
        recorded_at=_RECORDED_AT,
        created_by="synthetic-fixture",
        origin="EXPERIMENTAL_API_FIXTURE",
        content=content,
        audit_metadata=(("synthetic", "true"),),
    )


@dataclass(frozen=True, slots=True)
class SyntheticRuleA:
    version: TaxRuleVersion
    lifecycle: RuleLifecycle

    def evaluate(self, facts: FactSet) -> RuleDecision:
        attribute_x = facts.product_attributes.get("synthetic_attribute_x")
        conditions = (
            _equals_condition(
                condition_id="synthetic-a-x",
                description="Synthetic attribute X equals A",
                fact_name="product_attributes.synthetic_attribute_x",
                observed=attribute_x,
                expected="A",
            ),
            _equals_condition(
                condition_id="synthetic-a-operation",
                description="Synthetic operation type equals B",
                fact_name="operation_type",
                observed=facts.operation_type,
                expected="B",
            ),
        )
        missing = tuple(
            condition.fact_name
            for condition in conditions
            if condition.status is ConditionStatus.MISSING
        )
        if missing:
            return RuleDecision(
                status=RuleDecisionStatus.REQUIRES_VALIDATION,
                missing_facts=missing,
                conditions=conditions,
            )
        if all(condition.status is ConditionStatus.SATISFIED for condition in conditions):
            return RuleDecision(
                status=RuleDecisionStatus.MATCHED,
                candidates=("SYNTHETIC-Y",),
                conditions=conditions,
            )
        return RuleDecision(status=RuleDecisionStatus.NOT_MATCHED, conditions=conditions)


@dataclass(frozen=True, slots=True)
class SyntheticRuleB:
    version: TaxRuleVersion
    lifecycle: RuleLifecycle

    def evaluate(self, facts: FactSet) -> RuleDecision:
        attribute_x = facts.product_attributes.get("synthetic_attribute_x")
        condition_x = _equals_condition(
            condition_id="synthetic-b-x",
            description="Synthetic attribute X equals A",
            fact_name="product_attributes.synthetic_attribute_x",
            observed=attribute_x,
            expected="A",
        )
        if condition_x.status is ConditionStatus.MISSING:
            return RuleDecision(
                status=RuleDecisionStatus.REQUIRES_VALIDATION,
                missing_facts=(condition_x.fact_name,),
                conditions=(condition_x,),
            )
        if condition_x.status is ConditionStatus.NOT_SATISFIED:
            return RuleDecision(
                status=RuleDecisionStatus.NOT_MATCHED,
                conditions=(condition_x,),
            )

        attribute_z = facts.product_attributes.get("synthetic_attribute_z")
        if attribute_z is None:
            condition_z = ConditionResult(
                condition_id="synthetic-b-z",
                description="Synthetic attribute Z is required to resolve this branch",
                fact_name="product_attributes.synthetic_attribute_z",
                status=ConditionStatus.MISSING,
            )
            return RuleDecision(
                status=RuleDecisionStatus.REQUIRES_VALIDATION,
                missing_facts=(condition_z.fact_name,),
                conditions=(condition_x, condition_z),
            )
        condition_z = ConditionResult(
            condition_id="synthetic-b-z",
            description="Synthetic attribute Z is present; validation branch is not applicable",
            fact_name="product_attributes.synthetic_attribute_z",
            status=ConditionStatus.NOT_SATISFIED,
            expected_value="MISSING",
            observed_value=attribute_z,
        )
        return RuleDecision(
            status=RuleDecisionStatus.NOT_MATCHED,
            conditions=(condition_x, condition_z),
        )


def _equals_condition(
    *,
    condition_id: str,
    description: str,
    fact_name: str,
    observed: str | None,
    expected: str,
) -> ConditionResult:
    if observed is None:
        status = ConditionStatus.MISSING
    elif observed == expected:
        status = ConditionStatus.SATISFIED
    else:
        status = ConditionStatus.NOT_SATISFIED
    return ConditionResult(
        condition_id=condition_id,
        description=description,
        fact_name=fact_name,
        status=status,
        expected_value=expected,
        observed_value=observed,
    )


_VERSION_A = _version(
    code="SYNTHETIC-A",
    version_id="synthetic-a-v1",
    source_id="synthetic-source-a",
    content="SYNTHETIC ONLY: if attribute X is A and operation is B, candidate is Y",
)
_VERSION_B = _version(
    code="SYNTHETIC-B",
    version_id="synthetic-b-v1",
    source_id="synthetic-source-b",
    content="SYNTHETIC ONLY: if attribute X is A and attribute Z is absent, request validation",
)

_SYNTHETIC_RULES: tuple[DeterministicRule, ...] = (
    SyntheticRuleA(_VERSION_A, _published_lifecycle(_VERSION_A, "synthetic-a")),
    SyntheticRuleB(_VERSION_B, _published_lifecycle(_VERSION_B, "synthetic-b")),
)
EXPERIMENTAL_RULESET = RuleSet(
    ruleset_id="synthetic-api-ruleset",
    version="1.0.0-synthetic",
    rules=_SYNTHETIC_RULES,
)
EXPERIMENTAL_ENGINE = TaxEngine(engine_version="0.2.0-experimental")
