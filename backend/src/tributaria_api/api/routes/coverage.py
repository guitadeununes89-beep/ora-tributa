from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from tributaria_api.api.auth_dependencies import ReadContext
from tributaria_api.api.dependencies import RepositoryDep
from tributaria_api.api.taxonomy_dependencies import TaxonomyRepositoryDep
from tributaria_api.application.coverage import (
    build_national_coverage,
    load_specification_documents,
)
from tributaria_api.application.errors import NotFoundError
from tributaria_api.config import get_settings
from tributaria_api.contracts.coverage import CoverageItemView, NationalCoverageView

router = APIRouter(prefix="/taxonomy/ibs-cbs/coverage", tags=["IBS/CBS national coverage"])


@router.get("", response_model=NationalCoverageView)
def national_coverage(
    context: ReadContext,
    taxonomy: TaxonomyRepositoryDep,
    governance: RepositoryDep,
) -> dict[str, Any]:
    return _projection(context.organization_id, taxonomy, governance)


@router.get("/{code}", response_model=CoverageItemView)
def coverage_detail(
    code: str,
    context: ReadContext,
    taxonomy: TaxonomyRepositoryDep,
    governance: RepositoryDep,
) -> dict[str, Any]:
    projection = _projection(context.organization_id, taxonomy, governance)
    item = next((value for value in projection["items"] if value["cclasstrib"] == code), None)
    if item is None:
        raise NotFoundError("cClassTrib coverage not found")
    history: list[dict[str, Any]] = []
    for version in taxonomy.list_versions(context.organization_id, status="PUBLISHED"):
        try:
            historical = taxonomy.get_classification(
                context.organization_id, code, str(version["version"])
            )
        except NotFoundError:
            continue
        history.append(
            {
                "catalog_version": historical["catalog_version"],
                "catalog_version_id": historical["catalog_version_id"],
                "name": historical["name"],
                "official_description": historical["description"],
                "valid_from": historical["valid_from"],
                "valid_to": historical["valid_to"],
                "updated_on": historical["updated_on"],
                "artifact_hash": historical["source"]["artifact_hash"],
            }
        )
    return {**item, "history": history}


def _projection(
    organization_id: str,
    taxonomy: Any,
    governance: Any,
) -> dict[str, Any]:
    classifications = taxonomy.list_classifications(organization_id)
    specifications = load_specification_documents(
        Path(get_settings().tax_rule_specification_root).resolve()
    )
    versions = [
        value
        for value in governance.list_rule_versions()
        if value.get("organization_id") == organization_id
    ]
    return build_national_coverage(classifications, specifications, versions)
