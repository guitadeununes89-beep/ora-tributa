from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

ProcessingStatus = Literal["PENDING", "PROCESSED", "ERROR"]
ClassificationStatusLiteral = Literal[
    "CONCLUSIVO", "POSSIVEIS_ENQUADRAMENTOS", "NECESSITA_VALIDACAO", "SEM_COBERTURA_NORMATIVA"
]
BatchStatus = Literal["RECEIVED", "VALIDATED", "PROCESSING", "COMPLETED", "FAILED"]
ObjectKind = Literal["GOOD", "SERVICE", "OTHER"]


class BatchRowResult(BaseModel):
    row_number: int
    internal_code: str | None = None
    description: str | None = None
    ncm: str | None = None
    nbs: str | None = None
    object_kind: ObjectKind | None = None
    processing_status: ProcessingStatus
    error_message: str | None = None
    classification_status: ClassificationStatusLiteral | None = None
    cst: str | None = None
    cclasstrib: str | None = None
    tratamento: str | None = None
    fundamento_legal: list[dict[str, Any]] = []
    regra: dict[str, str] | None = None
    fatos_faltantes: list[str] = []
    decision_trace: list[dict[str, Any]] = []
    observacoes: str | None = None
    evaluation_id: str | None = None


class BatchSummary(BaseModel):
    batch_id: str
    file_name: str
    file_hash: str
    status: BatchStatus
    row_count: int
    processed_count: int
    error_count: int
    truncated: bool
    max_rows: int
    created_at: datetime
    completed_at: datetime | None = None


class BatchUploadResponse(BaseModel):
    batch: BatchSummary
    unknown_headers: list[str]
    recognized_headers: list[str]
    preview: list[BatchRowResult]


class BatchDetailResponse(BaseModel):
    batch: BatchSummary
    rows: list[BatchRowResult]
