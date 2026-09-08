from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from tributaria_api.application.errors import ConflictError, NotFoundError
from tributaria_api.application.taxonomy import CatalogStatus
from tributaria_api.infrastructure.database.models import LegalSourceRecord
from tributaria_api.infrastructure.database.ncm_models import (
    NcmCatalogLifecycleEventRecord,
    NcmCatalogRecord,
    NcmCatalogVersionRecord,
    NcmCodeRecord,
    NcmStagingRowRecord,
)

CATALOG_CODE = "NCM"


class SqlAlchemyNcmRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_version(self, organization_id: str, version_id: str) -> NcmCatalogVersionRecord:
        record = self.session.scalar(
            select(NcmCatalogVersionRecord).where(
                NcmCatalogVersionRecord.id == version_id,
                NcmCatalogVersionRecord.organization_id == organization_id,
            )
        )
        if record is None:
            raise NotFoundError("NCM catalog version not found")
        return record

    def ingest(
        self,
        *,
        organization_id: str,
        actor_id: str,
        artifact_path: str,
        artifact_file_name: str,
        artifact_media_type: str,
        artifact_size: int,
        parsed: Any,
        metadata: dict[str, Any],
        occurred_at: datetime,
        correlation_id: str,
    ) -> NcmCatalogVersionRecord:
        catalog = self.session.scalar(
            select(NcmCatalogRecord).where(
                NcmCatalogRecord.organization_id == organization_id,
                NcmCatalogRecord.code == CATALOG_CODE,
            )
        )
        if catalog is None:
            catalog = NcmCatalogRecord(
                id=str(uuid4()),
                organization_id=organization_id,
                code=CATALOG_CODE,
                name="Nomenclatura Comum do Mercosul (NCM)",
                created_at=occurred_at,
                created_by=actor_id,
            )
            self.session.add(catalog)
            self.session.flush()
        existing_artifact = self.session.scalar(
            select(NcmCatalogVersionRecord).where(
                NcmCatalogVersionRecord.catalog_id == catalog.id,
                NcmCatalogVersionRecord.artifact_hash == parsed.artifact_hash,
            )
        )
        if existing_artifact is not None:
            return existing_artifact
        existing_version = self.session.scalar(
            select(NcmCatalogVersionRecord).where(
                NcmCatalogVersionRecord.catalog_id == catalog.id,
                NcmCatalogVersionRecord.version == metadata["version"],
            )
        )
        if existing_version is not None:
            raise ConflictError("NCM catalog version already exists with a different artifact")
        source = LegalSourceRecord(
            id=str(uuid4()),
            source_type="OFFICIAL_TECHNICAL_CATALOG",
            number=metadata["technical_document"],
            year=metadata["publication_date"].year,
            issuing_authority=metadata["issuing_authority"],
            title=metadata["official_title"],
            official_url=metadata["official_url"],
            publication_date=metadata["publication_date"],
            jurisdiction="BR",
            notes=metadata.get("notes"),
            content_hash=parsed.artifact_hash,
            is_synthetic=False,
            created_at=occurred_at,
            organization_id=organization_id,
        )
        version = NcmCatalogVersionRecord(
            id=str(uuid4()),
            catalog_id=catalog.id,
            organization_id=organization_id,
            legal_source_id=source.id,
            version=metadata["version"],
            status=CatalogStatus.IMPORTED if parsed.valid else CatalogStatus.FAILED,
            official_title=metadata["official_title"],
            official_url=metadata["official_url"],
            technical_document=metadata["technical_document"],
            publication_date=metadata["publication_date"],
            consulted_at=metadata["consulted_at"],
            imported_at=occurred_at,
            artifact_file_name=artifact_file_name,
            artifact_path=artifact_path,
            artifact_media_type=artifact_media_type,
            artifact_size=artifact_size,
            artifact_hash=parsed.artifact_hash,
            normalized_hash=parsed.normalized_hash,
            code_count=len(parsed.codes) if parsed.valid else 0,
            import_report=parsed.report,
            imported_by=actor_id,
            validated_at=None,
            validated_by=None,
            submitted_at=None,
            submitted_by=None,
            approved_at=None,
            approved_by=None,
            published_at=None,
            published_by=None,
        )
        self.session.add_all([source, version])
        self.session.flush()
        self.session.add_all(
            NcmStagingRowRecord(
                id=str(uuid4()),
                catalog_version_id=version.id,
                row_number=row.row_number,
                raw_values=row.raw,
                errors=[asdict(issue) for issue in row.errors],
            )
            for row in parsed.staging_rows
        )
        self.session.add_all(
            NcmCodeRecord(
                catalog_version_id=version.id,
                code=item["code"],
                level=item["level"],
                is_final=item["is_final"],
                description=item["description"],
                valid_from=_date(item["valid_from"]),
                valid_to=_date(item["valid_to"]),
                legal_act=item["legal_act"],
            )
            for item in (parsed.codes if parsed.valid else ())
        )
        self.session.add(
            NcmCatalogLifecycleEventRecord(
                id=str(uuid4()),
                catalog_version_id=version.id,
                from_status=CatalogStatus.IMPORTED if parsed.valid else CatalogStatus.FAILED,
                to_status=CatalogStatus.IMPORTED if parsed.valid else CatalogStatus.FAILED,
                occurred_at=occurred_at,
                actor_id=actor_id,
                reason=(
                    "Official artifact imported"
                    if parsed.valid
                    else "Official artifact failed validation"
                ),
                correlation_id=correlation_id,
            )
        )
        self.session.commit()
        return version

    def transition(
        self, organization_id: str, version_id: str, target: CatalogStatus, **event: Any
    ) -> NcmCatalogVersionRecord:
        version = self.get_version(organization_id, version_id)
        previous = version.status
        version.status = target
        timestamp = event["occurred_at"]
        if target is CatalogStatus.VALIDATED:
            version.validated_at, version.validated_by = timestamp, event["actor_id"]
        elif target is CatalogStatus.IN_REVIEW:
            version.submitted_at, version.submitted_by = timestamp, event["actor_id"]
        elif target is CatalogStatus.APPROVED:
            version.approved_at, version.approved_by = timestamp, event["actor_id"]
        elif target is CatalogStatus.PUBLISHED:
            version.published_at, version.published_by = timestamp, event["actor_id"]
        self.session.add(
            NcmCatalogLifecycleEventRecord(
                id=str(uuid4()),
                catalog_version_id=version.id,
                from_status=previous,
                to_status=target,
                occurred_at=timestamp,
                actor_id=event["actor_id"],
                reason=event["reason"],
                correlation_id=event["correlation_id"],
            )
        )
        self.session.commit()
        return version

    def list_versions(
        self, organization_id: str, include_unpublished: bool = False, status: str | None = None
    ) -> list[dict[str, Any]]:
        statement = select(NcmCatalogVersionRecord).where(
            NcmCatalogVersionRecord.organization_id == organization_id
        )
        if status:
            statement = statement.where(NcmCatalogVersionRecord.status == status)
        elif not include_unpublished:
            statement = statement.where(NcmCatalogVersionRecord.status == CatalogStatus.PUBLISHED)
        return [
            _version_view(item)
            for item in self.session.scalars(
                statement.order_by(NcmCatalogVersionRecord.publication_date.desc())
            )
        ]

    def search(
        self, organization_id: str, q: str | None = None, version: str | None = None
    ) -> list[dict[str, Any]]:
        selected_version = self._published_version(organization_id, version)
        statement = select(NcmCodeRecord).where(
            NcmCodeRecord.catalog_version_id == selected_version.id
        )
        if q:
            term = f"%{q.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(NcmCodeRecord.code).like(term),
                    func.lower(NcmCodeRecord.description).like(term),
                )
            )
        return [
            _code_view(row, selected_version)
            for row in self.session.scalars(statement.order_by(NcmCodeRecord.code))
        ]

    def get_code(
        self, organization_id: str, code: str, version: str | None = None
    ) -> dict[str, Any]:
        for item in self.search(organization_id, code, version):
            if item["code"] == code:
                return item
        raise NotFoundError("NCM code not found")

    def _published_version(
        self, organization_id: str, version: str | None
    ) -> NcmCatalogVersionRecord:
        statement = select(NcmCatalogVersionRecord).where(
            NcmCatalogVersionRecord.organization_id == organization_id,
            NcmCatalogVersionRecord.status == CatalogStatus.PUBLISHED,
        )
        if version:
            statement = statement.where(NcmCatalogVersionRecord.version == version)
        record = self.session.scalar(
            statement.order_by(NcmCatalogVersionRecord.publication_date.desc()).limit(1)
        )
        if record is None:
            raise NotFoundError("Published NCM catalog version not found")
        return record


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _source(version: NcmCatalogVersionRecord) -> dict[str, Any]:
    return {
        "title": version.official_title,
        "official_url": version.official_url,
        "technical_document": version.technical_document,
        "publication_date": version.publication_date,
        "artifact_hash": version.artifact_hash,
        "consulted_at": version.consulted_at,
        "imported_at": version.imported_at,
        "status": version.status,
    }


def _version_view(version: NcmCatalogVersionRecord) -> dict[str, Any]:
    return {
        "id": version.id,
        "catalog_id": version.catalog_id,
        "version": version.version,
        "status": version.status,
        "publication_date": version.publication_date,
        "published_at": version.published_at,
        "code_count": version.code_count,
        "source": _source(version),
    }


def _code_view(row: NcmCodeRecord, version: NcmCatalogVersionRecord) -> dict[str, Any]:
    return {
        "code": row.code,
        "level": row.level,
        "is_final": row.is_final,
        "description": row.description,
        "valid_from": row.valid_from,
        "valid_to": row.valid_to,
        "legal_act": row.legal_act,
        "catalog_version": version.version,
        "catalog_version_id": version.id,
        "source": _source(version),
    }
