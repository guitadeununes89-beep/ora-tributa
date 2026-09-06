from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from tributaria_api.application.errors import ConflictError, GovernanceError
from tributaria_api.application.taxonomy import (
    CatalogLifecyclePolicy,
    CatalogStatus,
    TaxonomyService,
    structured_catalog_diff,
)


@dataclass
class Version:
    status: str = "IMPORTED"
    imported_by: str = "curator"
    submitted_by: str | None = None
    approved_by: str | None = None
    import_report: dict[str, Any] | None = None


class Repository:
    def __init__(self, version: Version) -> None:
        self.version = version

    def get_version(self, organization_id: str, version_id: str) -> Version:
        return self.version

    def transition(
        self, organization_id: str, version_id: str, target: CatalogStatus, **event: Any
    ) -> Version:
        self.version.status = target
        if target is CatalogStatus.IN_REVIEW:
            self.version.submitted_by = event["actor_id"]
        if target is CatalogStatus.APPROVED:
            self.version.approved_by = event["actor_id"]
        return self.version


def service(version: Version) -> TaxonomyService:
    return TaxonomyService(Repository(version), "org", CatalogLifecyclePolicy(True))


def transition(app: TaxonomyService, target: CatalogStatus, actor: str) -> Version:
    return app.transition(
        "version",
        target,
        actor_id=actor,
        reason="reviewed",
        correlation_id="test",
        occurred_at=datetime.now(UTC),
    )


def test_catalog_requires_ordered_human_lifecycle_and_segregation() -> None:
    version = Version(import_report={"valid": True})
    app = service(version)

    transition(app, CatalogStatus.VALIDATED, "curator")
    transition(app, CatalogStatus.IN_REVIEW, "curator")
    with pytest.raises(GovernanceError):
        transition(app, CatalogStatus.APPROVED, "curator")
    transition(app, CatalogStatus.APPROVED, "approver")
    with pytest.raises(GovernanceError):
        transition(app, CatalogStatus.PUBLISHED, "approver")
    assert transition(app, CatalogStatus.PUBLISHED, "publisher").status == "PUBLISHED"


def test_invalid_import_and_skipped_state_fail_closed() -> None:
    with pytest.raises(GovernanceError):
        transition(
            service(Version(import_report={"valid": False})), CatalogStatus.VALIDATED, "curator"
        )
    with pytest.raises(ConflictError):
        transition(
            service(Version(import_report={"valid": True})), CatalogStatus.PUBLISHED, "publisher"
        )


def test_structured_diff_is_deterministic_and_non_interpretive() -> None:
    result = structured_catalog_diff(
        [{"code": "000001", "name": "Antes", "cst": "000"}],
        [
            {"code": "000001", "name": "Depois", "cst": "000"},
            {"code": "000002", "name": "Nova", "cst": "200"},
        ],
    )

    assert [item["code"] for item in result["added"]] == ["000002"]
    assert result["removed"] == []
    assert result["changed"] == [
        {"code": "000001", "fields": {"name": {"before": "Antes", "after": "Depois"}}}
    ]
