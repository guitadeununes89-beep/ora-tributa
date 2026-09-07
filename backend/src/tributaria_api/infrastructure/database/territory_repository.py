"""Read-only access to governed territorial data (ADR-0021, ADR-0024).

Deliberately thin: this repository only reads already-approved, already-
published TaxJurisdictionAreaVersion rows. It has no write path - loading
real territorial data remains the exclusive job of
territory_governed_load_cli.py, gated on a human-approved specification.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.territory_models import (
    TaxJurisdictionAreaRecord,
    TaxJurisdictionAreaVersionRecord,
)


class SqlAlchemyTerritoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_published_areas(self, organization_id: str) -> list[dict[str, Any]]:
        statement = (
            select(TaxJurisdictionAreaRecord, TaxJurisdictionAreaVersionRecord)
            .join(
                TaxJurisdictionAreaVersionRecord,
                TaxJurisdictionAreaVersionRecord.area_id == TaxJurisdictionAreaRecord.id,
            )
            .where(
                TaxJurisdictionAreaRecord.organization_id == organization_id,
                TaxJurisdictionAreaVersionRecord.organization_id == organization_id,
                TaxJurisdictionAreaVersionRecord.lifecycle_status == "PUBLISHED",
            )
            .order_by(TaxJurisdictionAreaRecord.id, TaxJurisdictionAreaVersionRecord.version)
        )
        rows = self._session.execute(statement).all()
        return [
            {
                "area_id": area.id,
                "area_type": area.area_type,
                "official_name": area.official_name,
                "version": version.version,
                "version_id": version.id,
                "legal_device": version.legal_device,
                "criteria": version.criteria,
                "valid_from": version.valid_from,
                "valid_to": version.valid_to,
            }
            for area, version in rows
        ]
