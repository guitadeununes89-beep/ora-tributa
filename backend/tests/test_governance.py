from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from tax_engine.evaluation import EvaluationContext, FactSet
from tax_engine.rule_lifecycle import RuleLifecycleStatus
from tributaria_api.application.errors import ConflictError, GovernanceError
from tributaria_api.application.evaluations import EvaluationService
from tributaria_api.application.governance import GovernanceService, SegregationOfDutiesPolicy
from tributaria_api.infrastructure.database.models import Base, RuleSetRecord
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository

AT = datetime(2040, 1, 1, 12, tzinfo=UTC)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def sqlite_functions(connection: object, _: object) -> None:
        connection.create_function("char_length", 1, len)  # type: ignore[attr-defined]

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as value:
        yield value


def service(session: Session, *, segregation: bool = False) -> GovernanceService:
    return GovernanceService(
        SqlAlchemyGovernanceRepository(session),
        SegregationOfDutiesPolicy(enabled=segregation),
    )


def source_data() -> dict[str, object]:
    return {
        "id": "TEST-SOURCE-001",
        "source_type": "SYNTHETIC_TEST_ACT",
        "number": "TEST-001",
        "year": 2099,
        "issuing_authority": "SYNTHETIC AUTHORITY",
        "title": "Synthetic source",
        "official_url": "https://example.invalid/TEST-SOURCE-001",
        "publication_date": date(2099, 1, 1),
        "jurisdiction": "SYNTHETIC",
        "notes": "Fictitious",
        "content_hash": "a" * 64,
        "is_synthetic": True,
        "created_at": AT,
        "created_by": "author",
        "correlation_id": "corr-source",
    }


def create_version(
    app: GovernanceService,
    *,
    identity_id: str = "TEST-RULE-001",
    version_id: str = "TEST-RULE-001-V1",
    implementation: str = "SYNTHETIC_RULE_A_V1",
    legal_source_id: str | None = "TEST-SOURCE-001",
) -> dict[str, object]:
    app.create_rule_identity(
        {
            "id": identity_id,
            "code": identity_id,
            "title": "Synthetic rule",
            "description": "Fictitious",
            "is_synthetic": True,
            "created_at": AT,
            "created_by": "author",
            "correlation_id": f"corr-{identity_id}",
        }
    )
    return app.create_rule_version(
        {
            "id": version_id,
            "rule_identity_id": identity_id,
            "version": 1,
            "jurisdiction": "SYNTHETIC",
            "legal_source_id": legal_source_id,
            "legal_device": "SYNTHETIC DEVICE",
            "valid_from": date(2000, 1, 1),
            "valid_to": date(2100, 1, 1),
            "recorded_at": AT,
            "created_by": "author",
            "content": {"implementation_key": implementation},
            "metadata": {"synthetic": "true"},
            "correlation_id": f"corr-{version_id}",
        }
    )


def transition_to_published(app: GovernanceService, version_id: str) -> None:
    actors = (
        (RuleLifecycleStatus.IN_REVIEW, "author"),
        (RuleLifecycleStatus.APPROVED, "reviewer"),
        (RuleLifecycleStatus.PUBLISHED, "publisher"),
    )
    for index, (target, actor) in enumerate(actors, start=1):
        app.transition(
            version_id,
            target=target,
            event_id=f"event-{version_id}-{index}",
            occurred_at=AT + timedelta(days=index),
            actor_id=actor,
            reason="Synthetic workflow test",
            correlation_id=f"corr-transition-{index}",
        )


def test_full_lifecycle_is_append_only_and_segregated(session: Session) -> None:
    app = service(session, segregation=True)
    app.create_legal_source(source_data())
    created = create_version(app)
    updated = app.update_draft_version(
        "TEST-RULE-001-V1",
        content={"implementation_key": "SYNTHETIC_RULE_A_V1", "draft_revision": "2"},
        metadata={"synthetic": "true"},
        occurred_at=AT + timedelta(hours=1),
        actor_id="author",
        correlation_id="corr-draft-update",
    )
    assert updated["content_hash"] != created["content_hash"]
    transition_to_published(app, "TEST-RULE-001-V1")
    version = SqlAlchemyGovernanceRepository(session).get_rule_version("TEST-RULE-001-V1")
    assert version["lifecycle_status"] == "PUBLISHED"
    assert [event["to_status"] for event in version["events"]] == [
        "IN_REVIEW",
        "APPROVED",
        "PUBLISHED",
    ]
    assert version["approved_by"] == "reviewer"
    assert version["published_by"] == "publisher"


