from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from tax_engine.engine import DeterministicRule
from tax_engine.evaluation import (
    ClassificationStatus,
    ConditionResult,
    ConditionStatus,
    EvaluationContext,
    FactSet,
    RuleDecision,
    RuleDecisionStatus,
)
from tax_engine.ibs_cbs_rt_0003 import RtIbsCbs0003V1
from tax_engine.ibs_cbs_rt_0004 import RtIbsCbs0004V1
from tax_engine.ibs_cbs_rt_0005 import RtIbsCbs0005V1
from tax_engine.ibs_cbs_rt_0007 import RtIbsCbs0007V1
from tax_engine.ibs_cbs_rt_0008 import RtIbsCbs0008V1
from tax_engine.multi_rule_evaluation import (
    CandidateRuleSet,
    MultiRuleEngine,
    MultiRuleEvaluation,
    RuleCandidacy,
    RuleCandidacyStatus,
    RuleScope,
)
from tax_engine.rule_lifecycle import RuleLifecycle, RuleLifecycleStatus
from tax_engine.rule_models import LegalSource, TaxRuleIdentity, TaxRuleVersion
from tax_engine.rule_scope_registry import scope_for

CATALOG_ID = "2295b90f-2f92-4fa4-8181-3007f02b1679"
KNOWN_AT = datetime(2026, 9, 8, 12, tzinfo=UTC)


def _published(version: TaxRuleVersion, *, published_at: datetime) -> RuleLifecycle:
    return (
        RuleLifecycle(version)
        .transition(
            event_id=f"{version.version_id}-review",
            to_status=RuleLifecycleStatus.IN_REVIEW,
            occurred_at=published_at.replace(hour=1),
            actor_id="dev-curator",
            reason="test review",
        )
        .transition(
            event_id=f"{version.version_id}-approve",
            to_status=RuleLifecycleStatus.APPROVED,
            occurred_at=published_at.replace(hour=2),
            actor_id="legal-approver-guilherme-nunes",
            reason="test approval",
        )
        .transition(
            event_id=f"{version.version_id}-publish",
            to_status=RuleLifecycleStatus.PUBLISHED,
            occurred_at=published_at.replace(hour=3),
            actor_id="dev-publisher",
            reason="test publication",
        )
    )


def _legal_source(device: str) -> LegalSource:
    return LegalSource(
        source_id="23302183-6c92-4b34-a26d-cd272e2c1b1e",
        act_type="OFFICIAL_LEGAL_ACT",
        number="214",
        year=2025,
        issuing_authority="Presidência da República",
        device=device,
        official_uri="https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214compilado.htm",
        published_on=date(2025, 1, 16),
    )


def rule_0003() -> RtIbsCbs0003V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0003-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0003", code="RT-IBSCBS-0003", title="RT-IBSCBS-0003"
        ),
        version=1,
        jurisdiction="BR",
        legal_source=_legal_source("Art. 146, § 1º, I"),
        legal_device="LC nº 214/2025, art. 146, § 1º, I",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 8, 31, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0003 v2",
    )
    return RtIbsCbs0003V1(
        version, _published(version, published_at=datetime(2026, 8, 31, tzinfo=UTC)),
        CATALOG_ID, "200", "200010",
    )


def eligible_0003() -> dict[str, str]:
    return {
        "product.kind": "MEDICINE",
        "product.anvisa_registration_status": "REGISTERED",
        "buyer.legal_nature": "AUTARCHY",
        "operation.buyer_is_acquirer": "YES",
    }


def rule_0004() -> RtIbsCbs0004V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0004-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0004", code="RT-IBSCBS-0004", title="RT-IBSCBS-0004"
        ),
        version=1,
        jurisdiction="BR",
        legal_source=_legal_source("Art. 146, caput (redação original); Anexo XIV"),
        legal_device="LC nº 214/2025, art. 146, caput (redação original); Anexo XIV",
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 1, 14),
        recorded_at=datetime(2026, 9, 7, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0004 v1",
    )
    return RtIbsCbs0004V1(
        version, _published(version, published_at=datetime(2026, 9, 7, tzinfo=UTC)),
        CATALOG_ID, "200", "200009",
    )


