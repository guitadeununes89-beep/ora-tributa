from __future__ import annotations

from tributaria_api.application.coverage import build_national_coverage


def classification(code: str, device: str | None, family: str = "Padrão") -> dict:
    return {
        "code": code,
        "cst": "200",
        "cst_description": "Fixture CST",
        "name": f"Fixture {code}",
        "description": "Official fixture description",
        "valid_from": "2026-01-01",
        "valid_to": None,
        "updated_on": None,
        "attributes": {
            "LC214/25": device,
            "Link": "https://example.invalid/official",
            "TipodeAlíquota": family,
        },
        "catalog_version": "TEST-1",
        "catalog_version_id": "catalog",
        "source": {
            "status": "PUBLISHED",
            "title": "Synthetic official catalog",
            "official_url": "https://example.invalid/catalog",
            "technical_document": "TEST",
            "publication_date": "2040-01-01",
            "artifact_hash": "a" * 64,
        },
    }


def specification(rule_id: str, code: str, status: str = "DRAFT") -> dict:
    return {
        "rule_id": rule_id,
        "specification_version": 1,
        "title": "Synthetic specification",
        "status": status,
        "legal_foundation": {"specific_device": "Synthetic device"},
        "effective_from": "2040-01-01",
        "effective_to": None,
        "catalog": {"cclasstrib": code},
        "known_conflicts": [],
        "implementation": None,
    }


def test_coverage_keeps_catalog_specifications_and_rules_distinct() -> None:
    result = build_national_coverage(
        [classification("200001", "Art. 1"), classification("200002", None)],
        [
            specification("TEST-RULE-1", "200001"),
            specification("TEST-RULE-2", "200001"),
        ],
        [],
    )

    assert result["metrics"]["total_cclasstrib"] == 2
    assert result["metrics"]["draft_specification"] == 1
    assert result["metrics"]["ready_for_review"] == 1
    assert result["metrics"]["catalog_only"] == 1
    assert len(result["items"][0]["specifications"]) == 2
    assert result["metrics"]["executable_percentage"] == "0.00"
    assert result["families"] == [
        {
            "name": "Padrão",
            "total_cclasstrib": 2,
            "cataloged": 2,
            "foundation_identified": 1,
            "mapped": 1,
            "catalog_only": 1,
            "legal_mapping_required": 0,
            "draft_specification": 1,
            "ready_for_review": 1,
            "legal_review": 0,
            "approved": 0,
            "implemented": 0,
            "published": 0,
            "blocked": 0,
            "executable": 0,
            "executable_percentage": "0.00",
        }
    ]


def test_published_rule_counts_the_code_once_and_marks_scope_as_partial() -> None:
    result = build_national_coverage(
        [classification("200010", "Art. 146")],
        [specification("RT-IBSCBS-0003", "200010", "APPROVED")],
        [
            {
                "id": "version",
                "rule_identity_id": "identity",
                "identity_code": "RT-IBSCBS-0003",
                "version": 1,
                "lifecycle_status": "PUBLISHED",
                "cclasstrib_code": "200010",
                "legal_device": "Art. 146",
                "valid_from": "2026-01-01",
                "valid_to": None,
                "content_hash": "b" * 64,
                "queryable_rulesets": ["IBSCBS-PILOT-001"],
            }
        ],
    )

    assert result["metrics"]["published"] == 1
    assert result["metrics"]["executable_percentage"] == "100.00"
    assert result["items"][0]["coverage_status"] == "PUBLISHED"
    assert "sem afirmar cobertura integral" in result["items"][0]["coverage_caveat"]
    assert result["items"][0]["rules"][0]["queryable_rulesets"] == ["IBSCBS-PILOT-001"]


def test_published_rule_without_a_single_rule_ruleset_has_no_queryable_ruleset() -> None:
    """A rule can be PUBLISHED yet only belong to a bundled ruleset (e.g. the abandoned
    IBSCBS-ZFM-PILOT-001 combining two mutually-exclusive rules, see CLAUDE_STATUS.md
    Etapa 11) - the repository already excludes those, so this only has to prove the
    coverage projection surfaces whatever the repository sends, empty list included."""
    result = build_national_coverage(
        [classification("200022", "Art. 445")],
        [specification("RT-IBSCBS-0007", "200022", "APPROVED")],
        [
            {
                "id": "version",
                "rule_identity_id": "identity",
                "identity_code": "RT-IBSCBS-0007",
                "version": 1,
                "lifecycle_status": "PUBLISHED",
                "cclasstrib_code": "200022",
                "legal_device": "Art. 445",
                "valid_from": "2026-01-01",
                "valid_to": None,
                "content_hash": "c" * 64,
                "queryable_rulesets": [],
            }
        ],
    )

    assert result["items"][0]["coverage_status"] == "PUBLISHED"
    assert result["items"][0]["rules"][0]["queryable_rulesets"] == []


def test_coverage_groups_codes_by_official_family_without_assuming_one_rule_per_code() -> None:
    result = build_national_coverage(
        [
            classification("200001", "Art. 1", "Padrão"),
            classification("400001", "Art. 2", "Sem alíquota"),
        ],
        [
            specification("TEST-RULE-1", "200001"),
            specification("TEST-RULE-2", "200001"),
        ],
        [],
    )

    assert [family["name"] for family in result["families"]] == ["Padrão", "Sem alíquota"]
    assert result["families"][0]["draft_specification"] == 1
    assert result["families"][0]["total_cclasstrib"] == 1


def test_draft_with_explicit_blocker_is_not_ready_for_human_review() -> None:
    blocked = specification("TEST-RULE-1", "200001")
    blocked["known_conflicts"] = ["NEEDS_OFFICIAL_SOURCE: unresolved"]

    result = build_national_coverage([classification("200001", "Art. 1")], [blocked], [])

    assert result["items"][0]["coverage_status"] == "DRAFT_SPECIFICATION"
    assert result["items"][0]["review_readiness"] == "BLOCKED"
    assert result["metrics"]["ready_for_review"] == 0
    assert result["metrics"]["blocked"] == 1
    assert result["families"][0]["blocked"] == 1
