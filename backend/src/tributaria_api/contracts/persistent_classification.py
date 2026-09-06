from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from tributaria_api.contracts.classification import FactSetRequest


class PersistedClassificationEvaluationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "evaluation_id": "TEST-EVALUATION-001",
                "ruleset_id": "TEST-RULESET-001",
                "evaluated_at": "2040-06-15T12:00:00Z",
                "known_at": "2040-06-15T12:00:00Z",
                "correlation_id": "TEST-CORRELATION-001",
                "facts": {
                    "operation_date": "2040-06-15",
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
    ruleset_id: str = Field(min_length=1)
    company_id: str | None = None
    establishment_id: str | None = None
    evaluated_at: datetime
    known_at: datetime
    correlation_id: str = Field(min_length=1)
    facts: FactSetRequest

    @field_validator("evaluated_at", "known_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value


class EvaluationArchiveResponse(BaseModel):
    evaluation_id: str
    evaluated_at: datetime
    known_at: datetime
    operation_date: Any
    input_hash: str
    engine_version: str
    ruleset_id: str
    ruleset_fingerprint: str
    facts: dict[str, Any]
    outcome: dict[str, Any]
    decision_trace: list[dict[str, Any]]
    correlation_id: str
    reproduced_from_id: str | None
    rule_versions_used: list[str]
