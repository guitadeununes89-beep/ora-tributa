"""Add tenant products, immutable versions and tax review references.

Revision ID: 0005_products_assisted
Revises: 0004_ibs_cbs_taxonomy
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_products_assisted"
down_revision: str | None = "0004_ibs_cbs_taxonomy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("internal_code", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("gtin", sa.String(14)),
        sa.Column("ncm", sa.String(8)),
        sa.Column("cest", sa.String(7)),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_product_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("organization_id", "internal_code", name="uq_product_org_code"),
        sa.UniqueConstraint("id", "organization_id", name="uq_product_tenant_identity"),
    )
    op.create_table(
        "product_versions",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("product_id", sa.String(100), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("internal_code", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("gtin", sa.String(14)),
        sa.Column("ncm", sa.String(8)),
        sa.Column("cest", sa.String(7)),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.String(100), nullable=False),
        sa.Column("change_reason", sa.Text(), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_product_version_positive"),
        sa.CheckConstraint("status IN ('ACTIVE','INACTIVE')", name="ck_product_version_status"),
        sa.CheckConstraint("char_length(snapshot_hash) = 64", name="ck_product_snapshot_hash"),
        sa.ForeignKeyConstraint(
            ["product_id", "organization_id"],
            ["products.id", "products.organization_id"],
            ondelete="RESTRICT",
            name="fk_product_version_tenant",
        ),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("product_id", "version", name="uq_product_version"),
        sa.UniqueConstraint(
            "id", "product_id", "organization_id", name="uq_product_version_tenant_identity"
        ),
    )
    op.create_table(
        "product_tax_attributes",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("product_id", sa.String(100), nullable=False),
        sa.Column("product_version_id", sa.String(100), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("attribute_key", sa.String(200), nullable=False),
        sa.Column("value", JSON_DOCUMENT, nullable=False),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_by", sa.String(100), nullable=False),
        sa.CheckConstraint(
            "is_synthetic OR attribute_key NOT LIKE 'synthetic.%'",
            name="ck_product_attribute_synthetic_namespace",
        ),
        sa.ForeignKeyConstraint(
            ["product_version_id", "product_id", "organization_id"],
            [
                "product_versions.id",
                "product_versions.product_id",
                "product_versions.organization_id",
            ],
            ondelete="RESTRICT",
            name="fk_product_attribute_version_tenant",
        ),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "product_version_id", "attribute_key", name="uq_product_version_attribute"
        ),
    )
    op.create_table(
        "product_tax_reviews",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("product_id", sa.String(100), nullable=False),
        sa.Column("product_version_id", sa.String(100), nullable=False),
        sa.Column("evaluation_id", sa.String(100)),
        sa.Column("catalog_version_id", sa.String(100)),
        sa.Column("ruleset_id", sa.String(100)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('CURRENT','REVIEW_RECOMMENDED','REVIEWED')",
            name="ck_product_tax_review_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["product_id", "organization_id"],
            ["products.id", "products.organization_id"],
            ondelete="RESTRICT",
            name="fk_product_review_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["product_version_id", "product_id", "organization_id"],
            [
                "product_versions.id",
                "product_versions.product_id",
                "product_versions.organization_id",
            ],
            ondelete="RESTRICT",
            name="fk_product_review_version_tenant",
        ),
        sa.ForeignKeyConstraint(["evaluation_id"], ["evaluations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["catalog_version_id"], ["tax_classification_catalog_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["ruleset_id"], ["rulesets.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.add_column("evaluations", sa.Column("product_id", sa.String(100)))
    op.add_column("evaluations", sa.Column("product_version_id", sa.String(100)))
    op.add_column("evaluations", sa.Column("catalog_version_id", sa.String(100)))
    op.create_foreign_key(
        "fk_evaluation_product",
        "evaluations",
        "products",
        ["product_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_evaluation_product_version",
        "evaluations",
        "product_versions",
        ["product_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_evaluation_catalog_version",
        "evaluations",
        "tax_classification_catalog_versions",
        ["catalog_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    if op.get_context().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION protect_product_history() RETURNS trigger AS $$
            BEGIN
              RAISE EXCEPTION '% is immutable product history', TG_TABLE_NAME;
            END;
            $$ LANGUAGE plpgsql;
            CREATE TRIGGER product_versions_immutable
            BEFORE UPDATE OR DELETE ON product_versions
            FOR EACH ROW EXECUTE FUNCTION protect_product_history();
            CREATE TRIGGER product_attributes_immutable
            BEFORE UPDATE OR DELETE ON product_tax_attributes
            FOR EACH ROW EXECUTE FUNCTION protect_product_history();
            """
        )


def downgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute("DROP FUNCTION IF EXISTS protect_product_history() CASCADE")
    op.drop_constraint("fk_evaluation_catalog_version", "evaluations", type_="foreignkey")
    op.drop_constraint("fk_evaluation_product_version", "evaluations", type_="foreignkey")
    op.drop_constraint("fk_evaluation_product", "evaluations", type_="foreignkey")
    op.drop_column("evaluations", "catalog_version_id")
    op.drop_column("evaluations", "product_version_id")
    op.drop_column("evaluations", "product_id")
    op.drop_table("product_tax_reviews")
    op.drop_table("product_tax_attributes")
    op.drop_table("product_versions")
    op.drop_table("products")
