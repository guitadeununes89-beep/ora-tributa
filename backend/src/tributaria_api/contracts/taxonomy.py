from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field, HttpUrl, field_validator


class CatalogImportMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = Field(min_length=1, max_length=100)
    official_title: str = Field(min_length=1, max_length=500)
    official_url: HttpUrl
    technical_document: str = Field(min_length=1, max_length=300)
    issuing_authority: str = Field(min_length=1, max_length=200)
    publication_date: date
    consulted_at: datetime
    expected_artifact_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    notes: str | None = None

    @field_validator("consulted_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("consulted_at must include a timezone")
        return value


class CatalogImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metadata: CatalogImportMetadata
    artifact_file_name: str = Field(min_length=1, max_length=500, pattern=r"^[^/\\]+\.xlsx$")
    artifact_media_type: str = Field(
        default="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        pattern=r"^application/vnd\.openxmlformats-officedocument\.spreadsheetml\.sheet$",
    )
    artifact_base64: Base64Bytes


class CatalogTransitionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1, max_length=1000)
    occurred_at: datetime | None = None


class SourceView(BaseModel):
    title: str
    official_url: str
    technical_document: str
    publication_date: date
    artifact_hash: str
    consulted_at: datetime
    imported_at: datetime
    status: str


class CatalogVersionView(BaseModel):
    id: str
    catalog_id: str
    version: str
    status: str
    publication_date: date
    published_at: datetime | None
    cst_count: int
    cclasstrib_count: int
    source: SourceView


class CstView(BaseModel):
    code: str
    description: str
    indicators: dict[str, Any]
    catalog_version: str
    catalog_version_id: str
    source: SourceView


class ClassificationView(BaseModel):
    code: str
    cst: str
    cst_description: str | None
    name: str
    description: str
    valid_from: date | None
    valid_to: date | None
    updated_on: date | None
    attributes: dict[str, Any]
    catalog_version: str
    catalog_version_id: str
    source: SourceView


class ImportedVersionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    version: str
    status: str
    artifact_hash: str
    normalized_hash: str
    schema_signature: str
    cst_count: int
    cclasstrib_count: int
    import_report: dict[str, Any]
