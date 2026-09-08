"""Deploy RT-IBSCBS-0007 and RT-IBSCBS-0008 as real, published tax rules.

Mirrors the historical real_rule_deploy_cli.py flow used for RT-IBSCBS-0003,
but for the P1 ZFM block (Etapa 9/9.1) and adapted for a fresh database
instance: the legal_source_id and catalog_version_id literals baked into the
approved specification JSON files were generated in a different, earlier
database instance (uuid4 on first insert), so this script resolves both
dynamically instead of trusting those literals - the same fix already
applied in territory_governed_load_cli.py.

Both rules join a new ruleset, IBSCBS-ZFM-PILOT-001, distinct from the
original IBSCBS-PILOT-001 (which ADR-0017 scoped explicitly to RT-IBSCBS-0003
alone). Neither ruleset is a default or global configuration.
"""

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
from tributaria_api.governed_reference_resolution import (
    resolve_catalog_version_id,
    resolve_legal_source_id,
)
from tributaria_api.infrastructure.database.identity_models import (
    MembershipRecord,
    UserRecord,
)
from tributaria_api.infrastructure.database.models import (
    RuleSetRecord,
    TaxRuleIdentityRecord,
    TaxRuleVersionRecord,
)
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository
from tributaria_api.infrastructure.database.session import get_engine

ROOT = Path(__file__).resolve().parents[3]
ORGANIZATION_ID = "dev-governance-org"
HUMAN_ACTOR_ID = "legal-approver-guilherme-nunes"
LC_214_COMPILADO_URL = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm"
# Captured once from this project's own database (Etapa 21) - the content
# actually reviewed and approved for RT-IBSCBS-0007/0008. Never added to the
# approved specification JSON itself; see governed_reference_resolution.py.
LC_214_COMPILADO_CONTENT_HASH = "aacfd146f2c91291c3c8675035da70cb08b359bca03b3ccc21c5b3a14e6a7719"
SPEC_DIR = ROOT / "docs/tax/rules/specifications"

# RT-IBSCBS-0007 and RT-IBSCBS-0008 describe mutually exclusive operational
# scenarios (goods entering the ZFM from outside vs. goods moving between two
# ZFM-internal incentivized industries) that never share the same fact set.
# Each gets its own explicit, narrow ruleset - mirroring ADR-0017's own
# "IBSCBS-PILOT-001 contains only RT-IBSCBS-0003" precedent - so evaluating
# one scenario is never dragged into REQUIRES_VALIDATION by the other rule's
# unrelated missing facts (discovered by testing the first, combined-ruleset
# attempt end-to-end before this script was finalized).
RULES = (
    {
        "spec_file": "RT-IBSCBS-0007.json",
        "rule_id": "RT-IBSCBS-0007",
        "specification_version": 3,
        "cst": "200",
        "cclasstrib": "200022",
        "legal_scope": "LC 214/2025, art. 445; Resolução CGIBS 6/2026, art. 516",
        "legal_device": "LC nº 214/2025, art. 445; Resolução CGIBS nº 6/2026, art. 516",
        "implementation_key": "REAL_RT_IBSCBS_0007_V1",
        "title": "Bem nacional industrializado destinado a contribuinte habilitado na ZFM",
        "approval_path": ROOT / "docs/tax/rules/approvals/RT-IBSCBS-0007-v3.md",
        "ruleset_id": "IBSCBS-ZFM-0007-PILOT-001",
    },
    {
        "spec_file": "RT-IBSCBS-0008.json",
        "rule_id": "RT-IBSCBS-0008",
        "specification_version": 3,
        "cst": "200",
        "cclasstrib": "200023",
        "legal_scope": "LC 214/2025, art. 448; Resolução CGIBS 6/2026, art. 519",
        "ruleset_id": "IBSCBS-ZFM-0008-PILOT-001",
        "legal_device": "LC nº 214/2025, art. 448; Resolução CGIBS nº 6/2026, art. 519",
        "implementation_key": "REAL_RT_IBSCBS_0008_V1",
        "title": "Bem intermediário entre indústrias incentivadas na ZFM",
        "approval_path": ROOT / "docs/tax/rules/approvals/RT-IBSCBS-0008-v3.md",
    },
)


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


