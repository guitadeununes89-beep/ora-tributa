from datetime import date, datetime

import pytest
from pydantic import ValidationError
from tributaria_api.contracts.classification import FactSetRequest
from tributaria_api.contracts.persistent_classification import (
    PersistedClassificationEvaluationRequest,
)
from tributaria_api.main import app


def test_persisted_endpoint_is_registered_with_synthetic_example() -> None:
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/classifications/evaluate"]["post"]
    serialized = str(schema)
    assert operation["tags"] == ["classifications"]
    assert "TEST-RULESET-001" in serialized
    assert "synthetic" in serialized.casefold()
    # The deterministic endpoint remains generic; the taxonomy API may identify IBS/CBS.
    assert "IBS" not in str(operation)
    assert "CBS" not in str(operation)


def test_admin_and_reproduction_endpoints_are_registered() -> None:
    paths = app.openapi()["paths"]
    assert "/api/v1/admin/tax-rule-versions/{version_id}/publish" in paths
    assert "/api/v1/admin/rulesets/{ruleset_id}/publish" in paths
    assert "/api/v1/classifications/evaluations/{evaluation_id}/reproduce" in paths


def test_persisted_request_rejects_naive_timestamps() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        PersistedClassificationEvaluationRequest(
            evaluation_id="TEST-EVALUATION",
            ruleset_id="TEST-RULESET",
            evaluated_at=datetime(2040, 6, 15, 12),
            known_at=datetime(2040, 6, 15, 12),
            correlation_id="TEST-CORRELATION",
            facts=FactSetRequest(operation_date=date(2040, 6, 15)),
        )
