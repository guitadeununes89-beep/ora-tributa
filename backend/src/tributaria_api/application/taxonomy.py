from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from tributaria_api.application.errors import ConflictError, GovernanceError


class CatalogStatus(StrEnum):
    IMPORTED = "IMPORTED"
    VALIDATED = "VALIDATED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


TRANSITIONS: dict[CatalogStatus, frozenset[CatalogStatus]] = {
    CatalogStatus.IMPORTED: frozenset({CatalogStatus.VALIDATED, CatalogStatus.FAILED}),
    CatalogStatus.VALIDATED: frozenset({CatalogStatus.IN_REVIEW, CatalogStatus.FAILED}),
    CatalogStatus.IN_REVIEW: frozenset({CatalogStatus.APPROVED, CatalogStatus.FAILED}),
    CatalogStatus.APPROVED: frozenset({CatalogStatus.PUBLISHED, CatalogStatus.FAILED}),
    CatalogStatus.PUBLISHED: frozenset(),
    CatalogStatus.FAILED: frozenset(),
}


class TaxonomyRepository(Protocol):
    def get_version(self, organization_id: str, version_id: str) -> Any: ...

    def transition(
        self,
        organization_id: str,
        version_id: str,
        target: CatalogStatus,
        *,
        actor_id: str,
        occurred_at: datetime,
        reason: str,
        correlation_id: str,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class CatalogLifecyclePolicy:
    segregation_enabled: bool = True

    def check_actor(self, version: Any, target: CatalogStatus, actor_id: str) -> None:
        if not self.segregation_enabled:
            return
        if target is CatalogStatus.APPROVED and actor_id in {
            version.imported_by,
            version.submitted_by,
        }:
            raise GovernanceError("Reviewer and approver must be different users")
        if target is CatalogStatus.PUBLISHED and actor_id in {
            version.imported_by,
            version.submitted_by,
            version.approved_by,
        }:
            raise GovernanceError("Approver and publisher must be different users")


class TaxonomyService:
    def __init__(
        self,
        repository: TaxonomyRepository,
        organization_id: str,
        policy: CatalogLifecyclePolicy,
    ) -> None:
        self.repository = repository
        self.organization_id = organization_id
        self.policy = policy

    def transition(
        self,
        version_id: str,
        target: CatalogStatus,
        *,
        actor_id: str,
        reason: str,
        correlation_id: str,
        occurred_at: datetime | None = None,
    ) -> Any:
        version = self.repository.get_version(self.organization_id, version_id)
        current = CatalogStatus(version.status)
        if target not in TRANSITIONS[current]:
            raise ConflictError(f"Invalid catalog transition: {current} -> {target}")
        if target is CatalogStatus.VALIDATED and not bool(version.import_report.get("valid")):
            raise GovernanceError("An invalid import cannot be validated")
        self.policy.check_actor(version, target, actor_id)
        return self.repository.transition(
            self.organization_id,
            version_id,
            target,
            actor_id=actor_id,
            occurred_at=occurred_at or datetime.now(UTC),
            reason=reason,
            correlation_id=correlation_id,
        )


def structured_catalog_diff(
    previous: list[dict[str, Any]], current: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Return a deterministic, field-level diff without interpreting legal meaning."""
    before = {str(item["code"]): item for item in previous}
    after = {str(item["code"]): item for item in current}
    added = [after[code] for code in sorted(after.keys() - before.keys())]
    removed = [before[code] for code in sorted(before.keys() - after.keys())]
    changed: list[dict[str, Any]] = []
    for code in sorted(before.keys() & after.keys()):
        fields = {
            field: {"before": before[code].get(field), "after": after[code].get(field)}
            for field in sorted(before[code].keys() | after[code].keys())
            if before[code].get(field) != after[code].get(field)
        }
        if fields:
            changed.append({"code": code, "fields": fields})
    return {"added": added, "removed": removed, "changed": changed}
