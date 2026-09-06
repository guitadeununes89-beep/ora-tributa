from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Query, status
from tributaria_importers.ibs_cbs_catalog import (
    MAX_COMPRESSED_BYTES,
    CatalogImportError,
    ImportIssue,
    ParsedCatalog,
    import_official_catalog,
)

from tributaria_api.api.auth_dependencies import (
    ApproverContext,
    CorrelationId,
    CuratorContext,
    PublisherContext,
    ReadContext,
)
from tributaria_api.api.taxonomy_dependencies import TaxonomyRepositoryDep, TaxonomyServiceDep
from tributaria_api.application.errors import GovernanceError
from tributaria_api.application.taxonomy import CatalogStatus
from tributaria_api.config import get_settings
from tributaria_api.contracts.taxonomy import (
    CatalogImportRequest,
    CatalogTransitionCommand,
    CatalogVersionView,
    ClassificationView,
    CstView,
    ImportedVersionView,
)

router = APIRouter(prefix="/taxonomy/ibs-cbs", tags=["IBS/CBS taxonomy"])


@router.get("/catalogs", response_model=list[CatalogVersionView])
def list_catalogs(
    repository: TaxonomyRepositoryDep,
    context: ReadContext,
    status_filter: Annotated[CatalogStatus | None, Query(alias="status")] = None,
) -> list[dict[str, object]]:
    return repository.list_versions(
        context.organization_id, include_unpublished=True, status=status_filter
    )


@router.get("/csts", response_model=list[CstView])
def list_csts(
    repository: TaxonomyRepositoryDep,
    context: ReadContext,
    q: str | None = Query(default=None, max_length=200),
    version: str | None = Query(default=None, max_length=100),
) -> list[dict[str, object]]:
    return repository.list_csts(context.organization_id, q, version)


@router.get("/classifications", response_model=list[ClassificationView])
def list_classifications(
    repository: TaxonomyRepositoryDep,
    context: ReadContext,
    q: str | None = Query(default=None, max_length=200),
    cst: str | None = Query(default=None, pattern=r"^\d{3}$"),
    version: str | None = Query(default=None, max_length=100),
) -> list[dict[str, object]]:
    return repository.list_classifications(context.organization_id, q, cst, version)


@router.get("/csts/{code}", response_model=CstView)
def get_cst(
    code: str,
    repository: TaxonomyRepositoryDep,
    context: ReadContext,
    version: str | None = Query(default=None, max_length=100),
) -> dict[str, object]:
    return repository.get_cst(context.organization_id, code, version)


@router.get("/classifications/{code}", response_model=ClassificationView)
def get_classification(
    code: str,
    repository: TaxonomyRepositoryDep,
    context: ReadContext,
    version: str | None = Query(default=None, max_length=100),
) -> dict[str, object]:
    return repository.get_classification(context.organization_id, code, version)


@router.get("/catalogs/{previous_id}/diff/{current_id}")
def catalog_diff(
    previous_id: str,
    current_id: str,
    repository: TaxonomyRepositoryDep,
    context: ReadContext,
) -> dict[str, object]:
    return repository.diff(context.organization_id, previous_id, current_id)


admin_router = APIRouter(prefix="/admin/taxonomy/ibs-cbs", tags=["IBS/CBS taxonomy admin"])


@admin_router.get("/versions", response_model=list[CatalogVersionView])
def list_versions_for_review(
    repository: TaxonomyRepositoryDep,
    context: CuratorContext,
    status_filter: Annotated[CatalogStatus | None, Query(alias="status")] = None,
) -> list[dict[str, object]]:
    return repository.list_versions(
        context.organization_id, include_unpublished=True, status=status_filter
    )


