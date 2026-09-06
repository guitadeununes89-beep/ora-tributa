from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tributaria_api.contracts.classification import ClassificationEvaluationResponse


class AssistedClassificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evaluation_id: str = Field(min_length=1, max_length=100)
    ruleset_id: str = Field(min_length=1, max_length=100)
    catalog_version_id: str = Field(min_length=1, max_length=100)
    product_id: str | None = Field(default=None, max_length=100)
    operation_date: date
    evaluated_at: datetime
    known_at: datetime
    ncm: str | None = Field(default=None, pattern=r"^\d{8}$")
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    operation_type: str | None = Field(default=None, max_length=100)
    origin_state: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    destination_state: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    recipient_type: str | None = Field(default=None, max_length=100)
    taxpayer_regime: str | None = Field(default=None, max_length=100)
    product_attributes: dict[str, str] = Field(default_factory=dict)

    @field_validator("evaluated_at", "known_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value

    @field_validator("product_attributes")
    @classmethod
    def governed_pilot_attributes(cls, value: dict[str, str]) -> dict[str, str]:
        real_values = {
            "product.kind": {"MEDICINE", "OTHER", "UNKNOWN"},
            "product.anvisa_registration_status": {
                "REGISTERED",
                "NOT_REGISTERED",
                "UNKNOWN",
            },
            "buyer.legal_nature": {
                "DIRECT_PUBLIC_ADMINISTRATION_BODY",
                "AUTARCHY",
                "PUBLIC_FOUNDATION",
                "PUBLIC_COMPANY",
                "MIXED_CAPITAL_COMPANY",
                "PRIVATE_ENTITY",
                "UNKNOWN",
            },
            "operation.buyer_is_acquirer": {"YES", "NO", "UNKNOWN"},
        }
        for key, item in value.items():
            if key.startswith("synthetic."):
                continue
            if key not in real_values or item not in real_values[key]:
                raise ValueError(f"unsupported governed fact or value: {key}")
        return value

    @model_validator(mode="after")
    def product_or_manual_facts(self) -> AssistedClassificationRequest:
        pilot_facts = {
            "product.kind",
            "product.anvisa_registration_status",
            "buyer.legal_nature",
            "operation.buyer_is_acquirer",
        }
        if (
            self.product_id is None
            and self.ncm is None
            and self.description is None
            and not pilot_facts.intersection(self.product_attributes)
        ):
            raise ValueError("provide product_id or explicit manual product facts")
        return self


class OfficialCandidateDetail(BaseModel):
    catalog_version_id: str
    cst: str
    cst_description: str
    cclasstrib: str | None
    cclasstrib_name: str | None
    cclasstrib_description: str | None
    valid_from: date | None
    valid_to: date | None


class AssistedClassificationResponse(ClassificationEvaluationResponse):
    product_id: str | None
    product_version_id: str | None
    catalog_version_id: str
    official_candidates: list[OfficialCandidateDetail] = Field(default_factory=list)


class TaxClassificationReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_id: str = Field(min_length=1, max_length=100)
    reviewed_at: datetime

    @field_validator("reviewed_at")
    @classmethod
    def review_timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value


class TaxClassificationReviewResponse(BaseModel):
    review_id: str
    evaluation_id: str
    product_id: str
    product_version_id: str
    catalog_version_id: str
    ruleset_id: str
    status: str
    reviewed_at: datetime
    reviewed_by: str
