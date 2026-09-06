"""Enable governed provenance for the first real tax rule.

Revision ID: 0006_first_real_tax_rule
Revises: 0005_products_assisted
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_first_real_tax_rule"
down_revision: str | None = "0005_products_assisted"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.drop_constraint(
        "ck_rule_identity_synthetic_foundation", "tax_rule_identities", type_="check"
    )
    op.add_column("tax_rule_versions", sa.Column("specification_id", sa.String(100)))
    op.add_column("tax_rule_versions", sa.Column("specification_version", sa.Integer()))
    op.add_column("tax_rule_versions", sa.Column("specification_hash", sa.String(64)))
    op.add_column("tax_rule_versions", sa.Column("catalog_version_id", sa.String(100)))
    op.add_column("tax_rule_versions", sa.Column("cst_code", sa.String(3)))
    op.add_column("tax_rule_versions", sa.Column("cclasstrib_code", sa.String(6)))
    op.add_column("tax_rule_versions", sa.Column("approval_metadata", JSON_DOCUMENT))
    op.create_check_constraint(
        "ck_rule_specification_hash",
        "tax_rule_versions",
        "specification_hash IS NULL OR char_length(specification_hash) = 64",
    )
    op.create_check_constraint(
        "ck_rule_real_provenance_shape",
        "tax_rule_versions",
        "(specification_id IS NULL AND specification_version IS NULL "
        "AND specification_hash IS NULL AND catalog_version_id IS NULL "
        "AND cst_code IS NULL AND cclasstrib_code IS NULL AND approval_metadata IS NULL) "
        "OR (specification_id IS NOT NULL AND specification_version > 0 "
        "AND specification_hash IS NOT NULL AND catalog_version_id IS NOT NULL "
        "AND cst_code IS NOT NULL AND approval_metadata IS NOT NULL)",
    )
    op.create_foreign_key(
        "fk_rule_catalog_version",
        "tax_rule_versions",
        "tax_classification_catalog_versions",
        ["catalog_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_rule_catalog_cst",
        "tax_rule_versions",
        "ibs_cbs_csts",
        ["catalog_version_id", "cst_code"],
        ["catalog_version_id", "code"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_rule_catalog_cclasstrib",
        "tax_rule_versions",
        "ibs_cbs_tax_classifications",
        ["catalog_version_id", "cclasstrib_code"],
        ["catalog_version_id", "code"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_rule_catalog_cclasstrib", "tax_rule_versions", type_="foreignkey")
    op.drop_constraint("fk_rule_catalog_cst", "tax_rule_versions", type_="foreignkey")
    op.drop_constraint("fk_rule_catalog_version", "tax_rule_versions", type_="foreignkey")
    op.drop_constraint("ck_rule_real_provenance_shape", "tax_rule_versions", type_="check")
    op.drop_constraint("ck_rule_specification_hash", "tax_rule_versions", type_="check")
    for column in (
        "approval_metadata",
        "cclasstrib_code",
        "cst_code",
        "catalog_version_id",
        "specification_hash",
        "specification_version",
        "specification_id",
    ):
        op.drop_column("tax_rule_versions", column)
    op.create_check_constraint(
        "ck_rule_identity_synthetic_foundation", "tax_rule_identities", "is_synthetic"
    )
