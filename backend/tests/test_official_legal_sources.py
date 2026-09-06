from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from tributaria_api.application.errors import GovernanceError
from tributaria_api.application.governance import GovernanceService, SegregationOfDutiesPolicy


class Repository:
    def __init__(self) -> None:
        self.sources: dict[str, dict[str, Any]] = {}
        self.audits: list[dict[str, Any]] = []
        self.commits = 0

    def find_legal_source_by_hash(
        self, organization_id: str, source_hash: str
    ) -> dict[str, Any] | None:
        return next(
            (
                source
                for source in self.sources.values()
                if source["organization_id"] == organization_id
                and source["content_hash"] == source_hash
            ),
            None,
        )

    def create_legal_source(self, data: dict[str, Any]) -> dict[str, Any]:
        self.sources[data["id"]] = data
        return data

    def add_audit_event(self, event: dict[str, Any]) -> None:
        self.audits.append(event)

    def commit(self) -> None:
        self.commits += 1


def command(
    url: str = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
) -> dict[str, Any]:
    return {
        "id": None,
        "source_type": "OFFICIAL_LEGAL_ACT",
        "number": "214",
        "year": 2025,
        "issuing_authority": "Presidência da República",
        "title": "Fonte oficial sob teste",
        "official_url": url,
        "publication_date": date(2025, 1, 16),
        "jurisdiction": "BR",
        "notes": None,
        "content_hash": "a" * 64,
        "is_synthetic": False,
        "created_at": datetime(2026, 8, 30, tzinfo=UTC),
        "created_by": "curator",
        "correlation_id": "test-official-source",
        "organization_id": "org",
    }


def service(repository: Repository) -> GovernanceService:
    return GovernanceService(
        repository,  # type: ignore[arg-type]
        SegregationOfDutiesPolicy(enabled=True),
        organization_id="org",
        authenticated_user_id="curator",
    )


def test_official_source_gets_system_id_and_is_idempotent_by_hash() -> None:
    repository = Repository()
    first = service(repository).create_legal_source(command())
    second = service(repository).create_legal_source(command())

    assert first["id"]
    assert second["id"] == first["id"]
    assert len(repository.sources) == 1
    assert len(repository.audits) == 1
    assert repository.audits[0]["safe_metadata"] == {"synthetic": False}
    assert repository.commits == 1


def test_official_source_rejects_non_government_domain() -> None:
    with pytest.raises(GovernanceError, match="approved HTTPS domain"):
        service(Repository()).create_legal_source(command("https://example.com/lcp214"))
