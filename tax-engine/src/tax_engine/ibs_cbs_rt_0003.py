from __future__ import annotations

from dataclasses import dataclass

from tax_engine.evaluation import (
    CandidateSupport,
    ConditionResult,
    ConditionStatus,
    FactSet,
    RuleDecision,
    RuleDecisionStatus,
    TaxClassificationCandidate,
)
from tax_engine.rule_lifecycle import RuleLifecycle
from tax_engine.rule_models import RuleVersionRef, TaxRuleVersion

ELIGIBLE_BUYERS = frozenset({"DIRECT_PUBLIC_ADMINISTRATION_BODY", "AUTARCHY", "PUBLIC_FOUNDATION"})
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class RtIbsCbs0003V1:
    """LC 214/2025, art. 146, §1º, I — no inference from CNPJ or names."""

    version: TaxRuleVersion
    lifecycle: RuleLifecycle
    catalog_version_id: str
    cst_code: str
    cclasstrib_code: str

    def evaluate(self, facts: FactSet) -> RuleDecision:
        attributes = facts.product_attributes
        conditions = (
            _equals(
                "rt-ibscbs-0003-product-kind",
                "Produto confirmado como medicamento",
                "product.kind",
                attributes.get("product.kind"),
                "MEDICINE",
            ),
            _equals(
                "rt-ibscbs-0003-anvisa",
                "Medicamento com registro Anvisa confirmado",
                "product.anvisa_registration_status",
                attributes.get("product.anvisa_registration_status"),
                "REGISTERED",
            ),
            _member(
                "rt-ibscbs-0003-buyer-legal-nature",
                "Adquirente é administração direta, autarquia ou fundação pública",
                "buyer.legal_nature",
                attributes.get("buyer.legal_nature"),
                ELIGIBLE_BUYERS,
            ),
            _equals(
                "rt-ibscbs-0003-effective-buyer",
                "Ente qualificado é o adquirente efetivo da operação",
                "operation.buyer_is_acquirer",
                attributes.get("operation.buyer_is_acquirer"),
                "YES",
            ),
        )
        details = (
            ("legal_device", "LC 214/2025, art. 146, § 1º, I"),
            ("rule_version", str(self.version.version)),
            ("catalog_version_id", self.catalog_version_id),
            ("cst", self.cst_code),
            ("cclasstrib", self.cclasstrib_code),
        )
        if any(item.status is ConditionStatus.NOT_SATISFIED for item in conditions):
            return RuleDecision(
                status=RuleDecisionStatus.NOT_MATCHED,
                conditions=conditions,
                trace_metadata=details,
            )
        missing = tuple(
            item.fact_name for item in conditions if item.status is ConditionStatus.MISSING
        )
        if missing:
            return RuleDecision(
                status=RuleDecisionStatus.REQUIRES_VALIDATION,
                missing_facts=missing,
                conditions=conditions,
                trace_metadata=details,
            )
        reference = RuleVersionRef.from_version(self.version)
        candidate = TaxClassificationCandidate(
            catalog_version_id=self.catalog_version_id,
            cst_code=self.cst_code,
            classification_code=self.cclasstrib_code,
            rule=reference,
            support=CandidateSupport.SUPPORTED,
            conditions=conditions,
            legal_sources=(self.version.legal_source,),
        )
        return RuleDecision(
            status=RuleDecisionStatus.MATCHED,
            tax_candidates=(candidate,),
            conditions=conditions,
            trace_metadata=details,
        )


def _equals(
    condition_id: str,
    description: str,
    fact_name: str,
    observed: str | None,
    expected: str,
) -> ConditionResult:
    if observed is None or observed == UNKNOWN:
        status = ConditionStatus.MISSING
        value = None
    else:
        status = (
            ConditionStatus.SATISFIED if observed == expected else ConditionStatus.NOT_SATISFIED
        )
        value = observed
    return ConditionResult(
        condition_id=condition_id,
        description=description,
        fact_name=fact_name,
        status=status,
        expected_value=expected,
        observed_value=value,
    )


def _member(
    condition_id: str,
    description: str,
    fact_name: str,
    observed: str | None,
    expected: frozenset[str],
) -> ConditionResult:
    if observed is None or observed == UNKNOWN:
        status = ConditionStatus.MISSING
        value = None
    else:
        status = (
            ConditionStatus.SATISFIED if observed in expected else ConditionStatus.NOT_SATISFIED
        )
        value = observed
    return ConditionResult(
        condition_id=condition_id,
        description=description,
        fact_name=fact_name,
        status=status,
        expected_value="|".join(sorted(expected)),
        observed_value=value,
    )
