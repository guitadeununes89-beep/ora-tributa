from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.product_repository import ProductRepository
from tributaria_api.infrastructure.database.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def get_product_repository(session: SessionDep) -> ProductRepository:
    return ProductRepository(session)


ProductRepositoryDep = Annotated[ProductRepository, Depends(get_product_repository)]
