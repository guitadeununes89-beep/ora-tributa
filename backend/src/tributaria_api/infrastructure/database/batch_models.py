from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from tributaria_api.infrastructure.database.models import Base, JsonDocument


class ClassificationBatchRecord(Base):
    __tablename__ = "classification_batches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RECEIVED','VALIDATED','PROCESSING','COMPLETED','FAILED')",
            name="ck_classification_batch_status",
        ),
        CheckConstraint("char_length(file_hash) = 64", name="ck_classification_batch_hash"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    file_name: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str] = mapped_column(String(64))
    file_media_type: Mapped[str] = mapped_column(String(200))
    file_size: Mapped[int] = mapped_column(Integer)
    row_count: Mapped[int] = mapped_column(Integer)
    processed_count: Mapped[int] = mapped_column(Integer)
    error_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    truncated: Mapped[bool] = mapped_column(Boolean)
    max_rows: Mapped[int] = mapped_column(Integer)
    ncm_catalog_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("ncm_catalog_versions.id", ondelete="RESTRICT")
    )
    nbs_catalog_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("nbs_catalog_versions.id", ondelete="RESTRICT")
    )
    taxonomy_catalog_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="RESTRICT")
    )
    engine_version: Mapped[str | None] = mapped_column(String(100))
    reprocessed_from_id: Mapped[str | None] = mapped_column(
        ForeignKey("classification_batches.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ClassificationBatchRowRecord(Base):
    __tablename__ = "classification_batch_rows"
    __table_args__ = (
        UniqueConstraint("batch_id", "row_number", name="uq_classification_batch_row"),
        CheckConstraint(
            "object_kind IS NULL OR object_kind IN ('GOOD','SERVICE','OTHER')",
            name="ck_classification_batch_row_object_kind",
        ),
        CheckConstraint(
            "processing_status IN ('PENDING','PROCESSED','ERROR')",
            name="ck_classification_batch_row_processing_status",
        ),
        CheckConstraint(
            "classification_status IS NULL OR classification_status IN "
            "('CONCLUSIVO','POSSIVEIS_ENQUADRAMENTOS','NECESSITA_VALIDACAO',"
            "'SEM_COBERTURA_NORMATIVA')",
            name="ck_classification_batch_row_classification_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("classification_batches.id", ondelete="CASCADE")
    )
    row_number: Mapped[int] = mapped_column(Integer)
    raw_values: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    object_kind: Mapped[str | None] = mapped_column(String(10))
    internal_code: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    ncm: Mapped[str | None] = mapped_column(String(8))
    nbs: Mapped[str | None] = mapped_column(String(20))
    operation_date: Mapped[date | None] = mapped_column(Date)
    processing_status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text)
    classification_status: Mapped[str | None] = mapped_column(String(30))
    evaluation_id: Mapped[str | None] = mapped_column(
        ForeignKey("evaluations.id", ondelete="RESTRICT")
    )
    discovery_rule_codes: Mapped[list[str] | None] = mapped_column(JsonDocument)
    observations: Mapped[str | None] = mapped_column(Text)
