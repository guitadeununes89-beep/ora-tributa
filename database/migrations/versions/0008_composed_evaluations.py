"""Allow composed (multi-ruleset) evaluations (Etapa 21, ADR-0025).

A composed evaluation reasons over several single-rule rulesets at once and
has no single `rulesets.id` to point at - the set of rule versions actually
evaluated is still fully recorded, unchanged, in `evaluation_rule_versions`.
`composed_ruleset_ids` records which single-rule rulesets were composed, so
a rule version that also belongs to a historical combined ruleset (e.g.
IBSCBS-ZFM-PILOT-001) is never ambiguous to trace back. This migration only
relaxes `ruleset_id` and adds the new nullable column; no existing row is
affected, since every evaluation recorded so far already has a non-null
`ruleset_id` and no composed evaluation has ever been recorded.

Revision ID: 0008_composed_evaluations
Revises: 0007_tax_jurisdiction_areas
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_composed_evaluations"
down_revision: str | None = "0007_tax_jurisdiction_areas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_DOCUMENT = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.alter_column("evaluations", "ruleset_id", nullable=True)
    op.add_column("evaluations", sa.Column("composed_ruleset_ids", JSON_DOCUMENT))


def downgrade() -> None:
    op.drop_column("evaluations", "composed_ruleset_ids")
    op.alter_column("evaluations", "ruleset_id", nullable=False)
