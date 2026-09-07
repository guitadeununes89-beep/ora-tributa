from __future__ import annotations

import json
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any


class CoverageStatus(StrEnum):
    CATALOG_ONLY = "CATALOG_ONLY"
    LEGAL_MAPPING_REQUIRED = "LEGAL_MAPPING_REQUIRED"
    DRAFT_SPECIFICATION = "DRAFT_SPECIFICATION"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    APPROVED = "APPROVED"
    IMPLEMENTED = "IMPLEMENTED"
    PUBLISHED = "PUBLISHED"
    BLOCKED_EXTERNAL_SOURCE = "BLOCKED_EXTERNAL_SOURCE"


STATUS_PRIORITY = {
    CoverageStatus.CATALOG_ONLY: 0,
    CoverageStatus.LEGAL_MAPPING_REQUIRED: 1,
    CoverageStatus.BLOCKED_EXTERNAL_SOURCE: 2,
    CoverageStatus.DRAFT_SPECIFICATION: 3,
    CoverageStatus.LEGAL_REVIEW: 4,
    CoverageStatus.APPROVED: 5,
    CoverageStatus.IMPLEMENTED: 6,
    CoverageStatus.PUBLISHED: 7,
}

FAMILY_ORDER = {
    "Padrão": 0,
    "Sem alíquota": 1,
    "Uniforme setorial": 2,
    "Fixa": 3,
    "Uniforme nacional (referência)": 4,
    "Não informado": 5,
}


