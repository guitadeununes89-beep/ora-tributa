from datetime import UTC, date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from tributaria_api.application.errors import NotFoundError
from tributaria_api.infrastructure.database import identity_models as _identity_models
from tributaria_api.infrastructure.database.identity_models import OrganizationRecord, UserRecord
from tributaria_api.infrastructure.database.models import Base, LegalSourceRecord
from tributaria_api.infrastructure.database.nbs_models import (
    NbsCatalogRecord,
    NbsCatalogVersionRecord,
    NbsCodeRecord,
)
from tributaria_api.infrastructure.database.nbs_repository import SqlAlchemyNbsRepository

assert _identity_models


def _engine() -> object:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def sqlite_functions(connection: object, _: object) -> None:
        connection.create_function("char_length", 1, len)  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    return engine


def _seed(session: Session, organization_id: str, catalog_id: str, version_id: str) -> None:
    now = datetime(2040, 1, 1, tzinfo=UTC)
    user_id = f"user-{organization_id}"
    session.add_all(
        [
            OrganizationRecord(
                id=organization_id,
                name=organization_id,
                slug=organization_id,
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            ),
            UserRecord(
                id=user_id,
                email=f"{user_id}@example.invalid",
                display_name="User",
                status="ACTIVE",
                created_at=now,
                last_login_at=None,
            ),
            LegalSourceRecord(
                id=f"source-{organization_id}",
                source_type="OFFICIAL_TECHNICAL_CATALOG",
                number="1",
                year=2019,
                issuing_authority="MDIC/RFB",
                title="NBS",
                official_url="https://example.invalid/nbs",
                publication_date=date(2019, 1, 1),
                jurisdiction="BR",
                notes=None,
                content_hash="a" * 64,
                is_synthetic=True,
                created_at=now,
                organization_id=organization_id,
            ),
            NbsCatalogRecord(
                id=catalog_id,
                organization_id=organization_id,
                code="NBS",
                name="NBS",
                created_at=now,
                created_by=user_id,
            ),
            NbsCatalogVersionRecord(
                id=version_id,
                catalog_id=catalog_id,
                organization_id=organization_id,
                legal_source_id=f"source-{organization_id}",
                version="2.0",
                status="PUBLISHED",
                official_title="NBS",
                official_url="https://example.invalid/nbs",
                technical_document="Fixture",
                publication_date=date(2019, 1, 1),
                consulted_at=now,
                imported_at=now,
                artifact_file_name="nbs.csv",
                artifact_path="nbs.csv",
                artifact_media_type="text/csv",
                artifact_size=1,
                artifact_hash=version_id[-1] * 64,
                normalized_hash=version_id[-1] * 64,
                code_count=2,
                import_report={"valid": True},
                imported_by=user_id,
                validated_at=now,
                validated_by=user_id,
                submitted_at=now,
                submitted_by=user_id,
                approved_at=now,
                approved_by=user_id,
                published_at=now,
                published_by=user_id,
            ),
            NbsCodeRecord(
                catalog_version_id=version_id,
                code="1.01",
                level=2,
                description="Serviços de construção",
            ),
            NbsCodeRecord(
                catalog_version_id=version_id,
                code="1.0101.11.00",
                level=4,
                description="Serviços de construção de edificações residenciais",
            ),
        ]
    )
    session.commit()


def test_search_by_code_and_description_is_literal_and_scoped_to_published_version() -> None:
    engine = _engine()
    with Session(engine) as session:
        _seed(session, "org", "catalog", "version-1")
        repository = SqlAlchemyNbsRepository(session)

        by_description = repository.search("org", "residenciais")
        by_prefix = repository.search("org", "1.0101")

        assert [item["code"] for item in by_description] == ["1.0101.11.00"]
        assert [item["code"] for item in by_prefix] == ["1.0101.11.00"]
        assert repository.get_code("org", "1.01")["level"] == 2


def test_organizations_cannot_see_each_others_nbs_catalog() -> None:
    engine = _engine()
    with Session(engine) as session:
        _seed(session, "org-a", "catalog-a", "version-a")
        _seed(session, "org-b", "catalog-b", "version-b")
        repository = SqlAlchemyNbsRepository(session)

        assert len(repository.search("org-a", "residenciais")) == 1
        assert len(repository.search("org-b", "residenciais")) == 1
        try:
            repository.get_version("org-a", "version-b")
        except NotFoundError:
            pass
        else:
            raise AssertionError("org-a must not resolve org-b's catalog version")
