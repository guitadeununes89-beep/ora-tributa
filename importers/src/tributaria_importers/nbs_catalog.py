"""Governed import of the official NBS (Nomenclatura Brasileira de Serviços) table.

Source: MDIC/RFB (Decreto nº 7.708/2012), NBS versão 2.0, published as a
semicolon-delimited, Latin-1 (ISO-8859-1) encoded CSV
(https://www.gov.br/mdic/pt-br/images/REPOSITORIO/scs/decos/NBS/NBSa_2-0.csv).
Unlike NCM, NBS has no widely-used "flattened" digit convention - codes are
stored exactly as officially published, dots included (e.g. "1.0101.11.00"),
and `level` is the number of dot-separated segments (2, 3 or 4).

The whole table shares a single vigência (NBS 2.0, effective 2019-01-01 per
Portaria Conjunta RFB/SCS nº 1.429/2018 and nº 2.000/2018) - there is no
per-code validity window like NCM's Data_Inicio/Data_Fim.

No checksum is published by the source, so - exactly like the existing
IBS/CBS cClassTrib and NCM importers - this module computes its own
`artifact_hash` (raw bytes) and `normalized_hash` (canonical JSON over
sorted, normalized records), pinned once in the governed load manifest.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_ARTIFACT_BYTES = 5_000_000
EXPECTED_HEADER = ("NBS 2.0", "DESCRIÇÃO")


class NbsImportError(ValueError):
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
class ParsedNbsCatalog:
    artifact_hash: str
    normalized_hash: str
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


def import_official_nbs_catalog(path: str | Path) -> ParsedNbsCatalog:
    artifact = Path(path)
    if not artifact.is_file() or artifact.stat().st_size > MAX_ARTIFACT_BYTES:
        raise NbsImportError("Artifact is missing or exceeds the size limit")
    artifact_bytes = artifact.read_bytes()
    artifact_hash = hashlib.sha256(artifact_bytes).hexdigest()
    text = artifact_bytes.decode("latin-1")
    reader = csv.reader(io.StringIO(text), delimiter=";")
    rows = list(reader)
    if not rows or tuple(_text(cell) for cell in rows[0][:2]) != EXPECTED_HEADER:
        raise NbsImportError("Artifact does not have the expected NBS header")

    codes: list[dict[str, Any]] = []
    staging: list[StagingRow] = []
    issues: list[ImportIssue] = []
    seen: set[str] = set()
    for row_number, values in enumerate(rows[1:], start=2):
        if not any(_text(value) for value in values):
            continue
        raw = {"code": values[0] if len(values) > 0 else None,
               "description": values[1] if len(values) > 1 else None}
        row_errors: list[ImportIssue] = []
        code = _code(raw["code"])
        description = _text(raw["description"])
        if code is None or description is None:
            row_errors.append(
                _issue("MISSING_REQUIRED_FIELD", "code and description are required", row_number)
            )
        elif code in seen:
            row_errors.append(_issue("DUPLICATE_CODE", f"Duplicate NBS code {code}", row_number))
        else:
            seen.add(code)
            codes.append(
                {
                    "code": code,
                    "level": code.count(".") + 1,
                    "description": description,
                }
            )
        staging.append(StagingRow(row_number, _json_safe(raw), tuple(row_errors)))
    if not codes:
        issues.append(_issue("NO_CODE_ROWS", "No valid NBS code records found"))

    canonical = {"codes": sorted(codes, key=lambda item: item["code"])}
    normalized_hash = hashlib.sha256(_canonical_json(canonical).encode()).hexdigest()
    return ParsedNbsCatalog(
        artifact_hash=artifact_hash,
        normalized_hash=normalized_hash,
        codes=tuple(codes),
        staging_rows=tuple(staging),
        issues=tuple(issues),
    )


def _code(value: Any) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return text if all(part.isdigit() for part in text.split(".")) else None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).split())
    return normalized or None


def _json_safe(raw: dict[str, Any]) -> dict[str, Any]:
    return {key: _text(value) for key, value in raw.items()}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _issue(
    code: str, message: str, row_number: int | None = None, field: str | None = None
) -> ImportIssue:
    return ImportIssue(code, message, row_number, field)
