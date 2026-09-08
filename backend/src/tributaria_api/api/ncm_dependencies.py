from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.ncm_repository import SqlAlchemyNcmRepository
from tributaria_api.infrastructure.database.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def get_ncm_repository(session: SessionDep) -> SqlAlchemyNcmRepository:
    return SqlAlchemyNcmRepository(session)


NcmRepositoryDep = Annotated[SqlAlchemyNcmRepository, Depends(get_ncm_repository)]
