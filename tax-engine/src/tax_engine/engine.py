from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from tax_engine.evaluation import (
    ClassificationOutcome,
    ClassificationStatus,
    ConditionStatus,
    DecisionStep,
    Evaluation,
    EvaluationContext,
    FactSet,
    RuleDecision,
    RuleDecisionStatus,
    RuleSetRef,
    TracePhase,
)
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, RuleVersionRef, TaxRuleVersion


class DeterministicRule(Protocol):
    @property
    def version(self) -> TaxRuleVersion: ...

    @property
    def lifecycle(self) -> RuleLifecycle: ...

    def evaluate(self, facts: FactSet) -> RuleDecision: ...


@dataclass(frozen=True, slots=True)
class RuleSet:
    ruleset_id: str
    version: str
    rules: tuple[DeterministicRule, ...]

    def __post_init__(self) -> None:
        if not self.ruleset_id.strip() or not self.version.strip():
            raise ValueError("Ruleset identity and version are required")
        ordered = tuple(
            sorted(
                self.rules,
                key=lambda rule: (
                    rule.version.identity.code,
                    rule.version.version,
                    rule.version.version_id,
                ),
            )
        )
        version_ids = [rule.version.version_id for rule in ordered]
        if len(version_ids) != len(set(version_ids)):
            raise ValueError("Ruleset cannot contain duplicate rule versions")
        for rule in ordered:
            if rule.lifecycle.rule_version != rule.version:
                raise ValueError("Rule lifecycle must belong to its executable version")
        object.__setattr__(self, "rules", ordered)

    @property
    def content_hash(self) -> str:
        payload = [
            {
                "content_hash": rule.version.content_hash,
                "identity_id": rule.version.identity.identity_id,
                "jurisdiction": rule.version.jurisdiction,
                "legal_source_id": rule.version.legal_source.source_id,
                "recorded_at": rule.version.recorded_at.isoformat(),
                "valid_from": rule.version.valid_from.isoformat(),
                "valid_to": (
                    rule.version.valid_to.isoformat() if rule.version.valid_to is not None else None
                ),
                "version": rule.version.version,
                "version_id": rule.version.version_id,
            }
            for rule in self.rules
        ]
        canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def reference(self) -> RuleSetRef:
        return RuleSetRef(
            ruleset_id=self.ruleset_id,
            version=self.version,
            content_hash=self.content_hash,
        )