def test_invalid_transition_and_self_approval_are_rejected(session: Session) -> None:
    app = service(session, segregation=True)
    app.create_legal_source(source_data())
    create_version(app)
    with pytest.raises(ConflictError, match="Invalid"):
        app.transition(
            "TEST-RULE-001-V1",
            target=RuleLifecycleStatus.PUBLISHED,
            event_id="invalid",
            occurred_at=AT + timedelta(days=1),
            actor_id="author",
            reason="Invalid",
            correlation_id="corr-invalid",
        )
    app.transition(
        "TEST-RULE-001-V1",
        target=RuleLifecycleStatus.IN_REVIEW,
        event_id="submit",
        occurred_at=AT + timedelta(days=1),
        actor_id="author",
        reason="Submit",
        correlation_id="corr-submit",
    )
    with pytest.raises(GovernanceError, match="self-approval"):
        app.transition(
            "TEST-RULE-001-V1",
            target=RuleLifecycleStatus.APPROVED,
            event_id="approve",
            occurred_at=AT + timedelta(days=2),
            actor_id="author",
            reason="Approve",
            correlation_id="corr-approve",
        )


def test_publication_without_source_and_published_edit_are_rejected(session: Session) -> None:
    app = service(session)
    create_version(app, legal_source_id=None)
    app.transition(
        "TEST-RULE-001-V1",
        target=RuleLifecycleStatus.IN_REVIEW,
        event_id="submit",
        occurred_at=AT + timedelta(days=1),
        actor_id="author",
        reason="Submit",
        correlation_id="corr-submit",
    )
    app.transition(
        "TEST-RULE-001-V1",
        target=RuleLifecycleStatus.APPROVED,
        event_id="approve",
        occurred_at=AT + timedelta(days=2),
        actor_id="reviewer",
        reason="Approve",
        correlation_id="corr-approve",
    )
    with pytest.raises(GovernanceError, match="legal_source_id"):
        app.transition(
            "TEST-RULE-001-V1",
            target=RuleLifecycleStatus.PUBLISHED,
            event_id="publish",
            occurred_at=AT + timedelta(days=3),
            actor_id="publisher",
            reason="Publish",
            correlation_id="corr-publish",
        )


def test_ruleset_evaluation_and_reproduction(session: Session) -> None:
    app = service(session)
    app.create_legal_source(source_data())
    created = create_version(app)
    updated = app.update_draft_version(
        "TEST-RULE-001-V1",
        content={"implementation_key": "SYNTHETIC_RULE_A_V1", "draft_revision": "2"},
        metadata={"synthetic": "true"},
        occurred_at=AT + timedelta(hours=1),
        actor_id="author",
        correlation_id="corr-draft-update",
    )
    assert updated["content_hash"] != created["content_hash"]
    transition_to_published(app, "TEST-RULE-001-V1")
    ruleset = app.create_ruleset(
        {
            "id": "TEST-RULESET-001",
            "name": "Synthetic snapshot",
            "version": "1",
            "status": "DRAFT",
            "created_at": AT + timedelta(days=4),
            "created_by": "curator",
            "published_at": None,
            "published_by": None,
            "fingerprint": None,
            "correlation_id": "corr-ruleset",
        },
        ["TEST-RULE-001-V1"],
    )
    assert ruleset["status"] == "DRAFT"
    published = app.publish_ruleset(
        "TEST-RULESET-001",
        actor_id="ruleset-publisher",
        occurred_at=AT + timedelta(days=5),
        correlation_id="corr-ruleset-publish",
    )
    assert published["status"] == "PUBLISHED"
    assert len(published["fingerprint"]) == 64
    repository = SqlAlchemyGovernanceRepository(session)
    with pytest.raises(ConflictError, match="DRAFT"):
        repository.update_draft_version(
            "TEST-RULE-001-V1", {"content": {"implementation_key": "CHANGED"}}
        )
    app.transition(
        "TEST-RULE-001-V1",
        target=RuleLifecycleStatus.WITHDRAWN,
        event_id="withdraw-after-ruleset",
        occurred_at=AT + timedelta(days=6),
        actor_id="publisher",
        reason="Synthetic historical test",
        correlation_id="corr-withdraw",
    )
    with pytest.raises(ConflictError, match="DRAFT"):
        app.publish_ruleset(
            "TEST-RULESET-001",
            actor_id="other",
            occurred_at=AT + timedelta(days=6),
            correlation_id="corr-again",
        )

    evaluation_service = EvaluationService(repository, engine_version="test-persisted")
    facts_document = {
        "operation_date": "2040-06-15",
        "product_code": "SYNTHETIC-PRODUCT",
        "operation_type": "B",
        "product_attributes": {"synthetic_attribute_x": "A", "synthetic_attribute_z": "PRESENT"},
    }
    result = evaluation_service.evaluate(
        ruleset_id="TEST-RULESET-001",
        facts=FactSet(
            operation_date=date(2040, 6, 15),
            product_code="SYNTHETIC-PRODUCT",
            operation_type="B",
            product_attributes=facts_document["product_attributes"],
        ),
        context=EvaluationContext(
            evaluation_id="TEST-EVALUATION-001",
            evaluated_at=AT + timedelta(days=7),
            known_at=AT + timedelta(days=5),
            correlation_id="corr-evaluation",
        ),
        facts_document=facts_document,
    )
    assert result["status"] == "CONCLUSIVO"
    reproduced = evaluation_service.reproduce(
        "TEST-EVALUATION-001",
        new_evaluation_id="TEST-EVALUATION-002",
        evaluated_at=AT + timedelta(days=8),
        correlation_id="corr-reproduction",
    )
    assert reproduced["input_hash"] == result["input_hash"]
    assert reproduced["candidates"] == result["candidates"]


