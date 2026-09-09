from __future__ import annotations

import hashlib
import io
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from tributaria_importers.batch_workbook import BatchImportError, parse_batch_workbook

from tributaria_api.api.auth_dependencies import AnalystContext, CorrelationId, ReadContext
from tributaria_api.api.batch_dependencies import BatchRepositoryDep
from tributaria_api.api.dependencies import RepositoryDep
from tributaria_api.api.nbs_dependencies import NbsRepositoryDep
from tributaria_api.api.ncm_dependencies import NcmRepositoryDep
from tributaria_api.api.product_dependencies import ProductRepositoryDep
from tributaria_api.api.taxonomy_dependencies import TaxonomyRepositoryDep
from tributaria_api.application.batch_classification import expand_row_result, process_batch_row
from tributaria_api.application.errors import ConflictError
from tributaria_api.config import get_settings
from tributaria_api.contracts.batch_classification import (
    BatchDetailResponse,
    BatchRowResult,
    BatchSummary,
    BatchUploadResponse,
)
from tributaria_api.infrastructure.database.batch_models import ClassificationBatchRecord
from tributaria_api.infrastructure.database.batch_repository import (
    NewBatchRow,
    SqlAlchemyBatchRepository,
)
from tributaria_api.infrastructure.database.nbs_repository import SqlAlchemyNbsRepository
from tributaria_api.infrastructure.database.ncm_repository import SqlAlchemyNcmRepository
from tributaria_api.infrastructure.database.product_repository import ProductRepository
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository
from tributaria_api.infrastructure.database.taxonomy_repository import (
    SqlAlchemyTaxonomyRepository,
)

router = APIRouter(prefix="/batch-classification", tags=["batch classification"])
ENGINE_VERSION = "0.7.0-rt-ibscbs-unified"


@router.post("/upload", response_model=BatchUploadResponse)
async def upload(
    context: AnalystContext,
    batches: BatchRepositoryDep,
    file: Annotated[UploadFile, File()],
) -> BatchUploadResponse:
    """Parse a spreadsheet and stage its rows as PENDING - never evaluates.

    Reused unmodified between `.xlsx` and `.csv`: validation, zip-bomb/
    macro defenses and tolerant header mapping all live in
    `tributaria_importers.batch_workbook` (ADR-0027, decisions 8-9). The
    file's bytes are discarded once parsed - only the hash and each row's
    parsed values are kept.
    """
    settings = get_settings()
    content = await file.read()
    if len(content) > settings.batch_max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Arquivo excede o limite de {settings.batch_max_file_size_bytes} bytes "
                "(limite inicial configurável, não capacidade definitiva)"
            ),
        )
    try:
        parsed = parse_batch_workbook(
            content, file.filename or "upload.xlsx", max_rows=settings.batch_max_rows
        )
    except BatchImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    file_hash = hashlib.sha256(content).hexdigest()
    now = datetime.now(UTC)
    batch = batches.create_batch(
        organization_id=context.organization_id,
        actor_id=context.user_id,
        file_name=file.filename or "upload.xlsx",
        file_hash=file_hash,
        file_media_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        row_count=len(parsed.rows),
        truncated=parsed.truncated,
        max_rows=settings.batch_max_rows,
        occurred_at=now,
    )
    batches.add_rows(
        batch.id,
        (
            NewBatchRow(
                row_number=row.row_number,
                raw_values=row.raw,
                object_kind=row.object_kind,
                internal_code=row.internal_code,
                description=row.description,
                ncm=row.ncm,
                nbs=row.nbs,
                operation_date=row.operation_date,
                processing_status="ERROR" if row.date_error else "PENDING",
                error_message=(
                    "Data da operação em formato inválido" if row.date_error else None
                ),
            )
            for row in parsed.rows
        ),
    )
    batches.commit()
    rows = batches.list_rows(batch.id)
    return BatchUploadResponse(
        batch=_summary(batch),
        unknown_headers=list(parsed.unknown_headers),
        recognized_headers=list(parsed.recognized_headers),
        preview=[_row_result(row, governance_repository=None) for row in rows[:20]],
    )


@router.post("/{batch_id}/process", response_model=BatchDetailResponse)
def process(
    batch_id: str,
    context: AnalystContext,
    correlation_id: CorrelationId,
    batches: BatchRepositoryDep,
    repository: RepositoryDep,
    ncm_repository: NcmRepositoryDep,
    nbs_repository: NbsRepositoryDep,
    products: ProductRepositoryDep,
    taxonomy: TaxonomyRepositoryDep,
) -> BatchDetailResponse:
    batch = batches.get_batch(context.organization_id, batch_id)
    if batch.status != "RECEIVED":
        raise ConflictError(f"Batch {batch_id} is {batch.status}, expected RECEIVED")
    return _run_processing(
        batch,
        context_organization_id=context.organization_id,
        correlation_id=correlation_id,
        batches=batches,
        repository=repository,
        ncm_repository=ncm_repository,
        nbs_repository=nbs_repository,
        products=products,
        taxonomy=taxonomy,
    )


