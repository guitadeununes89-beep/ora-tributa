"""Etapa 21 (item 6): the real governed load/deploy CLIs, run against a
database that has never seen this machine's UUIDs before.

Every earlier stage's UUID-portability bug (Etapas 10, 14, 15) came from a
CLI trusting a `legal_source_id`/`catalog_version_id` literal that had been
generated on a *different* database instance. The only way to actually catch
a regression of that class is to run the CLIs, unmodified, against a brand
new database and confirm every reference is resolved dynamically. This test
creates a throwaway database on the same PostgreSQL server as the other
Postgres-gated tests, migrates it, runs the CLIs as real subprocesses (same
entrypoints used in production), and drops the database afterwards - so it
never leaves synthetic rows in any database a person might open later.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.skipif(
    os.getenv("POSTGRES_TESTS") != "1", reason="requires a real PostgreSQL server"
)

_APPROVER_EMAIL = "fresh-database-test-approver@example.invalid"
_REPO_ROOT = Path(__file__).resolve().parents[2]
# Every deploy CLI writes the identity/version it just deployed back into its
# tracked specification JSON as an `implementation` record - regardless of
# which database it targeted. Run against this test's throwaway database,
# that would overwrite each file with disposable UUIDs that don't match the
# real deployment, corrupting tracked, committed provenance data. Snapshot
# and restore them so this test never leaves the working tree dirty.
_SPEC_FILES_WRITTEN_BY_CLIS = tuple(
    _REPO_ROOT / relative
    for relative in (
        "docs/tax/rules/specifications/RT-IBSCBS-0003.json",
        "docs/tax/rules/specifications/RT-IBSCBS-0004.json",
        "docs/tax/rules/specifications/RT-IBSCBS-0005.json",
        "docs/tax/rules/specifications/RT-IBSCBS-0007.json",
        "docs/tax/rules/specifications/RT-IBSCBS-0008.json",
        "docs/tax/territory/specifications/TJA-ZFM.json",
        "docs/tax/territory/specifications/TJA-ALC-TABATINGA.json",
        "docs/tax/territory/specifications/TJA-ALC-GUAJARA-MIRIM.json",
        "docs/tax/territory/specifications/TJA-ALC-BOA-VISTA-BONFIM.json",
        "docs/tax/territory/specifications/TJA-ALC-MACAPA-SANTANA.json",
        "docs/tax/territory/specifications/TJA-ALC-BRASILEIA-CRUZEIRO-DO-SUL.json",
    )
)


def _admin_url(database: str) -> str:
    base = os.environ["DATABASE_URL"]
    prefix, _, _ = base.rpartition("/")
    return f"{prefix}/{database}"


def _run(module: str, *, database_url: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["DATABASE_URL"] = database_url
    env["REAL_RULE_APPROVER_EMAIL"] = _APPROVER_EMAIL
    return subprocess.run(
        [sys.executable, "-m", module],
        cwd=os.path.join(os.path.dirname(__file__), "..", "src"),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_fresh_database_reproduces_the_full_governed_deploy_without_stale_uuids() -> None:
    original_spec_bytes = {path: path.read_bytes() for path in _SPEC_FILES_WRITTEN_BY_CLIS}
    fresh_db_name = f"tributaria_fresh_test_{uuid.uuid4().hex[:12]}"
    admin_engine = create_engine(_admin_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{fresh_db_name}"'))
    try:
        fresh_url = _admin_url(fresh_db_name)

        migration = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
            env={**os.environ, "DATABASE_URL": fresh_url},
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert migration.returncode == 0, migration.stderr

        repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
        for script in (
            "database/seeds/development_governance.py",
            "database/seeds/development_identity.py",
            "database/seeds/development_synthetic.py",
        ):
            result = subprocess.run(
                [sys.executable, script],
                cwd=repo_root,
                env={**os.environ, "DATABASE_URL": fresh_url, "DEV_SEED_PASSWORD": "x" * 16},
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result.returncode == 0, result.stderr

        for module in (
            "tributaria_api.governed_load_cli",
            "tributaria_api.territory_governed_load_cli",
            "tributaria_api.real_rule_deploy_cli",
            "tributaria_api.real_rule_deploy_cli_p2_medicamentos",
            "tributaria_api.real_rule_deploy_cli_p1_zfm",
            "tributaria_api.governed_ncm_nbs_load_cli",
        ):
            result = _run(module, database_url=fresh_url)
            assert result.returncode == 0, result.stderr

        fresh_engine = create_engine(fresh_url)
        with fresh_engine.connect() as connection:
            published_codes = connection.execute(
                text(
                    """SELECT identity.code FROM tax_rule_versions AS version
                    JOIN tax_rule_identities AS identity
                        ON identity.id = version.rule_identity_id
                    WHERE version.lifecycle_status = 'PUBLISHED'
                    ORDER BY identity.code"""
                )
            ).scalars().all()
            assert published_codes == [
                "RT-IBSCBS-0003",
                "RT-IBSCBS-0004",
                "RT-IBSCBS-0005",
                "RT-IBSCBS-0007",
                "RT-IBSCBS-0008",
            ]
            ncm_status = connection.execute(
                text("SELECT status FROM ncm_catalog_versions")
            ).scalars().all()
            nbs_status = connection.execute(
                text("SELECT status FROM nbs_catalog_versions")
            ).scalars().all()
            assert ncm_status == ["PUBLISHED"]
            assert nbs_status == ["PUBLISHED"]
        fresh_engine.dispose()
    finally:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :name AND pid <> pg_backend_pid()"
                ),
                {"name": fresh_db_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{fresh_db_name}"'))
        admin_engine.dispose()
        for path, original_bytes in original_spec_bytes.items():
            if path.read_bytes() != original_bytes:
                path.write_bytes(original_bytes)
