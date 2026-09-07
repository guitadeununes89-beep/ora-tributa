from __future__ import annotations

from dataclasses import dataclass

from tax_engine.evaluation import (
    CandidateSupport,
    ConditionStatus,
    FactSet,
    RuleDecision,
    RuleDecisionStatus,
    TaxClassificationCandidate,
)
from tax_engine.rule_condition_helpers import equals
from tax_engine.rule_lifecycle import RuleLifecycle
from tax_engine.rule_models import RuleVersionRef, TaxRuleVersion


@dataclass(frozen=True, slots=True)
class RtIbsCbs0005V1:
    """LC 214/2025, art. 146, par. 1, II; LC 187/2021, arts. 9-11 (RT-IBSCBS-0005 v1).

    Medicamento registrado na Anvisa adquirido por entidade de saude imune ao
    IBS/CBS, com CEBAS valido e requisito legal de prestacao de servicos ao SUS
    comprovado. A cClassTrib 200010 tambem abrange o inciso I (RT-IBSCBS-0003);
    a coincidencia da classificacao oficial nao autoriza combinar as hipoteses
    juridicas - este modulo e o registro de RT-IBSCBS-0003 permanecem
    independentes, cada um com seu proprio ruleset explicito.
    """

    version: TaxRuleVersion
    lifecycle: RuleLifecycle
    catalog_version_id: str
    cst_code: str
    cclasstrib_code: str

    def evaluate(self, facts: FactSet) -> RuleDecision:
        a = facts.product_attributes
        conditions = (
            equals(
                "rt-ibscbs-0005-product-kind",
                "Produto confirmado como medicamento",
                "product.kind",
                a.get("product.kind"),
                "MEDICINE",
            ),
            equals(
                "rt-ibscbs-0005-anvisa",
                "Medicamento com registro Anvisa confirmado",
                "product.anvisa_registration_status",
                a.get("product.anvisa_registration_status"),
                "REGISTERED",
            ),
            equals(
                "rt-ibscbs-0005-health-entity",
                "Adquirente e entidade de saude",
                "buyer.health_entity_status",
                a.get("buyer.health_entity_status"),
                "HEALTH_ENTITY",
            ),
            equals(
                "rt-ibscbs-0005-immunity",
                "Adquirente imune ao IBS e a CBS",
                "buyer.ibs_cbs_immunity_status",
                a.get("buyer.ibs_cbs_immunity_status"),
                "IMMUNE",
            ),
            equals(
                "rt-ibscbs-0005-effective-buyer",
                "Entidade qualificada e a adquirente efetiva da operacao",
                "operation.effective_buyer_status",
                a.get("operation.effective_buyer_status"),
                "CONFIRMED",
            ),
            equals(
                "rt-ibscbs-0005-cebas",
                "CEBAS valido na data da operacao",
                "buyer.cebas_status",
                a.get("buyer.cebas_status"),
                "VALID",
            ),
            equals(
                "rt-ibscbs-0005-sus-requirement",
                "Requisito legal de prestacao de servicos ao SUS satisfeito",
                "buyer.sus_service_requirement_status",
                a.get("buyer.sus_service_requirement_status"),
                "SATISFIED",
            ),
        )
        details = (
            (
                "legal_device",
                "LC 214/2025, art. 146, par. 1, II; LC 187/2021, arts. 9 a 11",
            ),
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