@router.post("/{batch_id}/reprocess", response_model=BatchDetailResponse)
def reprocess(
    batch_id: str,
    context: AnalystContext,
    correlation_id: CorrelationId,
    batches: BatchRepositoryDep,
    repository: RepositoryDep,
    ncm_repository: NcmRepositoryDep,
    nbs_repository: NbsRepositoryDep,
    products: ProductRepositoryDep,
    taxonomy: TaxonomyRepositoryDep,
) -> BatchDetailResponse:
    """Reprocess a finished batch's raw rows as a brand-new batch.

    Never rewrites the original (`COMPLETED`/`FAILED` batches are
    immutable, ADR-0027 decision 11) - this is how the same input is proven
    to reproduce the same result deterministically.
    """
    original = batches.get_batch(context.organization_id, batch_id)
    if original.status not in ("COMPLETED", "FAILED"):
        raise ConflictError(
            f"Batch {batch_id} is {original.status}; only a finished batch can be reprocessed"
        )
    original_rows = batches.list_rows(batch_id)
    now = datetime.now(UTC)
    new_batch = batches.create_batch(
        organization_id=context.organization_id,
        actor_id=context.user_id,
        file_name=original.file_name,
        file_hash=original.file_hash,
        file_media_type=original.file_media_type,
        file_size=original.file_size,
        row_count=original.row_count,
        truncated=original.truncated,
        max_rows=original.max_rows,
        occurred_at=now,
        reprocessed_from_id=original.id,
    )
    batches.add_rows(
        new_batch.id,
        (
            NewBatchRow(
                row_number=row.row_number,
                raw_values=row.raw_values,
                object_kind=row.object_kind,
                internal_code=row.internal_code,
                description=row.description,
                ncm=row.ncm,
                nbs=row.nbs,
                operation_date=row.operation_date,
                processing_status=(
                    "ERROR"
                    if row.processing_status == "ERROR" and row.evaluation_id is None
                    else "PENDING"
                ),
                error_message=(
                    row.error_message
                    if row.processing_status == "ERROR" and row.evaluation_id is None
                    else None
                ),
            )
            for row in original_rows
        ),
    )
    batches.commit()
    return _run_processing(
        new_batch,
        context_organization_id=context.organization_id,
        correlation_id=correlation_id,
        batches=batches,
        repository=repository,
        ncm_repository=ncm_repository,
        nbs_repository=nbs_repository,
        products=products,
        taxonomy=taxonomy,
    )


@router.get("/{batch_id}", response_model=BatchDetailResponse)
def get_batch(
    batch_id: str, context: ReadContext, batches: BatchRepositoryDep, repository: RepositoryDep
) -> BatchDetailResponse:
    batch = batches.get_batch(context.organization_id, batch_id)
    rows = batches.list_rows(batch_id)
    return BatchDetailResponse(
        batch=_summary(batch),
        rows=[_row_result(row, governance_repository=repository) for row in rows],
    )


@router.get("", response_model=list[BatchSummary])
def list_batches(context: ReadContext, batches: BatchRepositoryDep) -> list[BatchSummary]:
    return [_summary(batch) for batch in batches.list_batches(context.organization_id)]


@router.get("/{batch_id}/export")
def export(
    batch_id: str, context: ReadContext, batches: BatchRepositoryDep, repository: RepositoryDep
) -> StreamingResponse:
    """Export original columns plus conclusion/pending/legal-basis columns.

    Never overwrites the user's original data - original columns come
    first, verbatim; result columns are appended after them. Cell values
    starting with `=`/`+`/`-`/`@` are neutralized against formula injection
    (ADR-0027, decision 8).
    """
    batches.get_batch(context.organization_id, batch_id)  # tenancy check
    rows = batches.list_rows(batch_id)
    original_columns = sorted({key for row in rows for key in row.raw_values})
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Resultado"
    headers = [
        *original_columns,
        "status",
        "cst",
        "cclasstrib",
        "tratamento",
        "fundamento_legal",
        "regra",
        "fatos_faltantes",
        "observacoes",
    ]
    sheet.append(headers)
    for row in rows:
        expanded = expand_row_result(row, governance_repository=repository)
        values = [
            _sanitize_cell(str(row.raw_values.get(column, ""))) for column in original_columns
        ]
        values.extend(
            [
                _sanitize_cell(row.classification_status or row.processing_status),
                _sanitize_cell(expanded["cst"] or ""),
                _sanitize_cell(expanded["cclasstrib"] or ""),
                _sanitize_cell(expanded["tratamento"] or ""),
                _sanitize_cell(_format_legal_references(expanded["fundamento_legal"])),
                _sanitize_cell(expanded["regra"]["rule_code"] if expanded["regra"] else ""),
                _sanitize_cell(", ".join(expanded["fatos_faltantes"])),
                _sanitize_cell(row.observations or row.error_message or ""),
            ]
        )
        sheet.append(values)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="lote-{batch_id}-resultado.xlsx"'
        },
    )