def load_specification_documents(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    documents: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and value.get("is_synthetic") is False:
            documents.append(value)
    return documents


def build_national_coverage(
    classifications: list[dict[str, Any]],
    specifications: list[dict[str, Any]],
    rule_versions: list[dict[str, Any]],
) -> dict[str, Any]:
    specifications_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for specification in specifications:
        code = specification.get("catalog", {}).get("cclasstrib")
        if code:
            specifications_by_code[str(code)].append(specification)

    versions_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for version in rule_versions:
        code = version.get("cclasstrib_code")
        if code and not version.get("is_synthetic", False):
            versions_by_code[str(code)].append(version)

    items = [
        _coverage_item(
            classification,
            specifications_by_code.get(str(classification["code"]), []),
            versions_by_code.get(str(classification["code"]), []),
        )
        for classification in classifications
    ]
    family_items: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        family_items[item["official_family"]].append(item)
    families = [
        {"name": name, **_family_metrics(values)}
        for name, values in sorted(
            family_items.items(), key=lambda entry: (FAMILY_ORDER.get(entry[0], 99), entry[0])
        )
    ]
    return {
        "catalog": _catalog_summary(items),
        "metrics": _coverage_metrics(items),
        "families": families,
        "items": items,
        "disclaimer": (
            "cClassTrib is an official catalog classification, not a TaxRule. "
            "PUBLISHED means at least one associated rule is published and may be partial."
        ),
    }


def _coverage_item(
    classification: dict[str, Any],
    specifications: list[dict[str, Any]],
    versions: list[dict[str, Any]],
) -> dict[str, Any]:
    attributes = dict(classification.get("attributes", {}))
    device = _text(attributes.get("LC214/25"))
    official_link = _text(attributes.get("Link"))
    spec_views = [_specification_view(item) for item in specifications]
    rule_views = [_rule_view(item) for item in versions]
    blockers = sorted(
        {
            conflict
            for specification in specifications
            for conflict in specification.get("known_conflicts", [])
            if "NEEDS_" in conflict
        }
    )
    status = _status(device, specifications, versions, blockers)
    review_readiness = _review_readiness(specifications, blockers)
    return {
        "cst": classification["cst"],
        "cst_description": classification.get("cst_description"),
        "cclasstrib": classification["code"],
        "name": classification["name"],
        "official_description": classification["description"],
        "legal_foundation": device,
        "legal_device": device,
        "official_url": official_link or classification["source"]["official_url"],
        "valid_from": classification.get("valid_from"),
        "valid_to": classification.get("valid_to"),
        "updated_on": classification.get("updated_on"),
        "indicators": attributes,
        "official_family": _text(attributes.get("TipodeAlíquota")) or "Não informado",
        "catalog_version": classification["catalog_version"],
        "catalog_version_id": classification["catalog_version_id"],
        "catalog_source": classification["source"],
        "coverage_status": status,
        "review_readiness": review_readiness,
        "foundation_identified": bool(device),
        "specifications": spec_views,
        "rules": rule_views,
        "blockers": blockers,
        "coverage_caveat": (
            "Há regra publicada associada, sem afirmar cobertura integral de todas as hipóteses "
            "jurídicas deste cClassTrib."
            if status is CoverageStatus.PUBLISHED
            else None
        ),
    }


def _coverage_metrics(items: list[dict[str, Any]]) -> dict[str, int | str]:
    counts = Counter(item["coverage_status"] for item in items)
    total = len(items)
    published = counts[CoverageStatus.PUBLISHED]
    percentage = (
        (Decimal(published) * Decimal("100") / Decimal(total)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if total
        else Decimal("0.00")
    )
    mapped = sum(1 for item in items if item["foundation_identified"])
    return {
        "total_cclasstrib": total,
        "cataloged": total,
        "foundation_identified": mapped,
        "mapped": mapped,
        "catalog_only": counts[CoverageStatus.CATALOG_ONLY],
        "legal_mapping_required": counts[CoverageStatus.LEGAL_MAPPING_REQUIRED],
        "draft_specification": counts[CoverageStatus.DRAFT_SPECIFICATION],
        "ready_for_review": sum(
            1 for item in items if item["review_readiness"] == "READY_FOR_HUMAN_REVIEW"
        ),
        "legal_review": counts[CoverageStatus.LEGAL_REVIEW],
        "approved": counts[CoverageStatus.APPROVED],
        "implemented": counts[CoverageStatus.IMPLEMENTED],
        "published": published,
        "blocked": sum(1 for item in items if item["review_readiness"] == "BLOCKED"),
        "executable": published,
        "executable_percentage": format(percentage, ".2f"),
    }


def _family_metrics(items: list[dict[str, Any]]) -> dict[str, int | str]:
    metrics = _coverage_metrics(items)
    published = sum(
        1 for item in items if any(rule["status"] == "PUBLISHED" for rule in item["rules"])
    )
    metrics.update(
        {
            "draft_specification": sum(
                1
                for item in items
                if any(
                    specification["status"] == "DRAFT" for specification in item["specifications"]
                )
            ),
            "ready_for_review": sum(
                1 for item in items if item["review_readiness"] == "READY_FOR_HUMAN_REVIEW"
            ),
            "legal_review": sum(
                1
                for item in items
                if any(
                    specification["status"] == "IN_REVIEW"
                    for specification in item["specifications"]
                )
            ),
            "approved": sum(
                1
                for item in items
                if any(
                    specification["status"] == "APPROVED"
                    for specification in item["specifications"]
                )
            ),
            "implemented": sum(
                1
                for item in items
                if any(
                    specification["implementation"] is not None
                    for specification in item["specifications"]
                )
            ),
            "published": published,
            "blocked": sum(1 for item in items if item["blockers"]),
            "executable": published,
            "executable_percentage": _percentage(published, len(items)),
        }
    )
    return metrics


def _percentage(numerator: int, denominator: int) -> str:
    value = (
        (Decimal(numerator) * Decimal("100") / Decimal(denominator)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if denominator
        else Decimal("0.00")
    )
    return format(value, ".2f")


def _status(
    device: str | None,
    specifications: list[dict[str, Any]],
    versions: list[dict[str, Any]],
    blockers: list[str],
) -> CoverageStatus:
    candidates = [CoverageStatus.LEGAL_MAPPING_REQUIRED if device else CoverageStatus.CATALOG_ONLY]
    if blockers and not specifications:
        candidates.append(CoverageStatus.BLOCKED_EXTERNAL_SOURCE)
    for specification in specifications:
        value = str(specification.get("status", "DRAFT"))
        mapping = {
            "DRAFT": CoverageStatus.DRAFT_SPECIFICATION,
            "IN_REVIEW": CoverageStatus.LEGAL_REVIEW,
            "APPROVED": (
                CoverageStatus.IMPLEMENTED
                if specification.get("implementation")
                else CoverageStatus.APPROVED
            ),
            "IMPLEMENTED": CoverageStatus.IMPLEMENTED,
        }
        candidates.append(mapping.get(value, CoverageStatus.DRAFT_SPECIFICATION))
    for version in versions:
        value = str(version.get("lifecycle_status"))
        candidates.append(
            CoverageStatus.PUBLISHED if value == "PUBLISHED" else CoverageStatus.IMPLEMENTED
        )
    return max(candidates, key=STATUS_PRIORITY.__getitem__)


def _review_readiness(specifications: list[dict[str, Any]], blockers: list[str]) -> str:
    if blockers:
        return "BLOCKED"
    if any(
        specification.get("status") == "DRAFT" and specification.get("implementation") is None
        for specification in specifications
    ):
        return "READY_FOR_HUMAN_REVIEW"
    return "NOT_APPLICABLE"


def _catalog_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return {}
    first = items[0]
    source = first["catalog_source"]
    return {
        "version": first["catalog_version"],
        "version_id": first["catalog_version_id"],
        "status": source["status"],
        "official_title": source["title"],
        "official_url": source["official_url"],
        "technical_document": source["technical_document"],
        "publication_date": source["publication_date"],
        "artifact_hash": source["artifact_hash"],
    }


def _specification_view(value: dict[str, Any]) -> dict[str, Any]:
    foundation = value.get("legal_foundation", {})
    return {
        "rule_id": value.get("rule_id"),
        "version": value.get("specification_version"),
        "title": value.get("title"),
        "status": value.get("status"),
        "legal_device": foundation.get("specific_device"),
        "effective_from": value.get("effective_from"),
        "effective_to": value.get("effective_to"),
        "implementation": value.get("implementation"),
    }


def _rule_view(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_identity_id": value.get("rule_identity_id"),
        "rule_code": value.get("identity_code"),
        "rule_version_id": value.get("id"),
        "version": value.get("version"),
        "status": value.get("lifecycle_status"),
        "legal_device": value.get("legal_device"),
        "valid_from": value.get("valid_from"),
        "valid_to": value.get("valid_to"),
        "content_hash": value.get("content_hash"),
        "queryable_rulesets": list(value.get("queryable_rulesets", [])),
    }


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
