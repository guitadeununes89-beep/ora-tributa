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
from tax_engine.rule_condition_helpers import equals, non_empty
from tax_engine.rule_lifecycle import RuleLifecycle
from tax_engine.rule_models import RuleVersionRef, TaxRuleVersion


@dataclass(frozen=True, slots=True)
class RtIbsCbs0004V1:
    """LC 214/2025, art. 146, caput, redação original; Anexo XIV (RT-IBSCBS-0004 v1).

    Janela histórica 01/01/2026-13/01/2026 (fim exclusivo em 14/01/2026), já
    aplicada pelo motor via vigência (TaxRuleVersion.valid_from/valid_to) - esta
    classe nao repete a checagem de data. Nao contem nem infere lista de NCM/SH
    do Anexo XIV; exige correspondencia ja comprovada por fonte oficial.
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
                "rt-ibscbs-0004-ncm-sh",
                "NCM/SH do produto informada",
                "product.ncm_sh",
                a.get("product.ncm_sh"),
            ),
            equals(
                "rt-ibscbs-0004-annex-match",
                "Correspondencia ao Anexo XIV original confirmada",
                "product.annex_xiv_match_status",
                a.get("product.annex_xiv_match_status"),
                "MATCHED",
            ),
            equals(
                "rt-ibscbs-0004-normative-version",
                "Versao normativa da publicacao original da LC 214/2025",
                "normative.annex_xiv_version",
                a.get("normative.annex_xiv_version"),
                "LC214_2025_ORIGINAL",
            ),
        )
        details = (
            ("legal_device", "LC 214/2025, art. 146, caput (redacao original); Anexo XIV"),
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
