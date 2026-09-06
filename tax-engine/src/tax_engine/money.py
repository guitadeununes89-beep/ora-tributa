from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TaxDecimal:
    """Exact decimal used by tax-domain values; rounding remains rule-specific."""

    value: Decimal

    def __post_init__(self) -> None:
        raw_value: object = self.value
        if isinstance(raw_value, float):
            raise TypeError("Tax-domain decimals must never be created from float")
        if not isinstance(raw_value, Decimal):
            raise TypeError("TaxDecimal requires decimal.Decimal")

    @classmethod
    def from_string(cls, value: str) -> TaxDecimal:
        return cls(Decimal(value))

    def as_string(self) -> str:
        return format(self.value, "f")
