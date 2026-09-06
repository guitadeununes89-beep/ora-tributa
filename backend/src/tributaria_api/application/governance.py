from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from tax_engine.rule_lifecycle import ALLOWED_RULE_TRANSITIONS, RuleLifecycleStatus

from tributaria_api.application.errors import ConflictError, GovernanceError
from tributaria_api.application.ports import GovernanceRepository


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def content_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SegregationOfDutiesPolicy:
    enabled: bool = False

    def approval(self, creator: str, approver: str) -> None:
        if self.enabled and creator == approver:
            raise GovernanceError("Segregation of duties forbids self-approval")

    def rule_publication(self, approver: str | None, publisher: str) -> None:
        if self.enabled and approver == publisher:
            raise GovernanceError("Approval and publication require different actors")

    def ruleset_publication(self, creators: set[str], publisher: str) -> None:
        if self.enabled and publisher in creators:
            raise GovernanceError("A rule creator cannot publish its ruleset")


class GovernanceService:
    def __init__(
        self,
        repository: GovernanceRepository,
        policy: SegregationOfDutiesPolicy,
        *,
        organization_id: str | None = None,
        authenticated_user_id: str | None = None,
    ) -> None:
        self.repository = repository
        self.policy = policy
        self.organization_id = organization_id
        self.authenticated_user_id = authenticated_user_id

    def create_legal_source(self, data: dict[str, Any]) -> dict[str, Any]:
        url = str(data["official_url"])
        if data.get("is_synthetic") is True:
            if ".invalid" not in url or not data.get("id"):
                raise GovernanceError(
                    "Synthetic sources require an explicit id and the reserved .invalid domain"
                )
        else:
            self._validate_official_source(data, url)
            if not self.organization_id:
                raise GovernanceError("Official sources require an organization")
            existing = self.repository.find_legal_source_by_hash(
                self.organization_id, data["content_hash"]
            )
            if existing is not None:
                return existing
            data = {**data, "id": data.get("id") or str(uuid4())}
        persistence = {
            key: value for key, value in data.items() if key not in {"correlation_id", "created_by"}
        }
        source = self.repository.create_legal_source(persistence)
        self._audit(data, "LEGAL_SOURCE", source["id"], "LEGAL_SOURCE_CREATED")
        self.repository.commit()
        return source

    @staticmethod
    def _validate_official_source(data: dict[str, Any], url: str) -> None:
        allowed_types = {"OFFICIAL_LEGAL_ACT", "OFFICIAL_TECHNICAL_CATALOG"}
        if data.get("source_type") not in allowed_types:
            raise GovernanceError("Unsupported official source type")
        parsed = urlparse(url)
        host = (parsed.hostname or "").casefold()
        allowed_hosts = ("planalto.gov.br", "camara.leg.br", "nfe.fazenda.gov.br")
        if parsed.scheme != "https" or not any(
            host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts
        ):
            raise GovernanceError("Official source URL is not on an approved HTTPS domain")

    def create_rule_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        synthetic = data.get("is_synthetic") is True
        if synthetic and not data["code"].startswith("TEST-"):
            raise GovernanceError("Synthetic identities require a TEST-* code")
        if not synthetic and not data["code"].startswith("RT-IBSCBS-"):
            raise GovernanceError("Real IBS/CBS identities require an RT-IBSCBS-* code")
        if not synthetic and not data.get("organization_id"):
            raise GovernanceError("Real identities require an organization")
        identity = self.repository.create_rule_identity(self._without_command_fields(data))
        self._audit(data, "TAX_RULE_IDENTITY", identity["id"], "RULE_CREATED")
        self.repository.commit()
        return identity

    def create_rule_version(self, data: dict[str, Any]) -> dict[str, Any]:
        identity = self.repository.get_rule_identity(data["rule_identity_id"])
        implementation = str(data["content"].get("implementation_key", ""))
        if identity["is_synthetic"]:
            if not implementation.startswith("SYNTHETIC_"):
                raise GovernanceError("Synthetic versions require a SYNTHETIC_* implementation")
        else:
            required = (
                "specification_id",
                "specification_version",
                "specification_hash",
                "catalog_version_id",
                "cst_code",
                "approval_metadata",
            )
            missing = [field for field in required if not data.get(field)]
            if missing or not implementation.startswith("REAL_RT_IBSCBS_"):
                raise GovernanceError("Real version provenance missing: " + ", ".join(missing))
        persistence = self._without_command_fields(data)
        persistence.update(
            lifecycle_status=RuleLifecycleStatus.DRAFT.value,
            content_hash=content_hash(data["content"]),
        )
        version = self.repository.create_rule_version(persistence)
        self._audit(data, "TAX_RULE_VERSION", version["id"], "RULE_VERSION_CREATED")
        self.repository.commit()
        return version

    def update_draft_version(
        self,
        version_id: str,
        *,
        content: dict[str, Any],
        metadata: dict[str, str],
        occurred_at: datetime,
        actor_id: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        implementation = str(content.get("implementation_key", ""))
        if not implementation.startswith("SYNTHETIC_"):
            raise GovernanceError("Draft content must remain explicitly synthetic")
        result = self.repository.update_draft_version(
            version_id,
            {"content": content, "content_hash": content_hash(content), "metadata": metadata},
        )
        self.repository.add_audit_event(
            self._audit_data(
                f"audit-draft-update-{version_id}-{occurred_at.isoformat()}",
                "TAX_RULE_VERSION",
                version_id,
                "RULE_DRAFT_UPDATED",
                occurred_at,
                actor_id,
                correlation_id,
                {"content_hash": result["content_hash"]},
            )
        )
        self.repository.commit()
        return result

    def transition(
        self,
        version_id: str,
        *,
        target: RuleLifecycleStatus,
        event_id: str,
        occurred_at: datetime,
        actor_id: str,
        reason: str,
        correlation_id: str,
        related_version: int | None = None,
    ) -> dict[str, Any]:
        version = self.repository.get_rule_version(version_id, for_update=True)
        current = RuleLifecycleStatus(version["lifecycle_status"])
        if target not in ALLOWED_RULE_TRANSITIONS[current]:
            raise ConflictError(f"Invalid lifecycle transition: {current} -> {target}")
        if not reason.strip():
            raise GovernanceError("A transition requires a reason")
        if target is RuleLifecycleStatus.APPROVED:
            self.policy.approval(version["created_by"], actor_id)
        if target is RuleLifecycleStatus.PUBLISHED:
            self._require_publication_metadata(version)
            self.policy.rule_publication(version["approved_by"], actor_id)
        projection = self._projection(target, occurred_at, actor_id, version, related_version)
        result = self.repository.transition_rule_version(
            version_id,
            expected_status=current.value,
            target_status=target.value,
            event={
                "id": event_id,
                "from_status": current.value,
                "to_status": target.value,
                "occurred_at": occurred_at,
                "actor_id": actor_id,
                "reason": reason,
                "related_version": related_version,
                "correlation_id": correlation_id,
            },
            projection=projection,
        )
        self.repository.add_audit_event(
            self._audit_data(
                f"audit-{event_id}",
                "TAX_RULE_VERSION",
                version_id,
                self._action(target),
                occurred_at,
                actor_id,
                correlation_id,
                {"from": current.value, "to": target.value},
            )
        )
        self.repository.commit()
        return result

    def create_ruleset(self, data: dict[str, Any], version_ids: list[str]) -> dict[str, Any]:
        if not version_ids or len(version_ids) != len(set(version_ids)):
            raise GovernanceError("A ruleset needs a non-empty list without duplicates")
        versions = [self.repository.get_rule_version(item) for item in version_ids]
        if any(item["lifecycle_status"] != "PUBLISHED" for item in versions):
            raise GovernanceError("Only PUBLISHED versions can enter a ruleset")
        ruleset = self.repository.create_ruleset(self._without_command_fields(data), version_ids)
        self._audit(data, "RULESET", ruleset["id"], "RULESET_CREATED")
        self.repository.commit()
        return ruleset

    def publish_ruleset(
        self, ruleset_id: str, *, actor_id: str, occurred_at: datetime, correlation_id: str
    ) -> dict[str, Any]:
        ruleset = self.repository.get_ruleset(ruleset_id, for_update=True)
        if ruleset["status"] != "DRAFT":
            raise ConflictError("Only DRAFT rulesets can be published")
        versions = [
            self.repository.get_rule_version(item, for_update=True)
            for item in ruleset["rule_version_ids"]
        ]
        if any(item["lifecycle_status"] != "PUBLISHED" for item in versions):
            raise GovernanceError("Atomic publication requires every version to be PUBLISHED")
        self.policy.ruleset_publication({item["created_by"] for item in versions}, actor_id)
        fingerprint = self.repository.load_executable_ruleset(ruleset_id).content_hash
        result = self.repository.publish_ruleset(
            ruleset_id,
            actor_id=actor_id,
            published_at=occurred_at,
            fingerprint=fingerprint,
            audit_event=self._audit_data(
                f"audit-ruleset-publish-{ruleset_id}",
                "RULESET",
                ruleset_id,
                "RULESET_PUBLISHED",
                occurred_at,
                actor_id,
                correlation_id,
                {"fingerprint": fingerprint},
            ),
        )
        self.repository.commit()
        return result

    @staticmethod
    def _without_command_fields(data: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in data.items() if key != "correlation_id"}

    def _audit(self, data: dict[str, Any], entity: str, entity_id: str, action: str) -> None:
        at = data.get("created_at", data.get("recorded_at"))
        if not isinstance(at, datetime):
            raise GovernanceError("Audit event requires a timezone-aware timestamp")
        self.repository.add_audit_event(
            self._audit_data(
                f"audit-{action.lower()}-{entity_id}",
                entity,
                entity_id,
                action,
                at,
                data["created_by"],
                data["correlation_id"],
                {"synthetic": bool(data.get("is_synthetic"))},
            )
        )

    def _audit_data(
        self,
        event_id: str,
        entity: str,
        entity_id: str,
        action: str,
        at: datetime,
        actor: str,
        correlation: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": event_id,
            "entity_type": entity,
            "entity_id": entity_id,
            "action": action,
            "occurred_at": at,
            "actor_id": actor,
            "origin": "EXPERIMENTAL_ADMIN_API",
            "correlation_id": correlation,
            "safe_metadata": metadata,
            "organization_id": self.organization_id,
            "authenticated_user_id": self.authenticated_user_id,
        }

    @staticmethod
    def _projection(
        target: RuleLifecycleStatus,
        at: datetime,
        actor: str,
        version: dict[str, Any],
        related: int | None,
    ) -> dict[str, Any]:
        if target is RuleLifecycleStatus.IN_REVIEW:
            return {"submitted_for_review_at": at}
        if target is RuleLifecycleStatus.APPROVED:
            return {"approved_at": at, "approved_by": actor}
        if target is RuleLifecycleStatus.PUBLISHED:
            return {"published_at": at, "published_by": actor}
        if target is RuleLifecycleStatus.SUPERSEDED:
            if related is None or related <= version["version"]:
                raise GovernanceError("Supersession requires a later related version")
            return {"superseded_at": at}
        if target is RuleLifecycleStatus.WITHDRAWN:
            return {"withdrawn_at": at}
        return {}

    @staticmethod
    def _require_publication_metadata(version: dict[str, Any]) -> None:
        required = (
            "legal_source_id",
            "legal_device",
            "jurisdiction",
            "valid_from",
            "content_hash",
            "approved_at",
            "approved_by",
        )
        missing = [field for field in required if not version.get(field)]
        if missing:
            raise GovernanceError(f"Publication metadata missing: {', '.join(missing)}")

    @staticmethod
    def _action(target: RuleLifecycleStatus) -> str:
        return {
            RuleLifecycleStatus.IN_REVIEW: "SUBMITTED_FOR_REVIEW",
            RuleLifecycleStatus.APPROVED: "APPROVED",
            RuleLifecycleStatus.PUBLISHED: "PUBLISHED",
            RuleLifecycleStatus.REJECTED: "REJECTED",
            RuleLifecycleStatus.SUPERSEDED: "SUPERSEDED",
            RuleLifecycleStatus.WITHDRAWN: "WITHDRAWN",
        }[target]