CURRENT_CATALOG_VERSION = "2026-06-23"


def _deploy_rule(
    session: Session,
    now: datetime,
    legal_source_id: str,
    spec: dict[str, Any],
) -> dict[str, Any]:
    document = json.loads((SPEC_DIR / spec["spec_file"]).read_text(encoding="utf-8"))
    if document["status"] != "APPROVED":
        raise RuntimeError(f"{spec['spec_file']}: specification is not APPROVED")
    if document["approval"]["approved_by"] != HUMAN_ACTOR_ID:
        raise RuntimeError(f"{spec['spec_file']}: governed human approval does not match")
    if document["rule_id"] != spec["rule_id"] or (
        document["specification_version"] != spec["specification_version"]
    ):
        raise RuntimeError(f"{spec['spec_file']}: unexpected rule_id/specification_version")
    if (document["catalog"]["cst"], document["catalog"]["cclasstrib"]) != (
        spec["cst"],
        spec["cclasstrib"],
    ):
        raise RuntimeError(f"{spec['spec_file']}: unexpected CST/cClassTrib")

    catalog_version_id = resolve_catalog_version_id(
        session, cclasstrib=spec["cclasstrib"], catalog_version=CURRENT_CATALOG_VERSION
    )
    specification_hash = _approval_hash(document)

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
            TaxRuleIdentityRecord.code == spec["rule_id"],
        )
    )
    if identity is None:
        identity_id = str(uuid4())
        service.create_rule_identity(
            {
                "id": identity_id,
                "code": spec["rule_id"],
                "title": spec["title"],
                "description": spec["legal_scope"],
                "is_synthetic": False,
                "created_at": now,
                "created_by": "dev-curator",
                "organization_id": ORGANIZATION_ID,
                "correlation_id": f"etapa10-{spec['rule_id'].casefold()}-identity",
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
            "approval_date": document["approval"]["approval_date"],
            "approval_evidence": document["approval"]["approval_evidence"],
        }
        content = {
            "implementation_key": spec["implementation_key"],
            "specification_id": spec["rule_id"],
            "specification_version": spec["specification_version"],
            "specification_hash": specification_hash,
            "catalog_version_id": catalog_version_id,
            "cst": spec["cst"],
            "cclasstrib": spec["cclasstrib"],
            "legal_scope": spec["legal_scope"],
        }
        service.create_rule_version(
            {
                "id": version_id,
                "rule_identity_id": identity.id,
                "version": 1,
                "jurisdiction": document["jurisdiction"],
                "legal_source_id": legal_source_id,
                "legal_device": spec["legal_device"],
                "valid_from": date.fromisoformat(document["effective_from"]),
                "valid_to": (
                    date.fromisoformat(document["effective_to"])
                    if document["effective_to"]
                    else None
                ),
                "recorded_at": now,
                "created_by": "dev-curator",
                "content": content,
                "metadata": {"rule_scope": "ZFM_P1_BLOCK", "ruleset_id": str(spec["ruleset_id"])},
                "specification_id": spec["rule_id"],
                "specification_version": spec["specification_version"],
                "specification_hash": specification_hash,
                "catalog_version_id": catalog_version_id,
                "cst_code": spec["cst"],
                "cclasstrib_code": spec["cclasstrib"],
                "approval_metadata": approval_metadata,
                "correlation_id": f"etapa10-{spec['rule_id'].casefold()}-version-v1",
            }
        )
        service.transition(
            version_id,
            target=RuleLifecycleStatus.IN_REVIEW,
            event_id=f"{spec['rule_id'].casefold()}-v1-in-review",
            occurred_at=now + timedelta(seconds=1),
            actor_id="dev-curator",
            reason="Approved specification submitted for implementation review",
            correlation_id=f"etapa10-{spec['rule_id'].casefold()}-in-review",
        )
        service.transition(
            version_id,
            target=RuleLifecycleStatus.APPROVED,
            event_id=f"{spec['rule_id'].casefold()}-v1-approved",
            occurred_at=now + timedelta(seconds=2),
            actor_id=HUMAN_ACTOR_ID,
            reason=(
                f"Implementation approved against {spec['rule_id']} "
                f"v{spec['specification_version']}"
            ),
            correlation_id=f"etapa10-{spec['rule_id'].casefold()}-approved",
        )
        service.transition(
            version_id,
            target=RuleLifecycleStatus.PUBLISHED,
            event_id=f"{spec['rule_id'].casefold()}-v1-published",
            occurred_at=now + timedelta(seconds=3),
            actor_id="dev-publisher",
            reason="ZFM P1 block real rule published",
            correlation_id=f"etapa10-{spec['rule_id'].casefold()}-published",
        )
        version = session.get(TaxRuleVersionRecord, version_id)
        assert version is not None

    document["implementation"] = {
        "tax_rule_identity_id": identity.id,
        "tax_rule_version_id": version.id,
        "implemented_at": now.date().isoformat(),
    }
    (SPEC_DIR / spec["spec_file"]).write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "rule_id": spec["rule_id"],
        "tax_rule_identity_id": identity.id,
        "tax_rule_version_id": version.id,
        "catalog_version_id": catalog_version_id,
        "ruleset_id": spec["ruleset_id"],
    }


