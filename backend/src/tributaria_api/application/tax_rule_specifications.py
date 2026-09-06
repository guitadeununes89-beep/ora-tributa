from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator


class SpecificationStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    IMPLEMENTED = "IMPLEMENTED"
    SUPERSEDED = "SUPERSEDED"


class Readiness(StrEnum):
    READY_FOR_IMPLEMENTATION = "READY_FOR_IMPLEMENTATION"
    NOT_READY = "NOT_READY"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LegalFoundation(StrictModel):
    legal_source_id: str = Field(min_length=1, max_length=100)
    source_title: str = Field(min_length=1, max_length=500)
    specific_device: str = Field(min_length=1, max_length=1000)
    official_url: HttpUrl
    verifiable_reference: str = Field(min_length=1, max_length=1000)


class CatalogReference(StrictModel):
    catalog_version_id: str = Field(min_length=1, max_length=100)
    cst: str = Field(pattern=r"^\d{3}$")
    cclasstrib: str | None = Field(pattern=r"^\d{6}$")


class FactDefinition(StrictModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_.]*$", max_length=200)
    legal_meaning: str = Field(min_length=1, max_length=2000)
    value_type: str = Field(min_length=1, max_length=100)
    allowed_values: list[str] | None
    source: str = Field(min_length=1, max_length=500)


class DeterministicCondition(StrictModel):
    condition_id: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    required_fact_names: list[str]


class RuleResult(StrictModel):
    classification_status: str = Field(
        pattern=r"^(CONCLUSIVO|POSSIVEIS_ENQUADRAMENTOS|NECESSITA_VALIDACAO|SEM_CLASSIFICACAO)$"
    )
    cst: str = Field(pattern=r"^\d{3}$")
    cclasstrib: str | None = Field(pattern=r"^\d{6}$")
    explanation: str = Field(min_length=1, max_length=3000)


class PrecedenceDefinition(StrictModel):
    precedes_rule_ids: list[str]
    legal_basis: str | None = Field(max_length=2000)


class ExpectedResult(StrictModel):
    status: str = Field(
        pattern=r"^(CONCLUSIVO|POSSIVEIS_ENQUADRAMENTOS|NECESSITA_VALIDACAO|SEM_CLASSIFICACAO)$"
    )
    cst: str | None = Field(pattern=r"^\d{3}$")
    cclasstrib: str | None = Field(pattern=r"^\d{6}$")
    missing_facts: list[str]


class LegalTestCase(StrictModel):
    case_id: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    input: dict[str, Any]
    expected: ExpectedResult


class TestCaseSet(StrictModel):
    positive_cases: list[LegalTestCase]
    negative_cases: list[LegalTestCase]
    insufficient_fact_cases: list[LegalTestCase]
    boundary_date_cases: list[LegalTestCase]


class ApprovalMetadata(StrictModel):
    prepared_by: str = Field(min_length=1, max_length=200)
    reviewed_by: str | None = Field(max_length=200)
    approved_by: str | None = Field(max_length=200)
    approval_date: date | None
    approval_evidence: str | None = Field(max_length=1000)


class ImplementationMapping(StrictModel):
    tax_rule_identity_id: str = Field(min_length=1, max_length=100)
    tax_rule_version_id: str = Field(min_length=1, max_length=100)
    implemented_at: date


