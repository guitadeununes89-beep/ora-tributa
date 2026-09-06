from pathlib import Path

from tributaria_importers.ibs_cbs_catalog import import_official_catalog

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_ARTIFACT = ROOT / "database/normative-artifacts/original/cClassTrib-2026-06-22.xlsx"
HISTORICAL_ARTIFACT = ROOT / "database/normative-artifacts/original/cClassTrib-2025-12-15.xlsx"


def test_official_artifact_is_reproducible_offline() -> None:
    parsed = import_official_catalog(OFFICIAL_ARTIFACT)

    assert parsed.valid is True
    assert parsed.artifact_hash == (
        "1448cb63a41bdb67ea30b4e11f4dc200d9568542c6b9335b6cff87a4fd664654"
    )
    assert parsed.normalized_hash == (
        "9b65c977cdd37b30f0146b10f8addd7175f11389fc08196a9dfebfd5258b2008"
    )
    assert parsed.schema_signature == (
        "fb87c22952135fe428a552f32d330d2cdd132bd5aae6dfc0a33747c58a6135c6"
    )
    assert len(parsed.csts) == 18
    assert len(parsed.classifications) == 164
    assert len(parsed.staging_rows) == 185
    assert all(isinstance(item["code"], str) for item in parsed.classifications)


def test_historical_official_schema_is_supported_without_inference() -> None:
    parsed = import_official_catalog(HISTORICAL_ARTIFACT)

    assert parsed.valid is True
    assert parsed.artifact_hash == (
        "15ce63cbbe53b5b00fc5e61e775221984a910dcdab547fd130d2ad0c478c7e46"
    )
    assert len(parsed.csts) == 18
    assert len(parsed.classifications) == 145
    assert len(parsed.staging_rows) == 166


def test_every_classification_references_a_cst_from_same_snapshot() -> None:
    parsed = import_official_catalog(OFFICIAL_ARTIFACT)
    csts = {item["code"] for item in parsed.csts}

    assert {item["cst"] for item in parsed.classifications} <= csts
    assert len({item["code"] for item in parsed.classifications}) == 164
