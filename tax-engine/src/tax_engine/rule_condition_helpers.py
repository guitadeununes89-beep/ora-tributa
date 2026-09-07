"""Shared deterministic-condition helpers for governed rule modules.

Extracted for RT-IBSCBS-0007 and RT-IBSCBS-0008 so their condition logic does
not duplicate the private helpers already embedded in ibs_cbs_rt_0003.py.
ibs_cbs_rt_0003.py (the only published rule at the time this was written) is
intentionally left untouched to avoid any risk to its existing, tested
behaviour; new governed rules should use these instead of re-declaring the
same primitives.
"""

from __future__ import annotations

from collections.abc import Mapping

from tax_engine.evaluation import ConditionResult, ConditionStatus

UNKNOWN = "UNKNOWN"


def equals(
    condition_id: str,
    description: str,
    fact_name: str,
    observed: str | None,
    expected: str,
) -> ConditionResult:
    """Exactly one accepted value; UNKNOWN or absent is MISSING, not violated."""
    if observed is None or observed == UNKNOWN:
        return ConditionResult(
            condition_id=condition_id,
            description=description,
            fact_name=fact_name,
            status=ConditionStatus.MISSING,
            expected_value=expected,
            observed_value=None,
        )
    status = ConditionStatus.SATISFIED if observed == expected else ConditionStatus.NOT_SATISFIED
    return ConditionResult(
        condition_id=condition_id,
        description=description,
        fact_name=fact_name,
        status=status,
        expected_value=expected,
        observed_value=observed,
    )


def member(
    condition_id: str,
    description: str,
    fact_name: str,
    observed: str | None,
    expected: frozenset[str],
) -> ConditionResult:
    """Any of a set of accepted values; UNKNOWN or absent is MISSING."""
    if observed is None or observed == UNKNOWN:
        return ConditionResult(
            condition_id=condition_id,
            description=description,
            fact_name=fact_name,
            status=ConditionStatus.MISSING,
            expected_value="|".join(sorted(expected)),
            observed_value=None,
        )
    status = ConditionStatus.SATISFIED if observed in expected else ConditionStatus.NOT_SATISFIED
    return ConditionResult(
        condition_id=condition_id,
        description=description,
        fact_name=fact_name,
        status=status,
        expected_value="|".join(sorted(expected)),
        observed_value=observed,
    )


def mapped(
    condition_id: str,
    description: str,
    fact_name: str,
    observed: str | None,
    status_by_value: Mapping[str, ConditionStatus],
    *,
    expected_value: str,
) -> ConditionResult:
    """Custom per-value status mapping, for enums with a genuine third state.

    `status_by_value` must map every value the caller intends to treat as
    SATISFIED or NOT_SATISFIED explicitly; anything absent from it (including
    None and UNKNOWN) resolves to MISSING - the same fail-closed default used
    by `equals`/`member`.
    """
    if observed is None:
        resolved = ConditionStatus.MISSING
    else:
        resolved = status_by_value.get(observed, ConditionStatus.MISSING)
    return ConditionResult(
        condition_id=condition_id,
        description=description,
        fact_name=fact_name,
        status=resolved,
        expected_value=expected_value,
        observed_value=observed if resolved is not ConditionStatus.MISSING else None,
    )


def non_empty(
    condition_id: str,
    description: str,
    fact_name: str,
    observed: str | None,
) -> ConditionResult:
    """A free-text/identifier fact that only needs to be present, not matched."""
    if observed is None or not observed.strip():
        return ConditionResult(
            condition_id=condition_id,
            description=description,
            fact_name=fact_name,
            status=ConditionStatus.MISSING,
            expected_value="NON_EMPTY",
            observed_value=None,
        )
    return ConditionResult(
        condition_id=condition_id,
        description=description,
        fact_name=fact_name,
        status=ConditionStatus.SATISFIED,
        expected_value="NON_EMPTY",
        observed_value=observed,
    )
