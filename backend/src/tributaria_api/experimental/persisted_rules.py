from __future__ import annotations

from collections.abc import Callable

from tax_engine.engine import DeterministicRule
from tax_engine.rule_lifecycle import RuleLifecycle
from tax_engine.rule_models import TaxRuleVersion

from tributaria_api.application.errors import GovernanceError
from tributaria_api.experimental.synthetic_rules import SyntheticRuleA, SyntheticRuleB

RuleFactory = Callable[[TaxRuleVersion, RuleLifecycle], DeterministicRule]


def _rule_a(version: TaxRuleVersion, lifecycle: RuleLifecycle) -> DeterministicRule:
    return SyntheticRuleA(version, lifecycle)


def _rule_b(version: TaxRuleVersion, lifecycle: RuleLifecycle) -> DeterministicRule:
    return SyntheticRuleB(version, lifecycle)


SYNTHETIC_IMPLEMENTATIONS: dict[str, RuleFactory] = {
    "SYNTHETIC_RULE_A_V1": _rule_a,
    "SYNTHETIC_RULE_B_V1": _rule_b,
}


def resolve_synthetic_rule(
    implementation_key: str,
    version: TaxRuleVersion,
    lifecycle: RuleLifecycle,
) -> DeterministicRule:
    try:
        factory = SYNTHETIC_IMPLEMENTATIONS[implementation_key]
    except KeyError as exc:
        raise GovernanceError(
            f"Executable synthetic implementation is not allowlisted: {implementation_key}"
        ) from exc
    return factory(version, lifecycle)
