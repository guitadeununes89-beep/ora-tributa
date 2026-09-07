from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tax_engine.engine import DeterministicRule
from tax_engine.ibs_cbs_rt_0003 import RtIbsCbs0003V1
from tax_engine.ibs_cbs_rt_0007 import RtIbsCbs0007V1
from tax_engine.ibs_cbs_rt_0008 import RtIbsCbs0008V1
from tax_engine.rule_lifecycle import RuleLifecycle
from tax_engine.rule_models import TaxRuleVersion

from tributaria_api.application.errors import GovernanceError
from tributaria_api.experimental.persisted_rules import resolve_synthetic_rule

RealRuleFactory = Callable[[TaxRuleVersion, RuleLifecycle, dict[str, Any]], DeterministicRule]


def _rt_0003(
    version: TaxRuleVersion, lifecycle: RuleLifecycle, content: dict[str, Any]
) -> DeterministicRule:
    expected = {
        "specification_id": "RT-IBSCBS-0003",
        "specification_version": 2,
        "cst": "200",
        "cclasstrib": "200010",
    }
    mismatches = [key for key, value in expected.items() if content.get(key) != value]
    if mismatches:
        raise GovernanceError(f"Real implementation provenance mismatch: {', '.join(mismatches)}")
    catalog_version_id = str(content.get("catalog_version_id", ""))
    if not catalog_version_id:
        raise GovernanceError("Real implementation requires catalog_version_id")
    return RtIbsCbs0003V1(
        version=version,
        lifecycle=lifecycle,
        catalog_version_id=catalog_version_id,
        cst_code="200",
        cclasstrib_code="200010",
    )


def _rt_0007(
    version: TaxRuleVersion, lifecycle: RuleLifecycle, content: dict[str, Any]
) -> DeterministicRule:
    expected = {
        "specification_id": "RT-IBSCBS-0007",
        "specification_version": 3,
        "cst": "200",
        "cclasstrib": "200022",
    }
    mismatches = [key for key, value in expected.items() if content.get(key) != value]
    if mismatches:
        raise GovernanceError(f"Real implementation provenance mismatch: {', '.join(mismatches)}")
    catalog_version_id = str(content.get("catalog_version_id", ""))
    if not catalog_version_id:
        raise GovernanceError("Real implementation requires catalog_version_id")
    return RtIbsCbs0007V1(
        version=version,
        lifecycle=lifecycle,
        catalog_version_id=catalog_version_id,
        cst_code="200",
        cclasstrib_code="200022",
    )


def _rt_0008(
    version: TaxRuleVersion, lifecycle: RuleLifecycle, content: dict[str, Any]
) -> DeterministicRule:
    expected = {
        "specification_id": "RT-IBSCBS-0008",
        "specification_version": 3,
        "cst": "200",
        "cclasstrib": "200023",
    }
    mismatches = [key for key, value in expected.items() if content.get(key) != value]
    if mismatches:
        raise GovernanceError(f"Real implementation provenance mismatch: {', '.join(mismatches)}")
    catalog_version_id = str(content.get("catalog_version_id", ""))
    if not catalog_version_id:
        raise GovernanceError("Real implementation requires catalog_version_id")
    return RtIbsCbs0008V1(
        version=version,
        lifecycle=lifecycle,
        catalog_version_id=catalog_version_id,
        cst_code="200",
        cclasstrib_code="200023",
    )


REAL_IMPLEMENTATIONS: dict[str, RealRuleFactory] = {
    "REAL_RT_IBSCBS_0003_V1": _rt_0003,
    "REAL_RT_IBSCBS_0007_V1": _rt_0007,
    "REAL_RT_IBSCBS_0008_V1": _rt_0008,
}


def resolve_persisted_rule(
    implementation_key: str,
    version: TaxRuleVersion,
    lifecycle: RuleLifecycle,
    *,
    is_synthetic: bool,
    content: dict[str, Any],
) -> DeterministicRule:
    if is_synthetic:
        return resolve_synthetic_rule(implementation_key, version, lifecycle)
    try:
        factory = REAL_IMPLEMENTATIONS[implementation_key]
    except KeyError as exc:
        raise GovernanceError(
            f"Executable real implementation is not allowlisted: {implementation_key}"
        ) from exc
    return factory(version, lifecycle, content)
