"""Tax-candidate discovery for a searched NCM/NBS object (Etapa 22).

Relates an object found in the governed NCM/NBS catalogs to the families of
already-published rules that might apply to it - never a tax determination,
never a CST/cClassTrib assignment, never an inference from description
similarity or AI. Each entry here is a reviewed governance decision citing a
real, structural fact (the NCM/NBS table's own official grouping, an
approved rule specification's own declared scope) - never invented.

Fail-closed by construction: `discover_by_ncm`/`discover_by_nbs` return
`None` for anything not explicitly registered below, exactly like
`rule_scope_registry.scope_for` (Etapa 21) - a missing entry means "not
governed yet", never "assume the most common case".

Current coverage (Etapa 22):
- NCM Capítulo 30 ("Produtos farmacêuticos", the NCM table's own official
  chapter grouping) -> candidate families RT-IBSCBS-0004/RT-IBSCBS-0005,
  both already published and already scoped to medicine by their own
  approved specifications. This is the only NCM/NBS -> rule relationship
  with a governed source that actually reaches a published rule.
- NBS: intentionally empty. A real official NBS<->cClassTrib correlation
  exists (Anexo VIII, RFB/Portal NFS-e,
  https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/
  anexoviii-correlacaoitemnbsindopcclasstrib_ibscbs_v1-00-00.xlsx) but none
  of the 27 cClassTrib codes it cites match any of the 5 rules published so
  far (it correlates general services taxation, not the medicine/ZFM/
  autarquia pilot rules) - so wiring it in now would only ever surface
  "candidate identified, no rule available", never a runnable evaluation.
  Documented here as a real source for a future stage, not used yet.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaxCandidateFamily:
    rule_codes: frozenset[str]
    fundamento: str
    fonte: str
    versao: str
    condicoes: str


NCM_CHAPTER_DISCOVERY: dict[str, TaxCandidateFamily] = {
    "30": TaxCandidateFamily(
        rule_codes=frozenset({"RT-IBSCBS-0004", "RT-IBSCBS-0005"}),
        fundamento=(
            "Capítulo 30 da NCM vigente (\"Produtos farmacêuticos\"), combinado com o escopo "
            "já declarado nas especificações aprovadas de RT-IBSCBS-0004 e RT-IBSCBS-0005 "
            "(medicamentos)."
        ),
        fonte="https://portalunico.siscomex.gov.br/classif (Res. Gecex nº 926/2026)",
        versao="NCM vigente em 08/09/2026",
        condicoes=(
            "Candidatura apenas pela classificação NCM do objeto pesquisado; cada regra "
            "continua exigindo seus próprios fatos (registro Anvisa, natureza jurídica do "
            "adquirente, entidade de saúde etc.) para produzir uma conclusão."
        ),
    ),
}

NBS_DISCOVERY: dict[str, TaxCandidateFamily] = {}


def discover_by_ncm(code: str) -> TaxCandidateFamily | None:
    return NCM_CHAPTER_DISCOVERY.get(code[:2])


def discover_by_nbs(code: str) -> TaxCandidateFamily | None:
    return NBS_DISCOVERY.get(code)
