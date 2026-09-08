from tax_engine.tax_candidate_discovery import discover_by_nbs, discover_by_ncm


def test_ncm_chapter_30_pharmaceutical_codes_discover_medicine_rules() -> None:
    family = discover_by_ncm("30012010")

    assert family is not None
    assert family.rule_codes == frozenset({"RT-IBSCBS-0004", "RT-IBSCBS-0005"})
    assert "Capítulo 30" in family.fundamento
    assert family.fonte.startswith("https://")


def test_ncm_chapter_30_lookup_works_from_any_length_code_in_that_chapter() -> None:
    assert discover_by_ncm("30") is not None
    assert discover_by_ncm("3001") is not None
    assert discover_by_ncm("30019010") is not None


def test_ncm_outside_chapter_30_has_no_coverage() -> None:
    assert discover_by_ncm("01012100") is None
    assert discover_by_ncm("84713012") is None
    assert discover_by_ncm("29") is None


def test_nbs_has_no_coverage_yet_by_design() -> None:
    assert discover_by_nbs("1.01") is None
    assert discover_by_nbs("1.0101.11.00") is None
    assert discover_by_nbs("anything") is None
