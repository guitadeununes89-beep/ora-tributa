"""Batch tax classification orchestration (Etapa 23, ADR-0027).

Processes one spreadsheet row at a time by reusing, unmodified, exactly the
same building blocks the unified consultation (Etapa 21) and the catalog
discovery layer (Etapa 22) already use: `tax_engine.tax_candidate_discovery`
for discovery, `EvaluationService.evaluate_many()` for evaluation. This
module adds no new tax logic - it only wires facts from a spreadsheet row
into that existing pipeline and maps its outputs into the four batch-facing
statuses (see ADR-0027, decision 4).

A processing failure (bad NCM format, code not found, ambiguous or missing
description match, unreadable date) never raises out of `process_batch_row`
- it always returns a `BatchRowOutcome`, so one bad row can never interrupt
the rest of the batch.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from tax_engine.evaluation import EvaluationContext, FactSet
from tributaria_importers.batch_workbook import extra_attributes_from_raw

from tributaria_api.application.catalog_discovery_service import resolve_discovery
from tributaria_api.application.errors import ApplicationError, NotFoundError
from tributaria_api.application.evaluations import EvaluationService

if TYPE_CHECKING:
    from tributaria_api.infrastructure.database.batch_models import ClassificationBatchRowRecord
    from tributaria_api.infrastructure.database.nbs_repository import SqlAlchemyNbsRepository
    from tributaria_api.infrastructure.database.ncm_repository import SqlAlchemyNcmRepository
    from tributaria_api.infrastructure.database.product_repository import ProductRepository
    from tributaria_api.infrastructure.database.repositories import (
        SqlAlchemyGovernanceRepository,
    )

_ENGINE_STATUS_MAP = {
    "CONCLUSIVO": "CONCLUSIVO",
    "POSSIVEIS_ENQUADRAMENTOS": "POSSIVEIS_ENQUADRAMENTOS",
    "NECESSITA_VALIDACAO": "NECESSITA_VALIDACAO",
    "SEM_CLASSIFICACAO": "SEM_COBERTURA_NORMATIVA",
}


@dataclass(frozen=True, slots=True)
class BatchRowOutcome:
    processing_status: str
    error_message: str | None = None
    classification_status: str | None = None
    evaluation_id: str | None = None
    discovery_rule_codes: tuple[str, ...] | None = None
    observations: str | None = None


def resolve_ruleset_ids_for_rule_codes(
    repository: SqlAlchemyGovernanceRepository, rule_codes: Iterable[str]
) -> list[str]:
    """Map governed `rule_code`s to their single-rule, PUBLISHED ruleset id.

    Uses `list_rule_versions()` (already backing `GET /taxonomy/ibs-cbs/
    coverage`, Etapa 14) instead of a hardcoded rule_code->ruleset_id table -
    a rule without a queryable ruleset is fail-closed omitted, never
    invented (see ADR-0027, decision 3).
    """
    by_code: dict[str, list[dict[str, Any]]] = {}
    for version in repository.list_rule_versions():
        by_code.setdefault(version["identity_code"], []).append(version)
    ruleset_ids: list[str] = []
    for code in sorted(rule_codes):
        published = [v for v in by_code.get(code, ()) if v["lifecycle_status"] == "PUBLISHED"]
        queryable = sorted({rid for v in published for rid in v["queryable_rulesets"]})
        if queryable:
            ruleset_ids.append(queryable[0])
    return ruleset_ids


def process_batch_row(
    row: ClassificationBatchRowRecord,
    *,
    organization_id: str,
    correlation_id: str,
    engine_version: str,
    taxonomy_catalog_version_id: str,
    ncm_repository: SqlAlchemyNcmRepository,
    nbs_repository: SqlAlchemyNbsRepository,
    products: ProductRepository,
    governance_repository: SqlAlchemyGovernanceRepository,
) -> BatchRowOutcome:
    try:
        ncm, nbs, error = _identify_object(
            ncm=row.ncm,
            nbs=row.nbs,
            description=row.description,
            object_kind=row.object_kind,
            internal_code=row.internal_code,
            organization_id=organization_id,
            ncm_repository=ncm_repository,
            nbs_repository=nbs_repository,
            products=products,
        )
        if error is not None:
            return BatchRowOutcome(processing_status="ERROR", error_message=error)
        if row.operation_date is None:
            return BatchRowOutcome(
                processing_status="ERROR",
                error_message="Data da operação ausente ou em formato inválido",
            )

        family = resolve_discovery(ncm=ncm, nbs=nbs)
        if family is None:
            target = f"NCM {ncm}" if ncm else f"NBS {nbs}"
            return BatchRowOutcome(
                processing_status="PROCESSED",
                classification_status="SEM_COBERTURA_NORMATIVA",
                observations=(
                    f"Descoberta não encontrou nenhuma família de regra candidata governada "
                    f"para {target} - sem cobertura normativa."
                ),
            )

        rule_codes = sorted(family.rule_codes)
        ruleset_ids = resolve_ruleset_ids_for_rule_codes(governance_repository, rule_codes)
        if not ruleset_ids:
            return BatchRowOutcome(
                processing_status="PROCESSED",
                classification_status="NECESSITA_VALIDACAO",
                discovery_rule_codes=tuple(rule_codes),
                observations=(
                    f"Família candidata encontrada (regras {', '.join(rule_codes)}) mas "
                    "nenhum ruleset publicado e consultável foi localizado - pendência de "
                    "publicação, não uma conclusão fiscal."
                ),
            )

        facts = FactSet(
            operation_date=row.operation_date,
            product_code=row.internal_code,
            product_description=row.description,
            ncm=ncm,
            nbs=nbs,
            product_attributes=extra_attributes_from_raw(row.raw_values),
        )
        now = datetime.now(UTC)
        evaluation_id = str(uuid4())
        service = EvaluationService(
            governance_repository,
            engine_version=engine_version,
            organization_id=organization_id,
            catalog_version_id=taxonomy_catalog_version_id,
        )
        document = service.evaluate_many(
            ruleset_ids=ruleset_ids,
            facts=facts,
            context=EvaluationContext(
                evaluation_id=evaluation_id,
                evaluated_at=now,
                known_at=now,
                correlation_id=correlation_id,
            ),
            facts_document=facts.canonical_payload(),
        )
    except ApplicationError as exc:
        return BatchRowOutcome(processing_status="ERROR", error_message=str(exc))

    engine_status = str(document["status"])
    return BatchRowOutcome(
        processing_status="PROCESSED",
        classification_status=_ENGINE_STATUS_MAP[engine_status],
        evaluation_id=evaluation_id,
        discovery_rule_codes=tuple(rule_codes),
        observations=_observations_for(engine_status, rule_codes, document),
    )


def expand_row_result(
    row: ClassificationBatchRowRecord, *, governance_repository: SqlAlchemyGovernanceRepository
) -> dict[str, Any]:
    """Render a row's stored result by reading its own persisted evaluation.

    Nothing here is recomputed or duplicated: CST/cClassTrib/legal
    references/rule identity all come straight from the real
    `EvaluationRecord` the row's `evaluation_id` points to, exactly as it
    was written by `process_batch_row` - so the report can never drift from
    what is actually stored.
    """
    result: dict[str, Any] = {
        "cst": None,
        "cclasstrib": None,
        "tratamento": None,
        "fundamento_legal": [],
        "regra": None,
        "fatos_faltantes": [],
        "decision_trace": [],
    }
    if row.evaluation_id is None:
        return result
    evaluation = governance_repository.get_evaluation(row.evaluation_id)
    outcome = evaluation["outcome"]
    result["fatos_faltantes"] = list(outcome.get("missing_facts", []))
    result["decision_trace"] = list(outcome.get("decision_trace", []))
    tax_candidates = outcome.get("tax_candidates", [])
    if tax_candidates:
        candidate = tax_candidates[0]
        cst = candidate["cst"]
        cclasstrib = candidate["cclasstrib"]
        result["cst"] = cst
        result["cclasstrib"] = cclasstrib
        result["tratamento"] = f"CST {cst}" + (f" / cClassTrib {cclasstrib}" if cclasstrib else "")
        result["regra"] = {
            "rule_code": candidate["rule"]["rule_code"],
            "version": str(candidate["rule"]["version"]),
        }
        result["fundamento_legal"] = candidate.get("legal_references", [])
    return result


def _valid_ncm_format(code: str) -> bool:
    return code.isdigit() and len(code) == 8


def _valid_nbs_format(code: str) -> bool:
    return bool(code) and all(character.isdigit() or character == "." for character in code)


def _identify_object(
    *,
    ncm: str | None,
    nbs: str | None,
    description: str | None,
    object_kind: str | None,
    internal_code: str | None,
    organization_id: str,
    ncm_repository: SqlAlchemyNcmRepository,
    nbs_repository: SqlAlchemyNbsRepository,
    products: ProductRepository,
) -> tuple[str | None, str | None, str | None]:
    """Resolve the row to a single governed NCM or NBS code, or an error.

    Never guesses: an ambiguous description match (more than one catalog
    hit) is an error asking the analyst for a direct NCM/NBS, never a
    silently-picked first result.
    """
    if ncm:
        if not _valid_ncm_format(ncm):
            return None, None, f"NCM em formato inválido: '{ncm}' (esperado 8 dígitos)"
        try:
            ncm_repository.get_code(organization_id, ncm)
        except NotFoundError:
            return None, None, f"NCM '{ncm}' não encontrado no catálogo NCM publicado"
        return ncm, None, None
    if nbs:
        if not _valid_nbs_format(nbs):
            return None, None, f"NBS em formato inválido: '{nbs}'"
        try:
            nbs_repository.get_code(organization_id, nbs)
        except NotFoundError:
            return None, None, f"NBS '{nbs}' não encontrado no catálogo NBS publicado"
        return None, nbs, None
    if internal_code:
        matches = [
            product
            for product in products.list_products(organization_id, internal_code)
            if product.internal_code == internal_code
        ]
        if not matches:
            return (
                None,
                None,
                f"Código interno '{internal_code}' não encontrado no cadastro de produtos",
            )
        if not matches[0].ncm:
            return None, None, f"Produto '{internal_code}' não possui NCM cadastrado"
        return matches[0].ncm, None, None
    if description:
        return _identify_by_description(
            description,
            object_kind=object_kind,
            organization_id=organization_id,
            ncm_repository=ncm_repository,
            nbs_repository=nbs_repository,
        )
    return None, None, "Linha sem NCM, NBS, código interno ou descrição para identificar o objeto"


def _identify_by_description(
    description: str,
    *,
    object_kind: str | None,
    organization_id: str,
    ncm_repository: SqlAlchemyNcmRepository,
    nbs_repository: SqlAlchemyNbsRepository,
) -> tuple[str | None, str | None, str | None]:
    try_ncm = object_kind != "SERVICE"
    try_nbs = object_kind != "GOOD"
    hits: list[tuple[str, str]] = []
    if try_ncm:
        try:
            hits.extend(("NCM", item["code"]) for item in ncm_repository.search(
                organization_id, description
            ))
        except NotFoundError:
            pass
    if try_nbs:
        try:
            hits.extend(("NBS", item["code"]) for item in nbs_repository.search(
                organization_id, description
            ))
        except NotFoundError:
            pass
    if not hits:
        return (
            None,
            None,
            f"Descrição '{description}' sem correspondência no(s) catálogo(s) consultado(s)",
        )
    if len(hits) > 1:
        return (
            None,
            None,
            f"Descrição '{description}' é ambígua ({len(hits)} correspondências) - informe "
            "o NCM/NBS diretamente",
        )
    origin, code = hits[0]
    return (code, None, None) if origin == "NCM" else (None, code, None)


def _observations_for(
    engine_status: str, rule_codes: list[str], document: dict[str, Any]
) -> str:
    if engine_status == "CONCLUSIVO":
        tax_candidates = document.get("tax_candidates", [])
        if tax_candidates:
            candidate = tax_candidates[0]
            return (
                f"Conclusivo via {candidate['rule']['rule_code']} "
                f"(CST {candidate['cst']} / cClassTrib {candidate['cclasstrib']})."
            )
        return f"Conclusivo (regras candidatas: {', '.join(rule_codes)})."
    if engine_status == "POSSIVEIS_ENQUADRAMENTOS":
        return (
            f"Mais de um enquadramento possível entre as regras candidatas "
            f"({', '.join(rule_codes)}); revisão manual necessária."
        )
    if engine_status == "NECESSITA_VALIDACAO":
        missing = ", ".join(document.get("missing_facts", []))
        return f"Fatos faltantes para concluir: {missing}."
    return (
        f"Candidato de descoberta encontrado (regras {', '.join(rule_codes)}), mas nenhuma "
        "delas se confirma para os fatos informados - candidato descartado pelos próprios "
        "fatos, não ausência de descoberta."
    )
