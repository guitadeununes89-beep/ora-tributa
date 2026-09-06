from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from hashlib import sha256

from tax_engine.money import TaxDecimal


class TaxDomain(StrEnum):
    IBS = "IBS"
    CBS = "CBS"
    SELECTIVE_TAX = "IS"
    ICMS = "ICMS"
    ISS = "ISS"
    IPI = "IPI"
    PIS = "PIS"
    COFINS = "COFINS"
    ICMS_ST = "ICMS_ST"


class ComputationStatus(StrEnum):
    CALCULATED = "CALCULATED"
    REQUIRES_VALIDATION = "REQUIRES_VALIDATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class BaseInteractionEffect(StrEnum):
    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"
    UNKNOWN = "UNKNOWN"


class CalculationOperation(StrEnum):
    STARTING_VALUE = "STARTING_VALUE"
    ADDITION = "ADDITION"
    EXCLUSION = "EXCLUSION"
    RATE_APPLICATION = "RATE_APPLICATION"
    TAX_AMOUNT = "TAX_AMOUNT"
    CREDIT = "CREDIT"
    CONSOLIDATION = "CONSOLIDATION"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True, slots=True)
class TaxTransitionPeriod:
    period_id: str
    label: str
    effective_from: date
    effective_to: date | None
    version: int
    legal_source_id: str
    legal_device: str
    content_hash: str

    def __post_init__(self) -> None:
        required = (
            self.period_id,
            self.label,
            self.legal_source_id,
            self.legal_device,
            self.content_hash,
        )
        if any(not value.strip() for value in required):
            raise ValueError("Transition period requires governed references")
        if self.version < 1:
            raise ValueError("Transition period version must be positive")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Transition period end cannot precede its start")

    def contains(self, operation_date: date) -> bool:
        return self.effective_from <= operation_date and (
            self.effective_to is None or operation_date <= self.effective_to
        )


@dataclass(frozen=True, slots=True)
class TaxInteractionRule:
    interaction_rule_id: str
    version: int
    calculated_tax: TaxDomain
    related_tax: TaxDomain
    effect: BaseInteractionEffect
    effective_from: date
    effective_to: date | None
    legal_source_id: str
    legal_device: str
    content_hash: str

    def __post_init__(self) -> None:
        required = (
            self.interaction_rule_id,
            self.legal_source_id,
            self.legal_device,
            self.content_hash,
        )
        if any(not value.strip() for value in required):
            raise ValueError("Interaction rule requires governed references")
        if self.version < 1:
            raise ValueError("Interaction rule version must be positive")
        if self.effect is BaseInteractionEffect.UNKNOWN:
            raise ValueError("A published interaction rule cannot have an unknown effect")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Interaction rule end cannot precede its start")


@dataclass(frozen=True, slots=True)
class BaseAdjustment:
    label: str
    amount: TaxDecimal
    related_tax: TaxDomain | None
    interaction_rule_id: str

    def __post_init__(self) -> None:
        if not self.label.strip() or not self.interaction_rule_id.strip():
            raise ValueError("Base adjustment requires label and interaction rule")


@dataclass(frozen=True, slots=True)
class CalculationStep:
    sequence: int
    operation: CalculationOperation
    description: str
    input_values: tuple[tuple[str, str], ...] = ()
    output_value: TaxDecimal | None = None
    rule_version_id: str | None = None
    legal_source_id: str | None = None

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("Calculation step sequence must be positive")
        if not self.description.strip():
            raise ValueError("Calculation step requires a description")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "description": self.description,
            "input_values": list(self.input_values),
            "legal_source_id": self.legal_source_id,
            "operation": self.operation.value,
            "output_value": self.output_value.as_string() if self.output_value else None,
            "rule_version_id": self.rule_version_id,
            "sequence": self.sequence,
        }


@dataclass(frozen=True, slots=True)
class CalculationTrace:
    trace_id: str
    operation_hash: str
    transition_period_id: str
    ruleset_fingerprint: str
    steps: tuple[CalculationStep, ...]
    decision_trace_id: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.trace_id,
            self.operation_hash,
            self.transition_period_id,
            self.ruleset_fingerprint,
        )
        if any(not value.strip() for value in required):
            raise ValueError("Calculation trace requires reproducibility references")
        sequences = tuple(step.sequence for step in self.steps)
        if sequences != tuple(sorted(set(sequences))):
            raise ValueError("Calculation steps must have unique ascending sequences")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "decision_trace_id": self.decision_trace_id,
            "operation_hash": self.operation_hash,
            "ruleset_fingerprint": self.ruleset_fingerprint,
            "steps": [step.canonical_payload() for step in self.steps],
            "trace_id": self.trace_id,
            "transition_period_id": self.transition_period_id,
        }

    def content_hash(self) -> str:
        payload = json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TaxComputationResult:
    status: ComputationStatus
    tax: TaxDomain
    tax_base: TaxDecimal | None
    nominal_rate: TaxDecimal | None
    effective_rate: TaxDecimal | None
    reduction: TaxDecimal | None
    amount: TaxDecimal | None
    exclusions: tuple[BaseAdjustment, ...]
    additions: tuple[BaseAdjustment, ...]
    credit: TaxDecimal | None
    legal_source_ids: tuple[str, ...]
    rule_version_ids: tuple[str, ...]
    calculation_trace: CalculationTrace
    missing_requirements: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required_values = (self.tax_base, self.nominal_rate, self.effective_rate, self.amount)
        if self.status is ComputationStatus.CALCULATED and any(
            value is None for value in required_values
        ):
            raise ValueError("A calculated result requires base, rates and amount")
        if self.status is ComputationStatus.CALCULATED and self.missing_requirements:
            raise ValueError("A calculated result cannot contain missing requirements")
        if self.status is ComputationStatus.REQUIRES_VALIDATION:
            if not self.missing_requirements:
                raise ValueError("An unresolved result must identify missing requirements")
            if self.amount is not None:
                raise ValueError("An unresolved result cannot silently expose a tax amount")


def unresolved_tax_computation(
    *,
    tax: TaxDomain,
    operation_hash: str,
    transition_period_id: str,
    ruleset_fingerprint: str,
    missing_requirements: tuple[str, ...],
    decision_trace_id: str | None = None,
) -> TaxComputationResult:
    if not missing_requirements:
        raise ValueError("Unresolved computation requires at least one missing requirement")
    trace = CalculationTrace(
        trace_id=f"unresolved:{operation_hash}:{tax.value}",
        operation_hash=operation_hash,
        transition_period_id=transition_period_id,
        ruleset_fingerprint=ruleset_fingerprint,
        decision_trace_id=decision_trace_id,
        steps=(
            CalculationStep(
                sequence=1,
                operation=CalculationOperation.UNRESOLVED,
                description="Tax computation stopped because governed rules are missing",
                input_values=tuple(
                    ("missing_requirement", requirement)
                    for requirement in missing_requirements
                ),
            ),
        ),
    )
    return TaxComputationResult(
        status=ComputationStatus.REQUIRES_VALIDATION,
        tax=tax,
        tax_base=None,
        nominal_rate=None,
        effective_rate=None,
        reduction=None,
        amount=None,
        exclusions=(),
        additions=(),
        credit=None,
        legal_source_ids=(),
        rule_version_ids=(),
        calculation_trace=trace,
        missing_requirements=missing_requirements,
    )
