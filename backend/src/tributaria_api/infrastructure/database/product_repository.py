from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tributaria_api.application.errors import ConflictError, NotFoundError
from tributaria_api.infrastructure.database.product_models import (
    ProductRecord,
    ProductTaxAttributeRecord,
    ProductTaxReviewRecord,
    ProductVersionRecord,
)


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_products(self, organization_id: str, q: str | None = None) -> list[ProductRecord]:
        statement = select(ProductRecord).where(ProductRecord.organization_id == organization_id)
        if q:
            term = f"%{q.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(ProductRecord.internal_code).like(term),
                    func.lower(ProductRecord.description).like(term),
                    ProductRecord.gtin.like(f"%{q}%"),
                    ProductRecord.ncm.like(f"%{q}%"),
                )
            )
        return list(self.session.scalars(statement.order_by(ProductRecord.internal_code)))

    def get_record(self, organization_id: str, product_id: str) -> ProductRecord:
        record = self.session.scalar(
            select(ProductRecord).where(
                ProductRecord.id == product_id,
                ProductRecord.organization_id == organization_id,
            )
        )
        if record is None:
            raise NotFoundError("Product not found")
        return record

    def create(
        self,
        organization_id: str,
        actor_id: str,
        occurred_at: datetime,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        attributes = data.pop("attributes", [])
        reason = data.pop("change_reason")
        product = ProductRecord(
            id=str(uuid4()),
            organization_id=organization_id,
            current_version=1,
            created_at=occurred_at,
            updated_at=occurred_at,
            **data,
        )
        self.session.add(product)
        try:
            self.session.flush()
            self._add_version(product, actor_id, occurred_at, reason, attributes)
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Product code already exists in this organization") from exc
        return self.get(organization_id, product.id)

    def update(
        self,
        organization_id: str,
        product_id: str,
        actor_id: str,
        occurred_at: datetime,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        product = self.get_record(organization_id, product_id)
        current = self._version(product.id, product.current_version)
        attributes = changes.pop("attributes", None)
        reason = changes.pop("change_reason")
        for field, value in changes.items():
            setattr(product, field, value)
        product.current_version += 1
        product.updated_at = occurred_at
        if attributes is None:
            attributes = [
                {"key": item.attribute_key, "value": item.value, "is_synthetic": item.is_synthetic}
                for item in self._attributes(current.id)
            ]
        try:
            self._add_version(product, actor_id, occurred_at, reason, attributes)
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Product update conflicts with an existing code") from exc
        return self.get(organization_id, product.id)

    def get(self, organization_id: str, product_id: str) -> dict[str, Any]:
        product = self.get_record(organization_id, product_id)
        versions = list(
            self.session.scalars(
                select(ProductVersionRecord)
                .where(
                    ProductVersionRecord.product_id == product.id,
                    ProductVersionRecord.organization_id == organization_id,
                )
                .order_by(ProductVersionRecord.version.desc())
            )
        )
        views = [self._version_view(item) for item in versions]
        return {**_product_view(product), "current": views[0], "history": views}

    def current_snapshot(self, organization_id: str, product_id: str) -> dict[str, Any]:
        product = self.get_record(organization_id, product_id)
        return self._version_view(self._version(product.id, product.current_version))

    def record_tax_review(
        self,
        *,
        review_id: str,
        organization_id: str,
        product_id: str,
        product_version_id: str,
        evaluation_id: str,
        catalog_version_id: str,
        ruleset_id: str | None,
        reviewed_at: datetime,
        reviewed_by: str,
    ) -> ProductTaxReviewRecord:
        self.get_record(organization_id, product_id)
        product_version = self.session.scalar(
            select(ProductVersionRecord).where(
                ProductVersionRecord.id == product_version_id,
                ProductVersionRecord.product_id == product_id,
                ProductVersionRecord.organization_id == organization_id,
            )
        )
        if product_version is None:
            raise NotFoundError("Product version not found")
        review = ProductTaxReviewRecord(
            id=review_id,
            organization_id=organization_id,
            product_id=product_id,
            product_version_id=product_version_id,
            evaluation_id=evaluation_id,
            catalog_version_id=catalog_version_id,
            ruleset_id=ruleset_id,
            status="REVIEWED",
            reviewed_at=reviewed_at,
            reviewed_by=reviewed_by,
            created_at=reviewed_at,
        )
        self.session.add(review)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Tax classification review conflicts with existing data") from exc
        return review
    def _version(self, product_id: str, version: int) -> ProductVersionRecord:
        record = self.session.scalar(
            select(ProductVersionRecord).where(
                ProductVersionRecord.product_id == product_id,
                ProductVersionRecord.version == version,
            )
        )
        if record is None:
            raise NotFoundError("Product version not found")
        return record

    def _attributes(self, version_id: str) -> list[ProductTaxAttributeRecord]:
        return list(
            self.session.scalars(
                select(ProductTaxAttributeRecord)
                .where(ProductTaxAttributeRecord.product_version_id == version_id)
                .order_by(ProductTaxAttributeRecord.attribute_key)
            )
        )

    def _add_version(
        self,
        product: ProductRecord,
        actor_id: str,
        occurred_at: datetime,
        reason: str,
        attributes: list[dict[str, Any]],
    ) -> ProductVersionRecord:
        snapshot = {
            "attributes": sorted(attributes, key=lambda item: item["key"]),
            "cest": product.cest,
            "description": product.description,
            "gtin": product.gtin,
            "internal_code": product.internal_code,
            "ncm": product.ncm,
            "status": product.status,
            "unit": product.unit,
            "version": product.current_version,
        }
        fingerprint = hashlib.sha256(
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        version = ProductVersionRecord(
            id=str(uuid4()),
            product_id=product.id,
            organization_id=product.organization_id,
            version=product.current_version,
            internal_code=product.internal_code,
            description=product.description,
            gtin=product.gtin,
            ncm=product.ncm,
            cest=product.cest,
            unit=product.unit,
            status=product.status,
            recorded_at=occurred_at,
            recorded_by=actor_id,
            change_reason=reason,
            snapshot_hash=fingerprint,
        )
        self.session.add(version)
        self.session.flush()
        self.session.add_all(
            ProductTaxAttributeRecord(
                id=str(uuid4()),
                product_id=product.id,
                product_version_id=version.id,
                organization_id=product.organization_id,
                attribute_key=item["key"],
                value=(
                    item["value"]
                    if isinstance(item["value"], dict)
                    else {"type": "STRING", "value": item["value"]}
                ),
                is_synthetic=item["is_synthetic"],
                recorded_at=occurred_at,
                recorded_by=actor_id,
            )
            for item in attributes
        )
        return version

    def _version_view(self, version: ProductVersionRecord) -> dict[str, Any]:
        return {
            "id": version.id,
            "version": version.version,
            "internal_code": version.internal_code,
            "description": version.description,
            "gtin": version.gtin,
            "ncm": version.ncm,
            "cest": version.cest,
            "unit": version.unit,
            "status": version.status,
            "recorded_at": version.recorded_at,
            "recorded_by": version.recorded_by,
            "change_reason": version.change_reason,
            "snapshot_hash": version.snapshot_hash,
            "attributes": [
                {"key": item.attribute_key, "value": item.value, "is_synthetic": item.is_synthetic}
                for item in self._attributes(version.id)
            ],
        }


def _product_view(product: ProductRecord) -> dict[str, Any]:
    return {
        "id": product.id,
        "internal_code": product.internal_code,
        "description": product.description,
        "gtin": product.gtin,
        "ncm": product.ncm,
        "cest": product.cest,
        "unit": product.unit,
        "status": product.status,
        "current_version": product.current_version,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