def _run_processing(
    batch: ClassificationBatchRecord,
    *,
    context_organization_id: str,
    correlation_id: str,
    batches: SqlAlchemyBatchRepository,
    repository: SqlAlchemyGovernanceRepository,
    ncm_repository: SqlAlchemyNcmRepository,
    nbs_repository: SqlAlchemyNbsRepository,
    products: ProductRepository,
    taxonomy: SqlAlchemyTaxonomyRepository,
) -> BatchDetailResponse:
    taxonomy_version = taxonomy.get_published_version(context_organization_id)
    ncm_versions = ncm_repository.list_versions(context_organization_id)
    nbs_versions = nbs_repository.list_versions(context_organization_id)
    batches.mark_processing(
        batch.id,
        ncm_catalog_version_id=ncm_versions[0]["id"] if ncm_versions else None,
        nbs_catalog_version_id=nbs_versions[0]["id"] if nbs_versions else None,
        taxonomy_catalog_version_id=taxonomy_version.id,
        engine_version=ENGINE_VERSION,
    )
    processed_count = 0
    error_count = 0
    for row in batches.list_rows(batch.id):
        if row.processing_status == "ERROR":
            error_count += 1
            continue
        outcome = process_batch_row(
            row,
            organization_id=context_organization_id,
            correlation_id=correlation_id,
            engine_version=ENGINE_VERSION,
            taxonomy_catalog_version_id=taxonomy_version.id,
            ncm_repository=ncm_repository,
            nbs_repository=nbs_repository,
            products=products,
            governance_repository=repository,
        )
        batches.update_row_result(
            row.id,
            processing_status=outcome.processing_status,
            error_message=outcome.error_message,
            classification_status=outcome.classification_status,
            evaluation_id=outcome.evaluation_id,
            discovery_rule_codes=outcome.discovery_rule_codes,
            observations=outcome.observations,
        )
        if outcome.processing_status == "ERROR":
            error_count += 1
        else:
            processed_count += 1
    final_batch = batches.mark_completed(
        batch.id,
        processed_count=processed_count,
        error_count=error_count,
        occurred_at=datetime.now(UTC),
    )
    final_rows = batches.list_rows(batch.id)
    return BatchDetailResponse(
        batch=_summary(final_batch),
        rows=[_row_result(row, governance_repository=repository) for row in final_rows],
    )


def _summary(batch: ClassificationBatchRecord) -> BatchSummary:
    return BatchSummary(
        batch_id=batch.id,
        file_name=batch.file_name,
        file_hash=batch.file_hash,
        status=batch.status,  # type: ignore[arg-type]
        row_count=batch.row_count,
        processed_count=batch.processed_count,
        error_count=batch.error_count,
        truncated=batch.truncated,
        max_rows=batch.max_rows,
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )


def _row_result(
    row: Any, *, governance_repository: SqlAlchemyGovernanceRepository | None
) -> BatchRowResult:
    expanded: dict[str, Any] = {
        "cst": None,
        "cclasstrib": None,
        "tratamento": None,
        "fundamento_legal": [],
        "regra": None,
        "fatos_faltantes": [],
        "decision_trace": [],
    }
    if row.evaluation_id and governance_repository is not None:
        expanded = expand_row_result(row, governance_repository=governance_repository)
    return BatchRowResult(
        row_number=row.row_number,
        internal_code=row.internal_code,
        description=row.description,
        ncm=row.ncm,
        nbs=row.nbs,
        object_kind=row.object_kind,
        processing_status=row.processing_status,
        error_message=row.error_message,
        classification_status=row.classification_status,
        cst=expanded["cst"],
        cclasstrib=expanded["cclasstrib"],
        tratamento=expanded["tratamento"],
        fundamento_legal=expanded["fundamento_legal"],
        regra=expanded["regra"],
        decision_trace=expanded["decision_trace"],
        fatos_faltantes=expanded["fatos_faltantes"],
        observacoes=row.observations,
        evaluation_id=row.evaluation_id,
    )


def _format_legal_references(references: list[dict[str, Any]]) -> str:
    return "; ".join(
        f"{item.get('act_type', '')} {item.get('number', '')}/{item.get('year', '')} "
        f"{item.get('device', '')}".strip()
        for item in references
    )


def _sanitize_cell(value: str) -> str:
    if value and value[0] in "=+-@":
        return "'" + value
    return value
