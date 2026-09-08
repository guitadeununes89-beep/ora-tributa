"""Multi-rule candidate evaluation (Etapa 21).

`TaxEngine.evaluate()` (engine.py) evaluates every rule in a *single* governed
ruleset and aggregates `missing_facts` as the union across every rule that
returned REQUIRES_VALIDATION - correct when a ruleset holds one legal
hypothesis, but wrong when several published rulesets describing mutually
exclusive hypotheses are queried together: a rule that was simply never the
right scenario still reports its own untouched fields as "missing", which
then vetoes every other rule's clean MATCHED result (see ADR-0008, and the
abandoned `IBSCBS-ZFM-PILOT-001` ruleset documented in CLAUDE_STATUS.md,
Etapa 11).

This module adds a second, independent evaluator for that specific case. It
never touches `engine.py`'s aggregation (existing single-ruleset behaviour,
and every rule module's own conditions, are untouched), and it never
produces a persisted `RuleSetRecord` - see ADR-0025: a `CandidateRuleSet` is
always an ephemeral, in-memory composition of rules that already live in
their own approved, published, single-rule rulesets.

The only genuinely new concept is per-rule *candidacy*: whether a rule, given
the facts, is a genuine candidate that just needs one more answer
(SCOPE_CONFIRMED_INCOMPLETE) versus a rule that was never engaged at all
because its own scope-defining facts (see `rule_scope_registry.py`) were
never even asked (SCOPE_UNCONFIRMED). Only the former contributes to the
aggregate `missing_facts` - that is the entire fix.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tax_engine.engine import DeterministicRule, RuleSet
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
    TracePhase,
)
from tax_engine.rule_lifecycle import RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, RuleVersionRef


class RuleCandidacyStatus(StrEnum):
    """Where a single rule stands once evaluated against the shared facts."""

    SUPPORTED = "SUPPORTED"
    SCOPE_CONFIRMED_INCOMPLETE = "SCOPE_CONFIRMED_INCOMPLETE"
    SCOPE_UNCONFIRMED = "SCOPE_UNCONFIRMED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True, slots=True)
class RuleScope:
    """The subset of a rule's own approved required facts that most directly
    signal whether its legal hypothesis is even in play. Not new legal
    content - see rule_scope_registry.py for the governed source of these
    fact names, already present in each rule's own specification."""

    rule_code: str
    scope_facts: frozenset[str]

    def __post_init__(self) -> None:
        if not self.rule_code.strip():
            raise ValueError("RuleScope requires a rule_code")
        if not self.scope_facts:
            raise ValueError(f"RuleScope for {self.rule_code} requires at least one scope fact")


@dataclass(frozen=True, slots=True)
class RuleCandidacy:
    rule: RuleVersionRef
    status: RuleCandidacyStatus
    decision: RuleDecision
    scope_facts: frozenset[str]

    @property
    def unconfirmed_scope_facts(self) -> tuple[str, ...]:
        return tuple(sorted(self.scope_facts.intersection(self.decision.missing_facts)))


@dataclass(frozen=True, slots=True)
class CandidateRuleSet:
    """An ephemeral, in-memory composition of rules for one query. Never
    persisted as a RuleSetRecord - see ADR-0025."""

    composed_id: str
    rules: tuple[tuple[DeterministicRule, RuleScope], ...]

    def __post_init__(self) -> None:
        if not self.composed_id.strip():
            raise ValueError("CandidateRuleSet requires a composed_id")
        if not self.rules:
            raise ValueError("CandidateRuleSet requires at least one candidate rule")


@dataclass(frozen=True, slots=True)
class MultiRuleEvaluation:
    evaluation: Evaluation
    candidacies: tuple[RuleCandidacy, ...]


