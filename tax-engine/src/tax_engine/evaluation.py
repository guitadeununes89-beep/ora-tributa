from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from hashlib import sha256
from types import MappingProxyType
from typing import Any

from tax_engine.rule_models import LegalSource, RuleVersionRef


class ClassificationStatus(StrEnum):
    CONCLUSIVE = "CONCLUSIVO"
    POSSIBLE_MATCHES = "POSSIVEIS_ENQUADRAMENTOS"
    REQUIRES_VALIDATION = "NECESSITA_VALIDACAO"
    UNCLASSIFIED = "SEM_CLASSIFICACAO"


class ConditionStatus(StrEnum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    MISSING = "MISSING"


class CandidateSupport(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT_FACTS = "INSUFFICIENT_FACTS"


class RuleDecisionStatus(StrEnum):
    MATCHED = "MATCHED"
    NOT_MATCHED = "NOT_MATCHED"
    REQUIRES_VALIDATION = "REQUIRES_VALIDATION"


class TracePhase(StrEnum):
    SELECTION = "SELECTION"
    EVALUATION = "EVALUATION"
    AGGREGATION = "AGGREGATION"


@dataclass(frozen=True, slots=True)
class FactSet:
    operation_date: date
    product_id: str | None = None
    product_version_id: str | None = None
    product_code: str | None = None
    product_description: str | None = None
    ncm: str | None = None
    nbs: str | None = None
    operation_type: str | None = None
    origin_state: str | None = None
    destination_state: str | None = None
    taxpayer_regime: str | None = None
    recipient_type: str | None = None
    product_attributes: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        normalized: dict[str, str] = {}
        for key, value in self.product_attributes.items():
            if not key.strip():
                raise ValueError("Product attribute names must be non-empty")
            normalized[key] = value
        object.__setattr__(
            self,
            "product_attributes",
            MappingProxyType(dict(sorted(normalized.items()))),
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "destination_state": self.destination_state,
            "product_id": self.product_id,
            "product_version_id": self.product_version_id,
            "product_description": self.product_description,
            "nbs": self.nbs,
            "ncm": self.ncm,
            "operation_date": self.operation_date.isoformat(),
            "operation_type": self.operation_type,
            "origin_state": self.origin_state,
            "product_attributes": dict(self.product_attributes),
            "product_code": self.product_code,
            "recipient_type": self.recipient_type,
            "taxpayer_regime": self.taxpayer_regime,
        }

    def input_hash(self) -> str:
        payload = json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ConditionResult:
    condition_id: str
    description: str
    fact_name: str
    status: ConditionStatus
    expected_value: str | None = None
    observed_value: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("condition_id", "description", "fact_name"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"Condition result requires {field_name}")
        if self.status is ConditionStatus.MISSING and self.observed_value is not None:
            raise ValueError("A missing condition cannot have an observed value")


@dataclass(frozen=True, slots=True)
class TaxClassificationCandidate:
    catalog_version_id: str
    cst_code: str
    classification_code: str | None
    rule: RuleVersionRef
    support: CandidateSupport
    conditions: tuple[ConditionResult, ...] = ()
    missing_facts: tuple[str, ...] = ()
    legal_sources: tuple[LegalSource, ...] = ()

    def __post_init__(self) -> None:
        if not self.catalog_version_id.strip():
            raise ValueError("Candidate requires an exact catalog version")
        if len(self.cst_code) != 3 or not self.cst_code.isdigit():
            raise ValueError("CST candidate must contain exactly three digits")
        if self.classification_code is not None and (
            len(self.classification_code) != 6 or not self.classification_code.isdigit()
        ):
            raise ValueError("cClassTrib candidate must contain exactly six digits")
        if self.support is CandidateSupport.INSUFFICIENT_FACTS and not self.missing_facts:
            raise ValueError("Insufficient candidate support must identify missing facts")

    @property
    def key(self) -> tuple[str, str, str | None]:
        return (self.catalog_version_id, self.cst_code, self.classification_code)


@dataclass(frozen=True, slots=True)
class RuleDecision:
    status: RuleDecisionStatus
    candidates: tuple[str, ...] = ()
    tax_candidates: tuple[TaxClassificationCandidate, ...] = ()
    missing_facts: tuple[str, ...] = ()
    conditions: tuple[ConditionResult, ...] = ()
    trace_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if (
            self.status is RuleDecisionStatus.MATCHED
            and not self.candidates
            and not self.tax_candidates
        ):
            raise ValueError("A matched rule must provide at least one candidate")
        if self.status is RuleDecisionStatus.NOT_MATCHED and (
            self.candidates or self.tax_candidates
        ):
            raise ValueError("A non-matched rule cannot provide candidates")
        if self.status is RuleDecisionStatus.REQUIRES_VALIDATION and not self.missing_facts:
            raise ValueError("A validation decision must identify missing facts")


@dataclass(frozen=True, slots=True)
class DecisionStep:
    sequence: int
    phase: TracePhase
    description: str
    outcome: str
    rule: RuleVersionRef | None = None
    conditions: tuple[ConditionResult, ...] = ()
    details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("Decision step sequence must be positive")
        if not self.description.strip() or not self.outcome.strip():
            raise ValueError("Decision step requires description and outcome")


@dataclass(frozen=True, slots=True)
class RuleSetRef:
    ruleset_id: str
    version: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class ClassificationOutcome:
    status: ClassificationStatus
    candidates: tuple[str, ...]
    missing_facts: tuple[str, ...]
    evaluated_rules: tuple[RuleVersionRef, ...]
    applicable_rules: tuple[RuleVersionRef, ...]
    satisfied_conditions: tuple[ConditionResult, ...]
    unsatisfied_conditions: tuple[ConditionResult, ...]
    legal_sources: tuple[LegalSource, ...]
    ruleset: RuleSetRef
    engine_version: str
    trace: tuple[DecisionStep, ...]
    tax_candidates: tuple[TaxClassificationCandidate, ...] = ()

    def __post_init__(self) -> None:
        if (
            self.status is ClassificationStatus.CONCLUSIVE
            and len(self.candidates) + len({item.key for item in self.tax_candidates}) != 1
        ):
            raise ValueError("A conclusive outcome requires exactly one candidate")
        if (
            self.status is ClassificationStatus.POSSIBLE_MATCHES
            and len(self.candidates) + len({item.key for item in self.tax_candidates}) < 2
        ):
            raise ValueError("Possible matches require at least two candidates")
        if self.status is ClassificationStatus.REQUIRES_VALIDATION and not self.missing_facts:
            raise ValueError("Validation outcome must explain missing facts")
        if self.status is ClassificationStatus.UNCLASSIFIED and (
            self.candidates or self.tax_candidates
        ):
            raise ValueError("An unclassified outcome cannot contain candidates")


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    evaluation_id: str
    evaluated_at: datetime
    known_at: datetime
    correlation_id: str

    def __post_init__(self) -> None:
        if not self.evaluation_id.strip() or not self.correlation_id.strip():
            raise ValueError("Evaluation and correlation identifiers are required")
        if self.evaluated_at.tzinfo is None or self.known_at.tzinfo is None:
            raise ValueError("Evaluation timestamps must be timezone-aware")


@dataclass(frozen=True, slots=True)
class Evaluation:
    evaluation_id: str
    evaluated_at: datetime
    known_at: datetime
    correlation_id: str
    input_hash: str
    engine_version: str
    ruleset: RuleSetRef
    rule_versions_used: tuple[RuleVersionRef, ...]
    outcome: ClassificationOutcome
