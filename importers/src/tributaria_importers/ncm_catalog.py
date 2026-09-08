"""Governed import of the official NCM (Nomenclatura Comum do Mercosul) table.

Source: Receita Federal / Portal Único Siscomex "Classif" public JSON download
(https://portalunico.siscomex.gov.br/classif/api/publico/nomenclatura/download/json).
The feed is a flat list mixing every hierarchy level (2-digit chapter, 4-digit
heading, 6-digit subheading, 8-digit item, and a handful of intermediate
"dash" groupings that don't land on those exact widths) - `level` records the
literal digit count observed rather than forcing every entry into 2/4/6/8, and
`is_final` marks the entries that are themselves usable NCM codes (8 digits),
matching the `String(8)` convention already used by `ProductRecord.ncm`.

No checksum is published by the source, so - exactly like the existing
IBS/CBS cClassTrib importer - this module computes its own `artifact_hash`
(raw bytes) and `normalized_hash` (canonical JSON over sorted, normalized
records), pinned once in the governed load manifest.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

MAX_ARTIFACT_BYTES = 20_000_000


class NcmImportError(ValueError):
    """The artifact cannot advance because its structure or content is unsafe."""


@dataclass(frozen=True, slots=True)
class ImportIssue:
    code: str
    message: str
    row_number: int | None = None
    field: str | None = None


@dataclass(frozen=True, slots=True)
class StagingRow:
    row_number: int
    raw: dict[str, Any]
    errors: tuple[ImportIssue, ...] = ()


@dataclass(frozen=True, slots=True)
class ParsedNcmCatalog:
    artifact_hash: str
    normalized_hash: str
    vigencia_label: str
    ato: str
    codes: tuple[dict[str, Any], ...]
    staging_rows: tuple[StagingRow, ...]
    issues: tuple[ImportIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.issues and all(not row.errors for row in self.staging_rows)

    @property
    def report(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "code_count": len(self.codes),
            "staging_row_count": len(self.staging_rows),
            "issue_count": len(self.issues) + sum(len(row.errors) for row in self.staging_rows),
            "vigencia_label": self.vigencia_label,
            "ato": self.ato,
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "row_number": issue.row_number,
                    "field": issue.field,
                }
                for issue in self.issues
            ],
        }


def import_official_ncm_catalog(path: str | Path) -> ParsedNcmCatalog:
    artifact = Path(path)
    if not artifact.is_file() or artifact.stat().st_size > MAX_ARTIFACT_BYTES:
        raise NcmImportError("Artifact is missing or exceeds the size limit")
    artifact_bytes = artifact.read_bytes()
    artifact_hash = hashlib.sha256(artifact_bytes).hexdigest()
    document = json.loads(artifact_bytes.decode("utf-8"))
    if not isinstance(document, dict) or "Nomenclaturas" not in document:
        raise NcmImportError("Artifact is not a recognized NCM 'Classif' export")
    entries = document["Nomenclaturas"]
    if not isinstance(entries, list):
        raise NcmImportError("'Nomenclaturas' must be a list")

    codes: list[dict[str, Any]] = []
    staging: list[StagingRow] = []
    issues: list[ImportIssue] = []
    seen: set[str] = set()
    for row_number, entry in enumerate(entries, start=1):
        raw = entry if isinstance(entry, dict) else {}
        row_errors: list[ImportIssue] = []
        code = _code(raw.get("Codigo"))
        description = _text(raw.get("Descricao"))
        if code is None or description is None:
            row_errors.append(
                _issue("MISSING_REQUIRED_FIELD", "Codigo and Descricao are required", row_number)
            )
        elif code in seen:
            row_errors.append(_issue("DUPLICATE_CODE", f"Duplicate NCM code {code}", row_number))
        else:
            seen.add(code)
            valid_from = _date_value(raw.get("Data_Inicio"), "Data_Inicio", row_number, row_errors)
            valid_to = _date_value(raw.get("Data_Fim"), "Data_Fim", row_number, row_errors)
            codes.append(
                {
                    "code": code,
                    "level": len(code),
                    "is_final": len(code) == 8,
                    "description": description,
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                    "legal_act": _legal_act(raw),
                }
            )
        staging.append(StagingRow(row_number, _json_safe(raw), tuple(row_errors)))
    if not codes:
        issues.append(_issue("NO_CODE_ROWS", "No valid NCM code records found"))

    canonical = {"codes": sorted(codes, key=lambda item: item["code"])}
    normalized_hash = hashlib.sha256(_canonical_json(canonical).encode()).hexdigest()
    return ParsedNcmCatalog(
        artifact_hash=artifact_hash,
        normalized_hash=normalized_hash,
        vigencia_label=_text(document.get("Data_Ultima_Atualizacao_NCM")) or "",
        ato=_text(document.get("Ato")) or "",
        codes=tuple(codes),
        staging_rows=tuple(staging),
        issues=tuple(issues),
    )


def _code(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    digits = value.replace(".", "").strip()
    return digits if digits.isdigit() else None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split())
    return normalized or None


def _legal_act(raw: dict[str, Any]) -> str | None:
    kind = _text(raw.get("Tipo_Ato_Ini"))
    number = _text(raw.get("Numero_Ato_Ini"))
    year = _text(raw.get("Ano_Ato_Ini"))
    if not (kind and number and year):
        return None
    return f"{kind} {number}/{year}"


def _date_value(
    value: Any, field: str, row_number: int, errors: list[ImportIssue]
) -> str | None:
    if value is None:
        return None
    try:
        day, month, year = str(value).split("/")
        return date(int(year), int(month), int(day)).isoformat()
    except (TypeError, ValueError):
        errors.append(_issue("INVALID_DATE", f"Invalid date in {field}", row_number, field))
        return None


def _json_safe(raw: dict[str, Any]) -> dict[str, Any]:
    return {key: (value if isinstance(value, str | int | float | bool) else str(value))
            for key, value in raw.items()}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _issue(
    code: str, message: str, row_number: int | None = None, field: str | None = None
) -> ImportIssue:
    return ImportIssue(code, message, row_number, field)
