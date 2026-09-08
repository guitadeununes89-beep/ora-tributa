from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from tax_engine.evaluation import ClassificationOutcome, EvaluationContext, FactSet

from tributaria_api.api.auth_dependencies import (
    AnalystContext,
    CorrelationId,
    IdentityRepositoryDep,
)
from tributaria_api.api.dependencies import RepositoryDep
from tributaria_api.api.product_dependencies import ProductRepositoryDep
from tributaria_api.api.taxonomy_dependencies import TaxonomyRepositoryDep
from tributaria_api.application.errors import ConflictError, GovernanceError
from tributaria_api.application.evaluations import EvaluationService
from tributaria_api.application.taxonomy import CatalogStatus
from tributaria_api.contracts.unified_classification import (
    UnifiedClassificationRequest,
    UnifiedClassificationResponse,
)

router = APIRouter(prefix="/tax/ibs-cbs", tags=["IBS/CBS unified classification"])
ENGINE_VERSION = "0.7.0-rt-ibscbs-unified"


@router.post("/classify-unified", response_model=UnifiedClassificationResponse)
def classify_unified(
    request: UnifiedClassificationRequest,
    context: AnalystContext,
    correlation_id: CorrelationId,
    repository: RepositoryDep,
    products: ProductRepositoryDep,
    taxonomy: TaxonomyRepositoryDep,
    identities: IdentityRepositoryDep,
) -> dict[str, Any]:
    catalog = taxonomy.get_version(context.organization_id, request.catalog_version_id)
    if catalog.status != CatalogStatus.PUBLISHED:
        raise ConflictError("Evaluations require a PUBLISHED catalog")

    snapshot: dict[str, Any] | None = None
    if request.product_id is not None:
        snapshot = products.current_snapshot(context.organization_id, request.product_id)
        if snapshot["status"] != "ACTIVE":
            raise ConflictError("Inactive product cannot use current classification flow")
    facts = _facts(request, snapshot)
    official_candidates: list[dict[str, Any]] = []

    def validate_candidates(outcome: ClassificationOutcome) -> None:
        if outcome.candidates:
            raise GovernanceError(
                "Unified classification rejects legacy candidates without catalog provenance"
            )
        for candidate in outcome.tax_candidates:
            if candidate.catalog_version_id != catalog.id:
                raise GovernanceError("Candidate references a different catalog snapshot")
            official_candidates.append(
                taxonomy.candidate_details(
                    context.organization_id,
                    candidate.catalog_version_id,
                    candidate.cst_code,
                    candidate.classification_code,
                )
            )

    requested_at = datetime.now(UTC)
    identities.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="tax_classification",
        entity_id=request.evaluation_id,
        action="TAX_CLASSIFICATION_REQUESTED",
        occurred_at=requested_at,
        correlation_id=correlation_id,
        metadata={
            "product_id": request.product_id,
            "catalog_version_id": catalog.id,
            "ruleset_ids": request.ruleset_ids,
        },
    )
    identities.session.commit()

    service = EvaluationService(
        repository,
        engine_version=ENGINE_VERSION,
        organization_id=context.organization_id,
        product_id=facts.product_id,
        product_version_id=facts.product_version_id,
        catalog_version_id=catalog.id,
        candidate_validator=validate_candidates,
    )
    document = service.evaluate_many(
        ruleset_ids=request.ruleset_ids,
        facts=facts,
        context=EvaluationContext(
            evaluation_id=request.evaluation_id,
            evaluated_at=request.evaluated_at,
            known_at=request.known_at,
            correlation_id=correlation_id,
        ),
        facts_document=facts.canonical_payload(),
    )
    completed_at = datetime.now(UTC)
    identities.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="tax_classification",
        entity_id=request.evaluation_id,
        action="TAX_CLASSIFICATION_COMPLETED",
        occurred_at=completed_at,
        correlation_id=correlation_id,
        metadata={
            "status": document["status"],
            "ruleset_ids": request.ruleset_ids,
            "ruleset_fingerprint": document["ruleset"]["content_hash"],
        },
    )
    identities.session.commit()
    return {
        **document,
        "product_id": facts.product_id,
        "product_version_id": facts.product_version_id,
        "catalog_version_id": catalog.id,
        "official_candidates": official_candidates,
        "evaluated_ruleset_ids": request.ruleset_ids,
    }


def _facts(request: UnifiedClassificationRequest, snapshot: dict[str, Any] | None) -> FactSet:
    if snapshot is None:
        return FactSet(
            operation_date=request.operation_date,
            ncm=request.ncm,
            product_description=request.description,
            operation_type=request.operation_type,
            origin_state=request.origin_state,
            destination_state=request.destination_state,
            taxpayer_regime=request.taxpayer_regime,
            recipient_type=request.recipient_type,
            product_attributes=request.product_attributes,
        )
    _reject_silent_override("ncm", request.ncm, snapshot["ncm"])
    _reject_silent_override("description", request.description, snapshot["description"])
    stored_attributes = {
        item["key"]: str(item["value"]["value"])
        for item in snapshot["attributes"]
        if item["value"].get("type") == "STRING"
    }
    for key, value in request.product_attributes.items():
        _reject_silent_override(key, value, stored_attributes.get(key))
        stored_attributes[key] = value
    return FactSet(
        operation_date=request.operation_date,
        product_id=request.product_id,
        product_version_id=str(snapshot["id"]),
        product_code=str(snapshot["internal_code"]),
        product_description=str(snapshot["description"]),
        ncm=snapshot["ncm"],
        operation_type=request.operation_type,
        origin_state=request.origin_state,
        destination_state=request.destination_state,
        taxpayer_regime=request.taxpayer_regime,
        recipient_type=request.recipient_type,
        product_attributes=stored_attributes,
    )


def _reject_silent_override(field: str, provided: str | None, stored: str | None) -> None:
    if provided is not None and stored is not None and provided != stored:
        raise ConflictError(f"Manual fact conflicts with stored product field: {field}")
