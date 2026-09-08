"""PostgreSQL persistence adapter."""

from __future__ import annotations

# Every mapped module below declares `ForeignKey("<table>.id", ...)` strings that cross
# module boundaries (e.g. `models.py` references `organizations.id`, owned by
# `identity_models.py`). SQLAlchemy only resolves those strings against tables that have
# actually been imported into `Base.metadata`. Importing the full set here — as a side
# effect of importing this package — guarantees that any entry point (API, CLI, seed
# script) that touches only one module still sees the complete schema graph.
from tributaria_api.infrastructure.database import (
    identity_models,
    models,
    nbs_models,
    ncm_models,
    product_models,
    taxonomy_models,
    territory_models,
)

__all__ = [
    "identity_models",
    "models",
    "nbs_models",
    "ncm_models",
    "product_models",
    "taxonomy_models",
    "territory_models",
]
