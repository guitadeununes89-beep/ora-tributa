from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query

from tributaria_api.api.auth_dependencies import (
    CompanyManagerContext,
    CorrelationId,
    IdentityRepositoryDep,
    ReadContext,
)
from tributaria_api.api.product_dependencies import ProductRepositoryDep
from tributaria_api.contracts.product import (
    ProductDetailView,
    ProductInput,
    ProductSummaryView,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductSummaryView])
def list_products(
    context: ReadContext,
    repository: ProductRepositoryDep,
    q: str | None = Query(default=None, max_length=200),
) -> list[Any]:
    return repository.list_products(context.organization_id, q)


@router.get("/{product_id}", response_model=ProductDetailView)
def get_product(
    product_id: str, context: ReadContext, repository: ProductRepositoryDep
) -> dict[str, object]:
    return repository.get(context.organization_id, product_id)


@router.post("", response_model=ProductDetailView, status_code=201)
def create_product(
    request: ProductInput,
    context: CompanyManagerContext,
    repository: ProductRepositoryDep,
    identities: IdentityRepositoryDep,
    correlation_id: CorrelationId,
) -> dict[str, object]:
    now = datetime.now(UTC)
    result = repository.create(
        context.organization_id,
        context.user_id,
        now,
        request.model_dump(mode="python"),
    )
    identities.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="product",
        entity_id=str(result["id"]),
        action="PRODUCT_CREATED",
        occurred_at=now,
        correlation_id=correlation_id,
        metadata={"version": 1},
    )
    repository.session.commit()
    return result


@router.patch("/{product_id}", response_model=ProductDetailView)
def update_product(
    product_id: str,
    request: ProductUpdate,
    context: CompanyManagerContext,
    repository: ProductRepositoryDep,
    identities: IdentityRepositoryDep,
    correlation_id: CorrelationId,
) -> dict[str, object]:
    now = datetime.now(UTC)
    fields = request.model_dump(mode="python", exclude_unset=True)
    attributes_changed = "attributes" in fields
    result = repository.update(context.organization_id, product_id, context.user_id, now, fields)
    identities.record_audit(
        organization_id=context.organization_id,
        user_id=context.user_id,
        entity_type="product",
        entity_id=product_id,
        action="PRODUCT_UPDATED",
        occurred_at=now,
        correlation_id=correlation_id,
        metadata={"version": result["current_version"]},
    )
    if attributes_changed:
        identities.record_audit(
            organization_id=context.organization_id,
            user_id=context.user_id,
            entity_type="product",
            entity_id=product_id,
            action="PRODUCT_TAX_ATTRIBUTE_CHANGED",
            occurred_at=now,
            correlation_id=correlation_id,
            metadata={"version": result["current_version"]},
        )
    repository.session.commit()
    return result
