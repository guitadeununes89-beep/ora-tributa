from datetime import UTC, date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from tributaria_api.infrastructure.database import identity_models as _identity_models
from tributaria_api.infrastructure.database.identity_models import OrganizationRecord, UserRecord
from tributaria_api.infrastructure.database.models import Base
from tributaria_api.infrastructure.database.taxonomy_models import (
    IbsCbsCstRecord,
    IbsCbsTaxClassificationRecord,
    TaxClassificationCatalogRecord,
    TaxClassificationCatalogVersionRecord,
)
from tributaria_api.infrastructure.database.taxonomy_repository import SqlAlchemyTaxonomyRepository

assert _identity_models


def version(identifier: str, label: str, published: date) -> TaxClassificationCatalogVersionRecord:
    now = datetime(2040, 1, 1, tzinfo=UTC)
    return TaxClassificationCatalogVersionRecord(
        id=identifier,
        catalog_id="catalog",
        organization_id="org",
        legal_source_id="source",
        version=label,
        status="PUBLISHED",
        official_title="Official fixture",
        official_url="https://example.invalid/official",
        technical_document="Fixture v1",
        publication_date=published,
        consulted_at=now,
        imported_at=now,
        artifact_file_name="fixture.xlsx",
        artifact_path="fixture.xlsx",
        artifact_media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        artifact_size=1,
        artifact_hash=identifier[-1] * 64,
        normalized_hash=identifier[-1] * 64,
        schema_signature="b" * 64,
        cst_count=1,
        cclasstrib_count=1,
        import_report={"valid": True},
        imported_by="user",
        validated_at=now,
        validated_by="user",
        submitted_at=now,
        submitted_by="user-2",
        approved_at=now,
        approved_by="user-3",
        published_at=now,
        published_by="user-4",
    )


def test_search_history_provenance_and_diff_are_snapshot_scoped() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def sqlite_functions(connection: object, _: object) -> None:
        connection.create_function("char_length", 1, len)  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    now = datetime(2040, 1, 1, tzinfo=UTC)
    with Session(engine) as session:
        session.add_all(
            [
                OrganizationRecord(
                    id="org",
                    name="Org",
                    slug="org",
                    status="ACTIVE",
                    created_at=now,
                    updated_at=now,
                ),
                UserRecord(
                    id="user",
                    email="user@example.invalid",
                    display_name="User",
                    status="ACTIVE",
                    created_at=now,
                    last_login_at=None,
                ),
                TaxClassificationCatalogRecord(
                    id="catalog",
                    organization_id="org",
                    code="IBSCBS-CCLASSTRIB",
                    name="Catalog",
                    created_at=now,
                    created_by="user",
                ),
                version("version-1", "v1", date(2039, 1, 1)),
                version("version-2", "v2", date(2040, 1, 1)),
                IbsCbsCstRecord(
                    catalog_version_id="version-1",
                    code="000",
                    description="Before",
                    indicators={"flag": 0},
                ),
                IbsCbsCstRecord(
                    catalog_version_id="version-2",
                    code="000",
                    description="After searchable",
                    indicators={"flag": 1},
                ),
                IbsCbsTaxClassificationRecord(
                    catalog_version_id="version-1",
                    code="000001",
                    cst_code="000",
                    cst_description="Before",
                    name="Before",
                    description="Before",
                    valid_from=date(2039, 1, 1),
                    valid_to=None,
                    updated_on=date(2039, 1, 1),
                    attributes={},
                ),
                IbsCbsTaxClassificationRecord(
                    catalog_version_id="version-2",
                    code="000001",
                    cst_code="000",
                    cst_description="After",
                    name="After searchable",
                    description="After",
                    valid_from=date(2040, 1, 1),
                    valid_to=None,
                    updated_on=date(2040, 1, 1),
                    attributes={},
                ),
            ]
        )
        session.commit()
        repository = SqlAlchemyTaxonomyRepository(session)

        latest = repository.list_classifications("org", "searchable")
        historical = repository.list_classifications("org", version="v1")
        result = repository.diff("org", "version-1", "version-2")

        assert [item["catalog_version"] for item in latest] == ["v2"]
        assert [item["catalog_version"] for item in historical] == ["v1"]
        assert latest[0]["source"]["artifact_hash"] == "2" * 64
        assert latest[0]["source"]["status"] == "PUBLISHED"
        assert result["cclasstrib"]["changed"][0]["code"] == "000001"
