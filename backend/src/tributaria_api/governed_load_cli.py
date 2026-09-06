from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy.orm import Session
from tributaria_importers.ibs_cbs_catalog import import_official_catalog

from tributaria_api.application.governance import GovernanceService, SegregationOfDutiesPolicy
from tributaria_api.application.taxonomy import (
    CatalogLifecyclePolicy,
    CatalogStatus,
    TaxonomyService,
)
from tributaria_api.infrastructure.database.identity_models import OrganizationRecord  # noqa: F401
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository
from tributaria_api.infrastructure.database.session import get_engine
from tributaria_api.infrastructure.database.taxonomy_repository import SqlAlchemyTaxonomyRepository

ROOT = Path(__file__).resolve().parents[3]
ORGANIZATION_ID = "dev-governance-org"
LEGAL_MANIFESTS = (
    "lcp214-compilado.json",
    "lcp214-original.json",
    "lcp227.json",
    "lcp187.json",
)
CATALOG_MANIFESTS = (
    "ibscbs-cclasstrib-2025-12-15.json",
    "ibscbs-cclasstrib-2026-06-23.json",
)


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Manifest must be an object: {path}")
    return value


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_sources(session: Session, now: datetime) -> dict[str, str]:
    repository = SqlAlchemyGovernanceRepository(session)
    service = GovernanceService(
        repository,
        SegregationOfDutiesPolicy(enabled=True),
        organization_id=ORGANIZATION_ID,
        authenticated_user_id="dev-curator",
    )
    result: dict[str, str] = {}
    root = ROOT / "database/normative-artifacts/legal/manifests"
    for file_name in LEGAL_MANIFESTS:
        manifest = _read(root / file_name)
        artifact = ROOT / str(manifest.pop("artifact_path"))
        expected = str(manifest["content_hash"])
        if _hash(artifact) != expected:
            raise RuntimeError(f"Legal artifact hash mismatch: {artifact}")
        source = service.create_legal_source(
            {
                **manifest,
                "publication_date": date.fromisoformat(str(manifest["publication_date"])),
                "is_synthetic": False,
                "organization_id": ORGANIZATION_ID,
                "created_at": now,
                "created_by": "dev-curator",
                "correlation_id": f"7b3-source-{file_name}",
            }
        )
        result[file_name] = str(source["id"])
    return result


def _load_catalogs(session: Session, now: datetime) -> list[dict[str, object]]:
    repository = SqlAlchemyTaxonomyRepository(session)
    service = TaxonomyService(
        repository, ORGANIZATION_ID, CatalogLifecyclePolicy(segregation_enabled=True)
    )
    output: list[dict[str, object]] = []
    manifest_root = ROOT / "database/normative-artifacts/manifests"
    ingested_root = ROOT / "database/normative-artifacts/ingested"
    ingested_root.mkdir(parents=True, exist_ok=True)
    for file_name in CATALOG_MANIFESTS:
        manifest = _read(manifest_root / file_name)
        artifact = ROOT / str(manifest["artifact_path"])
        parsed = import_official_catalog(artifact)
        expected_hash = str(manifest["artifact_sha256"])
        expected_csts = int(str(manifest["cst_count"]))
        expected_classes = int(str(manifest["cclasstrib_count"]))
        if not parsed.valid or parsed.artifact_hash != expected_hash:
            raise RuntimeError(f"Catalog validation/hash failed: {artifact}")
        if len(parsed.csts) != expected_csts or len(parsed.classifications) != expected_classes:
            raise RuntimeError(f"Catalog count mismatch: {artifact}")
        expected_staging = manifest.get("staging_row_count")
        if expected_staging is not None and len(parsed.staging_rows) != int(str(expected_staging)):
            raise RuntimeError(f"Catalog staging count mismatch: {artifact}")
        destination = ingested_root / f"{parsed.artifact_hash}.xlsx"
        if destination.exists() and destination.read_bytes() != artifact.read_bytes():
            raise RuntimeError("Artifact hash collision")
        if not destination.exists():
            shutil.copyfile(artifact, destination)
        version_label = str(manifest.get("version") or manifest["publication_date"])
        version = repository.ingest(
            organization_id=ORGANIZATION_ID,
            actor_id="dev-curator",
            artifact_path=destination.name,
            artifact_file_name=artifact.name,
            artifact_media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            artifact_size=artifact.stat().st_size,
            parsed=parsed,
            metadata={
                "version": version_label,
                "official_title": str(manifest["official_title"]),
                "official_url": str(manifest["source_url"]),
                "technical_document": str(manifest["technical_document"]),
                "issuing_authority": str(manifest["issuing_authority"]),
                "publication_date": date.fromisoformat(str(manifest["publication_date"])),
                "consulted_at": datetime.fromisoformat(str(manifest["consulted_at"])),
                "notes": "Carga governada reproduzível da Etapa 7B.3",
            },
            occurred_at=now,
            correlation_id=f"7b3-import-{version_label}",
        )
        transitions = (
            (CatalogStatus.VALIDATED, "dev-curator", "Validated against reviewed manifest"),
            (CatalogStatus.IN_REVIEW, "dev-curator", "Submitted for governed review"),
            (CatalogStatus.APPROVED, "dev-approver", "Technical catalog approved"),
            (CatalogStatus.PUBLISHED, "dev-publisher", "Technical catalog published"),
        )
        for target, actor, reason in transitions:
            if CatalogStatus(version.status) is target:
                continue
            if CatalogStatus(version.status) is CatalogStatus.PUBLISHED:
                break
            version = service.transition(
                version.id,
                target,
                actor_id=actor,
                reason=reason,
                correlation_id=f"7b3-{target.value.casefold()}-{version_label}",
                occurred_at=now,
            )
        output.append(
            {
                "catalog_id": version.catalog_id,
                "catalog_version_id": version.id,
                "version": version.version,
                "status": version.status,
                "artifact_hash": version.artifact_hash,
                "fingerprint": version.normalized_hash,
                "cst_count": version.cst_count,
                "cclasstrib_count": version.cclasstrib_count,
                "staging_row_count": len(parsed.staging_rows),
                "issue_count": parsed.report["issue_count"],
                "published_at": version.published_at.isoformat() if version.published_at else None,
                "published_by": version.published_by,
            }
        )
    return output


def main() -> int:
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        sources = _load_sources(session, now)
        catalogs = _load_catalogs(session, now)
    print(
        json.dumps(
            {"organization_id": ORGANIZATION_ID, "legal_sources": sources, "catalogs": catalogs},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
