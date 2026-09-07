from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.session import get_session
from tributaria_api.infrastructure.database.territory_repository import (
    SqlAlchemyTerritoryRepository,
)

SessionDep = Annotated[Session, Depends(get_session)]


def get_territory_repository(session: SessionDep) -> SqlAlchemyTerritoryRepository:
    return SqlAlchemyTerritoryRepository(session)


TerritoryRepositoryDep = Annotated[
    SqlAlchemyTerritoryRepository, Depends(get_territory_repository)
]
