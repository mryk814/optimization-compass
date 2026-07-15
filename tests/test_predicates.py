from typing import Any

import pytest
from pydantic import ValidationError

from optimization_compass.predicates import (
    AllExpression,
    AnyExpression,
    AtomicPredicate,
    NotExpression,
    PredicateCatalog,
    PredicateContractError,
    PredicateCoverage,
    PredicateFact,
    PredicateLeaf,
    PredicatePolicy,
    RuleTargetRetirement,
    WhenExpression,
    evaluate_eligibility,
    evaluate_expression,
    resolve_effective_policies,
)


def predicate(
    predicate_id: str,
    *,
    subject_type: str = "method",
    subject_id: str = "M_TEST",
    feature_id: str = "F_SMOOTHNESS",
    operator: str = "eq",
    value: object = "smooth",
    value_type: str = "controlled_code",
    **extra: object,
) -> AtomicPredicate:
    data: dict[str, object] = {
        "predicate_id": predicate_id,
        "schema_version": "1.0.0",
        "subject_type": subject_type,
        "subject_id": subject_id,
        "predicate_kind": "assumption",
        "feature_id": feature_id,
        "operator": operator,
        "value": value,
        "value_type": value_type,
        "rationale_key": "R_TEST",
        "source_ids": ["S_TEST"],
        "confidence": "high",
        "last_verified": "2026-07-15",
    }
    data.update(extra)
    return AtomicPredicate(**data)


def leaf(predicate_id: str) -> PredicateLeaf:
    return PredicateLeaf(kind="predicate", predicate_id=predicate_id)


def policy(
    policy_id: str,
    expression: Any,
    *,
    subject_type: str = "method",
    subject_id: str = "M_TEST",
    effect: str = "require",
    inheritance_mode: str = "local_only",
    override_action: str = "add",
    overrides_policy_id: str | None = None,
) -> PredicatePolicy:
    return PredicatePolicy(
        policy_id=policy_id,
        schema_version="1.0.0",
        subject_type=subject_type,
        subject_id=subject_id,
        effect=effect,
        expression=expression,
        inheritance_mode=inheritance_mode,
        override_action=override_action,
        overrides_policy_id=overrides_policy_id,
        rationale_key="R_POLICY",
        source_ids=["S_TEST"],
        confidence="high",
        last_verified="2026-07-15",
    )


def catalog(*predicates: AtomicPredicate, policies: list[PredicatePolicy] | None = None):
    default_policy = policy("POLICY", leaf(predicates[0].predicate_id))
    return PredicateCatalog(
        predicates=list(predicates),
        policies=policies or [default_policy],
    )


def coverage(subject_id: str = "M_TEST", status: str = "complete") -> PredicateCoverage:
    return PredicateCoverage(
        subject_type="method",
        subject_id=subject_id,
        status=status,
        rationale="migration audit",
        source_ids=["S_TEST"],
        last_verified="2026-07-15",
    )


def test_atomic_predicate_rejects_unknown_fields_versions_and_ambiguous_existence():
    with pytest.raises(ValidationError):
        predicate("P_TEST", unexpected=True)
    with pytest.raises(ValidationError):
        predicate("P_TEST", schema_version="2.0.0")
    with pytest.raises(ValidationError):
        predicate("P_TEST", operator="exists", value=True, value_type="boolean")


def test_atomic_predicate_validates_operator_value_contracts():
    with pytest.raises(ValidationError):
        predicate("P_TEST", operator="in", value="smooth")
    with pytest.raises(ValidationError):
        predicate("P_TEST", operator="in", value=[])
    with pytest.raises(ValidationError):
        predicate("P_TEST", operator="gte", value="large", value_type="string")


