from datetime import UTC, datetime

from fastapi import APIRouter

from tributaria_api.api.auth_dependencies import (
    CompanyManagerContext,
    CorrelationId,
    IdentityRepositoryDep,
    ReadContext,
)
from tributaria_api.contracts.identity import (
    CompanyInput,
    CompanyStatusInput,
    CompanyView,
    EstablishmentInput,
    EstablishmentView,
)
from tributaria_api.infrastructure.database.identity_models import (
    CompanyRecord,
    EstablishmentRecord,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyView])
def list_companies(context: ReadContext, repository: IdentityRepositoryDep) -> list[CompanyRecord]:
    return repository.list_companies(context.organization_id)


@router.post("", response_model=CompanyView, status_code=201)
def create_company(
    request: CompanyInput,
    context: CompanyManagerContext,
    repository: IdentityRepositoryDep,
    correlation_id: CorrelationId,
) -> object:
    now = datetime.now(UTC)
    record = repository.create_company(
        context.organization_id, now, **request.model_dump(mode="python")
    )
    repository.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="company",
        entity_id=record.id,
        action="COMPANY_CREATED",
        occurred_at=now,
        correlation_id=correlation_id,
    )
    repository.session.commit()
    return record


@router.patch("/{company_id}/status", response_model=CompanyView)
def change_company_status(
    company_id: str,
    request: CompanyStatusInput,
    context: CompanyManagerContext,
    repository: IdentityRepositoryDep,
    correlation_id: CorrelationId,
) -> object:
    now = datetime.now(UTC)
    record = repository.set_company_status(context.organization_id, company_id, request.status, now)
    repository.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="company",
        entity_id=record.id,
        action="COMPANY_STATUS_CHANGED",
        occurred_at=now,
        correlation_id=correlation_id,
        metadata={"status": request.status},
    )
    repository.session.commit()
    return record


@router.get("/{company_id}/establishments", response_model=list[EstablishmentView])
def list_establishments(
    company_id: str, context: ReadContext, repository: IdentityRepositoryDep
) -> list[EstablishmentRecord]:
    return repository.list_establishments(context.organization_id, company_id)


@router.post("/{company_id}/establishments", response_model=EstablishmentView, status_code=201)
def create_establishment(
    company_id: str,
    request: EstablishmentInput,
    context: CompanyManagerContext,
    repository: IdentityRepositoryDep,
    correlation_id: CorrelationId,
) -> object:
    now = datetime.now(UTC)
    record = repository.create_establishment(
        context.organization_id, company_id, now, **request.model_dump(mode="python")
    )
    repository.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="establishment",
        entity_id=record.id,
        action="ESTABLISHMENT_CREATED",
        occurred_at=now,
        correlation_id=correlation_id,
    )
    repository.session.commit()
    return record
