from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.session import get_session
from tributaria_api.infrastructure.database.tax_rule_spec_lookup import (
    SqlAlchemySpecificationReferenceLookup,
)

SessionDep = Annotated[Session, Depends(get_session)]


def get_specification_reference_lookup(
    session: SessionDep,
) -> SqlAlchemySpecificationReferenceLookup:
    return SqlAlchemySpecificationReferenceLookup(session)


SpecificationReferenceLookupDep = Annotated[
    SqlAlchemySpecificationReferenceLookup,
    Depends(get_specification_reference_lookup),
]

