from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from tributaria_api.infrastructure.database.models import Base


class OrganizationRecord(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_organization_status"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserRecord(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_user_status"),)

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserCredentialRecord(Base):
    __tablename__ = "user_credentials"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    password_hash: Mapped[str] = mapped_column(String(500))
    algorithm: Mapped[str] = mapped_column(String(30))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MembershipRecord(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
        UniqueConstraint("id", "organization_id", "user_id", name="uq_membership_context"),
        CheckConstraint(
            "role IN ('VIEWER','ANALYST','CURATOR','APPROVER','PUBLISHER','ADMIN')",
            name="ck_membership_role",
        ),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_membership_status"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuthSessionRecord(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["membership_id", "organization_id", "user_id"],
            ["memberships.id", "memberships.organization_id", "memberships.user_id"],
            ondelete="CASCADE",
            name="fk_session_membership_context",
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100))
    organization_id: Mapped[str] = mapped_column(String(100))
    membership_id: Mapped[str] = mapped_column(String(100))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompanyRecord(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("organization_id", "tax_id", name="uq_company_org_tax_id"),
        UniqueConstraint("id", "organization_id", name="uq_company_tenant_identity"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_company_status"),
        CheckConstraint("tax_id ~ '^[0-9]{14}$'", name="ck_company_tax_id_shape").ddl_if(
            dialect="postgresql"
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT")
    )
    legal_name: Mapped[str] = mapped_column(String(300))
    trade_name: Mapped[str | None] = mapped_column(String(300))
    tax_id: Mapped[str] = mapped_column(String(14))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EstablishmentRecord(Base):
    __tablename__ = "establishments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "organization_id"],
            ["companies.id", "companies.organization_id"],
            ondelete="CASCADE",
            name="fk_establishment_company_tenant",
        ),
        UniqueConstraint("organization_id", "tax_id", name="uq_establishment_org_tax_id"),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_establishment_status"),
        CheckConstraint("tax_id ~ '^[0-9]{14}$'", name="ck_establishment_tax_id_shape").ddl_if(
            dialect="postgresql"
        ),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(100))
    company_id: Mapped[str] = mapped_column(String(100))
    tax_id: Mapped[str] = mapped_column(String(14))
    name: Mapped[str] = mapped_column(String(300))
    state: Mapped[str] = mapped_column(String(2))
    municipality: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
