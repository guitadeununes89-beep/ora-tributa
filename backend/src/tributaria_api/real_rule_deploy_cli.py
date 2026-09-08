from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from tax_engine.rule_lifecycle import RuleLifecycleStatus

from tributaria_api.application.governance import GovernanceService, SegregationOfDutiesPolicy
from tributaria_api.application.tax_rule_specifications import load_specification
from tributaria_api.governed_reference_resolution import (
    resolve_catalog_version_id,
    resolve_legal_source_id,
)
from tributaria_api.infrastructure.database.identity_models import (
    MembershipRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.models import (
    AuditEventRecord,
    RuleSetRecord,
    TaxRuleIdentityRecord,
    TaxRuleVersionRecord,
)
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository
from tributaria_api.infrastructure.database.session import get_engine

ROOT = Path(__file__).resolve().parents[3]
ORGANIZATION_ID = "dev-governance-org"
SPEC_PATH = ROOT / "docs/tax/rules/specifications/RT-IBSCBS-0003.json"
APPROVAL_PATH = ROOT / "docs/tax/rules/approvals/RT-IBSCBS-0003-v2.md"
HUMAN_ACTOR_ID = "legal-approver-guilherme-nunes"
RULESET_ID = "IBSCBS-PILOT-001"

# Same non-portability issue already fixed in territory_governed_load_cli.py and
# real_rule_deploy_cli_p1_zfm.py: legal_source_id/catalog_version_id literals baked
# into the approved specification JSON were generated in a different database
# instance (uuid4 on first insert), so a fresh instance must resolve both instead of
# trusting those literals. Pinned to the same LC 214/2025 (compiled) legal source
# already used for RT-IBSCBS-0007/0008 - same law, same governed citation.
LC_214_COMPILADO_URL = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm"
CURRENT_CATALOG_VERSION = "2026-06-23"
# Captured once from this project's own database (Etapa 21) - see
# governed_reference_resolution.py for why this is a pinned constant rather
# than a field added to the approved specification JSON.
LC_214_COMPILADO_CONTENT_HASH = "aacfd146f2c91291c3c8675035da70cb08b359bca03b3ccc21c5b3a14e6a7719"


def _approval_hash(document: dict[str, Any]) -> str:
    approved = {**document, "implementation": None}
    canonical = json.dumps(approved, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _human_actor_email() -> str:
    value = os.getenv("REAL_RULE_APPROVER_EMAIL", "").strip()
    if not value:
        raise RuntimeError(
            "REAL_RULE_APPROVER_EMAIL is required only when creating the governed approver"
        )
    return value


def _ensure_human_actor(session: Session, now: datetime) -> None:
    user = session.get(UserRecord, HUMAN_ACTOR_ID)
    if user is None:
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
    membership = session.get(MembershipRecord, membership_id)
    if membership is None:
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
    if session.get(AuditEventRecord, f"audit-human-actor-{HUMAN_ACTOR_ID}") is None:
        session.add(
            AuditEventRecord(
                id=f"audit-human-actor-{HUMAN_ACTOR_ID}",
                entity_type="GOVERNED_HUMAN_ACTOR",
                entity_id=HUMAN_ACTOR_ID,
                action="HUMAN_LEGAL_ACTOR_REGISTERED",
                occurred_at=now,
                actor_id=HUMAN_ACTOR_ID,
                origin="ETAPA_7C_GOVERNED_DEPLOYMENT",
                correlation_id="7c-human-legal-actor",
                safe_metadata={
                    "capacity": "RESPONSAVEL_TRIBUTARIO_E_JURIDICO_DO_PROJETO",
                    "stores_personal_document": False,
                },
                organization_id=ORGANIZATION_ID,
                authenticated_user_id=HUMAN_ACTOR_ID,
            )
        )
    session.commit()


def _record_specification_events(session: Session, now: datetime, specification_hash: str) -> None:
    events = (
        (
            "audit-specification-reviewed-rt-ibscbs-0003-v2",
            "SPECIFICATION_REVIEWED",
        ),
        (
            "audit-specification-approved-rt-ibscbs-0003-v2",
            "SPECIFICATION_APPROVED",
        ),
    )
    for event_id, action in events:
        if session.get(AuditEventRecord, event_id) is not None:
            continue
        session.add(
            AuditEventRecord(
                id=event_id,
                entity_type="TAX_RULE_SPECIFICATION",
                entity_id="RT-IBSCBS-0003:v2",
                action=action,
                occurred_at=now,
                actor_id=HUMAN_ACTOR_ID,
                origin="ETAPA_7C_HUMAN_LEGAL_APPROVAL",
                correlation_id=f"7c-{action.casefold().replace('_', '-')}",
                safe_metadata={
                    "specification_hash": specification_hash,
                    "approval_evidence_hash": sha256(APPROVAL_PATH.read_bytes()).hexdigest(),
                    "same_person_review_and_approval": True,
                    "adr": "ADR-0017",
                },
                organization_id=ORGANIZATION_ID,
                authenticated_user_id=HUMAN_ACTOR_ID,
            )
        )
    session.commit()


def _deploy(session: Session, now: datetime) -> dict[str, Any]:
    document = load_specification(SPEC_PATH)
    if document["status"] != "APPROVED":
        raise RuntimeError("Specification is not APPROVED")
    if document["rule_id"] != "RT-IBSCBS-0003" or document["specification_version"] != 2:
        raise RuntimeError("Only RT-IBSCBS-0003 v2 is allowed in this deployment")
    if document["approval"]["approved_by"] != HUMAN_ACTOR_ID:
        raise RuntimeError("Governed human approval does not match the specification")
    if (document["catalog"]["cst"], document["catalog"]["cclasstrib"]) != ("200", "200010"):
        raise RuntimeError("Unexpected CST/cClassTrib in specification")
    legal_source_id = resolve_legal_source_id(
        session,
        official_url=LC_214_COMPILADO_URL,
        expected_content_hash=LC_214_COMPILADO_CONTENT_HASH,
    )
    catalog_version_id = resolve_catalog_version_id(
        session,
        cclasstrib=document["catalog"]["cclasstrib"],
        catalog_version=CURRENT_CATALOG_VERSION,
    )
    specification_hash = _approval_hash(document)
    _record_specification_events(session, now, specification_hash)

    repository = SqlAlchemyGovernanceRepository(session)
    service = GovernanceService(
        repository,
        SegregationOfDutiesPolicy(enabled=True),
        organization_id=ORGANIZATION_ID,
        authenticated_user_id="dev-curator",
    )
    identity = session.scalar(
        select(TaxRuleIdentityRecord).where(
            TaxRuleIdentityRecord.organization_id == ORGANIZATION_ID,
            TaxRuleIdentityRecord.code == "RT-IBSCBS-0003",
        )
    )
    if identity is None:
        identity_id = str(uuid4())
        service.create_rule_identity(
            {
                "id": identity_id,
                "code": "RT-IBSCBS-0003",
                "title": document["title"],
                "description": "LC 214/2025, art. 146, § 1º, I — piloto real restrito",
                "is_synthetic": False,
                "created_at": now,
                "created_by": "dev-curator",
                "organization_id": ORGANIZATION_ID,
                "correlation_id": "7c-real-rule-identity",
            }
        )
        identity = session.get(TaxRuleIdentityRecord, identity_id)
        assert identity is not None

    version = session.scalar(
        select(TaxRuleVersionRecord).where(
            TaxRuleVersionRecord.rule_identity_id == identity.id,
            TaxRuleVersionRecord.version == 1,
        )
    )
    if version is None:
        version_id = str(uuid4())
        approval_metadata = {
            "reviewed_by": HUMAN_ACTOR_ID,
            "approved_by": HUMAN_ACTOR_ID,
            "approval_date": "2026-08-31",
            "approval_evidence": document["approval"]["approval_evidence"],
            "same_person_exception_adr": "ADR-0017",
        }
        content = {
            "implementation_key": "REAL_RT_IBSCBS_0003_V1",
            "specification_id": document["rule_id"],
            "specification_version": document["specification_version"],
            "specification_hash": specification_hash,
            "catalog_version_id": catalog_version_id,
            "cst": document["catalog"]["cst"],
            "cclasstrib": document["catalog"]["cclasstrib"],
            "legal_scope": "LC 214/2025, art. 146, § 1º, I",
        }
        service.create_rule_version(
            {
                "id": version_id,
                "rule_identity_id": identity.id,
                "version": 1,
                "jurisdiction": document["jurisdiction"],
                "legal_source_id": legal_source_id,
                "legal_device": "LC nº 214/2025, art. 146, § 1º, I",
                "valid_from": date.fromisoformat(document["effective_from"]),
                "valid_to": (
                    date.fromisoformat(document["effective_to"])
                    if document["effective_to"]
                    else None
                ),
                "recorded_at": now,
                "created_by": "dev-curator",
                "content": content,
                "metadata": {
                    "rule_scope": "PUBLIC_DIRECT_ADMIN_AUTARCHY_PUBLIC_FOUNDATION_ONLY",
                    "catalog_description_is_shared": "true",
                },
                "specification_id": document["rule_id"],
                "specification_version": document["specification_version"],
                "specification_hash": specification_hash,
                "catalog_version_id": catalog_version_id,
                "cst_code": document["catalog"]["cst"],
                "cclasstrib_code": document["catalog"]["cclasstrib"],
                "approval_metadata": approval_metadata,
                "correlation_id": "7c-real-rule-version-v1",
            }
        )
        service.transition(
            version_id,
            target=RuleLifecycleStatus.IN_REVIEW,
            event_id="rt-ibscbs-0003-v1-in-review",
            occurred_at=now + timedelta(seconds=1),
            actor_id="dev-curator",
            reason="Approved specification submitted for implementation review",
            correlation_id="7c-rule-version-in-review",
        )
        service.transition(
            version_id,
            target=RuleLifecycleStatus.APPROVED,
            event_id="rt-ibscbs-0003-v1-approved",
            occurred_at=now + timedelta(seconds=2),
            actor_id=HUMAN_ACTOR_ID,
            reason="Implementation approved against RT-IBSCBS-0003 v2",
            correlation_id="7c-rule-version-approved",
        )
        service.transition(
            version_id,
            target=RuleLifecycleStatus.PUBLISHED,
            event_id="rt-ibscbs-0003-v1-published",
            occurred_at=now + timedelta(seconds=3),
            actor_id="dev-publisher",
            reason="First governed real IBS/CBS pilot rule published",
            correlation_id="7c-rule-version-published",
        )
        version = session.get(TaxRuleVersionRecord, version_id)
        assert version is not None

    ruleset = session.get(RuleSetRecord, RULESET_ID)
    if ruleset is None:
        service.create_ruleset(
            {
                "id": RULESET_ID,
                "name": "IBS/CBS Pilot 001 — RT-IBSCBS-0003 only",
                "version": "1.0.0",
                "status": "DRAFT",
                "created_at": now + timedelta(seconds=4),
                "created_by": "dev-curator",
                "organization_id": ORGANIZATION_ID,
                "correlation_id": "7c-ruleset-created",
            },
            [version.id],
        )
        service.publish_ruleset(
            RULESET_ID,
            actor_id="dev-publisher",
            occurred_at=now + timedelta(seconds=5),
            correlation_id="7c-ruleset-published",
        )
    ruleset_view = repository.get_ruleset(RULESET_ID)
    _update_mapping(document, identity.id, version.id)
    return {
        "specification_status": document["status"],
        "specification_hash": specification_hash,
        "tax_rule_identity_id": identity.id,
        "tax_rule_version_id": version.id,
        "version": version.version,
        "legal_source_id": version.legal_source_id,
        "catalog_version_id": version.catalog_version_id,
        "cst": version.cst_code,
        "cclasstrib": version.cclasstrib_code,
        "ruleset_id": ruleset_view["id"],
        "ruleset_status": ruleset_view["status"],
        "ruleset_fingerprint": ruleset_view["fingerprint"],
    }


def _update_mapping(document: dict[str, Any], identity_id: str, version_id: str) -> None:
    expected = {
        "tax_rule_identity_id": identity_id,
        "tax_rule_version_id": version_id,
        "implemented_at": "2026-08-31",
    }
    if document.get("implementation") == expected:
        return
    document["implementation"] = expected
    SPEC_PATH.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        _ensure_human_actor(session, now)
        result = _deploy(session, now)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