def test_fact_status_is_separate_from_three_valued_truth():
    p = predicate("P_SMOOTH")
    expression = leaf("P_SMOOTH")
    predicate_catalog = catalog(p)

    true_result = evaluate_expression(
        expression,
        predicate_catalog,
        {"F_SMOOTHNESS": PredicateFact(status="known", value="smooth")},
    )
    false_result = evaluate_expression(
        expression,
        predicate_catalog,
        {"F_SMOOTHNESS": PredicateFact(status="known", value="rough")},
    )
    unsupported_result = evaluate_expression(
        expression,
        predicate_catalog,
        {"F_SMOOTHNESS": PredicateFact(status="unsupported", reason="source cannot answer")},
    )
    not_applicable_result = evaluate_expression(
        expression,
        predicate_catalog,
        {"F_SMOOTHNESS": PredicateFact(status="not_applicable", reason="feature has no meaning")},
    )

    assert true_result.truth == "true"
    assert false_result.truth == "false"
    assert unsupported_result.truth == "unknown"
    assert unsupported_result.details[0].fact_status == "unsupported"
    assert not_applicable_result.truth == "unknown"
    assert not_applicable_result.details[0].fact_status == "not_applicable"


def test_missing_fact_is_unknown_but_missing_catalog_definition_is_an_error():
    p = predicate("P_SMOOTH")
    predicate_catalog = catalog(p)

    result = evaluate_expression(leaf("P_SMOOTH"), predicate_catalog, {})
    assert result.truth == "unknown"
    assert result.reason_code == "missing_fact"

    with pytest.raises(PredicateContractError, match="missing from the catalog"):
        evaluate_expression(leaf("P_MISSING"), predicate_catalog, {})


@pytest.mark.parametrize(
    ("operator", "observed", "expected", "value_type", "truth"),
    [
        ("eq", "smooth", "smooth", "controlled_code", "true"),
        ("neq", "rough", "smooth", "controlled_code", "true"),
        ("in", "smooth", ["smooth", "piecewise_smooth"], "controlled_code", "true"),
        ("not_in", "rough", ["smooth", "piecewise_smooth"], "controlled_code", "true"),
        ("lt", 2, 3, "number", "true"),
        ("gte", 3, 3, "number", "true"),
        ("contains", ["gradient", "bounds"], "gradient", "controlled_code", "true"),
    ],
)
def test_supported_operators(operator, observed, expected, value_type, truth):
    p = predicate(
        "P_OPERATOR",
        operator=operator,
        value=expected,
        value_type=value_type,
    )
    result = evaluate_expression(
        leaf("P_OPERATOR"),
        catalog(p),
        {"F_SMOOTHNESS": PredicateFact(status="known", value=observed)},
    )
    assert result.truth == truth


def test_invalid_known_fact_type_is_contract_error_not_unsupported():
    p = predicate("P_NUMERIC", operator="lt", value=10, value_type="number")
    with pytest.raises(PredicateContractError, match="invalid fact value"):
        evaluate_expression(
            leaf("P_NUMERIC"),
            catalog(p),
            {"F_SMOOTHNESS": PredicateFact(status="known", value="small")},
        )


def test_all_any_not_and_when_use_strict_strong_kleene_logic():
    smooth = predicate("P_SMOOTH")
    gradient = predicate(
        "P_GRADIENT",
        feature_id="F_GRADIENT",
        value=True,
        value_type="boolean",
    )
    smooth_leaf = leaf("P_SMOOTH")
    gradient_leaf = leaf("P_GRADIENT")
    predicate_catalog = catalog(smooth, gradient)
    facts = {
        "F_SMOOTHNESS": PredicateFact(status="known", value="smooth"),
        "F_GRADIENT": PredicateFact(status="unknown", reason="user has not answered"),
    }

    all_result = evaluate_expression(
        AllExpression(kind="all", items=[smooth_leaf, gradient_leaf]),
        predicate_catalog,
        facts,
    )
    any_result = evaluate_expression(
        AnyExpression(kind="any", items=[smooth_leaf, gradient_leaf]),
        predicate_catalog,
        facts,
    )
    not_result = evaluate_expression(
        NotExpression(kind="not", item=gradient_leaf),
        predicate_catalog,
        facts,
    )
    when_result = evaluate_expression(
        WhenExpression(
            kind="when",
            condition=gradient_leaf,
            then=smooth_leaf,
        ),
        predicate_catalog,
        facts,
    )

    assert all_result.truth == "unknown"
    assert any_result.truth == "true"
    assert not_result.truth == "unknown"
    assert when_result.truth == "unknown"


