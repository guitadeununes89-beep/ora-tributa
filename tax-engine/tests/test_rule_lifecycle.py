from datetime import UTC, date, datetime

import pytest
from tax_engine.rule_lifecycle import (
    RuleLifecycle,
    RuleLifecycleEvent,
    RuleLifecycleStatus,
)
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion


def at(day: int) -> datetime:
    return datetime(2029, 1, day, 12, tzinfo=UTC)


def version(*, number: int = 1) -> TaxRuleVersion:
    return TaxRuleVersion.create(
        version_id=f"synthetic-v{number}",
        identity=TaxRuleIdentity(
            identity_id="synthetic-identity",
            code="SYNTHETIC-001",
            title="Synthetic rule",
        ),
        version=number,
        jurisdiction="SYNTHETIC",
        legal_source=LegalSource(
            source_id="synthetic-source",
            act_type="SYNTHETIC_ACT",
            number="TEST-001",
            year=2099,
            issuing_authority="SYNTHETIC AUTHORITY",
            device="SYNTHETIC DEVICE",
            official_uri="https://example.invalid/source",
            notes="Not a real legal source.",
        ),
        legal_device="SYNTHETIC DEVICE",
        valid_from=date(2030, 1, 1),
        valid_to=date(2040, 1, 1),
        recorded_at=at(1),
        created_by="synthetic-test",
        origin="UNIT_TEST",
        content=f"SYNTHETIC CONTENT VERSION {number}",
        audit_metadata=(("synthetic", "true"),),
    )


def lifecycle(*, number: int = 1) -> RuleLifecycle:
    return RuleLifecycle(rule_version=version(number=number))


def publish(subject: RuleLifecycle) -> RuleLifecycle:
    return (
        subject.transition(
            event_id="submit",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=at(2),
            actor_id="author-id",
            reason="Submitted for synthetic review",
        )
        .transition(
            event_id="approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=at(3),
            actor_id="reviewer-id",
            reason="Synthetic review approved",
        )
        .transition(
            event_id="publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=at(4),
            actor_id="publisher-id",
            reason="Synthetic snapshot published",
        )
    )


def test_transition_returns_new_append_only_aggregate() -> None:
    draft = lifecycle()
    review = draft.transition(
        event_id="submit",
        to_status=RuleLifecycleStatus.IN_REVIEW,
        occurred_at=at(2),
        actor_id="author-id",
        reason="Submitted for synthetic review",
    )

    assert draft.current_status is RuleLifecycleStatus.DRAFT
    assert draft.events == ()
    assert review.current_status is RuleLifecycleStatus.IN_REVIEW
    assert len(review.events) == 1


def test_rule_cannot_be_published_without_review_and_approval() -> None:
    with pytest.raises(ValueError, match="Invalid rule lifecycle transition"):
        lifecycle().transition(
            event_id="publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=at(2),
            actor_id="publisher-id",
            reason="Invalid direct publication attempt",
        )


def test_every_transition_requires_a_reason() -> None:
    with pytest.raises(ValueError, match="requires a reason"):
        lifecycle().transition(
            event_id="submit",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=at(2),
            actor_id="author-id",
            reason="",
        )


def test_supersession_requires_a_later_version() -> None:
    published = publish(lifecycle(number=2))

    with pytest.raises(ValueError, match="later related version"):
        published.transition(
            event_id="supersede",
            to_status=RuleLifecycleStatus.SUPERSEDED,
            occurred_at=at(5),
            actor_id="publisher-id",
            reason="Synthetic supersession",
            related_version=2,
        )


def test_lifecycle_rejects_events_for_another_rule_version() -> None:
    subject = lifecycle()
    foreign_event = RuleLifecycleEvent(
        event_id="submit",
        rule_identity_id="another-rule",
        rule_version_id=subject.rule_version.version_id,
        version=1,
        from_status=RuleLifecycleStatus.DRAFT,
        to_status=RuleLifecycleStatus.IN_REVIEW,
        occurred_at=at(2),
        actor_id="author-id",
        reason="Submitted for synthetic review",
    )

    with pytest.raises(ValueError, match="aggregate rule version"):
        RuleLifecycle(rule_version=subject.rule_version, events=(foreign_event,))


def test_applicability_uses_legal_and_system_time() -> None:
    published = publish(lifecycle())
    superseded = published.transition(
        event_id="supersede",
        to_status=RuleLifecycleStatus.SUPERSEDED,
        occurred_at=at(6),
        actor_id="publisher-id",
        reason="Replaced by a later synthetic snapshot",
        related_version=2,
    )

    assert not superseded.is_potentially_applicable(legal_date=date(2030, 1, 1), known_at=at(3))
    assert superseded.is_potentially_applicable(legal_date=date(2030, 1, 1), known_at=at(5))
    assert not superseded.is_potentially_applicable(legal_date=date(2030, 1, 1), known_at=at(6))
    assert not superseded.is_potentially_applicable(legal_date=date(2040, 1, 1), known_at=at(5))


def test_system_timestamps_are_derived_from_events() -> None:
    published = publish(lifecycle())
    superseded = published.transition(
        event_id="supersede",
        to_status=RuleLifecycleStatus.SUPERSEDED,
        occurred_at=at(6),
        actor_id="publisher-id",
        reason="Replaced by a later synthetic snapshot",
        related_version=2,
    )

    assert superseded.approved_at == at(3)
    assert superseded.published_at == at(4)
    assert superseded.superseded_at == at(6)


def test_status_is_unknown_before_snapshot_was_recorded() -> None:
    assert lifecycle().status_at(datetime(2028, 12, 31, tzinfo=UTC)) is None