def eligible_0004() -> dict[str, str]:
    return {
        "product.ncm_sh": "VERIFIED_FROM_OFFICIAL_ANNEX_XIV",
        "product.annex_xiv_match_status": "MATCHED",
        "normative.annex_xiv_version": "LC214_2025_ORIGINAL",
    }


def rule_0005() -> RtIbsCbs0005V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0005-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0005", code="RT-IBSCBS-0005", title="RT-IBSCBS-0005"
        ),
        version=1,
        jurisdiction="BR",
        legal_source=_legal_source("Art. 146, § 1º, II"),
        legal_device="LC nº 214/2025, art. 146, § 1º, II; LC nº 187/2021, arts. 9º a 11",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 9, 7, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0005 v1",
    )
    return RtIbsCbs0005V1(
        version, _published(version, published_at=datetime(2026, 9, 7, tzinfo=UTC)),
        CATALOG_ID, "200", "200010",
    )


def eligible_0005() -> dict[str, str]:
    return {
        "product.kind": "MEDICINE",
        "product.anvisa_registration_status": "REGISTERED",
        "buyer.health_entity_status": "HEALTH_ENTITY",
        "buyer.ibs_cbs_immunity_status": "IMMUNE",
        "operation.effective_buyer_status": "CONFIRMED",
        "buyer.cebas_status": "VALID",
        "buyer.sus_service_requirement_status": "SATISFIED",
    }


def rule_0007() -> RtIbsCbs0007V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0007-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0007", code="RT-IBSCBS-0007", title="RT-IBSCBS-0007"
        ),
        version=1,
        jurisdiction="BR",
        legal_source=_legal_source("Art. 445"),
        legal_device="LC nº 214/2025, art. 445; Resolução CGIBS nº 6/2026, art. 516",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 9, 6, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0007 v3",
    )
    return RtIbsCbs0007V1(
        version, _published(version, published_at=datetime(2026, 9, 6, tzinfo=UTC)),
        CATALOG_ID, "200", "200022",
    )


def eligible_0007(**overrides: str) -> dict[str, str]:
    baseline = {
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
    baseline.update(overrides)
    return baseline


def rule_0008() -> RtIbsCbs0008V1:
    version = TaxRuleVersion.create(
        version_id="rt-ibscbs-0008-v1",
        identity=TaxRuleIdentity(
            identity_id="rt-ibscbs-0008", code="RT-IBSCBS-0008", title="RT-IBSCBS-0008"
        ),
        version=1,
        jurisdiction="BR",
        legal_source=_legal_source("Art. 448"),
        legal_device="LC nº 214/2025, art. 448; Resolução CGIBS nº 6/2026, art. 519",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 9, 6, tzinfo=UTC),
        created_by="dev-curator",
        origin="TEST_GOVERNED_REAL_RULE",
        content="approved specification RT-IBSCBS-0008 v3",
    )
    return RtIbsCbs0008V1(
        version, _published(version, published_at=datetime(2026, 9, 6, tzinfo=UTC)),
        CATALOG_ID, "200", "200023",
    )


def eligible_0008(**overrides: str) -> dict[str, str]:
    baseline = {
        "operation.zfm_area_version_id": "GOVERNED-ZFM-VERSION",
        "seller.establishment_zfm_relation": "INSIDE",
        "buyer.establishment_zfm_relation": "INSIDE",
        "seller.zfm_incentivized_industry_status": "VALID",
        "buyer.zfm_incentivized_industry_status": "VALID",
        "product.material_good_status": "MATERIAL_GOOD",
        "product.intermediate_good_status": "INTERMEDIATE_GOOD",
        "operation.delivery_area_status": "INSIDE_ZFM",
        "operation.flow_type": "DIRECT",
        "operation.taxable_scope_status": "FULL_OPERATION",
        "product.art_443_par1_exclusion_status": "NOT_EXCLUDED",
    }
    baseline.update(overrides)
    return baseline