def test_when_false_skips_guarded_requirement_or_uses_otherwise():
    condition = predicate("P_CONDITION", feature_id="F_NOISE", value="noisy")
    guarded = predicate("P_GUARDED")
    fallback = predicate("P_FALLBACK", feature_id="F_NOISE", value="deterministic")
    predicate_catalog = catalog(condition, guarded, fallback)
    facts = {
        "F_NOISE": PredicateFact(status="known", value="deterministic"),
        "F_SMOOTHNESS": PredicateFact(status="known", value="rough"),
    }
    skipped = evaluate_expression(
        WhenExpression(
            kind="when",
            condition=leaf("P_CONDITION"),
            then=leaf("P_GUARDED"),
        ),
        predicate_catalog,
        facts,
    )
    otherwise = evaluate_expression(
        WhenExpression(
            kind="when",
            condition=leaf("P_CONDITION"),
            then=leaf("P_GUARDED"),
            otherwise=leaf("P_FALLBACK"),
        ),
        predicate_catalog,
        facts,
    )

    assert skipped.truth == "true"
    assert skipped.reason_code == "guard_not_applicable"
    assert otherwise.truth == "true"


def test_when_is_rejected_inside_exclusion_policy():
    condition = predicate("P_CONDITION", feature_id="F_NOISE", value="noisy")
    trigger = predicate("P_TRIGGER")
    exclude_when = policy(
        "POLICY_EXCLUDE_WHEN",
        WhenExpression(
            kind="when",
            condition=leaf("P_CONDITION"),
            then=leaf("P_TRIGGER"),
        ),
        effect="exclude",
    )

    with pytest.raises(ValidationError, match="exclude policies.*not when"):
        PredicateCatalog(
            predicates=[condition, trigger],
            policies=[exclude_when],
        )


def test_catalog_rejects_cross_subject_predicates_and_implicit_overrides():
    family_predicate = predicate(
        "P_FAMILY",
        subject_type="method_family",
        subject_id="MF_TEST",
    )
    cross_subject_policy = policy("POLICY_BAD", leaf("P_FAMILY"))
    with pytest.raises(ValidationError, match="another subject"):
        PredicateCatalog(predicates=[family_predicate], policies=[cross_subject_policy])

    with pytest.raises(ValidationError, match="requires overrides_policy_id"):
        policy("POLICY_REPLACE", leaf("P_FAMILY"), override_action="replace")


def test_catalog_parses_versioned_nested_expression_from_exported_json():
    p = predicate("P_SMOOTH")
    payload = {
        "predicates": [p.model_dump(mode="json")],
        "policies": [
            {
                **policy("POLICY_JSON", leaf("P_SMOOTH")).model_dump(mode="json"),
                "expression": {
                    "kind": "all",
                    "items": [
                        {"kind": "predicate", "predicate_id": "P_SMOOTH"},
                        {
                            "kind": "not",
                            "item": {"kind": "predicate", "predicate_id": "P_SMOOTH"},
                        },
                    ],
                },
            }
        ],
    }

    parsed = PredicateCatalog.model_validate(payload)
    expression = parsed.policies[0].expression
    assert isinstance(expression, AllExpression)
    assert isinstance(expression.items[1], NotExpression)


