from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from tributaria_api.infrastructure.database.models import Base, JsonDocument


class ProductRecord(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("organization_id", "internal_code", name="uq_product_org_code"),
        UniqueConstraint("id", "organization_id", name="uq_product_tenant_identity"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_product_status"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    internal_code: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    gtin: Mapped[str | None] = mapped_column(String(14))
    ncm: Mapped[str | None] = mapped_column(String(8))
    cest: Mapped[str | None] = mapped_column(String(7))
    unit: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    current_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProductVersionRecord(Base):
    __tablename__ = "product_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id", "organization_id"],
            ["products.id", "products.organization_id"],
            ondelete="RESTRICT",
            name="fk_product_version_tenant",
        ),
        UniqueConstraint("product_id", "version", name="uq_product_version"),
        UniqueConstraint(
            "id", "product_id", "organization_id", name="uq_product_version_tenant_identity"
        ),
        CheckConstraint("version > 0", name="ck_product_version_positive"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_product_version_status"),
        CheckConstraint("char_length(snapshot_hash) = 64", name="ck_product_snapshot_hash"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(100))
    organization_id: Mapped[str] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer)
    internal_code: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    gtin: Mapped[str | None] = mapped_column(String(14))
    ncm: Mapped[str | None] = mapped_column(String(8))
    cest: Mapped[str | None] = mapped_column(String(7))
    unit: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    change_reason: Mapped[str] = mapped_column(Text)
    snapshot_hash: Mapped[str] = mapped_column(String(64))


class ProductTaxAttributeRecord(Base):
    __tablename__ = "product_tax_attributes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_version_id", "product_id", "organization_id"],
            [
                "product_versions.id",
                "product_versions.product_id",
                "product_versions.organization_id",
            ],
            ondelete="RESTRICT",
            name="fk_product_attribute_version_tenant",
        ),
        UniqueConstraint(
            "product_version_id", "attribute_key", name="uq_product_version_attribute"
        ),
        CheckConstraint(
            "is_synthetic OR attribute_key NOT LIKE 'synthetic.%'",
            name="ck_product_attribute_synthetic_namespace",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(100))
    product_version_id: Mapped[str] = mapped_column(String(100))
    organization_id: Mapped[str] = mapped_column(String(100))
    attribute_key: Mapped[str] = mapped_column(String(200))
    value: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    is_synthetic: Mapped[bool]
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class ProductTaxReviewRecord(Base):
    __tablename__ = "product_tax_reviews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id", "organization_id"],
            ["products.id", "products.organization_id"],
            ondelete="RESTRICT",
            name="fk_product_review_tenant",
        ),
        ForeignKeyConstraint(
            ["product_version_id", "product_id", "organization_id"],
            [
                "product_versions.id",
                "product_versions.product_id",
                "product_versions.organization_id",
            ],
            ondelete="RESTRICT",
            name="fk_product_review_version_tenant",
        ),
        CheckConstraint(
            "status IN ('CURRENT','REVIEW_RECOMMENDED','REVIEWED')",
            name="ck_product_tax_review_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    product_id: Mapped[str] = mapped_column(String(100))
    product_version_id: Mapped[str] = mapped_column(String(100))
    evaluation_id: Mapped[str | None] = mapped_column(
        ForeignKey("evaluations.id", ondelete="RESTRICT")
    )
    catalog_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="RESTRICT")
    )
    ruleset_id: Mapped[str | None] = mapped_column(ForeignKey("rulesets.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(30))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
