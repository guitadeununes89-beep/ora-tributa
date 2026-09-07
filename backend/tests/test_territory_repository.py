from __future__ import annotations

import os
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tributaria_api.infrastructure.database.identity_models import OrganizationRecord, UserRecord
from tributaria_api.infrastructure.database.models import LegalSourceRecord
from tributaria_api.infrastructure.database.territory_models import (
    TaxJurisdictionAreaRecord,
    TaxJurisdictionAreaVersionRecord,
)
from tributaria_api.infrastructure.database.territory_repository import (
    SqlAlchemyTerritoryRepository,
)

ORG_ID = "PG-TEST-TERRITORY-ORG"


@pytest.mark.skipif(os.getenv("POSTGRES_TESTS") != "1", reason="requires migrated PostgreSQL")
def test_list_published_areas_returns_only_this_organizations_published_versions() -> None:
    engine = create_engine(os.environ["DATABASE_URL"])
    now = datetime.now(UTC)
    with Session(engine) as session:
        session.add(
            OrganizationRecord(
                id=ORG_ID,
                name="Synthetic territory org",
                slug="pg-test-territory-org",
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            UserRecord(
                id="PG-TEST-TERRITORY-USER",
                email="pg-test-territory@example.invalid",
                display_name="Synthetic user",
                status="ACTIVE",
                created_at=now,
                last_login_at=None,
            )
        )
        session.add(
            LegalSourceRecord(
                id="PG-TEST-TERRITORY-SOURCE",
                source_type="SYNTHETIC",
                number="TEST",
                year=2099,
                issuing_authority="SYNTHETIC AUTHORITY",
                title="Synthetic source",
                official_url="https://example.invalid/pg-territory-source",
                publication_date=date(2099, 1, 1),
                jurisdiction="SYNTHETIC",
                notes="Fictitious",
                content_hash="f" * 64,
                is_synthetic=True,
                created_at=now,
            )
        )
        session.add(
            TaxJurisdictionAreaRecord(
                id="PG-TEST-TERRITORY-AREA",
                organization_id=ORG_ID,
                area_type="ZFM",
                code="PG-TEST-TERRITORY-AREA",
                official_name="Synthetic area",
                created_at=now,
                created_by="PG-TEST-TERRITORY-USER",
            )
        )
        session.flush()
        session.add(
            TaxJurisdictionAreaVersionRecord(
                id="PG-TEST-TERRITORY-AREA-V1-DRAFT",
                area_id="PG-TEST-TERRITORY-AREA",
                organization_id=ORG_ID,
                version=1,
                lifecycle_status="DRAFT",
                legal_source_id="PG-TEST-TERRITORY-SOURCE",
                legal_device="Synthetic device",
                criteria={"synthetic": "true"},
                content_hash="a" * 64,
                valid_from=date(2026, 1, 1),
                valid_to=None,
                recorded_at=now,
                created_by="PG-TEST-TERRITORY-USER",
            )
        )
        session.add(
            TaxJurisdictionAreaVersionRecord(
                id="PG-TEST-TERRITORY-AREA-V2-PUBLISHED",
                area_id="PG-TEST-TERRITORY-AREA",
                organization_id=ORG_ID,
                version=2,
                lifecycle_status="PUBLISHED",
                legal_source_id="PG-TEST-TERRITORY-SOURCE",
                legal_device="Synthetic device",
                criteria={"municipios_parcialmente_abrangidos": ["Synthetic City"]},
                content_hash="b" * 64,
                valid_from=date(2026, 1, 1),
                valid_to=None,
                recorded_at=now,
                created_by="PG-TEST-TERRITORY-USER",
                approved_at=now,
                approved_by="PG-TEST-TERRITORY-USER",
                published_at=now,
                published_by="PG-TEST-TERRITORY-USER",
            )
        )
        session.commit()

        repository = SqlAlchemyTerritoryRepository(session)
        areas = repository.list_published_areas(ORG_ID)

        assert len(areas) == 1
        assert areas[0]["area_id"] == "PG-TEST-TERRITORY-AREA"
        assert areas[0]["version"] == 2
        assert areas[0]["criteria"] == {"municipios_parcialmente_abrangidos": ["Synthetic City"]}

        assert repository.list_published_areas("some-other-org") == []
