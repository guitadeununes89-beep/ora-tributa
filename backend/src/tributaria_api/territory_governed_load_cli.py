"""Governed load of approved territorial specifications (ADR-0024).

Loads the six approved specifications in docs/tax/territory/specifications/
into tax_jurisdiction_areas / tax_jurisdiction_area_versions, reusing the
already-governed LC 214/2025 legal source (this script does not ingest new
legal sources). Each version is created DRAFT and immediately transitioned
through IN_REVIEW -> APPROVED -> PUBLISHED, mirroring the historical
real_rule_deploy_cli.py flow for RT-IBSCBS-0003. Idempotent: an already
loaded area/version is skipped.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.identity_models import (
    MembershipRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.models import AuditEventRecord, LegalSourceRecord
from tributaria_api.infrastructure.database.session import get_engine
from tributaria_api.infrastructure.database.territory_models import (
    TaxJurisdictionAreaLifecycleEventRecord,
    TaxJurisdictionAreaRecord,
    TaxJurisdictionAreaVersionRecord,
)

ROOT = Path(__file__).resolve().parents[3]
ORGANIZATION_ID = "dev-governance-org"
HUMAN_ACTOR_ID = "legal-approver-guilherme-nunes"
# The LC 214/2025 (compiled) legal_sources.id is generated per database instance by
# governed_load_cli.py (uuid4 on first insert for a given org+content_hash) - it is
# NOT the same value hardcoded in the RT-IBSCBS-*.json specs, which were written
# against a different, earlier database instance. Resolve it dynamically by official
# URL instead of trusting that stale literal.
LC_214_COMPILADO_URL = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm"
SPEC_DIR = ROOT / "docs/tax/territory/specifications"
SPEC_FILES = (
    "TJA-ZFM.json",
    "TJA-ALC-TABATINGA.json",
    "TJA-ALC-GUAJARA-MIRIM.json",
    "TJA-ALC-BOA-VISTA-BONFIM.json",
    "TJA-ALC-MACAPA-SANTANA.json",
    "TJA-ALC-BRASILEIA-CRUZEIRO-DO-SUL.json",
)


def _canonical_hash(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _human_actor_email() -> str:
    value = os.getenv("REAL_RULE_APPROVER_EMAIL", "").strip()
    if not value:
        raise RuntimeError(
            "REAL_RULE_APPROVER_EMAIL is required only when creating the governed approver"
        )
    return value


def _ensure_human_actor(session: Session, now: datetime) -> None:
    if session.get(UserRecord, HUMAN_ACTOR_ID) is None:
        session.add(
            UserRecord(
                id=HUMAN_ACTOR_ID,
                email=_human_actor_email(),
                display_name="Guilherme Nunes",
                status="ACTIVE",
                created_at=now,
                last_login_at=None,
            )
        )
        session.flush()
    membership_id = f"membership-{HUMAN_ACTOR_ID}"
    if session.get(MembershipRecord, membership_id) is None:
        session.add(
            MembershipRecord(
                id=membership_id,
                organization_id=ORGANIZATION_ID,
                user_id=HUMAN_ACTOR_ID,
                role="APPROVER",
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
        )
    session.commit()


def _resolve_lc214_legal_source_id(session: Session) -> str:
    source_id = session.scalar(
        select(LegalSourceRecord.id).where(LegalSourceRecord.official_url == LC_214_COMPILADO_URL)
    )
    if source_id is None:
        raise RuntimeError(
            "LC 214/2025 (compiled) legal source not found; run governed_load_cli first"
        )
    return source_id


def _load_area(
    session: Session, now: datetime, spec_path: Path, legal_source_id: str
) -> dict[str, Any]:
    document = json.loads(spec_path.read_text(encoding="utf-8"))
    if document["status"] != "APPROVED":
        raise RuntimeError(f"{spec_path.name}: specification is not APPROVED")
    if document["approval"]["approved_by"] != HUMAN_ACTOR_ID:
        raise RuntimeError(f"{spec_path.name}: governed human approval does not match")

    area_id = str(document["area_id"])
    area = session.get(TaxJurisdictionAreaRecord, area_id)
    if area is None:
        area = TaxJurisdictionAreaRecord(
            id=area_id,
            organization_id=ORGANIZATION_ID,
            area_type=document["area_type"],
            code=area_id,
            official_name=document["title"],
            created_at=now,
            created_by="dev-curator",
        )
        session.add(area)
        session.add(
            AuditEventRecord(
                id=f"audit-territory-area-created-{area_id}",
                entity_type="TAX_JURISDICTION_AREA",
                entity_id=area_id,
                action="TERRITORY_AREA_CREATED",
                occurred_at=now,
                actor_id="dev-curator",
                origin="TERRITORY_GOVERNED_LOAD",
                correlation_id=f"territory-load-{area_id}-area",
                safe_metadata={"specification_version": document["specification_version"]},
                organization_id=ORGANIZATION_ID,
                authenticated_user_id="dev-curator",
            )
        )
        session.flush()

    version_id = f"{area_id}-V1"
    if session.get(TaxJurisdictionAreaVersionRecord, version_id) is not None:
        return {"area_id": area_id, "version_id": version_id, "status": "already_loaded"}

    legal_device = "; ".join(item["specific_device"] for item in document["legal_foundation"])[:300]
    version_content_hash = _canonical_hash(
        {
            "criteria": document["criteria"],
            "legal_foundation": document["legal_foundation"],
            "known_conflicts": document["known_conflicts"],
        }
    )

    version = TaxJurisdictionAreaVersionRecord(
        id=version_id,
        area_id=area_id,
        organization_id=ORGANIZATION_ID,
        version=1,
        lifecycle_status="DRAFT",
        legal_source_id=legal_source_id,
        legal_device=legal_device,
        criteria=document["criteria"],
        content_hash=version_content_hash,
        valid_from=date.fromisoformat(document["effective_from"]),
        valid_to=None,
        recorded_at=now,
        created_by="dev-curator",
    )
    session.add(version)
    session.flush()

    transitions = (
        ("DRAFT", "IN_REVIEW", "dev-curator", "Submitted for governed review"),
        (
            "IN_REVIEW",
            "APPROVED",
            HUMAN_ACTOR_ID,
            "Territorial specification approved by tax/legal responsible (docs/tax/territory/"
            f"approvals/{area_id}-v1.md)",
        ),
        ("APPROVED", "PUBLISHED", "dev-publisher", "Governed territory version published"),
    )
    for index, (from_status, to_status, actor, reason) in enumerate(transitions, start=1):
        occurred_at = now + timedelta(seconds=index)
        session.add(
            TaxJurisdictionAreaLifecycleEventRecord(
                id=f"{version_id}-event-{index}",
                area_version_id=version_id,
                from_status=from_status,
                to_status=to_status,
                occurred_at=occurred_at,
                actor_id=actor,
                reason=reason,
                correlation_id=f"territory-load-{area_id}-{to_status.casefold()}",
            )
        )
        version.lifecycle_status = to_status
        if to_status == "APPROVED":
            version.approved_at = occurred_at
            version.approved_by = actor
        if to_status == "PUBLISHED":
            version.published_at = occurred_at
            version.published_by = actor
    session.add(
        AuditEventRecord(
            id=f"audit-territory-version-published-{version_id}",
            entity_type="TAX_JURISDICTION_AREA_VERSION",
            entity_id=version_id,
            action="TERRITORY_VERSION_PUBLISHED",
            occurred_at=now + timedelta(seconds=len(transitions)),
            actor_id="dev-publisher",
            origin="TERRITORY_GOVERNED_LOAD",
            correlation_id=f"territory-load-{area_id}-published",
            safe_metadata={"content_hash": version_content_hash},
            organization_id=ORGANIZATION_ID,
            authenticated_user_id="dev-publisher",
        )
    )
    session.commit()

    document["implementation"] = {
        "tax_jurisdiction_area_id": area_id,
        "tax_jurisdiction_area_version_id": version_id,
        "implemented_at": now.date().isoformat(),
    }
    spec_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {"area_id": area_id, "version_id": version_id, "status": "loaded"}


def main() -> int:
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        _ensure_human_actor(session, now)
        legal_source_id = _resolve_lc214_legal_source_id(session)
        results = [
            _load_area(session, now, SPEC_DIR / name, legal_source_id) for name in SPEC_FILES
        ]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