class TaxRuleSpecification(StrictModel):
    rule_id: str = Field(pattern=r"^(RT-IBSCBS-\d{4}|TEST-[A-Z0-9-]+)$", max_length=100)
    specification_version: int = Field(gt=0)
    is_synthetic: bool
    title: str = Field(min_length=1, max_length=500)
    tax_domain: str = Field(pattern=r"^IBS_CBS$")
    objective: str = Field(min_length=1, max_length=3000)
    jurisdiction: str = Field(min_length=1, max_length=100)
    status: SpecificationStatus
    legal_foundation: LegalFoundation
    effective_from: date
    effective_to: date | None
    catalog: CatalogReference
    required_facts: list[FactDefinition]
    optional_facts: list[FactDefinition]
    deterministic_conditions: list[DeterministicCondition]
    result: RuleResult
    exclusion_hypotheses: list[str]
    known_conflicts: list[str]
    precedence: PrecedenceDefinition
    tests: TestCaseSet
    approval: ApprovalMetadata
    implementation: ImplementationMapping | None
    superseded_by_specification_id: str | None = Field(max_length=100)

    @field_validator("exclusion_hypotheses", "known_conflicts")
    @classmethod
    def non_blank_entries(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("entries must not be blank")
        return value


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class SpecificationValidationResult:
    readiness: Readiness
    specification: TaxRuleSpecification | None
    issues: tuple[ValidationIssue, ...]


class SpecificationReferenceLookup(Protocol):
    def legal_source_exists(self, organization_id: str, source_id: str) -> bool: ...

    def catalog_version_status(
        self, organization_id: str, catalog_version_id: str
    ) -> str | None: ...

    def cst_exists(self, catalog_version_id: str, cst: str) -> bool: ...

    def classification_cst(
        self, catalog_version_id: str, cclasstrib: str
    ) -> tuple[bool, str | None]: ...


class TaxRuleSpecificationValidator:
    def __init__(self, references: SpecificationReferenceLookup) -> None:
        self.references = references

    def validate(
        self, document: Mapping[str, Any], organization_id: str
    ) -> SpecificationValidationResult:
        try:
            specification = TaxRuleSpecification.model_validate(document)
        except ValidationError as exc:
            schema_issues = tuple(
                ValidationIssue(
                    code="SCHEMA_INVALID",
                    path=".".join(str(item) for item in error["loc"]),
                    message=str(error["msg"]),
                )
                for error in exc.errors()
            )
            return SpecificationValidationResult(Readiness.NOT_READY, None, schema_issues)

        issues: list[ValidationIssue] = []
        self._validate_lifecycle(specification, issues)
        self._validate_dates(specification, issues)
        self._validate_facts(specification, issues)
        self._validate_cases(specification, issues)
        self._validate_references(specification, organization_id, issues)
        readiness = (
            Readiness.READY_FOR_IMPLEMENTATION
            if not issues and specification.status is SpecificationStatus.APPROVED
            else Readiness.NOT_READY
        )
        return SpecificationValidationResult(readiness, specification, tuple(issues))

    def _validate_lifecycle(
        self, specification: TaxRuleSpecification, issues: list[ValidationIssue]
    ) -> None:
        if specification.status is not SpecificationStatus.APPROVED:
            issues.append(
                ValidationIssue(
                    "STATUS_NOT_APPROVED",
                    "status",
                    "Only an APPROVED specification is ready for implementation",
                )
            )
        approval = specification.approval
        if specification.status in {
            SpecificationStatus.APPROVED,
            SpecificationStatus.IMPLEMENTED,
            SpecificationStatus.SUPERSEDED,
        } and not all(
            (
                approval.reviewed_by,
                approval.approved_by,
                approval.approval_date,
                approval.approval_evidence,
            )
        ):
            issues.append(
                ValidationIssue(
                    "APPROVAL_METADATA_INCOMPLETE",
                    "approval",
                    "Approved lifecycle states require reviewer, approver, date and evidence",
                )
            )
        if (
            specification.status is SpecificationStatus.IMPLEMENTED
            and specification.implementation is None
        ):
            issues.append(
                ValidationIssue(
                    "IMPLEMENTATION_MAPPING_MISSING",
                    "implementation",
                    "IMPLEMENTED requires the corresponding TaxRuleIdentity and TaxRuleVersion",
                )
            )
        if (
            specification.status is SpecificationStatus.SUPERSEDED
            and not specification.superseded_by_specification_id
        ):
            issues.append(
                ValidationIssue(
                    "SUPERSEDING_SPECIFICATION_MISSING",
                    "superseded_by_specification_id",
                    "SUPERSEDED requires the replacement specification identifier",
                )
            )

    def _validate_dates(
        self, specification: TaxRuleSpecification, issues: list[ValidationIssue]
    ) -> None:
        if (
            specification.effective_to is not None
            and specification.effective_to <= specification.effective_from
        ):
            issues.append(
                ValidationIssue(
                    "INVALID_EFFECTIVE_PERIOD",
                    "effective_to",
                    "effective_to must be later than effective_from (exclusive end)",
                )
            )

    def _validate_facts(
        self, specification: TaxRuleSpecification, issues: list[ValidationIssue]
    ) -> None:
        facts = [*specification.required_facts, *specification.optional_facts]
        names = [fact.name for fact in facts]
        if len(names) != len(set(names)):
            issues.append(
                ValidationIssue("DUPLICATE_FACT", "required_facts", "Fact names must be unique")
            )
        known = set(names)
        for index, condition in enumerate(specification.deterministic_conditions):
            for fact_name in condition.required_fact_names:
                if fact_name not in known:
                    issues.append(
                        ValidationIssue(
                            "UNKNOWN_CONDITION_FACT",
                            f"deterministic_conditions.{index}.required_fact_names",
                            f"Condition references undefined fact: {fact_name}",
                        )
                    )
        precedence = specification.precedence
        if precedence.precedes_rule_ids and not precedence.legal_basis:
            issues.append(
                ValidationIssue(
                    "PRECEDENCE_WITHOUT_LEGAL_BASIS",
                    "precedence.legal_basis",
                    "Precedence may only be declared with an explicit legal basis",
                )
            )
        if (
            specification.catalog.cst != specification.result.cst
            or specification.catalog.cclasstrib != specification.result.cclasstrib
        ):
            issues.append(
                ValidationIssue(
                    "RESULT_CATALOG_MISMATCH",
                    "result",
                    "Result codes must match the referenced catalog codes",
                )
            )

    def _validate_cases(
        self, specification: TaxRuleSpecification, issues: list[ValidationIssue]
    ) -> None:
        required = {
            "positive_cases": specification.tests.positive_cases,
            "negative_cases": specification.tests.negative_cases,
            "insufficient_fact_cases": specification.tests.insufficient_fact_cases,
            "boundary_date_cases": specification.tests.boundary_date_cases,
        }
        codes = {
            "positive_cases": "POSITIVE_CASE_MISSING",
            "negative_cases": "NEGATIVE_CASE_MISSING",
            "insufficient_fact_cases": "INSUFFICIENT_CASE_MISSING",
            "boundary_date_cases": "BOUNDARY_DATE_CASE_MISSING",
        }
        for name, cases in required.items():
            if not cases:
                issues.append(
                    ValidationIssue(codes[name], f"tests.{name}", f"{name} must not be empty")
                )

    def _validate_references(
        self,
        specification: TaxRuleSpecification,
        organization_id: str,
        issues: list[ValidationIssue],
    ) -> None:
        foundation = specification.legal_foundation
        if not self.references.legal_source_exists(organization_id, foundation.legal_source_id):
            issues.append(
                ValidationIssue(
                    "SOURCE_NOT_FOUND",
                    "legal_foundation.legal_source_id",
                    "Legal source does not exist for the organization",
                )
            )
        catalog = specification.catalog
        status = self.references.catalog_version_status(
            organization_id, catalog.catalog_version_id
        )
        if status is None:
            issues.append(
                ValidationIssue(
                    "CATALOG_VERSION_NOT_FOUND",
                    "catalog.catalog_version_id",
                    "Catalog version does not exist for the organization",
                )
            )
            return
        if status != "PUBLISHED":
            issues.append(
                ValidationIssue(
                    "CATALOG_NOT_PUBLISHED",
                    "catalog.catalog_version_id",
                    "Catalog version must be PUBLISHED",
                )
            )
            return
        if not self.references.cst_exists(catalog.catalog_version_id, catalog.cst):
            issues.append(
                ValidationIssue("CST_NOT_FOUND", "catalog.cst", "CST does not exist in catalog")
            )
        if catalog.cclasstrib is not None:
            exists, related_cst = self.references.classification_cst(
                catalog.catalog_version_id, catalog.cclasstrib
            )
            if not exists:
                issues.append(
                    ValidationIssue(
                        "CCLASSTRIB_NOT_FOUND",
                        "catalog.cclasstrib",
                        "cClassTrib does not exist in catalog",
                    )
                )
            elif related_cst != catalog.cst:
                issues.append(
                    ValidationIssue(
                        "CATALOG_RELATIONSHIP_MISMATCH",
                        "catalog.cclasstrib",
                        "cClassTrib is not structurally associated with the referenced CST",
                    )
                )


def load_specification(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Tax rule specification must be a JSON object")
    return value

