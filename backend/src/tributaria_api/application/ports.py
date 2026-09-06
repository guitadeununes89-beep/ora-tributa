from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any, Protocol

from tax_engine.engine import RuleSet
from tax_engine.evaluation import Evaluation


class GovernanceRepository(Protocol):
    """Transaction-bound persistence port used by application services."""

    def create_legal_source(self, data: dict[str, Any]) -> dict[str, Any]: ...

    def find_legal_source_by_hash(
        self, organization_id: str, source_hash: str
    ) -> dict[str, Any] | None: ...

    def create_rule_identity(self, data: dict[str, Any]) -> dict[str, Any]: ...

    def create_rule_version(self, data: dict[str, Any]) -> dict[str, Any]: ...

    def get_rule_identity(self, identity_id: str) -> dict[str, Any]: ...

    def get_rule_version(self, version_id: str, *, for_update: bool = False) -> dict[str, Any]: ...

    def update_draft_version(self, version_id: str, data: dict[str, Any]) -> dict[str, Any]: ...

    def transition_rule_version(
        self,
        version_id: str,
        *,
        expected_status: str,
        target_status: str,
        event: dict[str, Any],
        projection: dict[str, Any],
    ) -> dict[str, Any]: ...

    def create_ruleset(
        self, data: dict[str, Any], rule_version_ids: Sequence[str]
    ) -> dict[str, Any]: ...

    def get_ruleset(self, ruleset_id: str, *, for_update: bool = False) -> dict[str, Any]: ...

    def publish_ruleset(
        self,
        ruleset_id: str,
        *,
        actor_id: str,
        published_at: datetime,
        fingerprint: str,
        audit_event: dict[str, Any],
    ) -> dict[str, Any]: ...

    def load_executable_ruleset(self, ruleset_id: str) -> RuleSet: ...

    def list_rule_versions(self) -> list[dict[str, Any]]: ...

    def save_evaluation(
        self,
        evaluation: Evaluation,
        *,
        operation_date: date,
        facts: dict[str, Any],
        response: dict[str, Any],
        reproduced_from_id: str | None = None,
        organization_id: str | None = None,
        company_id: str | None = None,
        establishment_id: str | None = None,
        product_id: str | None = None,
        product_version_id: str | None = None,
        catalog_version_id: str | None = None,
    ) -> None: ...

    def get_evaluation(self, evaluation_id: str) -> dict[str, Any]: ...

    def add_audit_event(self, event: dict[str, Any]) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
