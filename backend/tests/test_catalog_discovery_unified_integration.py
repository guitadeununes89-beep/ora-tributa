"""Etapa 22 (item 6): the tax-candidate discovery layer feeds the exact same
`EvaluationService.evaluate_many()` the unified consultation (Etapa 21) already
uses - discovery only ever suggests which rulesets to compose, it never
bypasses the fact-based evaluation. Requires the real RT-IBSCBS-0004/0005
rules already deployed (see docs/DEVELOPMENT_ACCESS.md / real_rule_deploy_cli_
p2_medicamentos.py) - matches the precedent already set by test_evaluate_many.py.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tax_engine.evaluation import EvaluationContext, FactSet
from tax_engine.tax_candidate_discovery import discover_by_ncm
from tributaria_api.application.errors import NotFoundError
from tributaria_api.application.evaluations import EvaluationService
from tributaria_api.infrastructure.database.repositories import SqlAlchemyGovernanceRepository

pytestmark = pytest.mark.skipif(
    os.getenv("POSTGRES_TESTS") != "1",
    reason="requires migrated PostgreSQL with real rules deployed",
)

# Same rule_code -> ruleset_id mapping the frontend keeps in its own RULESETS
# constant (duplicated deliberately, not imported - Etapa 21/22 convention).
_RULESET_BY_RULE_CODE = {
    "RT-IBSCBS-0004": "IBSCBS-PILOT-0004-001",
    "RT-IBSCBS-0005": "IBSCBS-PILOT-0005-001",
}


def test_ncm_chapter_30_discovery_composes_into_a_real_unified_evaluation() -> None:
    family = discover_by_ncm("30019010")
    assert family is not None
    ruleset_ids = sorted(_RULESET_BY_RULE_CODE[code] for code in family.rule_codes)

    engine = create_engine(os.environ["DATABASE_URL"])
    with Session(engine) as session:
        repository = SqlAlchemyGovernanceRepository(session)
        try:
            for ruleset_id in ruleset_ids:
                repository.get_ruleset(ruleset_id)
        except NotFoundError:
            pytest.skip(
                f"{ruleset_ids} not deployed to this database - run the real rule deploy "
                "CLIs first (see docs/DEVELOPMENT_ACCESS.md)"
            )

        service = EvaluationService(repository, engine_version="test-etapa-22-discovery")
        now = datetime.now(UTC)
        # RT-IBSCBS-0005's own eligible() facts (medicine + Anvisa + health entity
        # immune to IBS/CBS with CEBAS and SUS service). operation_date is kept
        # inside RT-IBSCBS-0004's 01-13/01/2026 validity window too, so both rules
        # are actually selected and evaluated (0004 ends up SCOPE_UNCONFIRMED,
        # since none of its own facts were given - it must not block the result).
        rt_0005_facts = {
            "product.kind": "MEDICINE",
            "product.anvisa_registration_status": "REGISTERED",
            "buyer.health_entity_status": "HEALTH_ENTITY",
            "buyer.ibs_cbs_immunity_status": "IMMUNE",
            "operation.effective_buyer_status": "CONFIRMED",
            "buyer.cebas_status": "VALID",
            "buyer.sus_service_requirement_status": "SATISFIED",
        }
        facts = FactSet(
            operation_date=datetime(2026, 1, 5, tzinfo=UTC).date(),
            product_attributes=rt_0005_facts,
        )
        context = EvaluationContext(
            evaluation_id="PG-TEST-DISCOVERY-INTEGRATION-1",
            evaluated_at=now,
            known_at=now,
            correlation_id="PG-TEST-DISCOVERY-INTEGRATION-1",
        )

        document = service.evaluate_many(
            ruleset_ids=ruleset_ids,
            facts=facts,
            context=context,
            facts_document={
                "operation_date": "2026-01-05",
                "product_attributes": rt_0005_facts,
            },
        )

        assert document["status"] == "CONCLUSIVO"
        candidacies = {item["rule_code"]: item["status"] for item in document["rule_candidacies"]}
        assert candidacies["RT-IBSCBS-0005"] == "SUPPORTED"
        assert candidacies["RT-IBSCBS-0004"] == "SCOPE_UNCONFIRMED"
        stored = repository.get_evaluation("PG-TEST-DISCOVERY-INTEGRATION-1")
        assert stored["ruleset_id"] is None
        assert sorted(stored["composed_ruleset_ids"]) == ruleset_ids
