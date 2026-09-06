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
class PublishedReferences:
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
    "RT-IBSCBS-0004": "200009",
    "RT-IBSCBS-0005": "200010",
    "RT-IBSCBS-0006": "200053",
}


def load(rule_id: str) -> dict:
    path = Path(f"docs/tax/rules/specifications/{rule_id}.json")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("rule_id", "cclasstrib"), EXPECTED_CODES.items())
def test_stage_7_specifications_preserve_governed_lifecycle(
    rule_id: str, cclasstrib: str
) -> None:
    document = load(rule_id)
    references = PublishedReferences(
        classifications={code: "200" for code in set(EXPECTED_CODES.values())}
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
    assert len(result.specification.tests.boundary_date_cases) >= 2


def test_rule_0001_distinguishes_entities_and_blocks_incomplete_article_146() -> None:
    document = load("RT-IBSCBS-0001")
    facts = {fact["name"] for fact in document["required_facts"]}

    assert "supplier.art_133_price_condition" not in facts
    assert {
        "operation.supplier_identity",
        "product.manufacturer_identity",
        "product.responsible_importer_identity",
        "art_133.responsible_legal_entity_role",
        "art_133.responsible_entity_validation_status",
        "operation.art_146_coverage_status",
    } <= facts
    assert any(
        "NEEDS_LEGAL_VALIDATION_ART133_RESPONSIBLE_ENTITY" in conflict
        for conflict in document["known_conflicts"]
    )


def test_rule_0002_keeps_paragraph_3_list_blocker() -> None:
    document = load("RT-IBSCBS-0002")
    assert any(
        "NEEDS_ART146_PAR3_OFFICIAL_LIST" in conflict
        for conflict in document["known_conflicts"]
    )


def test_rule_0004_preserves_historical_exclusive_end() -> None:
    document = load("RT-IBSCBS-0004")
    assert document["effective_from"] == "2026-01-01"
    assert document["effective_to"] == "2026-01-14"
    assert "Anexo XIV" in document["legal_foundation"]["specific_device"]


def test_rules_0003_and_0005_share_code_but_not_legal_rule() -> None:
    public_rule = load("RT-IBSCBS-0003")
    immune_entity_rule = load("RT-IBSCBS-0005")

    assert public_rule["catalog"]["cclasstrib"] == "200010"
    assert immune_entity_rule["catalog"]["cclasstrib"] == "200010"
    assert public_rule["rule_id"] != immune_entity_rule["rule_id"]
    assert public_rule["legal_foundation"]["specific_device"] != immune_entity_rule[
        "legal_foundation"
    ]["specific_device"]


def test_rule_0006_requires_official_sanitary_regulation() -> None:
    document = load("RT-IBSCBS-0006")
    assert any(
        "NEEDS_OFFICIAL_SANITARY_REGULATION" in conflict
        for conflict in document["known_conflicts"]
    )

