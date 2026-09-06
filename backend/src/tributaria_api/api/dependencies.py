from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from tributaria_api.api.auth_dependencies import CurrentAuthContext
from tributaria_api.application.governance import (
    GovernanceService,
    SegregationOfDutiesPolicy,
)
from tributaria_api.config import get_settings
from tributaria_api.infrastructure.database.repositories import (
    SqlAlchemyGovernanceRepository,
)
from tributaria_api.infrastructure.database.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def get_repository(session: SessionDep) -> SqlAlchemyGovernanceRepository:
    return SqlAlchemyGovernanceRepository(session)


RepositoryDep = Annotated[SqlAlchemyGovernanceRepository, Depends(get_repository)]


def get_governance_service(
    repository: RepositoryDep, context: CurrentAuthContext
) -> GovernanceService:
    settings = get_settings()
    if not settings.admin_api_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return GovernanceService(
        repository,
        SegregationOfDutiesPolicy(enabled=settings.segregation_of_duties_enabled),
        organization_id=context.organization_id,
        authenticated_user_id=context.user_id,
    )


GovernanceServiceDep = Annotated[GovernanceService, Depends(get_governance_service)]
