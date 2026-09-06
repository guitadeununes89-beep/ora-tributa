from fastapi import APIRouter
from tax_engine.evaluation import EvaluationContext

from tributaria_api.api.auth_dependencies import (
    AnalystContext,
    IdentityRepositoryDep,
    ReadContext,
)
from tributaria_api.api.dependencies import RepositoryDep
from tributaria_api.application.errors import NotFoundError
from tributaria_api.application.evaluations import EvaluationService
from tributaria_api.contracts.admin import ReproduceEvaluationRequest
from tributaria_api.contracts.classification import ClassificationEvaluationResponse
from tributaria_api.contracts.persistent_classification import (
    EvaluationArchiveResponse,
    PersistedClassificationEvaluationRequest,
)

router = APIRouter(prefix="/classifications", tags=["classifications"])
ENGINE_VERSION = "0.4.0-experimental-persisted"


@router.post("/evaluate", response_model=ClassificationEvaluationResponse)
def evaluate_classification(
    request: PersistedClassificationEvaluationRequest,
    repository: RepositoryDep,
    identities: IdentityRepositoryDep,
    context: AnalystContext,
) -> ClassificationEvaluationResponse:
    if request.company_id:
        identities.get_company(context.organization_id, request.company_id)
    if request.establishment_id:
        if not request.company_id:
            raise NotFoundError("Establishment requires a company context")
        establishments = identities.list_establishments(context.organization_id, request.company_id)
        if request.establishment_id not in {item.id for item in establishments}:
            raise NotFoundError("Establishment not found")
    service = EvaluationService(
        repository,
        engine_version=ENGINE_VERSION,
        organization_id=context.organization_id,
        company_id=request.company_id,
        establishment_id=request.establishment_id,
    )
    document = service.evaluate(
        ruleset_id=request.ruleset_id,
        facts=request.facts.to_domain(),
        context=EvaluationContext(
            evaluation_id=request.evaluation_id,
            evaluated_at=request.evaluated_at,
            known_at=request.known_at,
            correlation_id=request.correlation_id,
        ),
        facts_document=request.facts.model_dump(mode="json"),
    )
    return ClassificationEvaluationResponse.model_validate(document)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationArchiveResponse)
def get_evaluation(
    evaluation_id: str, repository: RepositoryDep, context: ReadContext
) -> dict[str, object]:
    value = repository.get_evaluation(evaluation_id)
    if value.get("organization_id") != context.organization_id:
        raise NotFoundError("Evaluation not found")
    return value


@router.post(
    "/evaluations/{evaluation_id}/reproduce",
    response_model=ClassificationEvaluationResponse,
)
def reproduce_evaluation(
    evaluation_id: str,
    request: ReproduceEvaluationRequest,
    repository: RepositoryDep,
    context: AnalystContext,
) -> ClassificationEvaluationResponse:
    original = repository.get_evaluation(evaluation_id)
    if original.get("organization_id") != context.organization_id:
        raise NotFoundError("Evaluation not found")
    service = EvaluationService(
        repository,
        engine_version=str(original["engine_version"]),
        organization_id=context.organization_id,
        company_id=original.get("company_id"),
        establishment_id=original.get("establishment_id"),
    )
    document = service.reproduce(
        evaluation_id,
        new_evaluation_id=request.evaluation_id,
        evaluated_at=request.evaluated_at,
        correlation_id=request.correlation_id,
    )
    return ClassificationEvaluationResponse.model_validate(document)