class TaxEngine:
    def __init__(self, *, engine_version: str) -> None:
        if not engine_version.strip():
            raise ValueError("Engine version is required")
        self._engine_version = engine_version

    @property
    def engine_version(self) -> str:
        return self._engine_version

    def evaluate(
        self,
        *,
        facts: FactSet,
        context: EvaluationContext,
        ruleset: RuleSet,
    ) -> Evaluation:
        trace: list[DecisionStep] = []
        evaluated_rules: list[RuleVersionRef] = []
        applicable_rules: list[RuleVersionRef] = []
        decisions: list[tuple[DeterministicRule, RuleDecision]] = []
        sequence = 1

        for rule in ruleset.rules:
            reference = RuleVersionRef.from_version(rule.version)
            lifecycle_status = rule.lifecycle.status_at(context.known_at)
            if lifecycle_status is not RuleLifecycleStatus.PUBLISHED:
                trace.append(
                    DecisionStep(
                        sequence=sequence,
                        phase=TracePhase.SELECTION,
                        description="Rule excluded by lifecycle status at known_at",
                        outcome=(
                            lifecycle_status.value
                            if lifecycle_status is not None
                            else "NOT_RECORDED"
                        ),
                        rule=reference,
                    )
                )
                sequence += 1
                continue
            if not rule.lifecycle.is_legally_valid_on(facts.operation_date):
                trace.append(
                    DecisionStep(
                        sequence=sequence,
                        phase=TracePhase.SELECTION,
                        description="Rule excluded by legal validity interval",
                        outcome="OUTSIDE_LEGAL_VALIDITY",
                        rule=reference,
                    )
                )
                sequence += 1
                continue

            trace.append(
                DecisionStep(
                    sequence=sequence,
                    phase=TracePhase.SELECTION,
                    description="Published rule selected for deterministic evaluation",
                    outcome="SELECTED",
                    rule=reference,
                )
            )
            sequence += 1
            decision = rule.evaluate(facts)
            evaluated_rules.append(reference)
            decisions.append((rule, decision))
            if decision.status is RuleDecisionStatus.MATCHED:
                applicable_rules.append(reference)
            trace.append(
                DecisionStep(
                    sequence=sequence,
                    phase=TracePhase.EVALUATION,
                    description="Deterministic rule conditions evaluated",
                    outcome=decision.status.value,
                    rule=reference,
                    conditions=decision.conditions,
                    details=decision.trace_metadata,
                )
            )
            sequence += 1

        missing_facts = tuple(
            sorted(
                {
                    missing_fact
                    for _, decision in decisions
                    if decision.status is RuleDecisionStatus.REQUIRES_VALIDATION
                    for missing_fact in decision.missing_facts
                }
            )
        )
        candidates = tuple(
            sorted(
                {
                    candidate
                    for _, decision in decisions
                    if decision.status is RuleDecisionStatus.MATCHED
                    for candidate in decision.candidates
                }
            )
        )
        tax_candidates = tuple(
            sorted(
                (candidate for _, decision in decisions for candidate in decision.tax_candidates),
                key=lambda item: (*item.key, item.rule.version_id),
            )
        )
        distinct_candidate_count = len(candidates) + len(
            {candidate.key for candidate in tax_candidates}
        )
        if missing_facts:
            status = ClassificationStatus.REQUIRES_VALIDATION
        elif distinct_candidate_count > 1:
            status = ClassificationStatus.POSSIBLE_MATCHES
        elif distinct_candidate_count == 1:
            status = ClassificationStatus.CONCLUSIVE
        else:
            status = ClassificationStatus.UNCLASSIFIED

        all_conditions = tuple(
            condition for _, decision in decisions for condition in decision.conditions
        )
        satisfied_conditions = tuple(
            condition
            for condition in all_conditions
            if condition.status is ConditionStatus.SATISFIED
        )
        unsatisfied_conditions = tuple(
            condition
            for condition in all_conditions
            if condition.status is not ConditionStatus.SATISFIED
        )
        relevant_sources = self._relevant_legal_sources(decisions)
        trace.append(
            DecisionStep(
                sequence=sequence,
                phase=TracePhase.AGGREGATION,
                description="Rule decisions aggregated without arbitrary tie-breaking",
                outcome=status.value,
            )
        )

        outcome = ClassificationOutcome(
            status=status,
            candidates=candidates,
            missing_facts=missing_facts,
            evaluated_rules=tuple(evaluated_rules),
            applicable_rules=tuple(applicable_rules),
            satisfied_conditions=satisfied_conditions,
            unsatisfied_conditions=unsatisfied_conditions,
            legal_sources=relevant_sources,
            ruleset=ruleset.reference,
            engine_version=self.engine_version,
            trace=tuple(trace),
            tax_candidates=tax_candidates,
        )
        return Evaluation(
            evaluation_id=context.evaluation_id,
            evaluated_at=context.evaluated_at,
            known_at=context.known_at,
            correlation_id=context.correlation_id,
            input_hash=facts.input_hash(),
            engine_version=self.engine_version,
            ruleset=ruleset.reference,
            rule_versions_used=tuple(evaluated_rules),
            outcome=outcome,
        )

    @staticmethod
    def _relevant_legal_sources(
        decisions: list[tuple[DeterministicRule, RuleDecision]],
    ) -> tuple[LegalSource, ...]:
        relevant: dict[str, LegalSource] = {}
        for rule, decision in decisions:
            if decision.status in {
                RuleDecisionStatus.MATCHED,
                RuleDecisionStatus.REQUIRES_VALIDATION,
            }:
                relevant[rule.version.legal_source.source_id] = rule.version.legal_source
        return tuple(relevant[source_id] for source_id in sorted(relevant))
