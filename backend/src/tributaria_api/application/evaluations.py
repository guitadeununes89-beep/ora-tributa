from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from tax_engine.engine import TaxEngine
from tax_engine.evaluation import (
    ClassificationOutcome,
    Evaluation,
    EvaluationContext,
    FactSet,
)

from tributaria_api.application.errors import ConflictError, NotFoundError
from tributaria_api.application.ports import GovernanceRepository


class EvaluationService:
    def __init__(
        self,
        repository: GovernanceRepository,
        *,
        engine_version: str,
        organization_id: str | None = None,
        company_id: str | None = None,
        establishment_id: str | None = None,
        product_id: str | None = None,
        product_version_id: str | None = None,
        catalog_version_id: str | None = None,
        candidate_validator: Callable[[ClassificationOutcome], None] | None = None,
    ) -> None:
        self.repository = repository
        self.engine = TaxEngine(engine_version=engine_version)
        self.organization_id = organization_id
        self.company_id = company_id
        self.establishment_id = establishment_id
        self.product_id = product_id
        self.product_version_id = product_version_id
        self.catalog_version_id = catalog_version_id
        self.candidate_validator = candidate_validator

    def evaluate(
        self,
        *,
        ruleset_id: str,
        facts: FactSet,
        context: EvaluationContext,
        facts_document: dict[str, Any],
        reproduced_from_id: str | None = None,
    ) -> dict[str, Any]:
        persisted = self.repository.get_ruleset(ruleset_id)
        if (
            self.organization_id is not None
            and persisted.get("organization_id") != self.organization_id
        ):
            raise NotFoundError("Ruleset not found")
        if persisted["status"] != "PUBLISHED":
            raise ConflictError("Evaluations require a PUBLISHED ruleset")
        ruleset = self.repository.load_executable_ruleset(ruleset_id)
        if ruleset.content_hash != persisted["fingerprint"]:
            raise ConflictError("Persisted ruleset fingerprint verification failed")
        evaluation = self.engine.evaluate(facts=facts, context=context, ruleset=ruleset)
        if self.candidate_validator is not None:
            self.candidate_validator(evaluation.outcome)
        document = evaluation_document(evaluation)
        self.repository.save_evaluation(
            evaluation,
            operation_date=facts.operation_date,
            facts=facts_document,
            response=document,
            reproduced_from_id=reproduced_from_id,
            organization_id=self.organization_id,
            company_id=self.company_id,
            establishment_id=self.establishment_id,
            product_id=self.product_id,
            product_version_id=self.product_version_id,
            catalog_version_id=self.catalog_version_id,
        )
        self.repository.commit()
        return document

    def reproduce(
        self,
        original_id: str,
        *,
        new_evaluation_id: str,
        evaluated_at: datetime,
        correlation_id: str,
    ) -> dict[str, Any]:
        original = self.repository.get_evaluation(original_id)
        facts = fact_set_from_document(original["facts"])
        document = self.evaluate(
            ruleset_id=original["ruleset_id"],
            facts=facts,
            context=EvaluationContext(
                evaluation_id=new_evaluation_id,
                evaluated_at=evaluated_at,
                known_at=original["known_at"],
                correlation_id=correlation_id,
            ),
            facts_document=original["facts"],
            reproduced_from_id=original_id,
        )
        if (
            document["input_hash"] != original["input_hash"]
            or document["ruleset"]["content_hash"] != original["ruleset_fingerprint"]
            or document["status"] != original["outcome"]["status"]
            or document["candidates"] != original["outcome"]["candidates"]
        ):
            raise ConflictError("Reproduction diverged from the archived deterministic result")
        document["reproduced_from_id"] = original_id
        return document


def fact_set_from_document(data: dict[str, Any]) -> FactSet:
    operation_date = data["operation_date"]
    return FactSet(
        operation_date=(
            date.fromisoformat(operation_date)
            if isinstance(operation_date, str)
            else operation_date
        ),
        product_id=data.get("product_id"),
        product_version_id=data.get("product_version_id"),
        product_code=data.get("product_code"),
        product_description=data.get("product_description"),
        ncm=data.get("ncm"),
        nbs=data.get("nbs"),
        operation_type=data.get("operation_type"),
        origin_state=data.get("origin_state"),
        destination_state=data.get("destination_state"),
        taxpayer_regime=data.get("taxpayer_regime"),
        recipient_type=data.get("recipient_type"),
        product_attributes=data.get("product_attributes", {}),
    )


def evaluation_document(evaluation: Evaluation) -> dict[str, Any]:
    outcome = evaluation.outcome

    def rule(reference: Any) -> dict[str, Any]:
        return {
            "identity_id": reference.identity_id,
            "rule_code": reference.rule_code,
            "version_id": reference.version_id,
            "version": reference.version,
            "content_hash": reference.content_hash,
        }

    def condition(item: Any) -> dict[str, Any]:
        return {
            "condition_id": item.condition_id,
            "description": item.description,
            "fact_name": item.fact_name,
            "status": item.status.value,
            "expected_value": item.expected_value,
            "observed_value": item.observed_value,
        }

    def legal_source(source: Any) -> dict[str, Any]:
        return {
            "source_id": source.source_id,
            "act_type": source.act_type,
            "number": source.number,
            "year": source.year,
            "issuing_authority": source.issuing_authority,
            "device": source.device,
            "official_uri": source.official_uri,
            "published_on": (
                source.published_on.isoformat() if source.published_on is not None else None
            ),
            "notes": source.notes,
            "integrity_hash": source.integrity_hash,
        }

    return {
        "evaluation_id": evaluation.evaluation_id,
        "evaluated_at": evaluation.evaluated_at.isoformat(),
        "known_at": evaluation.known_at.isoformat(),
        "correlation_id": evaluation.correlation_id,
        "input_hash": evaluation.input_hash,
        "engine_version": evaluation.engine_version,
        "ruleset": {
            "ruleset_id": evaluation.ruleset.ruleset_id,
            "version": evaluation.ruleset.version,
            "content_hash": evaluation.ruleset.content_hash,
        },
        "status": outcome.status.value,
        "candidates": list(outcome.candidates),
        "tax_candidates": [
            {
                "catalog_version_id": item.catalog_version_id,
                "cst": item.cst_code,
                "cclasstrib": item.classification_code,
                "support": item.support.value,
                "rule": rule(item.rule),
                "conditions": [condition(value) for value in item.conditions],
                "missing_facts": list(item.missing_facts),
                "legal_references": [legal_source(source) for source in item.legal_sources],
            }
            for item in outcome.tax_candidates
        ],
        "missing_facts": list(outcome.missing_facts),
        "rules_evaluated": [rule(item) for item in outcome.evaluated_rules],
        "rules_applicable": [rule(item) for item in outcome.applicable_rules],
        "conditions_satisfied": [condition(item) for item in outcome.satisfied_conditions],
        "conditions_not_satisfied": [condition(item) for item in outcome.unsatisfied_conditions],
        "legal_references": [legal_source(source) for source in outcome.legal_sources],
        "decision_trace": [
            {
                "sequence": step.sequence,
                "phase": step.phase.value,
                "description": step.description,
                "outcome": step.outcome,
                "rule": rule(step.rule) if step.rule is not None else None,
                "conditions": [condition(item) for item in step.conditions],
                "details": dict(step.details),
            }
            for step in outcome.trace
        ],
    }