def evaluate_many(
    rules_and_scopes: list[tuple[DeterministicRule, RuleScope]],
    *,
    operation_date: date,
    attributes: dict[str, str],
) -> MultiRuleEvaluation:
    engine = MultiRuleEngine(engine_version="test-etapa-21")
    codes = sorted(r.version.identity.code for r, _ in rules_and_scopes)
    candidates = CandidateRuleSet(
        composed_id="COMPOSED:" + "+".join(codes),
        rules=tuple(rules_and_scopes),
    )
    context = EvaluationContext(
        evaluation_id="composed-evaluation",
        evaluated_at=KNOWN_AT,
        known_at=KNOWN_AT,
        correlation_id="correlation",
    )
    facts = FactSet(operation_date=operation_date, product_attributes=attributes)
    return engine.evaluate(facts=facts, context=context, candidates=candidates)


def candidacy_for(result: MultiRuleEvaluation, rule_code: str) -> RuleCandidacy:
    return next(c for c in result.candidacies if c.rule.rule_code == rule_code)


# 1. RT-IBSCBS-0007 and RT-IBSCBS-0008 evaluated together in the same context.
def test_zfm_scenario_0007_conclusive_ignores_0008_scope_unconfirmed() -> None:
    result = evaluate_many(
        [(rule_0007(), scope_for("RT-IBSCBS-0007")), (rule_0008(), scope_for("RT-IBSCBS-0008"))],
        operation_date=date(2026, 6, 1),
        attributes=eligible_0007(),
    )

    assert result.evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    assert result.evaluation.outcome.missing_facts == ()
    candidate = result.evaluation.outcome.tax_candidates[0]
    assert (candidate.cst_code, candidate.classification_code) == ("200", "200022")

    assert candidacy_for(result, "RT-IBSCBS-0007").status is RuleCandidacyStatus.SUPPORTED
    assert candidacy_for(result, "RT-IBSCBS-0008").status is RuleCandidacyStatus.SCOPE_UNCONFIRMED
    assert candidacy_for(result, "RT-IBSCBS-0008").unconfirmed_scope_facts == (
        "buyer.establishment_zfm_relation",
        "seller.establishment_zfm_relation",
    )


def test_zfm_scenario_0008_conclusive_ignores_0007_scope_unconfirmed() -> None:
    result = evaluate_many(
        [(rule_0007(), scope_for("RT-IBSCBS-0007")), (rule_0008(), scope_for("RT-IBSCBS-0008"))],
        operation_date=date(2026, 6, 1),
        attributes=eligible_0008(),
    )

    assert result.evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    candidate = result.evaluation.outcome.tax_candidates[0]
    assert (candidate.cst_code, candidate.classification_code) == ("200", "200023")
    assert candidacy_for(result, "RT-IBSCBS-0007").status is RuleCandidacyStatus.SCOPE_UNCONFIRMED


# 2. A rule proven not applicable does not contaminate the outcome.
def test_not_applicable_rule_is_excluded_without_polluting_others() -> None:
    facts_0003 = eligible_0003()
    facts_0007_contradicted = eligible_0007(product_art_443="EXCLUDED")
    facts_0007_contradicted["product.art_443_par1_exclusion_status"] = "EXCLUDED"
    attributes = {**facts_0003, **facts_0007_contradicted}

    result = evaluate_many(
        [(rule_0003(), scope_for("RT-IBSCBS-0003")), (rule_0007(), scope_for("RT-IBSCBS-0007"))],
        operation_date=date(2026, 6, 1),
        attributes=attributes,
    )

    assert candidacy_for(result, "RT-IBSCBS-0007").status is RuleCandidacyStatus.NOT_APPLICABLE
    assert result.evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    assert result.evaluation.outcome.missing_facts == ()
    candidate = result.evaluation.outcome.tax_candidates[0]
    assert candidate.classification_code == "200010"


# 3. A rule potentially applicable with a missing fact blocks the conclusion.
def test_scope_confirmed_incomplete_rule_blocks_conclusion() -> None:
    attributes = eligible_0007()
    del attributes["buyer.art_442_habilitation_status"]

    result = evaluate_many(
        [(rule_0007(), scope_for("RT-IBSCBS-0007"))],
        operation_date=date(2026, 6, 1),
        attributes=attributes,
    )

    assert candidacy_for(result, "RT-IBSCBS-0007").status is (
        RuleCandidacyStatus.SCOPE_CONFIRMED_INCOMPLETE
    )
    assert result.evaluation.outcome.status is ClassificationStatus.REQUIRES_VALIDATION
    assert result.evaluation.outcome.missing_facts == ("buyer.art_442_habilitation_status",)


