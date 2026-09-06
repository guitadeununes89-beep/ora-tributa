from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_sha256(value: str, field_name: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")


def compute_content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class LegalSource:
    source_id: str
    act_type: str
    number: str
    year: int
    issuing_authority: str
    device: str
    official_uri: str | None = None
    published_on: date | None = None
    notes: str | None = None
    integrity_hash: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "act_type",
            "number",
            "issuing_authority",
            "device",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not 1 <= self.year <= 9999:
            raise ValueError("Legal source year is invalid")
        if self.official_uri is not None:
            _require_text(self.official_uri, "official_uri")
        if self.notes is not None:
            _require_text(self.notes, "notes")
        if self.integrity_hash is not None:
            _validate_sha256(self.integrity_hash, "integrity_hash")


@dataclass(frozen=True, slots=True)
class TaxRuleIdentity:
    identity_id: str
    code: str
    title: str

    def __post_init__(self) -> None:
        _require_text(self.identity_id, "identity_id")
        _require_text(self.code, "code")
        _require_text(self.title, "title")


@dataclass(frozen=True, slots=True)
class TaxRuleVersion:
    version_id: str
    identity: TaxRuleIdentity
    version: int
    jurisdiction: str
    legal_source: LegalSource
    legal_device: str
    valid_from: date
    valid_to: date | None
    recorded_at: datetime
    created_by: str
    origin: str
    content: str
    content_hash: str
    audit_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "version_id",
            "jurisdiction",
            "legal_device",
            "created_by",
            "origin",
            "content",
        ):
            _require_text(getattr(self, field_name), field_name)
        if self.version < 1:
            raise ValueError("Rule version must be positive")
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("Rule valid_to must be later than valid_from")
        if self.recorded_at.tzinfo is None:
            raise ValueError("Rule recorded_at must be timezone-aware")
        _validate_sha256(self.content_hash, "content_hash")
        if self.content_hash != compute_content_hash(self.content):
            raise ValueError("Rule content does not match content_hash")
        keys = [key for key, _ in self.audit_metadata]
        empty_value = any(not value.strip() for _, value in self.audit_metadata)
        if any(not key.strip() for key in keys) or empty_value:
            raise ValueError("Audit metadata keys and values must be non-empty")
        if len(keys) != len(set(keys)):
            raise ValueError("Audit metadata keys must be unique")
        if self.audit_metadata != tuple(sorted(self.audit_metadata)):
            raise ValueError("Audit metadata must use canonical key order")

    @classmethod
    def create(
        cls,
        *,
        version_id: str,
        identity: TaxRuleIdentity,
        version: int,
        jurisdiction: str,
        legal_source: LegalSource,
        legal_device: str,
        valid_from: date,
        valid_to: date | None,
        recorded_at: datetime,
        created_by: str,
        origin: str,
        content: str,
        audit_metadata: tuple[tuple[str, str], ...] = (),
    ) -> TaxRuleVersion:
        return cls(
            version_id=version_id,
            identity=identity,
            version=version,
            jurisdiction=jurisdiction,
            legal_source=legal_source,
            legal_device=legal_device,
            valid_from=valid_from,
            valid_to=valid_to,
            recorded_at=recorded_at,
            created_by=created_by,
            origin=origin,
            content=content,
            content_hash=compute_content_hash(content),
            audit_metadata=audit_metadata,
        )


@dataclass(frozen=True, slots=True)
class RuleVersionRef:
    identity_id: str
    rule_code: str
    version_id: str
    version: int
    content_hash: str

    @classmethod
    def from_version(cls, version: TaxRuleVersion) -> RuleVersionRef:
        return cls(
            identity_id=version.identity.identity_id,
            rule_code=version.identity.code,
            version_id=version.version_id,
            version=version.version,
            content_hash=version.content_hash,
        )