def test_inheritance_requires_explicit_replace_or_suppress():
    family_predicate = predicate(
        "P_FAMILY",
        subject_type="method_family",
        subject_id="MF_TEST",
    )
    child_predicate = predicate("P_CHILD")
    family_policy = policy(
        "POLICY_FAMILY",
        leaf("P_FAMILY"),
        subject_type="method_family",
        subject_id="MF_TEST",
        inheritance_mode="inheritable",
    )
    replacement = policy(
        "POLICY_CHILD",
        leaf("P_CHILD"),
        override_action="replace",
        overrides_policy_id="POLICY_FAMILY",
    )
    predicate_catalog = PredicateCatalog(
        predicates=[family_predicate, child_predicate],
        policies=[family_policy, replacement],
    )

    effective = resolve_effective_policies(
        predicate_catalog,
        subject_type="method",
        subject_id="M_TEST",
        parent_by_subject={
            ("method", "M_TEST"): ("method_family", "MF_TEST"),
            ("method_family", "MF_TEST"): None,
        },
    )
    assert [item.policy_id for item in effective] == ["POLICY_CHILD"]


def test_inheritance_rejects_missing_or_cyclic_canonical_parent_rows():
    p = predicate("P_REQUIRED")
    required = policy("POLICY_REQUIRED", leaf("P_REQUIRED"))
    predicate_catalog = PredicateCatalog(predicates=[p], policies=[required])

    with pytest.raises(PredicateContractError, match="parent row is missing"):
        resolve_effective_policies(
            predicate_catalog,
            subject_type="method",
            subject_id="M_TEST",
            parent_by_subject={},
        )
    with pytest.raises(PredicateContractError, match="cycle"):
        resolve_effective_policies(
            predicate_catalog,
            subject_type="method",
            subject_id="M_TEST",
            parent_by_subject={
                ("method", "M_TEST"): ("method_family", "MF_TEST"),
                ("method_family", "MF_TEST"): ("method", "M_TEST"),
            },
        )


def test_exclusion_wins_and_unknown_required_policy_is_conditional():
    requirement_predicate = predicate("P_REQUIRED")
    exclusion_predicate = predicate(
        "P_EXCLUDE",
        feature_id="F_NOISE",
        value="large_noise",
        predicate_kind="incompatibility",
    )
    requirement = policy("POLICY_REQUIRED", leaf("P_REQUIRED"))
    exclusion = policy("POLICY_EXCLUDE", leaf("P_EXCLUDE"), effect="exclude")
    predicate_catalog = PredicateCatalog(
        predicates=[requirement_predicate, exclusion_predicate],
        policies=[requirement, exclusion],
        coverage=[coverage()],
    )

    excluded = evaluate_eligibility(
        predicate_catalog,
        {
            "F_SMOOTHNESS": PredicateFact(status="unknown", reason="not answered"),
            "F_NOISE": PredicateFact(status="known", value="large_noise"),
        },
        subject_type="method",
        subject_id="M_TEST",
        parent_by_subject={("method", "M_TEST"): None},
    )
    conditional = evaluate_eligibility(
        predicate_catalog,
        {
            "F_SMOOTHNESS": PredicateFact(status="unknown", reason="not answered"),
            "F_NOISE": PredicateFact(status="known", value="deterministic"),
        },
        subject_type="method",
        subject_id="M_TEST",
        parent_by_subject={("method", "M_TEST"): None},
    )

    assert excluded.status == "excluded"
    assert excluded.reason_code == "excluded_by_policy"
    assert conditional.status == "conditional"


def test_partial_coverage_is_visible_but_not_enforced():
    p = predicate("P_REQUIRED")
    required = policy("POLICY_REQUIRED", leaf("P_REQUIRED"))
    predicate_catalog = PredicateCatalog(
        predicates=[p],
        policies=[required],
        coverage=[coverage(status="partial")],
    )

    result = evaluate_eligibility(
        predicate_catalog,
        {"F_SMOOTHNESS": PredicateFact(status="known", value="rough")},
        subject_type="method",
        subject_id="M_TEST",
        parent_by_subject={("method", "M_TEST"): None},
    )
    assert result.status == "not_evaluated"
    assert result.reason_code == "coverage_incomplete"


