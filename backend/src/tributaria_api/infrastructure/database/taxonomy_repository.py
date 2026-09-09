from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from tributaria_api.application.errors import ConflictError, NotFoundError
from tributaria_api.application.taxonomy import CatalogStatus, structured_catalog_diff
from tributaria_api.infrastructure.database.models import LegalSourceRecord
from tributaria_api.infrastructure.database.taxonomy_models import (
    CatalogLifecycleEventRecord,
    IbsCbsCstRecord,
    IbsCbsTaxClassificationRecord,
    TaxClassificationCatalogRecord,
    TaxClassificationCatalogVersionRecord,
    TaxClassificationStagingRowRecord,
)


class SqlAlchemyTaxonomyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_version(
        self, organization_id: str, version_id: str
    ) -> TaxClassificationCatalogVersionRecord:
        record = self.session.scalar(
            select(TaxClassificationCatalogVersionRecord).where(
                TaxClassificationCatalogVersionRecord.id == version_id,
                TaxClassificationCatalogVersionRecord.organization_id == organization_id,
            )
        )
        if record is None:
            raise NotFoundError("Catalog version not found")
        return record

    def get_published_version(
        self, organization_id: str
    ) -> TaxClassificationCatalogVersionRecord:
        """Most recent PUBLISHED cClassTrib catalog version for an organization.

        Mirrors `SqlAlchemyNcmRepository._published_version`/`SqlAlchemyNbsRepository`
        (Etapa 22): batch processing (Etapa 23) needs to resolve the current
        catalog automatically, unlike `classify_unified` where the client
        already picks an explicit `catalog_version_id`.
        """
        record = self.session.scalar(
            select(TaxClassificationCatalogVersionRecord)
            .where(
                TaxClassificationCatalogVersionRecord.organization_id == organization_id,
                TaxClassificationCatalogVersionRecord.status == CatalogStatus.PUBLISHED,
            )
            .order_by(TaxClassificationCatalogVersionRecord.publication_date.desc())
            .limit(1)
        )
        if record is None:
            raise NotFoundError("Published cClassTrib catalog version not found")
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
    ) -> TaxClassificationCatalogVersionRecord:
        catalog = self.session.scalar(
            select(TaxClassificationCatalogRecord).where(
                TaxClassificationCatalogRecord.organization_id == organization_id,
                TaxClassificationCatalogRecord.code == "IBSCBS-CCLASSTRIB",
            )
        )
        if catalog is None:
            catalog = TaxClassificationCatalogRecord(
                id=str(uuid4()),
                organization_id=organization_id,
                code="IBSCBS-CCLASSTRIB",
                name="Catálogo CST IBS/CBS e cClassTrib",
                created_at=occurred_at,
                created_by=actor_id,
            )
            self.session.add(catalog)
            self.session.flush()
        existing_artifact = self.session.scalar(
            select(TaxClassificationCatalogVersionRecord).where(
                TaxClassificationCatalogVersionRecord.catalog_id == catalog.id,
                TaxClassificationCatalogVersionRecord.artifact_hash == parsed.artifact_hash,
            )
        )
        if existing_artifact is not None:
            return existing_artifact
        existing_version = self.session.scalar(
            select(TaxClassificationCatalogVersionRecord).where(
                TaxClassificationCatalogVersionRecord.catalog_id == catalog.id,
                TaxClassificationCatalogVersionRecord.version == metadata["version"],
            )
        )
        if existing_version is not None:
            raise ConflictError("Catalog version already exists with a different artifact")
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
        version = TaxClassificationCatalogVersionRecord(
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
            schema_signature=parsed.schema_signature,
            cst_count=len(parsed.csts) if parsed.valid else 0,
            cclasstrib_count=len(parsed.classifications) if parsed.valid else 0,
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
            TaxClassificationStagingRowRecord(
                id=str(uuid4()),
                catalog_version_id=version.id,
                sheet_name=row.sheet,
                row_number=row.row_number,
                raw_values=row.raw,
                errors=[asdict(issue) for issue in row.errors],
            )
            for row in parsed.staging_rows
        )
        self.session.add_all(
            IbsCbsCstRecord(
                catalog_version_id=version.id,
                code=item["code"],
                description=item["description"],
                indicators=item["indicators"],
            )
            for item in (parsed.csts if parsed.valid else ())
        )
        self.session.add_all(
            IbsCbsTaxClassificationRecord(
                catalog_version_id=version.id,
                code=item["code"],
                cst_code=item["cst"],
                cst_description=item["cst_description"],
                name=item["name"],
                description=item["description"],
                valid_from=_date(item["valid_from"]),
                valid_to=_date(item["valid_to"]),
                updated_on=_date(item["updated_on"]),
                attributes=item["attributes"],
            )
            for item in (parsed.classifications if parsed.valid else ())
        )
        self.session.add(
            CatalogLifecycleEventRecord(
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
    ) -> TaxClassificationCatalogVersionRecord:
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
            CatalogLifecycleEventRecord(
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
        statement = select(TaxClassificationCatalogVersionRecord).where(
            TaxClassificationCatalogVersionRecord.organization_id == organization_id
        )
        if status:
            statement = statement.where(TaxClassificationCatalogVersionRecord.status == status)
        elif not include_unpublished:
            statement = statement.where(
                TaxClassificationCatalogVersionRecord.status == CatalogStatus.PUBLISHED
            )
        return [
            _version_view(item)
            for item in self.session.scalars(
                statement.order_by(TaxClassificationCatalogVersionRecord.publication_date.desc())
            )
        ]

    def list_csts(
        self, organization_id: str, q: str | None = None, version: str | None = None
    ) -> list[dict[str, Any]]:
        selected_version = self._published_version(organization_id, version)
        statement = (
            select(IbsCbsCstRecord, TaxClassificationCatalogVersionRecord)
            .join(
                TaxClassificationCatalogVersionRecord,
                TaxClassificationCatalogVersionRecord.id == IbsCbsCstRecord.catalog_version_id,
            )
            .where(
                TaxClassificationCatalogVersionRecord.organization_id == organization_id,
                TaxClassificationCatalogVersionRecord.status == CatalogStatus.PUBLISHED,
                TaxClassificationCatalogVersionRecord.id == selected_version.id,
            )
        )
        if q:
            term = f"%{q.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(IbsCbsCstRecord.code).like(term),
                    func.lower(IbsCbsCstRecord.description).like(term),
                )
            )
        return [
            {
                "code": row.code,
                "description": row.description,
                "indicators": row.indicators,
                "catalog_version": version.version,
                "catalog_version_id": version.id,
                "source": _source(version),
            }
            for row, version in self.session.execute(statement.order_by(IbsCbsCstRecord.code))
        ]

    def list_classifications(
        self,
        organization_id: str,
        q: str | None = None,
        cst: str | None = None,
        version: str | None = None,
    ) -> list[dict[str, Any]]:
        selected_version = self._published_version(organization_id, version)
        statement = (
            select(IbsCbsTaxClassificationRecord, TaxClassificationCatalogVersionRecord)
            .join(
                TaxClassificationCatalogVersionRecord,
                TaxClassificationCatalogVersionRecord.id
                == IbsCbsTaxClassificationRecord.catalog_version_id,
            )
            .where(
                TaxClassificationCatalogVersionRecord.organization_id == organization_id,
                TaxClassificationCatalogVersionRecord.status == CatalogStatus.PUBLISHED,
                TaxClassificationCatalogVersionRecord.id == selected_version.id,
            )
        )
        if cst:
            statement = statement.where(IbsCbsTaxClassificationRecord.cst_code == cst)
        if q:
            term = f"%{q.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(IbsCbsTaxClassificationRecord.code).like(term),
                    func.lower(IbsCbsTaxClassificationRecord.name).like(term),
                    func.lower(IbsCbsTaxClassificationRecord.description).like(term),
                )
            )
        return [
            _classification_view(row, version)
            for row, version in self.session.execute(
                statement.order_by(IbsCbsTaxClassificationRecord.code)
            )
        ]

    def _published_version(
        self, organization_id: str, version: str | None
    ) -> TaxClassificationCatalogVersionRecord:
        statement = select(TaxClassificationCatalogVersionRecord).where(
            TaxClassificationCatalogVersionRecord.organization_id == organization_id,
            TaxClassificationCatalogVersionRecord.status == CatalogStatus.PUBLISHED,
        )
        if version:
            statement = statement.where(TaxClassificationCatalogVersionRecord.version == version)
        record = self.session.scalar(
            statement.order_by(TaxClassificationCatalogVersionRecord.publication_date.desc()).limit(
                1
            )
        )
        if record is None:
            raise NotFoundError("Published catalog version not found")
        return record

    def get_cst(
        self, organization_id: str, code: str, version: str | None = None
    ) -> dict[str, Any]:
        for item in self.list_csts(organization_id, code, version):
            if item["code"] == code:
                return item
        raise NotFoundError("CST not found")

    def get_classification(
        self, organization_id: str, code: str, version: str | None = None
    ) -> dict[str, Any]:
        for item in self.list_classifications(organization_id, code, version=version):
            if item["code"] == code:
                return item
        raise NotFoundError("cClassTrib not found")

    def candidate_details(
        self,
        organization_id: str,
        catalog_version_id: str,
        cst_code: str,
        classification_code: str | None,
    ) -> dict[str, Any]:
        version = self.get_version(organization_id, catalog_version_id)
        if version.status != CatalogStatus.PUBLISHED:
            raise ConflictError("Tax classification requires a PUBLISHED catalog")
        cst = self.session.scalar(
            select(IbsCbsCstRecord).where(
                IbsCbsCstRecord.catalog_version_id == version.id,
                IbsCbsCstRecord.code == cst_code,
            )
        )
        if cst is None:
            raise ConflictError("Candidate CST does not exist in the referenced catalog")
        classification = None
        if classification_code is not None:
            classification = self.session.scalar(
                select(IbsCbsTaxClassificationRecord).where(
                    IbsCbsTaxClassificationRecord.catalog_version_id == version.id,
                    IbsCbsTaxClassificationRecord.code == classification_code,
                    IbsCbsTaxClassificationRecord.cst_code == cst_code,
                )
            )
            if classification is None:
                raise ConflictError(
                    "Candidate cClassTrib/CST relationship does not exist in the catalog"
                )
        return {
            "catalog_version_id": version.id,
            "cst": cst.code,
            "cst_description": cst.description,
            "cclasstrib": classification.code if classification else None,
            "cclasstrib_name": classification.name if classification else None,
            "cclasstrib_description": classification.description if classification else None,
            "valid_from": classification.valid_from if classification else None,
            "valid_to": classification.valid_to if classification else None,
        }

    def diff(self, organization_id: str, previous_id: str, current_id: str) -> dict[str, Any]:
        previous = self.get_version(organization_id, previous_id)
        current = self.get_version(organization_id, current_id)
        if {
            CatalogStatus(previous.status),
            CatalogStatus(current.status),
        } != {CatalogStatus.PUBLISHED}:
            raise ConflictError("Both snapshots must be published for public comparison")
        return {
            "cst": structured_catalog_diff(self._cst_rows(previous.id), self._cst_rows(current.id)),
            "cclasstrib": structured_catalog_diff(
                self._class_rows(previous.id), self._class_rows(current.id)
            ),
        }

    def _cst_rows(self, version_id: str) -> list[dict[str, Any]]:
        return [
            {"code": row.code, "description": row.description, "indicators": row.indicators}
            for row in self.session.scalars(
                select(IbsCbsCstRecord).where(IbsCbsCstRecord.catalog_version_id == version_id)
            )
        ]

    def _class_rows(self, version_id: str) -> list[dict[str, Any]]:
        return [
            {
                "code": row.code,
                "cst": row.cst_code,
                "name": row.name,
                "description": row.description,
                "valid_from": str(row.valid_from) if row.valid_from else None,
                "valid_to": str(row.valid_to) if row.valid_to else None,
                "attributes": row.attributes,
            }
            for row in self.session.scalars(
                select(IbsCbsTaxClassificationRecord).where(
                    IbsCbsTaxClassificationRecord.catalog_version_id == version_id
                )
            )
        ]


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _source(version: TaxClassificationCatalogVersionRecord) -> dict[str, Any]:
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


def _version_view(version: TaxClassificationCatalogVersionRecord) -> dict[str, Any]:
    return {
        "id": version.id,
        "catalog_id": version.catalog_id,
        "version": version.version,
        "status": version.status,
        "publication_date": version.publication_date,
        "published_at": version.published_at,
        "cst_count": version.cst_count,
        "cclasstrib_count": version.cclasstrib_count,
        "source": _source(version),
    }


def _classification_view(
    row: IbsCbsTaxClassificationRecord, version: TaxClassificationCatalogVersionRecord
) -> dict[str, Any]:
    return {
        "code": row.code,
        "cst": row.cst_code,
        "cst_description": row.cst_description,
        "name": row.name,
        "description": row.description,
        "valid_from": row.valid_from,
        "valid_to": row.valid_to,
        "updated_on": row.updated_on,
        "attributes": row.attributes,
        "catalog_version": version.version,
        "catalog_version_id": version.id,
        "source": _source(version),
    }
