from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from tributaria_api.api.auth_dependencies import CurrentAuthContext
from tributaria_api.application.taxonomy import CatalogLifecyclePolicy, TaxonomyService
from tributaria_api.config import get_settings
from tributaria_api.infrastructure.database.session import get_session
from tributaria_api.infrastructure.database.taxonomy_repository import SqlAlchemyTaxonomyRepository

SessionDep = Annotated[Session, Depends(get_session)]


def get_taxonomy_repository(session: SessionDep) -> SqlAlchemyTaxonomyRepository:
    return SqlAlchemyTaxonomyRepository(session)


TaxonomyRepositoryDep = Annotated[SqlAlchemyTaxonomyRepository, Depends(get_taxonomy_repository)]


def get_taxonomy_service(
    repository: TaxonomyRepositoryDep, context: CurrentAuthContext
) -> TaxonomyService:
    settings = get_settings()
    if not settings.admin_api_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return TaxonomyService(
        repository,
        context.organization_id,
        CatalogLifecyclePolicy(settings.segregation_of_duties_enabled),
    )


TaxonomyServiceDep = Annotated[TaxonomyService, Depends(get_taxonomy_service)]