class MultiRuleEngine:
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
        candidates: CandidateRuleSet,
    ) -> MultiRuleEvaluation:
        # RuleSet is reused purely as a value object: it sorts rules into a
        # canonical order, rejects duplicate versions, and gives us a stable
        # content_hash/reference for free - the same guarantees engine.py
        # relies on. It is never handed to TaxEngine.evaluate().
        ruleset = RuleSet(
            ruleset_id=candidates.composed_id,
            version="1.0.0-composed",
            rules=tuple(rule for rule, _ in candidates.rules),
        )
        scope_by_version_id = {
            rule.version.version_id: scope for rule, scope in candidates.rules
        }

        trace: list[DecisionStep] = []
        evaluated_rules: list[RuleVersionRef] = []
        applicable_rules: list[RuleVersionRef] = []
        evaluated: list[tuple[DeterministicRule, RuleCandidacyStatus, RuleDecision]] = []
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
            if decision.status is RuleDecisionStatus.MATCHED:
                applicable_rules.append(reference)

            scope = scope_by_version_id[rule.version.version_id]
            candidacy_status = _classify_candidacy(decision, scope)
            evaluated.append((rule, candidacy_status, decision))
            unconfirmed = sorted(scope.scope_facts.intersection(decision.missing_facts))

            trace.append(
                DecisionStep(
                    sequence=sequence,
                    phase=TracePhase.EVALUATION,
                    description="Deterministic rule conditions evaluated",
                    outcome=decision.status.value,
                    rule=reference,
                    conditions=decision.conditions,
                    details=(
                        *decision.trace_metadata,
                        ("scope_candidacy", candidacy_status.value),
                        *(("unconfirmed_scope_fact", fact) for fact in unconfirmed),
                    ),
                )
            )
            sequence += 1

        # This is the fix: only rules whose scope is already confirmed
        # contribute their missing facts; a rule whose scope was never even
        # asked about (SCOPE_UNCONFIRMED) cannot veto another rule's clean
        # result just because its own, irrelevant fields are unset.
        missing_facts = tuple(
            sorted(
                {
                    fact
                    for _, status, decision in evaluated
                    if status is RuleCandidacyStatus.SCOPE_CONFIRMED_INCOMPLETE
                    for fact in decision.missing_facts
                }
            )
        )
        candidates_str = tuple(
            sorted(
                {
                    candidate
                    for _, status, decision in evaluated
                    if status is RuleCandidacyStatus.SUPPORTED
                    for candidate in decision.candidates
                }
            )
        )
        tax_candidates = tuple(
            sorted(
                (
                    candidate
                    for _, status, decision in evaluated
                    if status is RuleCandidacyStatus.SUPPORTED
                    for candidate in decision.tax_candidates
                ),
                key=lambda item: (*item.key, item.rule.version_id),
            )
        )
        distinct_candidate_count = len(candidates_str) + len(
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
            condition for _, _, decision in evaluated for condition in decision.conditions
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
        relevant_sources = _relevant_legal_sources(evaluated)

        candidacy_counts = {candidacy_status: 0 for candidacy_status in RuleCandidacyStatus}
        for _, candidacy_status, _ in evaluated:
            candidacy_counts[candidacy_status] += 1
        trace.append(
            DecisionStep(
                sequence=sequence,
                phase=TracePhase.AGGREGATION,
                description="Rule decisions aggregated without arbitrary tie-breaking",
                outcome=status.value,
                details=tuple(
                    (candidacy_status.value.lower(), str(count))
                    for candidacy_status, count in candidacy_counts.items()
                ),
            )
        )

        outcome = ClassificationOutcome(
            status=status,
            candidates=candidates_str,
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
        evaluation = Evaluation(
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
        candidacies = tuple(
            RuleCandidacy(
                rule=RuleVersionRef.from_version(rule.version),
                status=candidacy_status,
                decision=decision,
                scope_facts=scope_by_version_id[rule.version.version_id].scope_facts,
            )
            for rule, candidacy_status, decision in evaluated
        )
        return MultiRuleEvaluation(evaluation=evaluation, candidacies=candidacies)


def _classify_candidacy(decision: RuleDecision, scope: RuleScope) -> RuleCandidacyStatus:
    if decision.status is RuleDecisionStatus.MATCHED:
        return RuleCandidacyStatus.SUPPORTED
    if decision.status is RuleDecisionStatus.NOT_MATCHED:
        return RuleCandidacyStatus.NOT_APPLICABLE
    if scope.scope_facts.intersection(decision.missing_facts):
        return RuleCandidacyStatus.SCOPE_UNCONFIRMED
    return RuleCandidacyStatus.SCOPE_CONFIRMED_INCOMPLETE


def _relevant_legal_sources(
    evaluated: list[tuple[DeterministicRule, RuleCandidacyStatus, RuleDecision]],
) -> tuple[LegalSource, ...]:
    # Only hypotheses that are genuinely in play (matched, or a real
    # candidate still missing a non-scope fact) surface a legal basis - a
    # rule nobody ever engaged (SCOPE_UNCONFIRMED) or that was actively
    # contradicted (NOT_APPLICABLE) must not appear as if it were relevant.
    relevant: dict[str, LegalSource] = {}
    for rule, status, _ in evaluated:
        if status in {
            RuleCandidacyStatus.SUPPORTED,
            RuleCandidacyStatus.SCOPE_CONFIRMED_INCOMPLETE,
        }:
            relevant[rule.version.legal_source.source_id] = rule.version.legal_source
    return tuple(relevant[source_id] for source_id in sorted(relevant))
