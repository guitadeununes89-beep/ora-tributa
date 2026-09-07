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
        # Facts with no closed value set (governed identifiers, not enums) are
        # exempt from the enum check below but still real, allowlisted facts.
        free_text_facts = {"operation.zfm_area_version_id", "product.ncm_sh"}
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
            # RT-IBSCBS-0007 (LC 214/2025 art. 445; Resolução CGIBS 6/2026 art. 516)
            "operation.origin_area_status": {"OUTSIDE_ZFM", "INSIDE_ZFM", "UNKNOWN"},
            "operation.destination_area_status": {"ZFM", "OTHER", "UNKNOWN"},
            "product.material_good_status": {"MATERIAL_GOOD", "NOT_MATERIAL_GOOD", "UNKNOWN"},
            "product.industrialization_status": {
                "INDUSTRIALIZED",
                "NOT_INDUSTRIALIZED",
                "UNKNOWN",
            },
            "product.origin_status": {"NATIONAL", "FOREIGN", "UNKNOWN"},
            "buyer.establishment_area_status": {
                "ESTABLISHED_IN_ZFM",
                "NOT_ESTABLISHED_IN_ZFM",
                "UNKNOWN",
            },
            "buyer.taxpayer_status": {"TAXPAYER", "NOT_TAXPAYER", "UNKNOWN"},
            "buyer.art_442_habilitation_status": {"VALID", "INVALID", "UNKNOWN"},
            "buyer.tax_regime_status": {
                "REGULAR_IBS_CBS",
                "SIMPLES_NACIONAL",
                "OTHER",
                "UNKNOWN",
            },
            "operation.invoice_suframa_registration_status": {
                "PRESENT_AND_MATCHING",
                "ABSENT_OR_MISMATCH",
                "UNKNOWN",
            },
            "product.art_443_par1_exclusion_status": {"NOT_EXCLUDED", "EXCLUDED", "UNKNOWN"},
            "operation.zfm_entry_proof_status": {
                "CONFIRMED",
                "NOT_CONFIRMED_AFTER_DEADLINE",
                "PENDING_WITHIN_DEADLINE",
                "UNKNOWN",
            },
            "operation.entry_deadline_status": {
                "WITHIN_120_DAYS",
                "VALID_EXTENSION_WITHIN_210_DAYS",
                "EXPIRED",
                "UNKNOWN",
            },
            # RT-IBSCBS-0008 (LC 214/2025 art. 448; Resolução CGIBS 6/2026 art. 519)
            "seller.establishment_zfm_relation": {"INSIDE", "OUTSIDE", "BOUNDARY", "UNKNOWN"},
            "buyer.establishment_zfm_relation": {"INSIDE", "OUTSIDE", "BOUNDARY", "UNKNOWN"},
            "seller.zfm_incentivized_industry_status": {"VALID", "INVALID", "UNKNOWN"},
            "buyer.zfm_incentivized_industry_status": {"VALID", "INVALID", "UNKNOWN"},
            "product.intermediate_good_status": {
                "INTERMEDIATE_GOOD",
                "NOT_INTERMEDIATE_GOOD",
                "UNKNOWN",
            },
            "operation.delivery_area_status": {"INSIDE_ZFM", "OUTSIDE_ZFM", "UNKNOWN"},
            "operation.flow_type": {"DIRECT", "TOLL_MANUFACTURING", "UNKNOWN"},
            "operation.taxable_scope_status": {"FULL_OPERATION", "VALUE_ADDED_ONLY", "UNKNOWN"},
            # RT-IBSCBS-0004 (LC 214/2025, art. 146, caput, redação original; Anexo XIV)
            "product.annex_xiv_match_status": {"MATCHED", "NOT_MATCHED", "UNKNOWN"},
            "normative.annex_xiv_version": {"LC214_2025_ORIGINAL", "UNKNOWN"},
            # RT-IBSCBS-0005 (LC 214/2025, art. 146, § 1º, II; LC 187/2021, arts. 9º a 11)
            "buyer.health_entity_status": {"HEALTH_ENTITY", "NOT_HEALTH_ENTITY", "UNKNOWN"},
            "buyer.ibs_cbs_immunity_status": {"IMMUNE", "NOT_IMMUNE", "UNKNOWN"},
            "operation.effective_buyer_status": {"CONFIRMED", "NOT_CONFIRMED", "UNKNOWN"},
            "buyer.cebas_status": {"VALID", "INVALID", "UNKNOWN"},
            "buyer.sus_service_requirement_status": {"SATISFIED", "NOT_SATISFIED", "UNKNOWN"},
        }
        for key, item in value.items():
            if key.startswith("synthetic.") or key in free_text_facts:
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
            "operation.origin_area_status",
            "seller.establishment_zfm_relation",
            "product.annex_xiv_match_status",
            "buyer.health_entity_status",
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
