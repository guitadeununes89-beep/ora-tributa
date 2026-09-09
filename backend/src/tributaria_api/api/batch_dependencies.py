from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.batch_repository import SqlAlchemyBatchRepository
from tributaria_api.infrastructure.database.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def get_batch_repository(session: SessionDep) -> SqlAlchemyBatchRepository:
    return SqlAlchemyBatchRepository(session)


BatchRepositoryDep = Annotated[SqlAlchemyBatchRepository, Depends(get_batch_repository)]
