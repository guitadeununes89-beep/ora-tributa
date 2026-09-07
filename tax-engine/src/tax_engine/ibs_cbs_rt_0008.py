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
from tax_engine.rule_condition_helpers import equals, member, non_empty
from tax_engine.rule_lifecycle import RuleLifecycle
from tax_engine.rule_models import RuleVersionRef, TaxRuleVersion

FLOW_TYPES = frozenset({"DIRECT", "TOLL_MANUFACTURING"})
TAXABLE_SCOPES = frozenset({"FULL_OPERATION", "VALUE_ADDED_ONLY"})


@dataclass(frozen=True, slots=True)
class RtIbsCbs0008V1:
    """LC 214/2025, art. 448; Resolucao CGIBS 6/2026, art. 519 (RT-IBSCBS-0008 v3).

    Bem material intermediario entre duas industrias incentivadas, ambas
    estabelecidas na Zona Franca de Manaus, com entrega dentro da area. Nao
    infere DIRECT vs. TOLL_MANUFACTURING a partir de outros fatos, nem impoe
    correspondencia obrigatoria entre `operation.flow_type` e
    `operation.taxable_scope_status` alem da que a propria especificacao
    descreve; cada fato e avaliado pelo seu proprio valor informado.
    """

    version: TaxRuleVersion
    lifecycle: RuleLifecycle
    catalog_version_id: str
    cst_code: str
    cclasstrib_code: str

    def evaluate(self, facts: FactSet) -> RuleDecision:
        a = facts.product_attributes
        conditions = (
            non_empty(
                "rt-ibscbs-0008-zfm-area-version",
                "Versao territorial governada da ZFM informada",
                "operation.zfm_area_version_id",
                a.get("operation.zfm_area_version_id"),
            ),
            equals(
                "rt-ibscbs-0008-seller-inside",
                "Estabelecimento fornecedor dentro da Zona Franca de Manaus",
                "seller.establishment_zfm_relation",
                a.get("seller.establishment_zfm_relation"),
                "INSIDE",
            ),
            equals(
                "rt-ibscbs-0008-buyer-inside",
                "Estabelecimento adquirente dentro da Zona Franca de Manaus",
                "buyer.establishment_zfm_relation",
                a.get("buyer.establishment_zfm_relation"),
                "INSIDE",
            ),
            equals(
                "rt-ibscbs-0008-seller-incentivized",
                "Fornecedor qualificado como industria incentivada",
                "seller.zfm_incentivized_industry_status",
                a.get("seller.zfm_incentivized_industry_status"),
                "VALID",
            ),
            equals(
                "rt-ibscbs-0008-buyer-incentivized",
                "Adquirente qualificado como industria incentivada",
                "buyer.zfm_incentivized_industry_status",
                a.get("buyer.zfm_incentivized_industry_status"),
                "VALID",
            ),
            equals(
                "rt-ibscbs-0008-material-good",
                "Objeto e bem material",
                "product.material_good_status",
                a.get("product.material_good_status"),
                "MATERIAL_GOOD",
            ),
            equals(
                "rt-ibscbs-0008-intermediate-good",
                "Bem qualificado como intermediario para a operacao",
                "product.intermediate_good_status",
                a.get("product.intermediate_good_status"),
                "INTERMEDIATE_GOOD",
            ),
            equals(
                "rt-ibscbs-0008-delivery-inside",
                "Entrega ou disponibilizacao ocorre dentro da Zona Franca de Manaus",
                "operation.delivery_area_status",
                a.get("operation.delivery_area_status"),
                "INSIDE_ZFM",
            ),
            member(
                "rt-ibscbs-0008-flow-type",
                "Natureza do fluxo (operacao direta ou industrializacao por encomenda) informada",
                "operation.flow_type",
                a.get("operation.flow_type"),
                FLOW_TYPES,
            ),
            member(
                "rt-ibscbs-0008-taxable-scope",
                "Escopo tributavel (operacao completa ou valor adicionado) informado",
                "operation.taxable_scope_status",
                a.get("operation.taxable_scope_status"),
                TAXABLE_SCOPES,
            ),
            equals(
                "rt-ibscbs-0008-not-excluded",
                "Bem nao abrangido pelas exclusoes do art. 443, par. 1",
                "product.art_443_par1_exclusion_status",
                a.get("product.art_443_par1_exclusion_status"),
                "NOT_EXCLUDED",
            ),
        )
        details = (
            ("legal_device", "LC 214/2025, art. 448; Resolucao CGIBS 6/2026, art. 519"),
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
