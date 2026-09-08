from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from tax_engine.engine import DeterministicRule, RuleSet
from tax_engine.evaluation import Evaluation
from tax_engine.multi_rule_evaluation import CandidateRuleSet, MultiRuleEvaluation
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleEvent, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion
from tax_engine.rule_scope_registry import scope_for

from tributaria_api.application.errors import ConflictError, NotFoundError
from tributaria_api.infrastructure.database.models import (
    AuditEventRecord,
    EvaluationRecord,
    EvaluationRuleVersionRecord,
    LegalSourceRecord,
    RuleLifecycleEventRecord,
    RuleSetItemRecord,
    RuleSetRecord,
    TaxRuleIdentityRecord,
    TaxRuleVersionRecord,
)
from tributaria_api.persisted_rule_registry import resolve_persisted_rule


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class SqlAlchemyGovernanceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_legal_source(self, data: dict[str, Any]) -> dict[str, Any]:
        record = LegalSourceRecord(**data)
        self._session.add(record)
        self._flush()
        return self._source_dict(record)

    def find_legal_source_by_hash(
        self, organization_id: str, source_hash: str
    ) -> dict[str, Any] | None:
        record = self._session.scalar(
            select(LegalSourceRecord).where(
                LegalSourceRecord.organization_id == organization_id,
                LegalSourceRecord.content_hash == source_hash,
            )
        )
        return self._source_dict(record) if record is not None else None

    def create_rule_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        record = TaxRuleIdentityRecord(**data)
        self._session.add(record)
        self._flush()
        return self._identity_dict(record)

    def create_rule_version(self, data: dict[str, Any]) -> dict[str, Any]:
        payload = dict(data)
        payload["rule_metadata"] = payload.pop("metadata")
        record = TaxRuleVersionRecord(**payload)
        self._session.add(record)
        self._flush()
        return self._version_dict(record)

    def get_rule_identity(self, identity_id: str) -> dict[str, Any]:
        statement = (
            select(TaxRuleIdentityRecord)
            .where(TaxRuleIdentityRecord.id == identity_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(TaxRuleIdentityRecord.versions).selectinload(
                    TaxRuleVersionRecord.legal_source
                )
            )
        )
        record = self._session.scalar(statement)
        if record is None:
            raise NotFoundError(f"Tax rule identity not found: {identity_id}")
        result = self._identity_dict(record)
        result["versions"] = [self._version_dict(version) for version in record.versions]
        return result

    def get_rule_version(self, version_id: str, *, for_update: bool = False) -> dict[str, Any]:
        statement = (
            select(TaxRuleVersionRecord)
            .where(TaxRuleVersionRecord.id == version_id)
            .options(
                selectinload(TaxRuleVersionRecord.identity),
                selectinload(TaxRuleVersionRecord.legal_source),
                selectinload(TaxRuleVersionRecord.lifecycle_events),
            )
        )
        if for_update:
            statement = statement.with_for_update()
        record = self._session.scalar(statement)
        if record is None:
            raise NotFoundError(f"Tax rule version not found: {version_id}")
        return self._version_dict(record, include_events=True)

    def update_draft_version(self, version_id: str, data: dict[str, Any]) -> dict[str, Any]:
        record = self._version_record(version_id, for_update=True)
        if record.lifecycle_status != RuleLifecycleStatus.DRAFT.value:
            raise ConflictError("Only DRAFT rule versions can be edited")
        for key, value in data.items():
            attribute = "rule_metadata" if key == "metadata" else key
            setattr(record, attribute, value)
        self._flush()
        return self._version_dict(record)

    def transition_rule_version(
        self,
        version_id: str,
        *,
        expected_status: str,
        target_status: str,
        event: dict[str, Any],
        projection: dict[str, Any],
    ) -> dict[str, Any]:
        record = self._version_record(version_id, for_update=True)
        if record.lifecycle_status != expected_status:
            raise ConflictError(
                f"Concurrent lifecycle change: expected {expected_status}, "
                f"found {record.lifecycle_status}"
            )
        event_record = RuleLifecycleEventRecord(rule_version_id=version_id, **event)
        self._session.add(event_record)
        self._flush()
        self._session.expire(record, ["lifecycle_events"])
        record.lifecycle_status = target_status
        for key, value in projection.items():
            setattr(record, key, value)
        self._flush()
        return self.get_rule_version(version_id)

    def create_ruleset(
        self, data: dict[str, Any], rule_version_ids: Sequence[str]
    ) -> dict[str, Any]:
        record = RuleSetRecord(**data)
        self._session.add(record)
        for position, version_id in enumerate(rule_version_ids, start=1):
            self._session.add(
                RuleSetItemRecord(
                    ruleset_id=record.id,
                    rule_version_id=version_id,
                    position=position,
                )
            )
        self._flush()
        return self.get_ruleset(record.id)

    def get_ruleset(self, ruleset_id: str, *, for_update: bool = False) -> dict[str, Any]:
        statement = (
            select(RuleSetRecord)
            .where(RuleSetRecord.id == ruleset_id)
            .options(selectinload(RuleSetRecord.items).selectinload(RuleSetItemRecord.rule_version))
        )
        if for_update:
            statement = statement.with_for_update()
        record = self._session.scalar(statement)
        if record is None:
            raise NotFoundError(f"Ruleset not found: {ruleset_id}")
        return self._ruleset_dict(record)

    def publish_ruleset(
        self,
        ruleset_id: str,
        *,
        actor_id: str,
        published_at: datetime,
        fingerprint: str,
        audit_event: dict[str, Any],
    ) -> dict[str, Any]:
        record = self._ruleset_record(ruleset_id, for_update=True)
        if record.status != "DRAFT":
            raise ConflictError("Only DRAFT rulesets can be published")
        record.status = "PUBLISHED"
        record.published_by = actor_id
        record.published_at = published_at
        record.fingerprint = fingerprint
        self.add_audit_event(audit_event)
        self._flush()
        return self.get_ruleset(ruleset_id)

    def load_executable_ruleset(self, ruleset_id: str) -> RuleSet:
        record = self._ruleset_record(ruleset_id)
        executable_rules = []
        for item in sorted(record.items, key=lambda candidate: candidate.position):
            version_record = self._version_record(item.rule_version_id)
            version, lifecycle = self._to_domain_rule(version_record)
            key = cast(str, version_record.content.get("implementation_key", ""))
            executable_rules.append(
                resolve_persisted_rule(
                    key,
                    version,
                    lifecycle,
                    is_synthetic=version_record.identity.is_synthetic,
                    content=version_record.content,
                )
            )
        return RuleSet(
            ruleset_id=record.id,
            version=record.version,
            rules=tuple(executable_rules),
        )

    def load_composable_rule(self, ruleset_id: str) -> DeterministicRule:
        """Load a single-rule, PUBLISHED ruleset's rule for multi-rule composition.

        Reuses the same "exactly one rule" invariant as `_queryable_rulesets`
        (ADR-0017) - a combined ruleset such as `IBSCBS-ZFM-PILOT-001` is
        rejected here, so composition can never accidentally bundle a rule
        twice under two different aggregation strategies.
        """
        persisted = self.get_ruleset(ruleset_id)
        if persisted["status"] != "PUBLISHED":
            raise ConflictError(f"Ruleset {ruleset_id} is not PUBLISHED")
        rule_version_ids = persisted["rule_version_ids"]
        if len(rule_version_ids) != 1:
            raise ConflictError(
                f"Ruleset {ruleset_id} is not composable: expected exactly one rule, "
                f"found {len(rule_version_ids)}"
            )
        executable = self.load_executable_ruleset(ruleset_id)
        return executable.rules[0]

    def load_composed_rules(self, ruleset_ids: Sequence[str]) -> CandidateRuleSet:
        rules_and_scopes = []
        for ruleset_id in ruleset_ids:
            rule = self.load_composable_rule(ruleset_id)
            rules_and_scopes.append((rule, scope_for(rule.version.identity.code)))
        composed_id = "COMPOSED:" + "+".join(sorted(ruleset_ids))
        return CandidateRuleSet(composed_id=composed_id, rules=tuple(rules_and_scopes))

    def save_composed_evaluation(
        self,
        result: MultiRuleEvaluation,
        *,
        operation_date: date,
        facts: dict[str, Any],
        response: dict[str, Any],
        ruleset_ids: Sequence[str],
        reproduced_from_id: str | None = None,
        organization_id: str | None = None,
        company_id: str | None = None,
        establishment_id: str | None = None,
        product_id: str | None = None,
        product_version_id: str | None = None,
        catalog_version_id: str | None = None,
    ) -> None:
        evaluation = result.evaluation
        record = EvaluationRecord(
            id=evaluation.evaluation_id,
            evaluated_at=evaluation.evaluated_at,
            known_at=evaluation.known_at,
            operation_date=operation_date,
            input_hash=evaluation.input_hash,
            engine_version=evaluation.engine_version,
            ruleset_id=None,
            composed_ruleset_ids=list(ruleset_ids),
            ruleset_fingerprint=evaluation.ruleset.content_hash,
            input_facts=facts,
            outcome=response,
            decision_trace=cast(list[dict[str, Any]], response["decision_trace"]),
            correlation_id=evaluation.correlation_id,
            reproduced_from_id=reproduced_from_id,
            organization_id=organization_id,
            company_id=company_id,
            establishment_id=establishment_id,
            product_id=product_id,
            product_version_id=product_version_id,
            catalog_version_id=catalog_version_id,
        )
        self._session.add(record)
        for position, reference in enumerate(evaluation.rule_versions_used, start=1):
            self._session.add(
                EvaluationRuleVersionRecord(
                    evaluation_id=evaluation.evaluation_id,
                    rule_version_id=reference.version_id,
                    position=position,
                )
            )
        self._flush()

    def list_rule_versions(self) -> list[dict[str, Any]]:
        statement = (
            select(TaxRuleVersionRecord)
            .options(
                selectinload(TaxRuleVersionRecord.identity),
                selectinload(TaxRuleVersionRecord.legal_source),
            )
            .order_by(TaxRuleIdentityRecord.code, TaxRuleVersionRecord.version)
            .join(TaxRuleVersionRecord.identity)
        )
        result: list[dict[str, Any]] = []
        for record in self._session.scalars(statement).all():
            item = self._version_dict(record)
            ruleset_ids = self._session.scalars(
                select(RuleSetRecord.id)
                .join(RuleSetItemRecord, RuleSetItemRecord.ruleset_id == RuleSetRecord.id)
                .where(RuleSetItemRecord.rule_version_id == record.id)
                .order_by(RuleSetRecord.id)
            ).all()
            item["rulesets"] = list(ruleset_ids)
            item["queryable_rulesets"] = self._queryable_rulesets(record.id)
            result.append(item)
        return result

    def _queryable_rulesets(self, rule_version_id: str) -> list[str]:
        """Published rulesets that can actually be queried for this rule alone.

        A ruleset only qualifies if it is PUBLISHED *and* contains this rule and
        no other - mirroring ADR-0017's "one explicit ruleset per rule" design.
        A published ruleset that bundles mutually-exclusive rules together
        always reports missing facts for whichever rule does not apply (see
        CLAUDE_STATUS.md, Etapa 11), so it must never be suggested as a
        candidate here even though it is technically PUBLISHED.
        """
        single_item_rulesets = (
            select(RuleSetItemRecord.ruleset_id)
            .group_by(RuleSetItemRecord.ruleset_id)
            .having(func.count() == 1)
        )
        return list(
            self._session.scalars(
                select(RuleSetRecord.id)
                .join(RuleSetItemRecord, RuleSetItemRecord.ruleset_id == RuleSetRecord.id)
                .where(
                    RuleSetItemRecord.rule_version_id == rule_version_id,
                    RuleSetRecord.status == "PUBLISHED",
                    RuleSetRecord.id.in_(single_item_rulesets),
                )
                .order_by(RuleSetRecord.id)
            ).all()
        )

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
    ) -> None:
        record = EvaluationRecord(
            id=evaluation.evaluation_id,
            evaluated_at=evaluation.evaluated_at,
            known_at=evaluation.known_at,
            operation_date=operation_date,
            input_hash=evaluation.input_hash,
            engine_version=evaluation.engine_version,
            ruleset_id=evaluation.ruleset.ruleset_id,
            ruleset_fingerprint=evaluation.ruleset.content_hash,
            input_facts=facts,
            outcome=response,
            decision_trace=cast(list[dict[str, Any]], response["decision_trace"]),
            correlation_id=evaluation.correlation_id,
            reproduced_from_id=reproduced_from_id,
            organization_id=organization_id,
            company_id=company_id,
            establishment_id=establishment_id,
            product_id=product_id,
            product_version_id=product_version_id,
            catalog_version_id=catalog_version_id,
        )
        self._session.add(record)
        for position, reference in enumerate(evaluation.rule_versions_used, start=1):
            self._session.add(
                EvaluationRuleVersionRecord(
                    evaluation_id=evaluation.evaluation_id,
                    rule_version_id=reference.version_id,
                    position=position,
                )
            )
        self._flush()

    def get_evaluation(self, evaluation_id: str) -> dict[str, Any]:
        record = self._session.get(EvaluationRecord, evaluation_id)
        if record is None:
            raise NotFoundError(f"Evaluation not found: {evaluation_id}")
        rule_version_ids = self._session.scalars(
            select(EvaluationRuleVersionRecord.rule_version_id)
            .where(EvaluationRuleVersionRecord.evaluation_id == evaluation_id)
            .order_by(EvaluationRuleVersionRecord.position)
        ).all()
        return {
            "evaluation_id": record.id,
            "evaluated_at": _aware(record.evaluated_at),
            "known_at": _aware(record.known_at),
            "operation_date": record.operation_date,
            "input_hash": record.input_hash,
            "engine_version": record.engine_version,
            "ruleset_id": record.ruleset_id,
            "ruleset_fingerprint": record.ruleset_fingerprint,
            "facts": record.input_facts,
            "outcome": record.outcome,
            "decision_trace": record.decision_trace,
            "correlation_id": record.correlation_id,
            "reproduced_from_id": record.reproduced_from_id,
            "organization_id": record.organization_id,
            "company_id": record.company_id,
            "establishment_id": record.establishment_id,
            "product_id": record.product_id,
            "product_version_id": record.product_version_id,
            "catalog_version_id": record.catalog_version_id,
            "rule_versions_used": list(rule_version_ids),
            **(
                {"composed_ruleset_ids": record.composed_ruleset_ids}
                if record.ruleset_id is None
                else {}
            ),
        }

    def add_audit_event(self, event: dict[str, Any]) -> None:
        self._session.add(AuditEventRecord(**event))

    def commit(self) -> None:
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("Database invariant rejected the operation") from exc

    def rollback(self) -> None:
        self._session.rollback()

    def _flush(self) -> None:
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("Database invariant rejected the operation") from exc

    def _version_record(self, version_id: str, *, for_update: bool = False) -> TaxRuleVersionRecord:
        statement = (
            select(TaxRuleVersionRecord)
            .where(TaxRuleVersionRecord.id == version_id)
            .options(
                selectinload(TaxRuleVersionRecord.identity),
                selectinload(TaxRuleVersionRecord.legal_source),
                selectinload(TaxRuleVersionRecord.lifecycle_events),
            )
        )
        if for_update:
            statement = statement.with_for_update()
        record = self._session.scalar(statement)
        if record is None:
            raise NotFoundError(f"Tax rule version not found: {version_id}")
        return record

    def _ruleset_record(self, ruleset_id: str, *, for_update: bool = False) -> RuleSetRecord:
        statement = (
            select(RuleSetRecord)
            .where(RuleSetRecord.id == ruleset_id)
            .options(selectinload(RuleSetRecord.items))
        )
        if for_update:
            statement = statement.with_for_update()
        record = self._session.scalar(statement)
        if record is None:
            raise NotFoundError(f"Ruleset not found: {ruleset_id}")
        return record

    @staticmethod
    def _source_dict(record: LegalSourceRecord) -> dict[str, Any]:
        return {column.name: getattr(record, column.name) for column in record.__table__.columns}

    @staticmethod
    def _identity_dict(record: TaxRuleIdentityRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "code": record.code,
            "title": record.title,
            "description": record.description,
            "is_synthetic": record.is_synthetic,
            "created_at": record.created_at,
            "created_by": record.created_by,
            "organization_id": record.organization_id,
        }

    @staticmethod
    def _version_dict(
        record: TaxRuleVersionRecord, *, include_events: bool = False
    ) -> dict[str, Any]:
        result = {
            "id": record.id,
            "rule_identity_id": record.rule_identity_id,
            "identity_code": record.identity.code if record.identity is not None else None,
            "version": record.version,
            "lifecycle_status": record.lifecycle_status,
            "jurisdiction": record.jurisdiction,
            "legal_source_id": record.legal_source_id,
            "legal_source_title": (
                record.legal_source.title if record.legal_source is not None else None
            ),
            "legal_device": record.legal_device,
            "valid_from": record.valid_from,
            "valid_to": record.valid_to,
            "recorded_at": record.recorded_at,
            "submitted_for_review_at": record.submitted_for_review_at,
            "approved_at": record.approved_at,
            "published_at": record.published_at,
            "superseded_at": record.superseded_at,
            "withdrawn_at": record.withdrawn_at,
            "created_by": record.created_by,
            "approved_by": record.approved_by,
            "published_by": record.published_by,
            "content": record.content,
            "content_hash": record.content_hash,
            "metadata": record.rule_metadata,
            "specification_id": record.specification_id,
            "specification_version": record.specification_version,
            "specification_hash": record.specification_hash,
            "catalog_version_id": record.catalog_version_id,
            "cst_code": record.cst_code,
            "cclasstrib_code": record.cclasstrib_code,
            "approval_metadata": record.approval_metadata,
            "organization_id": record.identity.organization_id,
        }
        if include_events:
            result["events"] = [
                {
                    "id": event.id,
                    "from_status": event.from_status,
                    "to_status": event.to_status,
                    "occurred_at": event.occurred_at,
                    "actor_id": event.actor_id,
                    "reason": event.reason,
                    "related_version": event.related_version,
                    "correlation_id": event.correlation_id,
                }
                for event in record.lifecycle_events
            ]
        return result

    @staticmethod
    def _ruleset_dict(record: RuleSetRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "name": record.name,
            "version": record.version,
            "status": record.status,
            "created_at": record.created_at,
            "created_by": record.created_by,
            "published_at": record.published_at,
            "published_by": record.published_by,
            "fingerprint": record.fingerprint,
            "organization_id": record.organization_id,
            "rule_version_ids": [
                item.rule_version_id
                for item in sorted(record.items, key=lambda item: item.position)
            ],
        }

    @staticmethod
    def _to_domain_rule(
        record: TaxRuleVersionRecord,
    ) -> tuple[TaxRuleVersion, RuleLifecycle]:
        if record.legal_source is None:
            raise ConflictError("Rule version has no legal source")
        source = record.legal_source
        legal_source = LegalSource(
            source_id=source.id,
            act_type=source.source_type,
            number=source.number,
            year=source.year,
            issuing_authority=source.issuing_authority,
            device=record.legal_device,
            official_uri=source.official_url,
            published_on=source.publication_date,
            notes=source.notes,
            integrity_hash=source.content_hash,
        )
        content = json.dumps(
            record.content, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
        version = TaxRuleVersion(
            version_id=record.id,
            identity=TaxRuleIdentity(
                identity_id=record.identity.id,
                code=record.identity.code,
                title=record.identity.title,
            ),
            version=record.version,
            jurisdiction=record.jurisdiction,
            legal_source=legal_source,
            legal_device=record.legal_device,
            valid_from=record.valid_from,
            valid_to=record.valid_to,
            recorded_at=_aware(record.recorded_at),
            created_by=record.created_by,
            origin=(
                "PERSISTED_SYNTHETIC_CATALOG"
                if record.identity.is_synthetic
                else "PERSISTED_GOVERNED_REAL_RULE"
            ),
            content=content,
            content_hash=record.content_hash,
            audit_metadata=tuple(
                sorted((str(key), str(value)) for key, value in record.rule_metadata.items())
            ),
        )
        events = tuple(
            RuleLifecycleEvent(
                event_id=event.id,
                rule_identity_id=record.rule_identity_id,
                rule_version_id=record.id,
                version=record.version,
                from_status=RuleLifecycleStatus(event.from_status),
                to_status=RuleLifecycleStatus(event.to_status),
                occurred_at=_aware(event.occurred_at),
                actor_id=event.actor_id,
                reason=event.reason,
                related_version=event.related_version,
            )
            for event in sorted(
                record.lifecycle_events, key=lambda candidate: candidate.occurred_at
            )
        )
        return version, RuleLifecycle(rule_version=version, events=events)