def test_missing_coverage_cannot_be_promoted_to_complete_by_the_caller():
    p = predicate("P_REQUIRED")
    required = policy("POLICY_REQUIRED", leaf("P_REQUIRED"))
    predicate_catalog = PredicateCatalog(predicates=[p], policies=[required])

    result = evaluate_eligibility(
        predicate_catalog,
        {"F_SMOOTHNESS": PredicateFact(status="known", value="rough")},
        subject_type="method",
        subject_id="M_TEST",
        parent_by_subject={("method", "M_TEST"): None},
    )
    assert result.status == "not_evaluated"
    assert "missing" in result.reason


def test_rule_target_retirement_requires_complete_method_policy_coverage():
    p = predicate("P_REQUIRED")
    required = policy("POLICY_REQUIRED", leaf("P_REQUIRED"))
    retirement = RuleTargetRetirement(
        retirement_id="RETIRE_R034_BFGS",
        rule_id="R034",
        method_id="M_TEST",
        policy_id="POLICY_REQUIRED",
        reason="predicate policy now owns this hard exclusion",
        source_ids=["S_TEST"],
        last_verified="2026-07-15",
    )

    with pytest.raises(ValidationError, match="complete predicate coverage"):
        PredicateCatalog(
            predicates=[p],
            policies=[required],
            coverage=[coverage(status="partial")],
            rule_target_retirements=[retirement],
        )
    complete = PredicateCatalog(
        predicates=[p],
        policies=[required],
        coverage=[coverage()],
        rule_target_retirements=[retirement],
    )
    assert complete.rule_target_retirements == [retirement]


def test_rule_target_retirement_can_reference_an_inherited_family_policy():
    family_predicate = predicate(
        "P_FAMILY",
        subject_type="method_family",
        subject_id="MF_TEST",
    )
    family_policy = policy(
        "POLICY_FAMILY",
        leaf("P_FAMILY"),
        subject_type="method_family",
        subject_id="MF_TEST",
        inheritance_mode="inheritable",
    )
    retirement = RuleTargetRetirement(
        retirement_id="RETIRE_R034_TEST",
        rule_id="R034",
        method_id="M_TEST",
        policy_id="POLICY_FAMILY",
        reason="inherited predicate policy owns this method target",
        source_ids=["S_TEST"],
        last_verified="2026-07-15",
    )

    predicate_catalog = PredicateCatalog(
        predicates=[family_predicate],
        policies=[family_policy],
        coverage=[coverage()],
        rule_target_retirements=[retirement],
    )
    effective = resolve_effective_policies(
        predicate_catalog,
        subject_type="method",
        subject_id="M_TEST",
        parent_by_subject={
            ("method", "M_TEST"): ("method_family", "MF_TEST"),
            ("method_family", "MF_TEST"): None,
        },
    )
    assert [item.policy_id for item in effective] == ["POLICY_FAMILY"]


def test_composite_evaluation_preserves_unresolved_status_path_and_branch_role():
    condition = predicate("P_CONDITION", feature_id="F_NOISE", value="noisy")
    guarded = predicate("P_GUARDED")
    expression = WhenExpression(
        kind="when",
        condition=leaf("P_CONDITION"),
        then=leaf("P_GUARDED"),
    )
    result = evaluate_expression(
        expression,
        catalog(condition, guarded),
        {"F_NOISE": PredicateFact(status="unsupported", reason="oracle unavailable")},
    )

    assert result.truth == "unknown"
    assert result.unresolved_fact_statuses == ["unsupported"]
    assert result.details[0].path == "$.condition"
    assert result.details[0].role == "condition"


def test_complete_coverage_requires_at_least_one_effective_policy():
    p = predicate("P_REQUIRED")
    required = policy("POLICY_REQUIRED", leaf("P_REQUIRED"))
    predicate_catalog = PredicateCatalog(
        predicates=[p],
        policies=[required],
        coverage=[coverage(subject_id="M_EMPTY")],
    )

    with pytest.raises(PredicateContractError, match="requires effective policies"):
        evaluate_eligibility(
            predicate_catalog,
            {},
            subject_type="method",
            subject_id="M_EMPTY",
            parent_by_subject={("method", "M_EMPTY"): None},
        )
