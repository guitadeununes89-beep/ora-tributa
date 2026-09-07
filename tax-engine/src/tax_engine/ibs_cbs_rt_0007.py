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
from tax_engine.rule_condition_helpers import equals, mapped, member, non_empty
from tax_engine.rule_lifecycle import RuleLifecycle
from tax_engine.rule_models import RuleVersionRef, TaxRuleVersion

ADMITTED_REGIMES = frozenset({"REGULAR_IBS_CBS", "SIMPLES_NACIONAL"})

_ENTRY_PROOF_STATUS = {
    "CONFIRMED": ConditionStatus.SATISFIED,
    "NOT_CONFIRMED_AFTER_DEADLINE": ConditionStatus.NOT_SATISFIED,
    # PENDING_WITHIN_DEADLINE is deliberately not mapped: still inside the legal
    # grace period, so it resolves to MISSING (needs continued follow-up), never
    # a silent match nor a rejection (LC 214/2025, art. 445, §§ 6-7; Resolucao
    # CGIBS 6/2026, arts. 516, §§ 6-7, and 552).
}

_ENTRY_DEADLINE_STATUS = {
    "WITHIN_120_DAYS": ConditionStatus.SATISFIED,
    "VALID_EXTENSION_WITHIN_210_DAYS": ConditionStatus.SATISFIED,
    "EXPIRED": ConditionStatus.NOT_SATISFIED,
}


@dataclass(frozen=True, slots=True)
class RtIbsCbs0007V1:
    """LC 214/2025, art. 445; Resolucao CGIBS 6/2026, art. 516 (RT-IBSCBS-0007 v3).

    Bem industrializado de origem nacional, originado fora da ZFM, destinado a
    contribuinte habilitado estabelecido na ZFM. Extensao a bens estrangeiros
    (Resolucao CGIBS 6/2026, art. 516, par. 3) esta fora do escopo desta
    especificacao (ver known_conflicts em TJA-ZFM/RT-IBSCBS-0007), e nao e
    avaliada por este modulo.
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
                "rt-ibscbs-0007-zfm-area-version",
                "Versao territorial governada da ZFM informada",
                "operation.zfm_area_version_id",
                a.get("operation.zfm_area_version_id"),
            ),
            equals(
                "rt-ibscbs-0007-origin",
                "Operacao originada fora da Zona Franca de Manaus",
                "operation.origin_area_status",
                a.get("operation.origin_area_status"),
                "OUTSIDE_ZFM",
            ),
            equals(
                "rt-ibscbs-0007-destination",
                "Operacao destinada a Zona Franca de Manaus",
                "operation.destination_area_status",
                a.get("operation.destination_area_status"),
                "ZFM",
            ),
            equals(
                "rt-ibscbs-0007-material-good",
                "Objeto e bem material",
                "product.material_good_status",
                a.get("product.material_good_status"),
                "MATERIAL_GOOD",
            ),
            equals(
                "rt-ibscbs-0007-industrialized",
                "Bem industrializado",
                "product.industrialization_status",
                a.get("product.industrialization_status"),
                "INDUSTRIALIZED",
            ),
            equals(
                "rt-ibscbs-0007-national-origin",
                "Origem nacional do bem",
                "product.origin_status",
                a.get("product.origin_status"),
                "NATIONAL",
            ),
            equals(
                "rt-ibscbs-0007-buyer-established",
                "Adquirente estabelecido na Zona Franca de Manaus",
                "buyer.establishment_area_status",
                a.get("buyer.establishment_area_status"),
                "ESTABLISHED_IN_ZFM",
            ),
            equals(
                "rt-ibscbs-0007-buyer-taxpayer",
                "Adquirente e contribuinte do IBS/CBS",
                "buyer.taxpayer_status",
                a.get("buyer.taxpayer_status"),
                "TAXPAYER",
            ),
            equals(
                "rt-ibscbs-0007-buyer-habilitation",
                "Adquirente habilitado nos termos do art. 442 da LC 214/2025",
                "buyer.art_442_habilitation_status",
                a.get("buyer.art_442_habilitation_status"),
                "VALID",
            ),
            member(
                "rt-ibscbs-0007-buyer-regime",
                "Adquirente no regime regular do IBS/CBS ou no Simples Nacional",
                "buyer.tax_regime_status",
                a.get("buyer.tax_regime_status"),
                ADMITTED_REGIMES,
            ),
            equals(
                "rt-ibscbs-0007-suframa-invoice",
                "Documento fiscal com inscricao Suframa do destinatario",
                "operation.invoice_suframa_registration_status",
                a.get("operation.invoice_suframa_registration_status"),
                "PRESENT_AND_MATCHING",
            ),
            equals(
                "rt-ibscbs-0007-not-excluded",
                "Bem nao abrangido pelas exclusoes do art. 443, par. 1",
                "product.art_443_par1_exclusion_status",
                a.get("product.art_443_par1_exclusion_status"),
                "NOT_EXCLUDED",
            ),
            mapped(
                "rt-ibscbs-0007-entry-proof",
                "Internamento na Zona Franca de Manaus comprovado",
                "operation.zfm_entry_proof_status",
                a.get("operation.zfm_entry_proof_status"),
                _ENTRY_PROOF_STATUS,
                expected_value="CONFIRMED",
            ),
            mapped(
                "rt-ibscbs-0007-entry-deadline",
                "Prazo de internamento (120 ou prorrogacao ate 210 dias) nao expirado",
                "operation.entry_deadline_status",
                a.get("operation.entry_deadline_status"),
                _ENTRY_DEADLINE_STATUS,
                expected_value="WITHIN_120_DAYS|VALID_EXTENSION_WITHIN_210_DAYS",
            ),
        )
        details = (
            ("legal_device", "LC 214/2025, art. 445; Resolucao CGIBS 6/2026, art. 516"),
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
