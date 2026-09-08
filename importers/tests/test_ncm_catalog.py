from pathlib import Path

import pytest
from tributaria_importers.ncm_catalog import NcmImportError, import_official_ncm_catalog

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_ARTIFACT = ROOT / "database/normative-artifacts/original/ncm-2026-09-08.json"


def test_official_artifact_is_reproducible_offline() -> None:
    parsed = import_official_ncm_catalog(OFFICIAL_ARTIFACT)

    assert parsed.valid is True
    assert parsed.artifact_hash == (
        "3bee2080f939d65fc7565dc3ec96ea23d5cee23e0795fabcc658e8417fdee67d"
    )
    assert parsed.normalized_hash == (
        "c9ced173b065cb37354a728844bd6aec70cdcdc1e60fa40fa1d7b0d95664bbdd"
    )
    assert len(parsed.codes) == 15156
    assert len(parsed.staging_rows) == 15156
    assert parsed.vigencia_label == "Vigente em 08/09/2026"


def test_leading_zeros_are_preserved_and_dots_are_stripped() -> None:
    parsed = import_official_ncm_catalog(OFFICIAL_ARTIFACT)
    by_code = {item["code"]: item for item in parsed.codes}

    assert "01012100" in by_code
    assert by_code["01012100"]["level"] == 8
    assert by_code["01012100"]["is_final"] is True
    assert by_code["01"]["level"] == 2
    assert by_code["01"]["is_final"] is False


def test_final_codes_are_exactly_the_eight_digit_entries() -> None:
    parsed = import_official_ncm_catalog(OFFICIAL_ARTIFACT)

    final = [item for item in parsed.codes if item["is_final"]]
    assert all(len(item["code"]) == 8 for item in final)
    assert all(len(item["code"]) != 8 for item in parsed.codes if not item["is_final"])


def test_chapter_30_pharmaceutical_codes_are_present() -> None:
    parsed = import_official_ncm_catalog(OFFICIAL_ARTIFACT)

    chapter_30 = [
        item for item in parsed.codes if item["code"].startswith("30") and item["is_final"]
    ]
    assert len(chapter_30) > 0
    assert all(item["code"][:2] == "30" for item in chapter_30)


def test_per_code_validity_dates_are_converted_to_iso() -> None:
    parsed = import_official_ncm_catalog(OFFICIAL_ARTIFACT)
    by_code = {item["code"]: item for item in parsed.codes}

    assert by_code["01"]["valid_from"] == "2022-04-01"
    assert by_code["01"]["valid_to"] == "9999-12-31"
    assert by_code["01"]["legal_act"] == "Res Gecex 272/2021"


def test_missing_artifact_is_rejected() -> None:
    with pytest.raises(NcmImportError):
        import_official_ncm_catalog(
            ROOT / "database/normative-artifacts/original/does-not-exist.json"
        )
