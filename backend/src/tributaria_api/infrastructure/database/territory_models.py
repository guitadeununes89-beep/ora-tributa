"""Governed tax jurisdiction areas (ADR-0021, ADR-0024).

Schema only: no real ZFM/ALC data is loaded by this module. Populating a version's
`criteria` with an actual official territorial description is a governed-load
concern with its own legal-sourcing review, out of scope here.
"""

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


class TaxJurisdictionAreaRecord(Base):
    __tablename__ = "tax_jurisdiction_areas"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_jurisdiction_area_org_code"),
        UniqueConstraint("id", "organization_id", name="uq_jurisdiction_area_tenant_identity"),
        CheckConstraint("area_type IN ('ZFM','ALC')", name="ck_jurisdiction_area_type"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    area_type: Mapped[str] = mapped_column(String(20))
    code: Mapped[str] = mapped_column(String(100))
    official_name: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class TaxJurisdictionAreaVersionRecord(Base):
    __tablename__ = "tax_jurisdiction_area_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["area_id", "organization_id"],
            ["tax_jurisdiction_areas.id", "tax_jurisdiction_areas.organization_id"],
            ondelete="RESTRICT",
            name="fk_jurisdiction_area_version_tenant",
        ),
        UniqueConstraint("area_id", "version", name="uq_jurisdiction_area_version"),
        CheckConstraint("version > 0", name="ck_jurisdiction_area_version_positive"),
        CheckConstraint(
            "valid_to IS NULL OR valid_to > valid_from", name="ck_jurisdiction_area_validity"
        ),
        CheckConstraint(
            "char_length(content_hash) = 64", name="ck_jurisdiction_area_content_hash_length"
        ),
        CheckConstraint(
            "lifecycle_status IN "
            "('DRAFT','IN_REVIEW','APPROVED','PUBLISHED','REJECTED','SUPERSEDED','WITHDRAWN')",
            name="ck_jurisdiction_area_lifecycle_status",
        ),
        CheckConstraint(
            "lifecycle_status NOT IN ('APPROVED','PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR approved_at IS NOT NULL AND approved_by IS NOT NULL",
            name="ck_jurisdiction_area_approval_metadata",
        ),
        CheckConstraint(
            "lifecycle_status NOT IN ('PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR published_at IS NOT NULL AND published_by IS NOT NULL",
            name="ck_jurisdiction_area_publication_metadata",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    area_id: Mapped[str] = mapped_column(String(100))
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    version: Mapped[int] = mapped_column(Integer)
    lifecycle_status: Mapped[str] = mapped_column(String(30))
    legal_source_id: Mapped[str] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="RESTRICT")
    )
    legal_device: Mapped[str] = mapped_column(String(300))
    # Structured administrative description (e.g. covered municipalities or
    # subdivisions) as decided by the official source. Never a geometry, and
    # never referenced directly from tax-engine rule code (ADR-0021).
    criteria: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    content_hash: Mapped[str] = mapped_column(String(64))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class TaxJurisdictionAreaLifecycleEventRecord(Base):
    __tablename__ = "tax_jurisdiction_area_lifecycle_events"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    area_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_jurisdiction_area_versions.id", ondelete="RESTRICT")
    )
    from_status: Mapped[str] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reason: Mapped[str] = mapped_column(Text)
    correlation_id: Mapped[str] = mapped_column(String(100))
