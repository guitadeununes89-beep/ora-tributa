from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from tributaria_api.application.tax_rule_specifications import (
    Readiness,
    TaxRuleSpecificationValidator,
)


@dataclass
class PublishedStage7bReferences:
    classifications: dict[str, str]

    def legal_source_exists(self, organization_id: str, source_id: str) -> bool:
        return True

    def catalog_version_status(self, organization_id: str, catalog_version_id: str) -> str | None:
        return "PUBLISHED"

    def cst_exists(self, catalog_version_id: str, cst: str) -> bool:
        return cst == "200"

    def classification_cst(
        self, catalog_version_id: str, cclasstrib: str
    ) -> tuple[bool, str | None]:
        exists = cclasstrib in self.classifications
        return exists, self.classifications.get(cclasstrib)


EXPECTED_CODES = {
    "RT-IBSCBS-0001": "200032",
    "RT-IBSCBS-0002": "200009",
    "RT-IBSCBS-0003": "200010",
}


@pytest.mark.parametrize(("rule_id", "cclasstrib"), EXPECTED_CODES.items())
def test_stage_7_specifications_preserve_governed_lifecycle(rule_id: str, cclasstrib: str) -> None:
    path = Path(f"docs/tax/rules/specifications/{rule_id}.json")
    document = json.loads(path.read_text(encoding="utf-8"))
    references = PublishedStage7bReferences(
        classifications={code: "200" for code in EXPECTED_CODES.values()}
    )

    result = TaxRuleSpecificationValidator(references).validate(document, "test-org")

    assert result.specification is not None
    if rule_id == "RT-IBSCBS-0003":
        assert result.specification.status == "APPROVED"
        assert result.specification.implementation is not None
        assert result.readiness is Readiness.READY_FOR_IMPLEMENTATION
        assert result.issues == ()
    else:
        assert result.specification.status == "DRAFT"
        assert result.specification.implementation is None
        assert result.readiness is Readiness.NOT_READY
        assert {issue.code for issue in result.issues} == {"STATUS_NOT_APPROVED"}
    assert result.specification.catalog.cst == "200"
    assert result.specification.catalog.cclasstrib == cclasstrib
    assert len(result.specification.tests.positive_cases) >= 2
    assert len(result.specification.tests.negative_cases) >= 2
    assert len(result.specification.tests.insufficient_fact_cases) >= 2


def test_zero_rate_specifications_have_express_precedence_over_sixty_percent_draft() -> None:
    for rule_id in ("RT-IBSCBS-0002", "RT-IBSCBS-0003"):
        path = Path(f"docs/tax/rules/specifications/{rule_id}.json")
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["precedence"]["precedes_rule_ids"] == ["RT-IBSCBS-0001"]
        assert "art. 133" in document["precedence"]["legal_basis"]

