from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from tributaria_api.application.tax_rule_specifications import (
    Readiness,
    TaxRuleSpecificationValidator,
)
from tributaria_api.main import app


@dataclass
class FakeReferences:
    source_exists: bool = True
    catalog_status: str | None = "PUBLISHED"
    known_cst: str = "999"
    classification_exists: bool = True
    classification_related_cst: str | None = "999"

    def legal_source_exists(self, organization_id: str, source_id: str) -> bool:
        return self.source_exists

    def catalog_version_status(
        self, organization_id: str, catalog_version_id: str
    ) -> str | None:
        return self.catalog_status

    def cst_exists(self, catalog_version_id: str, cst: str) -> bool:
        return cst == self.known_cst

    def classification_cst(
        self, catalog_version_id: str, cclasstrib: str
    ) -> tuple[bool, str | None]:
        return self.classification_exists, self.classification_related_cst


@pytest.fixture
def valid_document() -> dict[str, Any]:
    path = Path("docs/tax/examples/TEST-IBSCBS-0001.json")
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def validate(
    document: dict[str, Any],
    references: FakeReferences | None = None,
):
    return TaxRuleSpecificationValidator(references or FakeReferences()).validate(document, "org")


def issue_codes(result: object) -> set[str]:
    return {issue.code for issue in result.issues}  # type: ignore[attr-defined]


def test_approved_synthetic_specification_is_structurally_ready(
    valid_document: dict[str, Any],
) -> None:
    result = validate(valid_document)
    assert result.readiness is Readiness.READY_FOR_IMPLEMENTATION
    assert result.issues == ()


def test_incomplete_specification_is_not_ready(valid_document: dict[str, Any]) -> None:
    document = copy.deepcopy(valid_document)
    del document["title"]
    result = validate(document)
    assert result.readiness is Readiness.NOT_READY
    assert issue_codes(result) == {"SCHEMA_INVALID"}


def test_missing_source_is_reported(valid_document: dict[str, Any]) -> None:
    result = validate(valid_document, FakeReferences(source_exists=False))
    assert "SOURCE_NOT_FOUND" in issue_codes(result)


def test_non_approved_specification_is_not_ready(valid_document: dict[str, Any]) -> None:
    document = copy.deepcopy(valid_document)
    document["status"] = "IN_REVIEW"
    result = validate(document)
    assert result.readiness is Readiness.NOT_READY
    assert "STATUS_NOT_APPROVED" in issue_codes(result)


def test_unknown_cst_is_reported(valid_document: dict[str, Any]) -> None:
    result = validate(valid_document, FakeReferences(known_cst="998"))
    assert "CST_NOT_FOUND" in issue_codes(result)


def test_unknown_cclasstrib_is_reported(valid_document: dict[str, Any]) -> None:
    result = validate(valid_document, FakeReferences(classification_exists=False))
    assert "CCLASSTRIB_NOT_FOUND" in issue_codes(result)


def test_cclasstrib_cst_mismatch_is_reported(valid_document: dict[str, Any]) -> None:
    result = validate(
        valid_document,
        FakeReferences(classification_related_cst="998"),
    )
    assert "CATALOG_RELATIONSHIP_MISMATCH" in issue_codes(result)


@pytest.mark.parametrize(
    ("group", "code"),
    [
        ("positive_cases", "POSITIVE_CASE_MISSING"),
        ("negative_cases", "NEGATIVE_CASE_MISSING"),
        ("insufficient_fact_cases", "INSUFFICIENT_CASE_MISSING"),
        ("boundary_date_cases", "BOUNDARY_DATE_CASE_MISSING"),
    ],
)
def test_required_legal_case_group_cannot_be_empty(
    valid_document: dict[str, Any], group: str, code: str
) -> None:
    document = copy.deepcopy(valid_document)
    document["tests"][group] = []
    result = validate(document)
    assert code in issue_codes(result)


def test_unknown_catalog_version_is_reported(valid_document: dict[str, Any]) -> None:
    result = validate(valid_document, FakeReferences(catalog_status=None))
    assert "CATALOG_VERSION_NOT_FOUND" in issue_codes(result)


def test_unpublished_catalog_is_reported(valid_document: dict[str, Any]) -> None:
    result = validate(valid_document, FakeReferences(catalog_status="APPROVED"))
    assert "CATALOG_NOT_PUBLISHED" in issue_codes(result)


def test_invalid_effective_period_is_reported(valid_document: dict[str, Any]) -> None:
    document = copy.deepcopy(valid_document)
    document["effective_to"] = document["effective_from"]
    result = validate(document)
    assert "INVALID_EFFECTIVE_PERIOD" in issue_codes(result)


def test_precedence_without_legal_basis_is_rejected(valid_document: dict[str, Any]) -> None:
    document = copy.deepcopy(valid_document)
    document["precedence"]["precedes_rule_ids"] = ["TEST-OTHER-RULE"]
    result = validate(document)
    assert "PRECEDENCE_WITHOUT_LEGAL_BASIS" in issue_codes(result)


def test_specification_endpoints_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/admin/tax-rule-specifications" in paths
    assert "/api/v1/admin/tax-rule-specifications/{rule_id}/preflight" in paths

