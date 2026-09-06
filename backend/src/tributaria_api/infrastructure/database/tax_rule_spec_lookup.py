from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.models import LegalSourceRecord
from tributaria_api.infrastructure.database.taxonomy_models import (
    IbsCbsCstRecord,
    IbsCbsTaxClassificationRecord,
    TaxClassificationCatalogVersionRecord,
)


class SqlAlchemySpecificationReferenceLookup:
    def __init__(self, session: Session) -> None:
        self.session = session

    def legal_source_exists(self, organization_id: str, source_id: str) -> bool:
        return (
            self.session.scalar(
                select(LegalSourceRecord.id).where(
                    LegalSourceRecord.id == source_id,
                    LegalSourceRecord.organization_id == organization_id,
                )
            )
            is not None
        )

    def catalog_version_status(
        self, organization_id: str, catalog_version_id: str
    ) -> str | None:
        return self.session.scalar(
            select(TaxClassificationCatalogVersionRecord.status).where(
                TaxClassificationCatalogVersionRecord.id == catalog_version_id,
                TaxClassificationCatalogVersionRecord.organization_id == organization_id,
            )
        )

    def cst_exists(self, catalog_version_id: str, cst: str) -> bool:
        return (
            self.session.scalar(
                select(IbsCbsCstRecord.code).where(
                    IbsCbsCstRecord.catalog_version_id == catalog_version_id,
                    IbsCbsCstRecord.code == cst,
                )
            )
            is not None
        )

    def classification_cst(
        self, catalog_version_id: str, cclasstrib: str
    ) -> tuple[bool, str | None]:
        value = self.session.scalar(
            select(IbsCbsTaxClassificationRecord.cst_code).where(
                IbsCbsTaxClassificationRecord.catalog_version_id == catalog_version_id,
                IbsCbsTaxClassificationRecord.code == cclasstrib,
            )
        )
        return value is not None, value

