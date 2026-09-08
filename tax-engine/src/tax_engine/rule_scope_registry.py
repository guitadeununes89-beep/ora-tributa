"""Scope-defining facts for each real rule, for multi-rule composition only.

Each entry names the subset of a rule's own already-approved `required_facts`
that most directly signals whether that rule's legal hypothesis is even in
play - not new legal content, just metadata about what is already in each
approved specification (`docs/tax/rules/specifications/RT-IBSCBS-*.json`).
Used exclusively by `multi_rule_evaluation.py` to distinguish a rule that is a
genuine, incomplete candidate from one that was simply never engaged.

Adding a rule here is itself a judgment call ("which fact is the gate for
this hypothesis") and must go through the same human review as everything
else this project treats as governed - `scope_for` refuses (fail-closed)
any rule code without an explicit, reviewed entry rather than defaulting to
"every fact is scope" or "no fact is scope", either of which would silently
reintroduce a form of the Etapa 11 bug.
"""

from __future__ import annotations

from tax_engine.multi_rule_evaluation import RuleScope

RULE_SCOPES: dict[str, RuleScope] = {
    "RT-IBSCBS-0003": RuleScope(
        rule_code="RT-IBSCBS-0003",
        scope_facts=frozenset({"buyer.legal_nature"}),
    ),
    "RT-IBSCBS-0004": RuleScope(
        rule_code="RT-IBSCBS-0004",
        scope_facts=frozenset({"product.annex_xiv_match_status"}),
    ),
    "RT-IBSCBS-0005": RuleScope(
        rule_code="RT-IBSCBS-0005",
        scope_facts=frozenset({"buyer.health_entity_status"}),
    ),
    "RT-IBSCBS-0007": RuleScope(
        rule_code="RT-IBSCBS-0007",
        scope_facts=frozenset(
            {"operation.origin_area_status", "operation.destination_area_status"}
        ),
    ),
    "RT-IBSCBS-0008": RuleScope(
        rule_code="RT-IBSCBS-0008",
        scope_facts=frozenset(
            {"seller.establishment_zfm_relation", "buyer.establishment_zfm_relation"}
        ),
    ),
}


def scope_for(rule_code: str) -> RuleScope:
    try:
        return RULE_SCOPES[rule_code]
    except KeyError as exc:
        raise KeyError(
            f"No registered scope-defining facts for {rule_code}; multi-rule "
            "composition requires an explicit, reviewed RuleScope entry"
        ) from exc
