from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProductTaxAttributeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1, max_length=200, pattern=r"^synthetic\.[a-z0-9_.-]+$")
    value: str = Field(min_length=1, max_length=1000)
    is_synthetic: Literal[True] = True


class ProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    internal_code: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    gtin: str | None = Field(default=None, pattern=r"^\d{8,14}$")
    ncm: str | None = Field(default=None, pattern=r"^\d{8}$")
    cest: str | None = Field(default=None, pattern=r"^\d{7}$")
    unit: str = Field(min_length=1, max_length=20)
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"
    attributes: list[ProductTaxAttributeInput] = Field(default_factory=list)
    change_reason: str = Field(
        default="Initial product registration", min_length=1, max_length=1000
    )

    @field_validator("internal_code", "description", "unit", "change_reason")
    @classmethod
    def strip_non_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped

    @model_validator(mode="after")
    def unique_attributes(self) -> ProductInput:
        keys = [item.key for item in self.attributes]
        if len(keys) != len(set(keys)):
            raise ValueError("product attribute keys must be unique")
        return self


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    internal_code: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    gtin: str | None = Field(default=None, pattern=r"^\d{8,14}$")
    ncm: str | None = Field(default=None, pattern=r"^\d{8}$")
    cest: str | None = Field(default=None, pattern=r"^\d{7}$")
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    status: Literal["ACTIVE", "INACTIVE"] | None = None
    attributes: list[ProductTaxAttributeInput] | None = None
    change_reason: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def meaningful_update(self) -> ProductUpdate:
        changed = self.model_fields_set - {"change_reason"}
        if not changed:
            raise ValueError("at least one product field must change")
        if self.attributes is not None:
            keys = [item.key for item in self.attributes]
            if len(keys) != len(set(keys)):
                raise ValueError("product attribute keys must be unique")
        return self


class ProductAttributeView(BaseModel):
    key: str
    value: str = Field(min_length=1, max_length=1000)
    is_synthetic: bool


class ProductVersionView(BaseModel):
    id: str
    version: int
    internal_code: str
    description: str
    gtin: str | None
    ncm: str | None
    cest: str | None
    unit: str
    status: str
    recorded_at: datetime
    recorded_by: str
    change_reason: str
    snapshot_hash: str
    attributes: list[ProductAttributeView]


class ProductSummaryView(BaseModel):
    id: str
    internal_code: str
    description: str
    gtin: str | None
    ncm: str | None
    cest: str | None
    unit: str
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class ProductDetailView(ProductSummaryView):
    current: ProductVersionView
    history: list[ProductVersionView]
