"""Etapa 21 (item 5/7): the centralized governed reference resolver must
refuse to link a legal source whose content_hash or vigência diverges from
what the caller expects - a URL match alone is not proof of identity."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from tributaria_api.governed_reference_resolution import (
    resolve_catalog_version_id,
    resolve_legal_source_id,
)

pytestmark = pytest.mark.skipif(
    os.getenv("POSTGRES_TESTS") != "1", reason="requires migrated PostgreSQL"
)

_URL = "https://example.invalid/pg-grr-source"
_SEEDED_CONTENT_HASH = "a" * 64
_SEEDED_PUBLICATION_DATE = date(2040, 1, 1)


@pytest.fixture(scope="module")
def engine() -> Iterator[Engine]:
    database_engine = create_engine(os.environ["DATABASE_URL"])
    with Session(database_engine) as session:
        session.execute(
            text(
                """INSERT INTO legal_sources
                (id, source_type, number, year, issuing_authority, title, official_url,
                 publication_date, jurisdiction, notes, content_hash, is_synthetic, created_at)
                VALUES ('PG-TEST-GRR-SOURCE', 'SYNTHETIC', 'TEST', 2099, 'SYNTHETIC AUTHORITY',
                'Synthetic reference-resolution source', :url, :publication_date, 'SYNTHETIC',
                'Fictitious', :hash, true, '2040-01-01T00:00:00Z')"""
            ),
            {
                "url": _URL,
                "publication_date": _SEEDED_PUBLICATION_DATE,
                "hash": _SEEDED_CONTENT_HASH,
            },
        )
        session.commit()
    yield database_engine
    database_engine.dispose()


def test_resolve_legal_source_id_accepts_matching_hash_and_vigencia(engine: Engine) -> None:
    with Session(engine) as session:
        resolved = resolve_legal_source_id(
            session,
            official_url=_URL,
            expected_content_hash=_SEEDED_CONTENT_HASH,
            as_of=date(2040, 6, 1),
        )
        assert resolved == "PG-TEST-GRR-SOURCE"


def test_resolve_legal_source_id_refuses_diverged_content_hash(engine: Engine) -> None:
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="diverged"):
            resolve_legal_source_id(
                session,
                official_url=_URL,
                expected_content_hash="b" * 64,
            )


def test_resolve_legal_source_id_refuses_not_yet_effective_source(engine: Engine) -> None:
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="not-yet-effective"):
            resolve_legal_source_id(
                session,
                official_url=_URL,
                expected_content_hash=_SEEDED_CONTENT_HASH,
                as_of=date(2039, 1, 1),
            )


def test_resolve_legal_source_id_refuses_unknown_url(engine: Engine) -> None:
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="not found"):
            resolve_legal_source_id(
                session,
                official_url="https://example.invalid/never-loaded",
                expected_content_hash=_SEEDED_CONTENT_HASH,
            )


def test_resolve_catalog_version_id_refuses_unknown_cclasstrib_for_pinned_version(
    engine: Engine,
) -> None:
    with Session(engine) as session:
        with pytest.raises(RuntimeError, match="not found in catalog version"):
            resolve_catalog_version_id(
                session,
                cclasstrib="000000-DOES-NOT-EXIST",
                catalog_version="9999-99-99",
            )