# 4. Two rules sharing cclasstrib 200010 (RT-IBSCBS-0003 vs RT-IBSCBS-0005).
def test_shared_cclasstrib_200010_deduplicates_to_conclusive() -> None:
    result = evaluate_many(
        [(rule_0003(), scope_for("RT-IBSCBS-0003")), (rule_0005(), scope_for("RT-IBSCBS-0005"))],
        operation_date=date(2026, 6, 1),
        attributes=eligible_0003(),
    )

    assert result.evaluation.outcome.status is ClassificationStatus.CONCLUSIVE
    assert len(result.evaluation.outcome.tax_candidates) == 1
    assert candidacy_for(result, "RT-IBSCBS-0005").status is RuleCandidacyStatus.SCOPE_UNCONFIRMED


def test_shared_cclasstrib_200010_conservatively_waits_when_0005_scope_engaged() -> None:
    # 0005's scope fact is confirmed (health entity), but its other facts are
    # unanswered - even though 0003 already produced a clean candidate with
    # the *same* cClassTrib, the conservative choice (documented in
    # ADR-0025) is to keep waiting rather than assume the two candidates
    # would necessarily coincide.
    attributes = {**eligible_0003(), "buyer.health_entity_status": "HEALTH_ENTITY"}

    result = evaluate_many(
        [(rule_0003(), scope_for("RT-IBSCBS-0003")), (rule_0005(), scope_for("RT-IBSCBS-0005"))],
        operation_date=date(2026, 6, 1),
        attributes=attributes,
    )

    assert candidacy_for(result, "RT-IBSCBS-0005").status is (
        RuleCandidacyStatus.SCOPE_CONFIRMED_INCOMPLETE
    )
    assert result.evaluation.outcome.status is ClassificationStatus.REQUIRES_VALIDATION


# 5. RT-IBSCBS-0004's temporal boundaries are respected at selection time.
def test_0004_outside_validity_window_is_excluded_at_selection_not_evaluation() -> None:
    result = evaluate_many(
        [(rule_0004(), scope_for("RT-IBSCBS-0004"))],
        operation_date=date(2026, 1, 14),
        attributes=eligible_0004(),
    )

    assert result.candidacies == ()
    assert result.evaluation.outcome.status is ClassificationStatus.UNCLASSIFIED
    selection_steps = [
        step for step in result.evaluation.outcome.trace if step.phase.value == "SELECTION"
    ]
    assert selection_steps[0].outcome == "OUTSIDE_LEGAL_VALIDITY"


def test_0004_inside_validity_window_is_conclusive() -> None:
    result = evaluate_many(
        [(rule_0004(), scope_for("RT-IBSCBS-0004"))],
        operation_date=date(2026, 1, 13),
        attributes=eligible_0004(),
    )

    assert result.evaluation.outcome.status is ClassificationStatus.CONCLUSIVE


# 6. A conflict without approved precedence returns POSSIBLE_MATCHES, never an
#    arbitrary tie-break - using two synthetic rules since none of the 5 real
#    rules can simultaneously match with different cClassTrib codes today.
@dataclass(frozen=True, slots=True)
class _SyntheticAlwaysMatchedRule:
    version: TaxRuleVersion
    lifecycle: RuleLifecycle
    cclasstrib: str

    def evaluate(self, facts: FactSet) -> RuleDecision:
        from tax_engine.evaluation import CandidateSupport, TaxClassificationCandidate
        from tax_engine.rule_models import RuleVersionRef

        condition = ConditionResult(
            condition_id=f"synthetic-{self.cclasstrib}",
            description="Synthetic always-satisfied condition",
            fact_name="synthetic.always_true",
            status=ConditionStatus.SATISFIED,
            expected_value="TRUE",
            observed_value="TRUE",
        )
        candidate = TaxClassificationCandidate(
            catalog_version_id=CATALOG_ID,
            cst_code="200",
            classification_code=self.cclasstrib,
            rule=RuleVersionRef.from_version(self.version),
            support=CandidateSupport.SUPPORTED,
            conditions=(condition,),
            legal_sources=(self.version.legal_source,),
        )
        return RuleDecision(
            status=RuleDecisionStatus.MATCHED,
            tax_candidates=(candidate,),
            conditions=(condition,),
        )


