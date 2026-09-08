from datetime import UTC, date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from tributaria_api.application.errors import NotFoundError
from tributaria_api.infrastructure.database import identity_models as _identity_models
from tributaria_api.infrastructure.database.identity_models import OrganizationRecord, UserRecord
from tributaria_api.infrastructure.database.models import Base, LegalSourceRecord
from tributaria_api.infrastructure.database.ncm_models import (
    NcmCatalogRecord,
    NcmCatalogVersionRecord,
    NcmCodeRecord,
)
from tributaria_api.infrastructure.database.ncm_repository import SqlAlchemyNcmRepository

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
                year=2026,
                issuing_authority="RFB",
                title="NCM",
                official_url="https://example.invalid/ncm",
                publication_date=date(2026, 1, 1),
                jurisdiction="BR",
                notes=None,
                content_hash="a" * 64,
                is_synthetic=True,
                created_at=now,
                organization_id=organization_id,
            ),
            NcmCatalogRecord(
                id=catalog_id,
                organization_id=organization_id,
                code="NCM",
                name="NCM",
                created_at=now,
                created_by=user_id,
            ),
            NcmCatalogVersionRecord(
                id=version_id,
                catalog_id=catalog_id,
                organization_id=organization_id,
                legal_source_id=f"source-{organization_id}",
                version="2026-09-08",
                status="PUBLISHED",
                official_title="NCM",
                official_url="https://example.invalid/ncm",
                technical_document="Fixture",
                publication_date=date(2026, 9, 8),
                consulted_at=now,
                imported_at=now,
                artifact_file_name="ncm.json",
                artifact_path="ncm.json",
                artifact_media_type="application/json",
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
            NcmCodeRecord(
                catalog_version_id=version_id,
                code="30",
                level=2,
                is_final=False,
                description="Produtos farmacêuticos.",
                valid_from=date(2022, 1, 1),
                valid_to=None,
                legal_act="Res Gecex 1/2022",
            ),
            NcmCodeRecord(
                catalog_version_id=version_id,
                code="30019010",
                level=8,
                is_final=True,
                description="Heparina e seus sais",
                valid_from=date(2022, 1, 1),
                valid_to=None,
                legal_act="Res Gecex 1/2022",
            ),
        ]
    )
    session.commit()


def test_search_by_code_and_description_is_literal_and_scoped_to_published_version() -> None:
    engine = _engine()
    with Session(engine) as session:
        _seed(session, "org", "catalog", "version-1")
        repository = SqlAlchemyNcmRepository(session)

        by_description = repository.search("org", "heparina")
        by_prefix = repository.search("org", "3001")

        assert [item["code"] for item in by_description] == ["30019010"]
        assert [item["code"] for item in by_prefix] == ["30019010"]
        assert repository.get_code("org", "30019010")["is_final"] is True
        assert repository.get_code("org", "30")["is_final"] is False


def test_organizations_cannot_see_each_others_ncm_catalog() -> None:
    engine = _engine()
    with Session(engine) as session:
        _seed(session, "org-a", "catalog-a", "version-a")
        _seed(session, "org-b", "catalog-b", "version-b")
        repository = SqlAlchemyNcmRepository(session)

        assert len(repository.search("org-a", "heparina")) == 1
        assert len(repository.search("org-b", "heparina")) == 1
        try:
            repository.get_version("org-a", "version-b")
        except NotFoundError:
            pass
        else:
            raise AssertionError("org-a must not resolve org-b's catalog version")
