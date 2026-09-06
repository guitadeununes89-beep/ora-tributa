from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import Path as ApiPath

from tributaria_api.api.auth_dependencies import CuratorContext
from tributaria_api.api.specification_dependencies import SpecificationReferenceLookupDep
from tributaria_api.application.tax_rule_specifications import (
    Readiness,
    SpecificationValidationResult,
    TaxRuleSpecificationValidator,
    ValidationIssue,
    load_specification,
)
from tributaria_api.config import get_settings
from tributaria_api.contracts.tax_rule_specification import SpecificationReadinessView

router = APIRouter(
    prefix="/admin/tax-rule-specifications",
    tags=["tax rule specifications"],
)
DISCLAIMER = (
    "Structural readiness does not attest to the correctness of legal interpretation."
)


@router.get("", response_model=list[SpecificationReadinessView])
def list_specifications(
    context: CuratorContext,
    references: SpecificationReferenceLookupDep,
) -> list[dict[str, Any]]:
    root = _root()
    if not root.exists():
        return []
    return [
        _validate_path(path, context.organization_id, references)
        for path in sorted(root.glob("*.json"))
    ]


@router.post(
    "/{rule_id}/preflight",
    response_model=SpecificationReadinessView,
)
def preflight_specification(
    context: CuratorContext,
    references: SpecificationReferenceLookupDep,
    rule_id: str = ApiPath(pattern=r"^(RT-IBSCBS-\d{4}|TEST-[A-Z0-9-]+)$"),
) -> dict[str, Any]:
    return _validate_path(_root() / f"{rule_id}.json", context.organization_id, references)


def _root() -> Path:
    return Path(get_settings().tax_rule_specification_root).resolve()


def _validate_path(
    path: Path,
    organization_id: str,
    references: SpecificationReferenceLookupDep,
) -> dict[str, Any]:
    if not path.is_file():
        return _view(
            SpecificationValidationResult(
                Readiness.NOT_READY,
                None,
                (
                    ValidationIssue(
                        "DOCUMENT_NOT_FOUND",
                        str(path),
                        "Specification document was not found",
                    ),
                ),
            ),
            {},
        )
    try:
        document = load_specification(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _view(
            SpecificationValidationResult(
                Readiness.NOT_READY,
                None,
                (ValidationIssue("DOCUMENT_INVALID", str(path), str(exc)),),
            ),
            {},
        )
    result = TaxRuleSpecificationValidator(references).validate(document, organization_id)
    return _view(result, document)


def _view(
    result: SpecificationValidationResult, document: dict[str, Any]
) -> dict[str, Any]:
    specification = result.specification
    foundation = document.get("legal_foundation", {})
    catalog = document.get("catalog", {})
    approval = document.get("approval", {})
    return {
        "readiness": result.readiness,
        "rule_id": specification.rule_id if specification else document.get("rule_id"),
        "specification_version": (
            specification.specification_version
            if specification
            else document.get("specification_version")
        ),
        "title": specification.title if specification else document.get("title"),
        "status": specification.status if specification else document.get("status"),
        "responsible_party": (
            specification.approval.prepared_by
            if specification
            else approval.get("prepared_by")
        ),
        "legal_source_id": (
            specification.legal_foundation.legal_source_id
            if specification
            else foundation.get("legal_source_id")
        ),
        "catalog_version_id": (
            specification.catalog.catalog_version_id
            if specification
            else catalog.get("catalog_version_id")
        ),
        "cst": specification.catalog.cst if specification else catalog.get("cst"),
        "cclasstrib": (
            specification.catalog.cclasstrib
            if specification
            else catalog.get("cclasstrib")
        ),
        "effective_from": (
            specification.effective_from if specification else document.get("effective_from")
        ),
        "effective_to": (
            specification.effective_to if specification else document.get("effective_to")
        ),
        "issues": [
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in result.issues
        ],
        "disclaimer": DISCLAIMER,
    }

