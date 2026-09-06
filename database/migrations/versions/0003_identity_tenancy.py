"""Add identity, tenancy, companies and authenticated audit context.

Revision ID: 0003_identity_tenancy
Revises: 0002_harden_governance
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_identity_tenancy"
down_revision: str | None = "0002_harden_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_organization_status"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_user_status"),
    )
    op.create_table(
        "user_credentials",
        sa.Column(
            "user_id",
            sa.String(100),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("password_hash", sa.String(500), nullable=False),
        sa.Column("algorithm", sa.String(30), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(100),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.String(100), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
        sa.UniqueConstraint("id", "organization_id", "user_id", name="uq_membership_context"),
        sa.CheckConstraint(
            "role IN ('VIEWER','ANALYST','CURATOR','APPROVER','PUBLISHER','ADMIN')",
            name="ck_membership_role",
        ),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_membership_status"),
    )
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("membership_id", sa.String(100), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("csrf_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["membership_id", "organization_id", "user_id"],
            ["memberships.id", "memberships.organization_id", "memberships.user_id"],
            ondelete="CASCADE",
            name="fk_session_membership_context",
        ),
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(100),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("legal_name", sa.String(300), nullable=False),
        sa.Column("trade_name", sa.String(300)),
        sa.Column("tax_id", sa.String(14), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("organization_id", "tax_id", name="uq_company_org_tax_id"),
        sa.UniqueConstraint("id", "organization_id", name="uq_company_tenant_identity"),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_company_status"),
        sa.CheckConstraint("tax_id ~ '^[0-9]{14}$'", name="ck_company_tax_id_shape"),
    )
    op.create_table(
        "establishments",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("company_id", sa.String(100), nullable=False),
        sa.Column("tax_id", sa.String(14), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("municipality", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id", "organization_id"],
            ["companies.id", "companies.organization_id"],
            ondelete="CASCADE",
            name="fk_establishment_company_tenant",
        ),
        sa.UniqueConstraint("organization_id", "tax_id", name="uq_establishment_org_tax_id"),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_establishment_status"),
        sa.CheckConstraint("tax_id ~ '^[0-9]{14}$'", name="ck_establishment_tax_id_shape"),
    )
    for table in (
        "legal_sources",
        "tax_rule_identities",
        "rulesets",
        "evaluations",
        "audit_events",
    ):
        op.add_column(table, sa.Column("organization_id", sa.String(100)))
        op.create_foreign_key(
            f"fk_{table}_organization",
            table,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
    op.add_column("audit_events", sa.Column("authenticated_user_id", sa.String(100)))
    op.create_foreign_key(
        "fk_audit_authenticated_user",
        "audit_events",
        "users",
        ["authenticated_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.add_column("evaluations", sa.Column("company_id", sa.String(100)))
    op.add_column("evaluations", sa.Column("establishment_id", sa.String(100)))
    op.create_foreign_key(
        "fk_evaluation_company",
        "evaluations",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_evaluation_establishment",
        "evaluations",
        "establishments",
        ["establishment_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_evaluation_establishment", "evaluations", type_="foreignkey")
    op.drop_constraint("fk_evaluation_company", "evaluations", type_="foreignkey")
    op.drop_column("evaluations", "establishment_id")
    op.drop_column("evaluations", "company_id")
    op.drop_constraint("fk_audit_authenticated_user", "audit_events", type_="foreignkey")
    op.drop_column("audit_events", "authenticated_user_id")
    for table in reversed(
        ("legal_sources", "tax_rule_identities", "rulesets", "evaluations", "audit_events")
    ):
        op.drop_constraint(f"fk_{table}_organization", table, type_="foreignkey")
        op.drop_column(table, "organization_id")
    op.drop_table("establishments")
    op.drop_table("companies")
    op.drop_table("auth_sessions")
    op.drop_table("memberships")
    op.drop_table("user_credentials")
    op.drop_table("users")
    op.drop_table("organizations")
