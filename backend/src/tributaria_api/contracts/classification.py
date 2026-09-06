from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from tax_engine.evaluation import (
    ClassificationStatus,
    ConditionResult,
    ConditionStatus,
    Evaluation,
    EvaluationContext,
    FactSet,
    TracePhase,
)
from tax_engine.rule_models import LegalSource, RuleVersionRef


class FactSetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_date: date
    product_id: str | None = None
    product_version_id: str | None = None
    product_code: str | None = None
    product_description: str | None = None
    ncm: str | None = None
    nbs: str | None = None
    operation_type: str | None = None
    origin_state: str | None = None
    destination_state: str | None = None
    taxpayer_regime: str | None = None
    recipient_type: str | None = None
    product_attributes: dict[str, str] = Field(default_factory=dict)

    @field_validator("product_attributes")
    @classmethod
    def validate_attribute_names(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not key.strip() for key in value):
            raise ValueError("product attribute names must be non-empty")
        return value

    def to_domain(self) -> FactSet:
        return FactSet(
            operation_date=self.operation_date,
            product_id=self.product_id,
            product_version_id=self.product_version_id,
            product_code=self.product_code,
            product_description=self.product_description,
            ncm=self.ncm,
            nbs=self.nbs,
            operation_type=self.operation_type,
            origin_state=self.origin_state,
            destination_state=self.destination_state,
            taxpayer_regime=self.taxpayer_regime,
            recipient_type=self.recipient_type,
            product_attributes=self.product_attributes,
        )


class ClassificationEvaluationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "evaluation_id": "eval-synthetic-001",
                "evaluated_at": "2040-06-15T12:00:00Z",
                "known_at": "2040-06-15T12:00:00Z",
                "correlation_id": "corr-synthetic-001",
                "facts": {
                    "operation_date": "2040-06-15",
                    "product_code": "SYNTHETIC-PRODUCT",
                    "operation_type": "B",
                    "product_attributes": {
                        "synthetic_attribute_x": "A",
                        "synthetic_attribute_z": "PRESENT",
                    },
                },
            }
        },
    )

    evaluation_id: str = Field(min_length=1)
    evaluated_at: datetime
    known_at: datetime
    correlation_id: str = Field(min_length=1)
    facts: FactSetRequest

    @field_validator("evaluation_id", "correlation_id")
    @classmethod
    def reject_blank_identifiers(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("identifier must be non-blank")
        return value

    @field_validator("evaluated_at", "known_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value

    def context(self) -> EvaluationContext:
        return EvaluationContext(
            evaluation_id=self.evaluation_id,
            evaluated_at=self.evaluated_at,
            known_at=self.known_at,
            correlation_id=self.correlation_id,
        )


class RuleReferenceResponse(BaseModel):
    identity_id: str
    rule_code: str
    version_id: str
    version: int
    content_hash: str

    @classmethod
    def from_domain(cls, reference: RuleVersionRef) -> RuleReferenceResponse:
        return _rule_response(reference)


class ConditionResponse(BaseModel):
    condition_id: str
    description: str
    fact_name: str
    status: ConditionStatus
    expected_value: str | None
    observed_value: str | None


class LegalSourceResponse(BaseModel):
    source_id: str
    act_type: str
    number: str
    year: int
    issuing_authority: str
    device: str
    official_uri: str | None
    published_on: date | None
    notes: str | None
    integrity_hash: str | None

    @classmethod
    def from_domain(cls, source: LegalSource) -> LegalSourceResponse:
        return cls(
            source_id=source.source_id,
            act_type=source.act_type,
            number=source.number,
            year=source.year,
            issuing_authority=source.issuing_authority,
            device=source.device,
            official_uri=source.official_uri,
            published_on=source.published_on,
            notes=source.notes,
            integrity_hash=source.integrity_hash,
        )


class TaxCandidateResponse(BaseModel):
    catalog_version_id: str
    cst: str
    cclasstrib: str | None
    support: str
    rule: RuleReferenceResponse
    conditions: list[ConditionResponse]
    missing_facts: list[str]
    legal_references: list[LegalSourceResponse]


class DecisionStepResponse(BaseModel):
    sequence: int
    phase: TracePhase
    description: str
    outcome: str
    rule: RuleReferenceResponse | None
    conditions: list[ConditionResponse]
    details: dict[str, str] = Field(default_factory=dict)


class RuleSetResponse(BaseModel):
    ruleset_id: str
    version: str
    content_hash: str


class ClassificationEvaluationResponse(BaseModel):
    evaluation_id: str
    evaluated_at: datetime
    known_at: datetime
    correlation_id: str
    input_hash: str
    engine_version: str
    ruleset: RuleSetResponse
    status: ClassificationStatus
    candidates: list[str]
    tax_candidates: list[TaxCandidateResponse] = Field(default_factory=list)
    missing_facts: list[str]
    rules_evaluated: list[RuleReferenceResponse]
    rules_applicable: list[RuleReferenceResponse]
    conditions_satisfied: list[ConditionResponse]
    conditions_not_satisfied: list[ConditionResponse]
    legal_references: list[LegalSourceResponse]
    decision_trace: list[DecisionStepResponse]

    @classmethod
    def from_domain(cls, evaluation: Evaluation) -> ClassificationEvaluationResponse:
        outcome = evaluation.outcome
        return cls(
            evaluation_id=evaluation.evaluation_id,
            evaluated_at=evaluation.evaluated_at,
            known_at=evaluation.known_at,
            correlation_id=evaluation.correlation_id,
            input_hash=evaluation.input_hash,
            engine_version=evaluation.engine_version,
            ruleset=RuleSetResponse(
                ruleset_id=evaluation.ruleset.ruleset_id,
                version=evaluation.ruleset.version,
                content_hash=evaluation.ruleset.content_hash,
            ),
            status=outcome.status,
            candidates=list(outcome.candidates),
            tax_candidates=[
                TaxCandidateResponse(
                    catalog_version_id=item.catalog_version_id,
                    cst=item.cst_code,
                    cclasstrib=item.classification_code,
                    support=item.support.value,
                    rule=_rule_response(item.rule),
                    conditions=[_condition_response(value) for value in item.conditions],
                    missing_facts=list(item.missing_facts),
                    legal_references=[
                        LegalSourceResponse.from_domain(source) for source in item.legal_sources
                    ],
                )
                for item in outcome.tax_candidates
            ],
            missing_facts=list(outcome.missing_facts),
            rules_evaluated=[_rule_response(rule) for rule in outcome.evaluated_rules],
            rules_applicable=[_rule_response(rule) for rule in outcome.applicable_rules],
            conditions_satisfied=[
                _condition_response(condition) for condition in outcome.satisfied_conditions
            ],
            conditions_not_satisfied=[
                _condition_response(condition) for condition in outcome.unsatisfied_conditions
            ],
            legal_references=[
                LegalSourceResponse.from_domain(source) for source in outcome.legal_sources
            ],
            decision_trace=[
                DecisionStepResponse(
                    sequence=step.sequence,
                    phase=step.phase,
                    description=step.description,
                    outcome=step.outcome,
                    rule=_rule_response(step.rule) if step.rule is not None else None,
                    conditions=[_condition_response(condition) for condition in step.conditions],
                    details=dict(step.details),
                )
                for step in outcome.trace
            ],
        )


def _rule_response(reference: RuleVersionRef) -> RuleReferenceResponse:
    return RuleReferenceResponse(
        identity_id=reference.identity_id,
        rule_code=reference.rule_code,
        version_id=reference.version_id,
        version=reference.version,
        content_hash=reference.content_hash,
    )


def _condition_response(condition: ConditionResult) -> ConditionResponse:
    return ConditionResponse(
        condition_id=condition.condition_id,
        description=condition.description,
        fact_name=condition.fact_name,
        status=condition.status,
        expected_value=condition.expected_value,
        observed_value=condition.observed_value,
    )
