"""Governed load of the official NCM and NBS catalogs (Etapa 22).

Mirrors governed_load_cli.py's shape exactly: read a versioned JSON manifest,
verify the artifact hash against it, import, and run the full
IMPORTED -> VALIDATED -> IN_REVIEW -> APPROVED -> PUBLISHED chain with
distinct actors. Unlike the real-rule deploy CLIs, this never writes back
into any tracked file - no risk of the Etapa 21 CRLF/hash regression class.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session
from tributaria_importers.nbs_catalog import import_official_nbs_catalog
from tributaria_importers.ncm_catalog import import_official_ncm_catalog

from tributaria_api.application.taxonomy import (
    CatalogLifecyclePolicy,
    CatalogStatus,
    TaxonomyService,
)
from tributaria_api.infrastructure.database.nbs_repository import SqlAlchemyNbsRepository
from tributaria_api.infrastructure.database.ncm_repository import SqlAlchemyNcmRepository
from tributaria_api.infrastructure.database.session import get_engine

ROOT = Path(__file__).resolve().parents[3]
ORGANIZATION_ID = "dev-governance-org"
NCM_MANIFEST = "ncm-2026-09-08.json"
NBS_MANIFEST = "nbs-2.0.json"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Manifest must be an object: {path}")
    return value


def _load_ncm_catalog(session: Session, now: datetime) -> dict[str, object]:
    repository = SqlAlchemyNcmRepository(session)
    service = TaxonomyService(
        repository, ORGANIZATION_ID, CatalogLifecyclePolicy(segregation_enabled=True)
    )
    manifest_root = ROOT / "database/normative-artifacts/manifests"
    ingested_root = ROOT / "database/normative-artifacts/ingested"
    ingested_root.mkdir(parents=True, exist_ok=True)
    manifest = _read(manifest_root / NCM_MANIFEST)
    artifact = ROOT / str(manifest["artifact_path"])
    parsed = import_official_ncm_catalog(artifact)
    expected_hash = str(manifest["artifact_sha256"])
    expected_codes = int(str(manifest["code_count"]))
    if not parsed.valid or parsed.artifact_hash != expected_hash:
        raise RuntimeError(f"NCM catalog validation/hash failed: {artifact}")
    if len(parsed.codes) != expected_codes:
        raise RuntimeError(f"NCM catalog count mismatch: {artifact}")
    destination = ingested_root / f"{parsed.artifact_hash}.json"
    if destination.exists() and destination.read_bytes() != artifact.read_bytes():
        raise RuntimeError("Artifact hash collision")
    if not destination.exists():
        shutil.copyfile(artifact, destination)
    version_label = str(manifest["publication_date"])
    version = repository.ingest(
        organization_id=ORGANIZATION_ID,
        actor_id="dev-curator",
        artifact_path=destination.name,
        artifact_file_name=artifact.name,
        artifact_media_type="application/json",
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
            "notes": "Carga governada reproduzível da Etapa 22",
        },
        occurred_at=now,
        correlation_id=f"etapa22-ncm-import-{version_label}",
    )
    return _publish(service, version, version_label, "ncm")


def _load_nbs_catalog(session: Session, now: datetime) -> dict[str, object]:
    repository = SqlAlchemyNbsRepository(session)
    service = TaxonomyService(
        repository, ORGANIZATION_ID, CatalogLifecyclePolicy(segregation_enabled=True)
    )
    manifest_root = ROOT / "database/normative-artifacts/manifests"
    ingested_root = ROOT / "database/normative-artifacts/ingested"
    ingested_root.mkdir(parents=True, exist_ok=True)
    manifest = _read(manifest_root / NBS_MANIFEST)
    artifact = ROOT / str(manifest["artifact_path"])
    parsed = import_official_nbs_catalog(artifact)
    expected_hash = str(manifest["artifact_sha256"])
    expected_codes = int(str(manifest["code_count"]))
    if not parsed.valid or parsed.artifact_hash != expected_hash:
        raise RuntimeError(f"NBS catalog validation/hash failed: {artifact}")
    if len(parsed.codes) != expected_codes:
        raise RuntimeError(f"NBS catalog count mismatch: {artifact}")
    destination = ingested_root / f"{parsed.artifact_hash}.csv"
    if destination.exists() and destination.read_bytes() != artifact.read_bytes():
        raise RuntimeError("Artifact hash collision")
    if not destination.exists():
        shutil.copyfile(artifact, destination)
    version_label = str(manifest["version"])
    version = repository.ingest(
        organization_id=ORGANIZATION_ID,
        actor_id="dev-curator",
        artifact_path=destination.name,
        artifact_file_name=artifact.name,
        artifact_media_type="text/csv",
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
            "notes": "Carga governada reproduzível da Etapa 22",
        },
        occurred_at=now,
        correlation_id=f"etapa22-nbs-import-{version_label}",
    )
    return _publish(service, version, version_label, "nbs")


def _publish(
    service: TaxonomyService, version: Any, version_label: str, prefix: str
) -> dict[str, object]:
    transitions = (
        (CatalogStatus.VALIDATED, "dev-curator", "Validated against reviewed manifest"),
        (CatalogStatus.IN_REVIEW, "dev-curator", "Submitted for governed review"),
        (CatalogStatus.APPROVED, "dev-approver", "Catalog approved"),
        (CatalogStatus.PUBLISHED, "dev-publisher", "Catalog published"),
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
            correlation_id=f"etapa22-{prefix}-{target.value.casefold()}-{version_label}",
        )
    return {
        "catalog_id": version.catalog_id,
        "catalog_version_id": version.id,
        "version": version.version,
        "status": version.status,
        "artifact_hash": version.artifact_hash,
        "fingerprint": version.normalized_hash,
        "code_count": version.code_count,
        "published_at": version.published_at.isoformat() if version.published_at else None,
        "published_by": version.published_by,
    }


def main() -> int:
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        ncm = _load_ncm_catalog(session, now)
        nbs = _load_nbs_catalog(session, now)
    print(
        json.dumps(
            {"organization_id": ORGANIZATION_ID, "ncm": ncm, "nbs": nbs},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
