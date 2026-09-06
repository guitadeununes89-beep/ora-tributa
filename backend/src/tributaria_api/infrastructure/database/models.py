from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JsonDocument = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class LegalSourceRecord(Base):
    __tablename__ = "legal_sources"
    __table_args__ = (
        CheckConstraint("char_length(content_hash) = 64", name="ck_legal_source_hash_length"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(80))
    number: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    issuing_authority: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(300))
    official_url: Mapped[str] = mapped_column(String(500))
    publication_date: Mapped[date] = mapped_column(Date)
    jurisdiction: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    is_synthetic: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )


class TaxRuleIdentityRecord(Base):
    __tablename__ = "tax_rule_identities"
    __table_args__ = ()

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    is_synthetic: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(String(100))
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    versions: Mapped[list[TaxRuleVersionRecord]] = relationship(back_populates="identity")


class TaxRuleVersionRecord(Base):
    __tablename__ = "tax_rule_versions"
    __table_args__ = (
        UniqueConstraint("rule_identity_id", "version", name="uq_rule_identity_version"),
        CheckConstraint("version > 0", name="ck_rule_version_positive"),
        CheckConstraint(
            "lifecycle_status IN ('DRAFT','IN_REVIEW','APPROVED','PUBLISHED',"
            "'REJECTED','SUPERSEDED','WITHDRAWN')",
            name="ck_rule_lifecycle_status",
        ),
        CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="ck_rule_validity"),
        CheckConstraint("char_length(content_hash) = 64", name="ck_rule_content_hash_length"),
        CheckConstraint(
            "lifecycle_status NOT IN ('APPROVED','PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR approved_at IS NOT NULL AND approved_by IS NOT NULL",
            name="ck_rule_approval_metadata",
        ),
        CheckConstraint(
            "lifecycle_status NOT IN ('PUBLISHED','SUPERSEDED','WITHDRAWN') "
            "OR published_at IS NOT NULL AND published_by IS NOT NULL "
            "AND legal_source_id IS NOT NULL AND legal_device <> ''",
            name="ck_rule_publication_metadata",
        ),
        CheckConstraint(
            "specification_hash IS NULL OR char_length(specification_hash) = 64",
            name="ck_rule_specification_hash",
        ),
        CheckConstraint(
            "(specification_id IS NULL AND specification_version IS NULL "
            "AND specification_hash IS NULL AND catalog_version_id IS NULL "
            "AND cst_code IS NULL AND cclasstrib_code IS NULL AND approval_metadata IS NULL) "
            "OR (specification_id IS NOT NULL AND specification_version > 0 "
            "AND specification_hash IS NOT NULL AND catalog_version_id IS NOT NULL "
            "AND cst_code IS NOT NULL AND approval_metadata IS NOT NULL)",
            name="ck_rule_real_provenance_shape",
        ),
        ForeignKeyConstraint(
            ["catalog_version_id", "cst_code"],
            ["ibs_cbs_csts.catalog_version_id", "ibs_cbs_csts.code"],
            ondelete="RESTRICT",
            name="fk_rule_catalog_cst",
        ),
        ForeignKeyConstraint(
            ["catalog_version_id", "cclasstrib_code"],
            [
                "ibs_cbs_tax_classifications.catalog_version_id",
                "ibs_cbs_tax_classifications.code",
            ],
            ondelete="RESTRICT",
            name="fk_rule_catalog_cclasstrib",
        ),
        Index("ix_rule_versions_bitemporal", "valid_from", "valid_to", "recorded_at"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    rule_identity_id: Mapped[str] = mapped_column(
        ForeignKey("tax_rule_identities.id", ondelete="RESTRICT")
    )
    version: Mapped[int] = mapped_column(Integer)
    lifecycle_status: Mapped[str] = mapped_column(String(30))
    jurisdiction: Mapped[str] = mapped_column(String(100))
    legal_source_id: Mapped[str | None] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="RESTRICT")
    )
    legal_device: Mapped[str] = mapped_column(String(300))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_for_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(String(100))
    approved_by: Mapped[str | None] = mapped_column(String(100))
    published_by: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    content_hash: Mapped[str] = mapped_column(String(64))
    rule_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JsonDocument)
    specification_id: Mapped[str | None] = mapped_column(String(100))
    specification_version: Mapped[int | None] = mapped_column(Integer)
    specification_hash: Mapped[str | None] = mapped_column(String(64))
    catalog_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="RESTRICT")
    )
    cst_code: Mapped[str | None] = mapped_column(String(3))
    cclasstrib_code: Mapped[str | None] = mapped_column(String(6))
    approval_metadata: Mapped[dict[str, Any] | None] = mapped_column(JsonDocument)
    identity: Mapped[TaxRuleIdentityRecord] = relationship(back_populates="versions")
    legal_source: Mapped[LegalSourceRecord | None] = relationship()
    lifecycle_events: Mapped[list[RuleLifecycleEventRecord]] = relationship(
        back_populates="rule_version", order_by="RuleLifecycleEventRecord.occurred_at"
    )