def _synthetic_rule(code: str, cclasstrib: str) -> _SyntheticAlwaysMatchedRule:
    version = TaxRuleVersion.create(
        version_id=f"{code.lower()}-v1",
        identity=TaxRuleIdentity(identity_id=code.lower(), code=code, title="Synthetic rule"),
        version=1,
        jurisdiction="SYNTHETIC",
        legal_source=LegalSource(
            source_id=f"source-{code.lower()}",
            act_type="SYNTHETIC_ACT",
            number="TEST",
            year=2099,
            issuing_authority="SYNTHETIC AUTHORITY",
            device="SYNTHETIC DEVICE",
        ),
        legal_device="SYNTHETIC DEVICE",
        valid_from=date(2026, 1, 1),
        valid_to=None,
        recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
        created_by="synthetic-test",
        origin="UNIT_TEST",
        content=f"SYNTHETIC ONLY: {code}",
    )
    return _SyntheticAlwaysMatchedRule(
        version, _published(version, published_at=datetime(2026, 1, 1, tzinfo=UTC)), cclasstrib
    )


def test_two_incompatible_matches_yield_possible_matches_not_arbitrary_tiebreak() -> None:
    rule_a = _synthetic_rule("SYN-TEST-A", "100001")
    rule_b = _synthetic_rule("SYN-TEST-B", "100002")
    scope_a = RuleScope(rule_code="SYN-TEST-A", scope_facts=frozenset({"synthetic.gate_a"}))
    scope_b = RuleScope(rule_code="SYN-TEST-B", scope_facts=frozenset({"synthetic.gate_b"}))

    result = evaluate_many(
        [(rule_a, scope_a), (rule_b, scope_b)],
        operation_date=date(2026, 6, 1),
        attributes={},
    )

    assert result.evaluation.outcome.status is ClassificationStatus.POSSIBLE_MATCHES
    assert {c.classification_code for c in result.evaluation.outcome.tax_candidates} == {
        "100001",
        "100002",
    }


# 7. Historical reproduction: identical inputs, identical composed outcome.
def test_same_inputs_are_deterministic_and_reproducible() -> None:
    rules_and_scopes: list[tuple[DeterministicRule, RuleScope]] = [
        (rule_0007(), scope_for("RT-IBSCBS-0007")),
        (rule_0008(), scope_for("RT-IBSCBS-0008")),
    ]
    first = evaluate_many(
        rules_and_scopes, operation_date=date(2026, 6, 1), attributes=eligible_0007()
    )
    second = evaluate_many(
        [(rule_0007(), scope_for("RT-IBSCBS-0007")), (rule_0008(), scope_for("RT-IBSCBS-0008"))],
        operation_date=date(2026, 6, 1),
        attributes=eligible_0007(),
    )

    assert first.evaluation.input_hash == second.evaluation.input_hash
    assert first.evaluation.ruleset.content_hash == second.evaluation.ruleset.content_hash
    assert first.evaluation.outcome.status == second.evaluation.outcome.status
    assert first.evaluation.outcome.tax_candidates == second.evaluation.outcome.tax_candidates


# 8. Absence of coverage must never silently become a generic candidate.
def test_all_rules_scope_unconfirmed_yields_unclassified_never_a_generic_candidate() -> None:
    result = evaluate_many(
        [(rule_0007(), scope_for("RT-IBSCBS-0007")), (rule_0008(), scope_for("RT-IBSCBS-0008"))],
        operation_date=date(2026, 6, 1),
        attributes={},
    )

    assert result.evaluation.outcome.status is ClassificationStatus.UNCLASSIFIED
    assert result.evaluation.outcome.candidates == ()
    assert result.evaluation.outcome.tax_candidates == ()
    assert candidacy_for(result, "RT-IBSCBS-0007").status is RuleCandidacyStatus.SCOPE_UNCONFIRMED
    assert candidacy_for(result, "RT-IBSCBS-0008").status is RuleCandidacyStatus.SCOPE_UNCONFIRMED