@admin_router.post(
    "/imports", response_model=ImportedVersionView, status_code=status.HTTP_201_CREATED
)
def import_catalog(
    request: CatalogImportRequest,
    context: CuratorContext,
    correlation_id: CorrelationId,
    repository: TaxonomyRepositoryDep,
) -> object:
    content = bytes(request.artifact_base64)
    if len(content) > MAX_COMPRESSED_BYTES:
        raise GovernanceError("Artifact exceeds the upload size limit")
    metadata = request.metadata
    root = Path(get_settings().normative_artifact_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / f"upload-{uuid4()}.xlsx"
    temporary.write_bytes(content)
    try:
        try:
            parsed = import_official_catalog(temporary)
        except CatalogImportError as exc:
            artifact_hash = hashlib.sha256(content).hexdigest()
            issue = ImportIssue("INCOMPATIBLE_ARTIFACT", str(exc))
            parsed = ParsedCatalog(
                artifact_hash=artifact_hash,
                normalized_hash=hashlib.sha256(b"UNPARSED").hexdigest(),
                schema_signature=hashlib.sha256(str(exc).encode("utf-8")).hexdigest(),
                csts=(),
                classifications=(),
                staging_rows=(),
                issues=(issue,),
            )
        if parsed.artifact_hash != metadata.expected_artifact_hash:
            parsed = replace(
                parsed,
                issues=(
                    *parsed.issues,
                    ImportIssue(
                        "ARTIFACT_HASH_MISMATCH",
                        "Artifact hash differs from the reviewed manifest",
                    ),
                ),
            )
        destination = root / f"{parsed.artifact_hash}.xlsx"
        if destination.exists():
            if destination.read_bytes() != content:
                raise GovernanceError("Artifact hash collision")
            temporary.unlink()
        else:
            temporary.replace(destination)
        return repository.ingest(
            organization_id=context.organization_id,
            actor_id=context.user_id,
            artifact_path=str(destination.relative_to(root)),
            artifact_file_name=request.artifact_file_name,
            artifact_media_type=request.artifact_media_type,
            artifact_size=len(content),
            parsed=parsed,
            metadata={
                **metadata.model_dump(mode="python"),
                "official_url": str(metadata.official_url),
            },
            occurred_at=datetime.now(UTC),
            correlation_id=correlation_id,
        )
    finally:
        temporary.unlink(missing_ok=True)


def _transition(
    version_id: str,
    request: CatalogTransitionCommand,
    target: CatalogStatus,
    service: TaxonomyServiceDep,
    actor_id: str,
    correlation_id: str,
) -> object:
    return service.transition(
        version_id,
        target,
        actor_id=actor_id,
        reason=request.reason,
        correlation_id=correlation_id,
        occurred_at=request.occurred_at,
    )


@admin_router.post("/versions/{version_id}/validate", response_model=ImportedVersionView)
def validate(
    version_id: str,
    request: CatalogTransitionCommand,
    service: TaxonomyServiceDep,
    context: CuratorContext,
    correlation_id: CorrelationId,
) -> object:
    return _transition(
        version_id, request, CatalogStatus.VALIDATED, service, context.user_id, correlation_id
    )


@admin_router.post("/versions/{version_id}/submit-review", response_model=ImportedVersionView)
def submit_review(
    version_id: str,
    request: CatalogTransitionCommand,
    service: TaxonomyServiceDep,
    context: CuratorContext,
    correlation_id: CorrelationId,
) -> object:
    return _transition(
        version_id, request, CatalogStatus.IN_REVIEW, service, context.user_id, correlation_id
    )


@admin_router.post("/versions/{version_id}/approve", response_model=ImportedVersionView)
def approve(
    version_id: str,
    request: CatalogTransitionCommand,
    service: TaxonomyServiceDep,
    context: ApproverContext,
    correlation_id: CorrelationId,
) -> object:
    return _transition(
        version_id, request, CatalogStatus.APPROVED, service, context.user_id, correlation_id
    )


@admin_router.post("/versions/{version_id}/publish", response_model=ImportedVersionView)
def publish(
    version_id: str,
    request: CatalogTransitionCommand,
    service: TaxonomyServiceDep,
    context: PublisherContext,
    correlation_id: CorrelationId,
) -> object:
    return _transition(
        version_id, request, CatalogStatus.PUBLISHED, service, context.user_id, correlation_id
    )