def test_non_published_member_rolls_back_ruleset_creation(session: Session) -> None:
    app = service(session)
    app.create_legal_source(source_data())
    create_version(app)
    with pytest.raises(GovernanceError, match="PUBLISHED"):
        app.create_ruleset(
            {
                "id": "TEST-RULESET-INVALID",
                "name": "Invalid",
                "version": "1",
                "status": "DRAFT",
                "created_at": AT,
                "created_by": "curator",
                "published_at": None,
                "published_by": None,
                "fingerprint": None,
                "correlation_id": "corr-invalid-ruleset",
            },
            ["TEST-RULE-001-V1"],
        )
    assert (
        session.scalar(select(RuleSetRecord).where(RuleSetRecord.id == "TEST-RULESET-INVALID"))
        is None
    )


def test_identity_accepts_a_new_immutable_version(session: Session) -> None:
    app = service(session)
    app.create_legal_source(source_data())
    create_version(app)
    second = app.create_rule_version(
        {
            "id": "TEST-RULE-001-V2",
            "rule_identity_id": "TEST-RULE-001",
            "version": 2,
            "jurisdiction": "SYNTHETIC",
            "legal_source_id": "TEST-SOURCE-001",
            "legal_device": "SYNTHETIC DEVICE",
            "valid_from": date(2050, 1, 1),
            "valid_to": date(2100, 1, 1),
            "recorded_at": AT + timedelta(days=10),
            "created_by": "author",
            "content": {"implementation_key": "SYNTHETIC_RULE_A_V1", "revision": "2"},
            "metadata": {"synthetic": "true"},
            "correlation_id": "corr-version-2",
        }
    )
    identity = SqlAlchemyGovernanceRepository(session).get_rule_identity("TEST-RULE-001")
    assert second["version"] == 2
    assert {item["id"] for item in identity["versions"]} == {"TEST-RULE-001-V1", "TEST-RULE-001-V2"}


def test_invalid_ruleset_publication_rolls_back_atomically(session: Session) -> None:
    app = service(session)
    app.create_legal_source(source_data())
    created = create_version(app)
    updated = app.update_draft_version(
        "TEST-RULE-001-V1",
        content={"implementation_key": "SYNTHETIC_RULE_A_V1", "draft_revision": "2"},
        metadata={"synthetic": "true"},
        occurred_at=AT + timedelta(hours=1),
        actor_id="author",
        correlation_id="corr-draft-update",
    )
    assert updated["content_hash"] != created["content_hash"]
    transition_to_published(app, "TEST-RULE-001-V1")
    app.create_ruleset(
        {
            "id": "TEST-RULESET-ROLLBACK",
            "name": "Rollback snapshot",
            "version": "1",
            "status": "DRAFT",
            "created_at": AT + timedelta(days=4),
            "created_by": "curator",
            "published_at": None,
            "published_by": None,
            "fingerprint": None,
            "correlation_id": "corr-ruleset-rollback",
        },
        ["TEST-RULE-001-V1"],
    )
    app.transition(
        "TEST-RULE-001-V1",
        target=RuleLifecycleStatus.WITHDRAWN,
        event_id="withdraw-before-ruleset",
        occurred_at=AT + timedelta(days=5),
        actor_id="publisher",
        reason="Synthetic rollback test",
        correlation_id="corr-withdraw-before-ruleset",
    )
    with pytest.raises(GovernanceError, match="every version"):
        app.publish_ruleset(
            "TEST-RULESET-ROLLBACK",
            actor_id="ruleset-publisher",
            occurred_at=AT + timedelta(days=6),
            correlation_id="corr-invalid-publication",
        )
    persisted = SqlAlchemyGovernanceRepository(session).get_ruleset("TEST-RULESET-ROLLBACK")
    assert persisted["status"] == "DRAFT"
    assert persisted["fingerprint"] is None