class RuleLifecycleEventRecord(Base):
    __tablename__ = "rule_lifecycle_events"
    __table_args__ = (Index("ix_rule_events_version_time", "rule_version_id", "occurred_at"),)

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    rule_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_rule_versions.id", ondelete="RESTRICT")
    )
    from_status: Mapped[str] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(Text)
    related_version: Mapped[int | None] = mapped_column(Integer)
    correlation_id: Mapped[str] = mapped_column(String(100))
    rule_version: Mapped[TaxRuleVersionRecord] = relationship(back_populates="lifecycle_events")


class RuleSetRecord(Base):
    __tablename__ = "rulesets"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','PUBLISHED')", name="ck_ruleset_status"),
        CheckConstraint(
            "status <> 'PUBLISHED' OR published_at IS NOT NULL AND published_by IS NOT NULL "
            "AND fingerprint IS NOT NULL",
            name="ck_ruleset_publication_metadata",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str] = mapped_column(String(100))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[str | None] = mapped_column(String(100))
    fingerprint: Mapped[str | None] = mapped_column(String(64), unique=True)
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    items: Mapped[list[RuleSetItemRecord]] = relationship(
        back_populates="ruleset", order_by="RuleSetItemRecord.position"
    )


class RuleSetItemRecord(Base):
    __tablename__ = "ruleset_items"
    __table_args__ = (
        UniqueConstraint("ruleset_id", "rule_version_id", name="uq_ruleset_rule_version"),
        UniqueConstraint("ruleset_id", "position", name="uq_ruleset_position"),
    )

    ruleset_id: Mapped[str] = mapped_column(
        ForeignKey("rulesets.id", ondelete="CASCADE"), primary_key=True
    )
    rule_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_rule_versions.id", ondelete="RESTRICT"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer)
    ruleset: Mapped[RuleSetRecord] = relationship(back_populates="items")
    rule_version: Mapped[TaxRuleVersionRecord] = relationship()


class EvaluationRecord(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint("char_length(input_hash) = 64", name="ck_evaluation_input_hash"),
        CheckConstraint("char_length(ruleset_fingerprint) = 64", name="ck_evaluation_ruleset_hash"),
        Index("ix_evaluations_ruleset_time", "ruleset_id", "evaluated_at"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    known_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    operation_date: Mapped[date] = mapped_column(Date)
    input_hash: Mapped[str] = mapped_column(String(64))
    engine_version: Mapped[str] = mapped_column(String(100))
    ruleset_id: Mapped[str] = mapped_column(ForeignKey("rulesets.id", ondelete="RESTRICT"))
    ruleset_fingerprint: Mapped[str] = mapped_column(String(64))
    input_facts: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    outcome: Mapped[dict[str, Any]] = mapped_column(JsonDocument)
    decision_trace: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument)
    correlation_id: Mapped[str] = mapped_column(String(100))
    reproduced_from_id: Mapped[str | None] = mapped_column(
        ForeignKey("evaluations.id", ondelete="RESTRICT")
    )
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"))
    establishment_id: Mapped[str | None] = mapped_column(
        ForeignKey("establishments.id", ondelete="RESTRICT")
    )
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("product_versions.id", ondelete="RESTRICT")
    )
    catalog_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("tax_classification_catalog_versions.id", ondelete="RESTRICT")
    )
    rule_versions: Mapped[list[EvaluationRuleVersionRecord]] = relationship(
        back_populates="evaluation", order_by="EvaluationRuleVersionRecord.position"
    )


class EvaluationRuleVersionRecord(Base):
    __tablename__ = "evaluation_rule_versions"
    __table_args__ = (UniqueConstraint("evaluation_id", "position", name="uq_evaluation_position"),)

    evaluation_id: Mapped[str] = mapped_column(
        ForeignKey("evaluations.id", ondelete="RESTRICT"), primary_key=True
    )
    rule_version_id: Mapped[str] = mapped_column(
        ForeignKey("tax_rule_versions.id", ondelete="RESTRICT"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer)
    evaluation: Mapped[EvaluationRecord] = relationship(back_populates="rule_versions")


class AuditEventRecord(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_entity_time", "entity_type", "entity_id", "occurred_at"),)

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(80))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor_id: Mapped[str] = mapped_column(String(100))
    origin: Mapped[str] = mapped_column(String(100))
    correlation_id: Mapped[str] = mapped_column(String(100))
    safe_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JsonDocument)
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    authenticated_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT")
    )
