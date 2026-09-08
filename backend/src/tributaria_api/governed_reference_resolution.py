"""Centralized resolution of governed cross-database references (Etapa 21).

Every deployment CLI (`territory_governed_load_cli.py`, `real_rule_deploy_cli.py`,
`real_rule_deploy_cli_p1_zfm.py`, `real_rule_deploy_cli_p2_medicamentos.py`) used
to carry its own copy of "resolve legal_source_id/catalog_version_id by exact
official URL" - a fix already applied piecemeal across Etapas 10, 14 and 15
after each one independently hit the same bug (a `uuid4()` literal baked into
an approved specification JSON is only valid on the database instance it was
generated on). This module is the single place that logic lives now.

Two databases can expose a legal source at the same URL with different
content (a corrected transcription, a different snapshot) - matching the URL
alone is not enough to trust that a specification's approval still applies to
what is actually persisted. `resolve_legal_source_id` therefore also requires
the caller's `expected_content_hash`, a hash the caller captured once from a
database it already trusted, and refuses to link if the two disagree. This is
deliberately NOT a field added to the approved specification JSON files: doing
that would change their canonical document and invalidate the SHA-256 already
recorded in `approval_evidence` (`_approval_hash()` hashes the whole document),
which would require a new legal approval outside this stage's scope. Instead,
each CLI pins its own expected hash as a plain module-level constant, exactly
like the existing `CURRENT_CATALOG_VERSION` pattern.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from tributaria_api.infrastructure.database.models import LegalSourceRecord
from tributaria_api.infrastructure.database.taxonomy_models import (
    IbsCbsTaxClassificationRecord,
    TaxClassificationCatalogVersionRecord,
)


def resolve_legal_source_id(
    session: Session,
    *,
    official_url: str,
    expected_content_hash: str,
    as_of: date | None = None,
) -> str:
    """Resolve a legal source by exact URL, validating identity and vigência.

    Fails closed: a URL match alone never proves the persisted source is the
    one a specification was actually approved against - the content hash
    must match too, and (when `as_of` is given) the source must already have
    been published as of that date.
    """
    record = session.scalar(
        select(LegalSourceRecord).where(LegalSourceRecord.official_url == official_url)
    )
    if record is None:
        raise RuntimeError(
            f"Legal source not found for {official_url}; run governed_load_cli first"
        )
    if record.content_hash != expected_content_hash:
        raise RuntimeError(
            f"Legal source at {official_url} has content_hash {record.content_hash}, "
            f"expected {expected_content_hash} - refusing to link a diverged source"
        )
    if as_of is not None and record.publication_date > as_of:
        raise RuntimeError(
            f"Legal source at {official_url} was published on {record.publication_date}, "
            f"after the required as_of date {as_of} - refusing to link a not-yet-effective source"
        )
    return record.id


def resolve_catalog_version_id(session: Session, *, cclasstrib: str, catalog_version: str) -> str:
    """Resolve the catalog version a given cClassTrib was actually approved against.

    More than one catalog version can carry the same cClassTrib code (e.g. the
    historical 2025-12-15 snapshot and a later one both can), so this pins to
    an explicit `catalog_version` label rather than taking whichever version
    happens to sort first.
    """
    catalog_version_id = session.scalar(
        select(IbsCbsTaxClassificationRecord.catalog_version_id)
        .join(
            TaxClassificationCatalogVersionRecord,
            TaxClassificationCatalogVersionRecord.id
            == IbsCbsTaxClassificationRecord.catalog_version_id,
        )
        .where(
            IbsCbsTaxClassificationRecord.code == cclasstrib,
            TaxClassificationCatalogVersionRecord.version == catalog_version,
        )
    )
    if catalog_version_id is None:
        raise RuntimeError(
            f"cClassTrib {cclasstrib} not found in catalog version {catalog_version}; "
            "run governed_load_cli first"
        )
    return catalog_version_id
