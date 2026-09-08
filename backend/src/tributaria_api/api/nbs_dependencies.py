from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.nbs_repository import SqlAlchemyNbsRepository
from tributaria_api.infrastructure.database.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def get_nbs_repository(session: SessionDep) -> SqlAlchemyNbsRepository:
    return SqlAlchemyNbsRepository(session)


NbsRepositoryDep = Annotated[SqlAlchemyNbsRepository, Depends(get_nbs_repository)]
