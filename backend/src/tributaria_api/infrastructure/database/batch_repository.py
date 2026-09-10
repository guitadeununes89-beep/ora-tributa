from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tributaria_api.application.errors import ConflictError, NotFoundError
from tributaria_api.infrastructure.database.batch_models import (
    ClassificationBatchRecord,
    ClassificationBatchRowRecord,
)


class NewBatchRow:
    """A parsed spreadsheet row, ready to be persisted as PENDING.

    Kept separate from `ClassificationBatchRowRecord` so the importer
    (`tributaria_importers.batch_workbook`) never has to depend on the
    backend's SQLAlchemy models.
    """

    __slots__ = (
        "description",
        "error_message",
        "internal_code",
        "nbs",
        "ncm",
        "object_kind",
        "operation_date",
        "processing_status",
        "raw_values",
        "row_number",
    )

    def __init__(
        self,
        *,
        row_number: int,
        raw_values: dict[str, Any],
        object_kind: str | None,
        internal_code: str | None,
        description: str | None,
        ncm: str | None,
        nbs: str | None,
        operation_date: date | None,
        processing_status: str = "PENDING",
        error_message: str | None = None,
    ) -> None:
        self.row_number = row_number
        self.raw_values = raw_values
        self.object_kind = object_kind
        self.internal_code = internal_code
        self.description = description
        self.ncm = ncm
        self.nbs = nbs
        self.operation_date = operation_date
        self.processing_status = processing_status
        self.error_message = error_message


class SqlAlchemyBatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_batch(
        self,
        *,
        organization_id: str,
        actor_id: str,
        file_name: str,
        file_hash: str,
        file_media_type: str,
        file_size: int,
        row_count: int,
        truncated: bool,
        max_rows: int,
        occurred_at: datetime,
        reprocessed_from_id: str | None = None,
    ) -> ClassificationBatchRecord:
        record = ClassificationBatchRecord(
            id=str(uuid4()),
            organization_id=organization_id,
            created_by=actor_id,
            file_name=file_name,
            file_hash=file_hash,
            file_media_type=file_media_type,
            file_size=file_size,
            row_count=row_count,
            processed_count=0,
            error_count=0,
            status="RECEIVED",
            truncated=truncated,
            max_rows=max_rows,
            ncm_catalog_version_id=None,
            nbs_catalog_version_id=None,
            taxonomy_catalog_version_id=None,
            engine_version=None,
            reprocessed_from_id=reprocessed_from_id,
            created_at=occurred_at,
            completed_at=None,
        )
        self.session.add(record)
        self._flush()
        return record

    def add_rows(self, batch_id: str, rows: Iterable[NewBatchRow]) -> None:
        self.session.add_all(
            ClassificationBatchRowRecord(
                id=str(uuid4()),
                batch_id=batch_id,
                row_number=row.row_number,
                raw_values=row.raw_values,
                object_kind=row.object_kind,
                internal_code=row.internal_code,
                description=row.description,
                ncm=row.ncm,
                nbs=row.nbs,
                operation_date=row.operation_date,
                processing_status=row.processing_status,
                error_message=row.error_message,
                classification_status=None,
                evaluation_id=None,
                discovery_rule_codes=None,
                observations=None,
            )
            for row in rows
        )
        self._flush()

    def get_batch(self, organization_id: str, batch_id: str) -> ClassificationBatchRecord:
        record = self.session.scalar(
            select(ClassificationBatchRecord).where(
                ClassificationBatchRecord.id == batch_id,
                ClassificationBatchRecord.organization_id == organization_id,
            )
        )
        if record is None:
            raise NotFoundError("Classification batch not found")
        return record

    def list_batches(self, organization_id: str) -> list[ClassificationBatchRecord]:
        return list(
            self.session.scalars(
                select(ClassificationBatchRecord)
                .where(ClassificationBatchRecord.organization_id == organization_id)
                .order_by(ClassificationBatchRecord.created_at.desc())
            )
        )

    def list_rows(self, batch_id: str) -> list[ClassificationBatchRowRecord]:
        return list(
            self.session.scalars(
                select(ClassificationBatchRowRecord)
                .where(ClassificationBatchRowRecord.batch_id == batch_id)
                .order_by(ClassificationBatchRowRecord.row_number)
            )
        )

    def mark_processing(
        self,
        batch_id: str,
        *,
        ncm_catalog_version_id: str | None,
        nbs_catalog_version_id: str | None,
        taxonomy_catalog_version_id: str,
        engine_version: str,
    ) -> None:
        record = self._record(batch_id)
        record.status = "PROCESSING"
        record.ncm_catalog_version_id = ncm_catalog_version_id
        record.nbs_catalog_version_id = nbs_catalog_version_id
        record.taxonomy_catalog_version_id = taxonomy_catalog_version_id
        record.engine_version = engine_version
        # Committed (Etapa 24), not just flushed: this runs on the request's
        # own session, synchronously, before the background job (a separate
        # session/connection) is enqueued. A flush alone is invisible outside
        # this session and - worse - leaves the row's lock held until the
        # request's session is torn down, which would deadlock against the
        # background job trying to update the same row.
        self.commit()

    def update_row_result(
        self,
        row_id: str,
        *,
        processing_status: str,
        error_message: str | None = None,
        classification_status: str | None = None,
        evaluation_id: str | None = None,
        discovery_rule_codes: Sequence[str] | None = None,
        observations: str | None = None,
    ) -> None:
        record = self.session.get(ClassificationBatchRowRecord, row_id)
        if record is None:
            raise NotFoundError("Classification batch row not found")
        record.processing_status = processing_status
        record.error_message = error_message
        record.classification_status = classification_status
        record.evaluation_id = evaluation_id
        record.discovery_rule_codes = list(discovery_rule_codes) if discovery_rule_codes else None
        record.observations = observations
        # Committed (not just flushed) so a concurrent GET /{batch_id} - a different
        # session, the frontend's polling (Etapa 24, ADR-0028) - observes this row's
        # result as soon as it lands, not only once the whole batch finishes.
        self.commit()

    def update_progress(self, batch_id: str, *, processed_count: int, error_count: int) -> None:
        """Committed per-row progress update (Etapa 24) for polling clients to observe."""
        record = self._record(batch_id)
        record.processed_count = processed_count
        record.error_count = error_count
        self.commit()

    def mark_completed(
        self, batch_id: str, *, processed_count: int, error_count: int, occurred_at: datetime
    ) -> ClassificationBatchRecord:
        record = self._record(batch_id)
        record.status = "COMPLETED"
        record.processed_count = processed_count
        record.error_count = error_count
        record.completed_at = occurred_at
        self.commit()
        return record

    def mark_failed(self, batch_id: str, *, occurred_at: datetime) -> ClassificationBatchRecord:
        """Mark a batch FAILED after an unhandled error in its background job.

        Etapa 24: `FAILED` existed in the CHECK constraint since migration 0010
        but was never actually reachable - a background job that raises must
        never leave a batch stuck silently in PROCESSING forever.
        """
        record = self._record(batch_id)
        record.status = "FAILED"
        record.completed_at = occurred_at
        self.commit()
        return record

    def commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Database invariant rejected the operation") from exc

    def _record(self, batch_id: str) -> ClassificationBatchRecord:
        record = self.session.get(ClassificationBatchRecord, batch_id)
        if record is None:
            raise NotFoundError("Classification batch not found")
        return record

    def _flush(self) -> None:
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Database invariant rejected the operation") from exc
