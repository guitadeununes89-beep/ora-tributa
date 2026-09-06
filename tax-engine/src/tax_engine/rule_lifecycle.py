from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from tax_engine.rule_models import TaxRuleVersion


class RuleLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"


ALLOWED_RULE_TRANSITIONS: Final[Mapping[RuleLifecycleStatus, frozenset[RuleLifecycleStatus]]] = (
    MappingProxyType(
        {
            RuleLifecycleStatus.DRAFT: frozenset({RuleLifecycleStatus.IN_REVIEW}),
            RuleLifecycleStatus.IN_REVIEW: frozenset(
                {RuleLifecycleStatus.APPROVED, RuleLifecycleStatus.REJECTED}
            ),
            RuleLifecycleStatus.APPROVED: frozenset({RuleLifecycleStatus.PUBLISHED}),
            RuleLifecycleStatus.PUBLISHED: frozenset(
                {RuleLifecycleStatus.SUPERSEDED, RuleLifecycleStatus.WITHDRAWN}
            ),
            RuleLifecycleStatus.REJECTED: frozenset(),
            RuleLifecycleStatus.SUPERSEDED: frozenset(),
            RuleLifecycleStatus.WITHDRAWN: frozenset(),
        }
    )
)


@dataclass(frozen=True, slots=True)
class RuleLifecycleEvent:
    event_id: str
    rule_identity_id: str
    rule_version_id: str
    version: int
    from_status: RuleLifecycleStatus
    to_status: RuleLifecycleStatus
    occurred_at: datetime
    actor_id: str
    reason: str
    related_version: int | None = None

    def __post_init__(self) -> None:
        for field_name in ("event_id", "rule_identity_id", "rule_version_id", "actor_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"Lifecycle event requires {field_name}")
        if self.version < 1:
            raise ValueError("Lifecycle event version must be positive")
        if self.occurred_at.tzinfo is None:
            raise ValueError("Lifecycle event timestamp must be timezone-aware")
        if self.to_status not in ALLOWED_RULE_TRANSITIONS[self.from_status]:
            raise ValueError(
                f"Invalid rule lifecycle transition: {self.from_status} -> {self.to_status}"
            )
        if not self.reason.strip():
            raise ValueError("Lifecycle transition requires a reason")
        if self.to_status is RuleLifecycleStatus.SUPERSEDED:
            if self.related_version is None or self.related_version <= self.version:
                raise ValueError("Supersession requires a later related version")
        elif self.related_version is not None:
            raise ValueError("Related version is only valid for supersession")


@dataclass(frozen=True, slots=True)
class RuleLifecycle:
    """Append-only lifecycle of one immutable tax-rule version."""

    rule_version: TaxRuleVersion
    events: tuple[RuleLifecycleEvent, ...] = ()

    def __post_init__(self) -> None:
        expected_status = RuleLifecycleStatus.DRAFT
        previous_time = self.rule_version.recorded_at
        event_ids: set[str] = set()

        for index, event in enumerate(self.events):
            if event.event_id in event_ids:
                raise ValueError("Lifecycle event identifiers must be unique")
            event_ids.add(event.event_id)
            if (
                event.rule_identity_id,
                event.rule_version_id,
                event.version,
            ) != (
                self.rule_version.identity.identity_id,
                self.rule_version.version_id,
                self.rule_version.version,
            ):
                raise ValueError("Lifecycle event must reference its aggregate rule version")
            if event.from_status is not expected_status:
                raise ValueError("Lifecycle event chain is not continuous")
            if event.occurred_at < previous_time:
                raise ValueError("Lifecycle events must be chronological")
            if index > 0 and event.occurred_at == previous_time:
                raise ValueError("Lifecycle events after the first must have distinct timestamps")
            expected_status = event.to_status
            previous_time = event.occurred_at

    @property
    def current_status(self) -> RuleLifecycleStatus:
        if not self.events:
            return RuleLifecycleStatus.DRAFT
        return self.events[-1].to_status

    @property
    def approved_at(self) -> datetime | None:
        return self._first_transition_time(RuleLifecycleStatus.APPROVED)

    @property
    def published_at(self) -> datetime | None:
        return self._first_transition_time(RuleLifecycleStatus.PUBLISHED)

    @property
    def superseded_at(self) -> datetime | None:
        return self._first_transition_time(RuleLifecycleStatus.SUPERSEDED)

    def _first_transition_time(self, status: RuleLifecycleStatus) -> datetime | None:
        return next(
            (event.occurred_at for event in self.events if event.to_status is status),
            None,
        )

    def status_at(self, known_at: datetime) -> RuleLifecycleStatus | None:
        if known_at.tzinfo is None:
            raise ValueError("Knowledge timestamp must be timezone-aware")
        if known_at < self.rule_version.recorded_at:
            return None

        status = RuleLifecycleStatus.DRAFT
        for event in self.events:
            if event.occurred_at > known_at:
                break
            status = event.to_status
        return status

    def is_legally_valid_on(self, legal_date: date) -> bool:
        if legal_date < self.rule_version.valid_from:
            return False
        return self.rule_version.valid_to is None or legal_date < self.rule_version.valid_to

    def is_potentially_applicable(self, *, legal_date: date, known_at: datetime) -> bool:
        return self.status_at(
            known_at
        ) is RuleLifecycleStatus.PUBLISHED and self.is_legally_valid_on(legal_date)

    def transition(
        self,
        *,
        event_id: str,
        to_status: RuleLifecycleStatus,
        occurred_at: datetime,
        actor_id: str,
        reason: str,
        related_version: int | None = None,
    ) -> RuleLifecycle:
        event = RuleLifecycleEvent(
            event_id=event_id,
            rule_identity_id=self.rule_version.identity.identity_id,
            rule_version_id=self.rule_version.version_id,
            version=self.rule_version.version,
            from_status=self.current_status,
            to_status=to_status,
            occurred_at=occurred_at,
            actor_id=actor_id,
            reason=reason,
            related_version=related_version,
        )
        return replace(self, events=(*self.events, event))
