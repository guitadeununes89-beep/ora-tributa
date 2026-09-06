from decimal import Decimal

import pytest
from tax_engine.evaluation import ClassificationStatus
from tax_engine.money import TaxDecimal


def test_tax_decimal_rejects_float() -> None:
    with pytest.raises(TypeError, match="never"):
        TaxDecimal(0.1)  # type: ignore[arg-type]


def test_tax_decimal_preserves_exact_representation() -> None:
    assert TaxDecimal(Decimal("0.10")).as_string() == "0.10"


def test_all_required_classification_statuses_are_explicit() -> None:
    assert {status.value for status in ClassificationStatus} == {
        "CONCLUSIVO",
        "POSSIVEIS_ENQUADRAMENTOS",
        "NECESSITA_VALIDACAO",
        "SEM_CLASSIFICACAO",
    }
