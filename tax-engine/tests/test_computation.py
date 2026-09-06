from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

import pytest
from tax_engine.computation import (
    BaseInteractionEffect,
    CalculationOperation,
    CalculationStep,
    CalculationTrace,
    ComputationStatus,
    TaxDomain,
    TaxInteractionRule,
    TaxTransitionPeriod,
    unresolved_tax_computation,
)
from tax_engine.money import TaxDecimal


def period(*, version: int = 1, content_hash: str = "period-hash-v1") -> TaxTransitionPeriod:
    return TaxTransitionPeriod(
        period_id="TRANSITION-TEST",
        label="Synthetic governed test period",
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 12, 31),
        version=version,
        legal_source_id="LEGAL-SOURCE-TEST",
        legal_device="Synthetic test device",
        content_hash=content_hash,
    )


def test_tax_domains_are_explicit_and_extensible() -> None:
    assert {item.value for item in TaxDomain} == {
        "IBS",
        "CBS",
        "IS",
        "ICMS",
        "ISS",
        "IPI",
        "PIS",
        "COFINS",
        "ICMS_ST",
    }


def test_transition_period_is_temporal_and_historical_version_is_immutable() -> None:
    first = period()
    second = period(version=2, content_hash="period-hash-v2")

    assert first.contains(date(2026, 1, 1))
    assert first.contains(date(2026, 12, 31))
    assert not first.contains(date(2027, 1, 1))
    assert first.version == 1
    assert second.version == 2
    with pytest.raises(FrozenInstanceError):
        first.version = 2  # type: ignore[misc]


def test_tax_interaction_rule_requires_version_and_governed_source() -> None:
    rule = TaxInteractionRule(
        interaction_rule_id="INTERACTION-TEST",
        version=1,
        calculated_tax=TaxDomain.IBS,
        related_tax=TaxDomain.SELECTIVE_TAX,
        effect=BaseInteractionEffect.INCLUDED,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        legal_source_id="LEGAL-SOURCE-TEST",
        legal_device="Synthetic test device",
        content_hash="interaction-hash-v1",
    )

    assert rule.version == 1
    assert rule.effect is BaseInteractionEffect.INCLUDED


def test_calculation_trace_is_reproducible_with_decimal_strings() -> None:
    step = CalculationStep(
        sequence=1,
        operation=CalculationOperation.STARTING_VALUE,
        description="Synthetic operation value",
        input_values=(("operation_value", "100000.00"),),
        output_value=TaxDecimal(Decimal("100000.00")),
    )
    left = CalculationTrace(
        trace_id="TRACE-TEST",
        operation_hash="operation-hash",
        transition_period_id="TRANSITION-TEST",
        ruleset_fingerprint="ruleset-hash",
        steps=(step,),
    )
    right = CalculationTrace(
        trace_id="TRACE-TEST",
        operation_hash="operation-hash",
        transition_period_id="TRANSITION-TEST",
        ruleset_fingerprint="ruleset-hash",
        steps=(step,),
    )

    assert left.content_hash() == right.content_hash()
    assert left.canonical_payload()["steps"] == [step.canonical_payload()]


def test_missing_rule_is_uncertainty_and_never_silent_zero() -> None:
    result = unresolved_tax_computation(
        tax=TaxDomain.SELECTIVE_TAX,
        operation_hash="operation-hash",
        transition_period_id="TRANSITION-TEST",
        ruleset_fingerprint="ruleset-hash",
        missing_requirements=("published_rate_rule",),
    )

    assert result.status is ComputationStatus.REQUIRES_VALIDATION
    assert result.amount is None
    assert result.tax_base is None
    assert result.nominal_rate is None
    assert result.missing_requirements == ("published_rate_rule",)


def test_float_cannot_enter_calculation_contract() -> None:
    with pytest.raises(TypeError, match="never"):
        TaxDecimal(100000.0)  # type: ignore[arg-type]
