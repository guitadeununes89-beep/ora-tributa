from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class CommandModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correlation_id: str = Field(min_length=1)

    @field_validator("correlation_id")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @model_validator(mode="after")
    def require_timezone_on_command_timestamps(self) -> CommandModel:
        for name in ("created_at", "recorded_at", "occurred_at", "evaluated_at"):
            value = getattr(self, name, None)
            if isinstance(value, datetime) and value.tzinfo is None:
                raise ValueError(f"{name} must include a timezone")
        return self


class LegalSourceCreate(CommandModel):
    id: str | None = None
    source_type: str
    number: str
    year: int = Field(ge=1, le=9999)
    issuing_authority: str
    title: str
    official_url: HttpUrl
    publication_date: date
    jurisdiction: str
    notes: str | None = None
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    is_synthetic: bool
    created_at: datetime


class TaxRuleIdentityCreate(CommandModel):
    id: str
    code: str = Field(pattern=r"^TEST-[A-Z0-9-]+$")
    title: str
    description: str | None = None
    is_synthetic: Literal[True]
    created_at: datetime


class TaxRuleVersionCreate(CommandModel):
    id: str
    version: int = Field(gt=0)
    jurisdiction: str
    legal_source_id: str | None
    legal_device: str
    valid_from: date
    valid_to: date | None = None
    recorded_at: datetime
    content: dict[str, Any]
    metadata: dict[str, str] = Field(default_factory=dict)


class TaxRuleVersionDraftUpdate(CommandModel):
    occurred_at: datetime
    content: dict[str, Any]
    metadata: dict[str, str] = Field(default_factory=dict)


class LifecycleCommand(CommandModel):
    event_id: str
    occurred_at: datetime
    reason: str
    related_version: int | None = None


class RuleSetCreate(CommandModel):
    id: str
    name: str
    version: str
    created_at: datetime
    rule_version_ids: list[str] = Field(min_length=1)


class RuleSetPublish(CommandModel):
    occurred_at: datetime


class ReproduceEvaluationRequest(CommandModel):
    evaluation_id: str
    evaluated_at: datetime


class LegalSourceView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    source_type: str
    number: str
    year: int
    issuing_authority: str
    title: str
    official_url: str
    publication_date: date
    jurisdiction: str
    notes: str | None
    content_hash: str
    is_synthetic: bool
    created_at: datetime


class TaxRuleVersionView(BaseModel):
    id: str
    rule_identity_id: str
    identity_code: str | None = None
    version: int
    lifecycle_status: str
    jurisdiction: str
    legal_source_id: str | None
    legal_source_title: str | None = None
    legal_device: str
    valid_from: date
    valid_to: date | None
    recorded_at: datetime
    submitted_for_review_at: datetime | None
    approved_at: datetime | None
    published_at: datetime | None
    superseded_at: datetime | None
    withdrawn_at: datetime | None
    created_by: str
    approved_by: str | None
    published_by: str | None
    content: dict[str, Any]
    content_hash: str
    metadata: dict[str, Any]
    events: list[dict[str, Any]] = Field(default_factory=list)
    rulesets: list[str] = Field(default_factory=list)


class TaxRuleIdentityView(BaseModel):
    id: str
    code: str
    title: str
    description: str | None
    is_synthetic: bool
    created_at: datetime
    created_by: str
    versions: list[TaxRuleVersionView] = Field(default_factory=list)


class RuleSetView(BaseModel):
    id: str
    name: str
    version: str
    status: str
    created_at: datetime
    created_by: str
    published_at: datetime | None
    published_by: str | None
    fingerprint: str | None
    rule_version_ids: list[str]
