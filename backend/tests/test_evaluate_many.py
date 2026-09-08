"""EvaluationService-level regression for the Etapa 21 multi-rule orchestrator.

The tax-engine-level aggregation algorithm already has thorough coverage in
`tax-engine/tests/test_multi_rule_evaluation.py`. This file proves the new
backend wiring around it end to end, against the two *real*, already
PUBLISHED single-rule rulesets for RT-IBSCBS-0007 and RT-IBSCBS-0008
(`IBSCBS-ZFM-0007-PILOT-001` / `IBSCBS-ZFM-0008-PILOT-001`, deployed by
`real_rule_deploy_cli_p1_zfm.py`): `load_composed_rules` resolves both
rulesets through the real repository/database and the real, unmodified
`rule_scope_registry`, `save_composed_evaluation` persists a
`ruleset_id IS NULL` row with `composed_ruleset_ids` populated, and
`get_evaluation` reads it back correctly. This is also the exact scenario
that reproduced the Etapa 11 bug (`IBSCBS-ZFM-PILOT-001` always returning
NECESSITA_VALIDACAO) - giving only RT-0007's facts must now come back
CONCLUSIVO at this layer, not just inside the tax-engine.

Requires the real rules to already be deployed (`real_rule_deploy_cli.py`,
`real_rule_deploy_cli_p2_medicamentos.py`, `real_rule_deploy_cli_p1_zfm.py`
run against `DATABASE_URL`), exactly as `docs/DEVELOPMENT_ACCESS.md`
describes for local development - this test does not deploy them itself
(see `test_governed_deploy_cli_fresh_database.py` for that).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tax_engine.evaluation import EvaluationContext, FactSet
from tributaria_api.application.errors import NotFoundError
from tributaria_api.application.evaluations import EvaluationService
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository

pytestmark = pytest.mark.skipif(
    os.getenv("POSTGRES_TESTS") != "1",
    reason="requires migrated PostgreSQL with real rules deployed",
)

_RULESET_0007 = "IBSCBS-ZFM-0007-PILOT-001"
_RULESET_0008 = "IBSCBS-ZFM-0008-PILOT-001"


def _eligible_0007_facts() -> dict[str, str]:
    return {
        "operation.zfm_area_version_id": "GOVERNED-ZFM-VERSION",
        "operation.origin_area_status": "OUTSIDE_ZFM",
        "operation.destination_area_status": "ZFM",
        "product.material_good_status": "MATERIAL_GOOD",
        "product.industrialization_status": "INDUSTRIALIZED",
        "product.origin_status": "NATIONAL",
        "buyer.establishment_area_status": "ESTABLISHED_IN_ZFM",
        "buyer.taxpayer_status": "TAXPAYER",
        "buyer.art_442_habilitation_status": "VALID",
        "buyer.tax_regime_status": "REGULAR_IBS_CBS",
        "operation.invoice_suframa_registration_status": "PRESENT_AND_MATCHING",
        "product.art_443_par1_exclusion_status": "NOT_EXCLUDED",
        "operation.zfm_entry_proof_status": "CONFIRMED",
        "operation.entry_deadline_status": "WITHIN_120_DAYS",
    }


def _skip_if_real_rules_missing(repository: SqlAlchemyGovernanceRepository) -> None:
    try:
        repository.get_ruleset(_RULESET_0007)
        repository.get_ruleset(_RULESET_0008)
    except NotFoundError:
        pytest.skip(
            f"{_RULESET_0007}/{_RULESET_0008} not deployed to this database - run the real "
            "rule deploy CLIs first (see docs/DEVELOPMENT_ACCESS.md)"
        )


def test_evaluate_many_reproduces_the_etapa_11_zfm_scenario_as_conclusive() -> None:
    engine = create_engine(os.environ["DATABASE_URL"])
    with Session(engine) as session:
        repository = SqlAlchemyGovernanceRepository(session)
        _skip_if_real_rules_missing(repository)
        service = EvaluationService(repository, engine_version="test-etapa-21-evaluate-many")

        now = datetime.now(UTC)
        facts = FactSet(
            operation_date=datetime(2026, 6, 1, tzinfo=UTC).date(),
            product_attributes=_eligible_0007_facts(),
        )
        context = EvaluationContext(
            evaluation_id="PG-TEST-EM-EVALUATION-0007-0008",
            evaluated_at=now,
            known_at=now,
            correlation_id="PG-TEST-EM-CORRELATION-0007-0008",
        )

        document = service.evaluate_many(
            ruleset_ids=[_RULESET_0007, _RULESET_0008],
            facts=facts,
            context=context,
            facts_document={
                "operation_date": "2026-06-01",
                "product_attributes": _eligible_0007_facts(),
            },
        )

        assert document["status"] == "CONCLUSIVO"
        assert document["missing_facts"] == []
        assert len(document["tax_candidates"]) == 1
        assert document["tax_candidates"][0]["cclasstrib"] == "200022"

        candidacies = {item["rule_code"]: item for item in document["rule_candidacies"]}
        assert candidacies["RT-IBSCBS-0007"]["status"] == "SUPPORTED"
        assert candidacies["RT-IBSCBS-0008"]["status"] == "SCOPE_UNCONFIRMED"

        stored = repository.get_evaluation("PG-TEST-EM-EVALUATION-0007-0008")
        assert stored["ruleset_id"] is None
        assert stored["composed_ruleset_ids"] == [_RULESET_0007, _RULESET_0008]
        assert len(stored["rule_versions_used"]) == 2
