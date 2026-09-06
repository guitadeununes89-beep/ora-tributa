from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
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


class TaxClassificationCatalogRecord(Base):
    __tablename__ = "tax_classification_catalogs"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_tax_catalog_org_code"),
        UniqueConstraint("id", "organization_id", name="uq_tax_catalog_tenant_identity"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    code: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class TaxClassificationCatalogVersionRecord(Base):
    __tablename__ = "tax_classification_catalog_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["catalog_id", "organization_id"],
            ["tax_classification_catalogs.id", "tax_classification_catalogs.organization_id"],
            ondelete="RESTRICT",
            name="fk_tax_catalog_version_tenant",
        ),
        UniqueConstraint("catalog_id", "version", name="uq_tax_catalog_version"),
        UniqueConstraint("catalog_id", "artifact_hash", name="uq_tax_catalog_artifact"),
        CheckConstraint(
            "status IN ('IMPORTED','VALIDATED','IN_REVIEW','APPROVED','PUBLISHED','FAILED')",
            name="ck_tax_catalog_version_status",
        ),
        CheckConstraint("char_length(artifact_hash) = 64", name="ck_tax_catalog_artifact_hash"),
        CheckConstraint("char_length(normalized_hash) = 64", name="ck_tax_catalog_normalized_hash"),
        CheckConstraint("char_length(schema_signature) = 64", name="ck_tax_catalog_schema_hash"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    catalog_id: Mapped[str] = mapped_column(String(100))
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    legal_source_id: Mapped[str] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="RESTRICT")
    )
    version: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    official_title: Mapped[str] = mapped_column(String(500))
    official_url: Mapped[str] = mapped_column(String(1000))
    technical_document: Mapped[str] = mapped_column(String(300))
    publication_date: Mapped[date] = mapped_column(Date)
    consulted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    artifact_file_name: Mapped[str] = mapped_column(String(500))
    artifact_path: Mapped[str] = mapped_column(String(1000))
    artifact_media_type: Mapped[str] = mapped_column(String(200))
    artifact_size: Mapped[int] = mapped_column(Integer)
    artifact_hash: Mapped[str] = mapped_column(String(64))
    normalized_hash: Mapped[str] = mapped_column(String(64))
    schema_signature: Mapped[str] = mapped_column(String(64))
    cst_count: Mapped[int] = mapped_column(Integer)
    cclasstrib_count: Mapped[int] = mapped_column(Integer)
    import_report: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    imported_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class TaxClassificationStagingRowRecord(Base):
    __tablename__ = "tax_classification_staging_rows"
    __table_args__ = (
        UniqueConstraint(
            "catalog_version_id", "sheet_name", "row_number", name="uq_tax_staging_row"
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    catalog_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="CASCADE")
    )
    sheet_name: Mapped[str] = mapped_column(String(200))
    row_number: Mapped[int] = mapped_column(Integer)
    raw_values: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)


class IbsCbsCstRecord(Base):
    __tablename__ = "ibs_cbs_csts"
    __table_args__ = (CheckConstraint("char_length(code) = 3", name="ck_ibs_cbs_cst_length"),)

    catalog_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    description: Mapped[str] = mapped_column(Text)
    indicators: Mapped[dict[str, Any]] = mapped_column(JsonDocument)


class IbsCbsTaxClassificationRecord(Base):
    __tablename__ = "ibs_cbs_tax_classifications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["catalog_version_id", "cst_code"],
            ["ibs_cbs_csts.catalog_version_id", "ibs_cbs_csts.code"],
            ondelete="RESTRICT",
            name="fk_cclasstrib_cst_version",
        ),
        CheckConstraint("char_length(code) = 6", name="ck_cclasstrib_length"),
    )

    catalog_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(String(6), primary_key=True)
    cst_code: Mapped[str] = mapped_column(String(3))
    cst_description: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    updated_on: Mapped[date | None] = mapped_column(Date)
    attributes: Mapped[dict[str, Any]] = mapped_column(JsonDocument)


class CatalogLifecycleEventRecord(Base):
    __tablename__ = "catalog_lifecycle_events"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    catalog_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="RESTRICT")
    )
    from_status: Mapped[str] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reason: Mapped[str] = mapped_column(Text)
    correlation_id: Mapped[str] = mapped_column(String(100))