def main() -> int:
    now = datetime.now(UTC)
    with Session(get_engine()) as session:
        _ensure_human_actor(session, now)
        legal_source_id = resolve_legal_source_id(
            session,
            official_url=LC_214_COMPILADO_URL,
            expected_content_hash=LC_214_COMPILADO_CONTENT_HASH,
        )
        deployed = [_deploy_rule(session, now, legal_source_id, spec) for spec in RULES]

        repository = SqlAlchemyGovernanceRepository(session)
        service = GovernanceService(
            repository,
            SegregationOfDutiesPolicy(enabled=True),
            organization_id=ORGANIZATION_ID,
            authenticated_user_id="dev-curator",
        )
        rulesets: list[dict[str, Any]] = []
        for offset, (spec, item) in enumerate(zip(RULES, deployed, strict=True)):
            ruleset_id = str(spec["ruleset_id"])
            if not _ruleset_exists(session, ruleset_id):
                service.create_ruleset(
                    {
                        "id": ruleset_id,
                        "name": f"IBS/CBS ZFM Pilot — {spec['rule_id']} apenas",
                        "version": "1.0.0",
                        "status": "DRAFT",
                        "created_at": now + timedelta(seconds=10 + offset * 2),
                        "created_by": "dev-curator",
                        "organization_id": ORGANIZATION_ID,
                        "correlation_id": f"etapa10-{ruleset_id.casefold()}-created",
                    },
                    [item["tax_rule_version_id"]],
                )
                service.publish_ruleset(
                    ruleset_id,
                    actor_id="dev-publisher",
                    occurred_at=now + timedelta(seconds=11 + offset * 2),
                    correlation_id=f"etapa10-{ruleset_id.casefold()}-published",
                )
            rulesets.append(repository.get_ruleset(ruleset_id))

    print(
        json.dumps(
            {
                "rules": deployed,
                "rulesets": [
                    {
                        "id": rs["id"],
                        "status": rs["status"],
                        "fingerprint": rs["fingerprint"],
                    }
                    for rs in rulesets
                ],
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
    return 0


def _ruleset_exists(session: Session, ruleset_id: str) -> bool:
    return session.get(RuleSetRecord, ruleset_id) is not None


if __name__ == "__main__":
    raise SystemExit(main())
