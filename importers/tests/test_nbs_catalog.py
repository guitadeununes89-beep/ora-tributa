from pathlib import Path

import pytest
from tributaria_importers.nbs_catalog import NbsImportError, import_official_nbs_catalog

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_ARTIFACT = ROOT / "database/normative-artifacts/original/nbs-2.0.csv"


def test_official_artifact_is_reproducible_offline() -> None:
    parsed = import_official_nbs_catalog(OFFICIAL_ARTIFACT)

    assert parsed.valid is True
    assert parsed.artifact_hash == (
        "99c9ca66b58223d7c32af4079ee9443b5b6a172a18643017bb7ed9d75d2cf5b8"
    )
    assert parsed.normalized_hash == (
        "2dac2c3c07ad9a77828a7d5422ab7881706a362d97bc24b6500d0be2d902533a"
    )
    assert len(parsed.codes) == 1237
    assert len(parsed.staging_rows) == 1237


def test_codes_keep_their_official_dotted_form() -> None:
    parsed = import_official_nbs_catalog(OFFICIAL_ARTIFACT)
    by_code = {item["code"]: item for item in parsed.codes}

    assert "1.01" in by_code
    assert by_code["1.01"]["level"] == 2
    assert "1.0101.11.00" in by_code
    assert by_code["1.0101.11.00"]["level"] == 4


def test_no_duplicate_codes() -> None:
    parsed = import_official_nbs_catalog(OFFICIAL_ARTIFACT)

    codes = [item["code"] for item in parsed.codes]
    assert len(codes) == len(set(codes))


def test_missing_artifact_is_rejected() -> None:
    with pytest.raises(NbsImportError):
        import_official_nbs_catalog(
            ROOT / "database/normative-artifacts/original/does-not-exist.csv"
        )


def test_wrong_header_is_rejected(tmp_path: Path) -> None:
    bogus = tmp_path / "wrong.csv"
    bogus.write_bytes("NOT;NBS\n1.01;something\n".encode("latin-1"))

    with pytest.raises(NbsImportError):
        import_official_nbs_catalog(bogus)
