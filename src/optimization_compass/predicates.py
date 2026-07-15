from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Annotated, Literal, TypeGuard

from pydantic import Field, model_validator

from optimization_compass.metadata_models import MetadataModel, NonBlank

PredicateKind = Literal["assumption", "capability", "incompatibility", "recommendation_guard"]
PredicateOperator = Literal[
    "eq",
    "neq",
    "in",
    "not_in",
    "lt",
    "lte",
    "gt",
    "gte",
    "contains",
]
PredicateValueType = Literal["controlled_code", "number", "string", "boolean", "list"]
PredicateConfidence = Literal["high", "medium", "low"]
PredicateSubjectType = Literal["method", "method_family", "implementation"]
FactStatus = Literal["known", "unknown", "unsupported", "not_applicable"]
PredicateTruth = Literal["true", "false", "unknown"]
PolicyEffect = Literal["require", "exclude"]
InheritanceMode = Literal["inheritable", "local_only"]
OverrideAction = Literal["add", "replace", "suppress"]
CoverageStatus = Literal["complete", "partial", "not_started", "not_applicable"]
EligibilityStatus = Literal["eligible", "conditional", "excluded", "not_evaluated"]
DetailRole = Literal["operand", "condition", "then", "otherwise"]
SubjectKey = tuple[PredicateSubjectType, str]
ReasonCode = Literal[
    "matched",
    "mismatch",
    "missing_fact",
    "unknown_fact",
    "unsupported_fact",
    "not_applicable_fact",
    "all_expression",
    "any_expression",
    "not_expression",
    "guard_not_applicable",
    "required_policy_satisfied",
    "required_policy_violated",
    "excluded_by_policy",
    "exclusion_not_triggered",
    "policy_unresolved",
    "all_policies_satisfied",
    "coverage_incomplete",
]


class PredicateContractError(ValueError):
    """Raised when the predicate catalog or supplied facts violate the contract."""


class AtomicPredicate(MetadataModel):
    """A versioned condition over one canonical problem feature."""

    predicate_id: NonBlank
    schema_version: Literal["1.0.0"]
    subject_type: PredicateSubjectType
    subject_id: NonBlank
    predicate_kind: PredicateKind
    feature_id: NonBlank
    operator: PredicateOperator
    value: object
    value_type: PredicateValueType
    rationale_key: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    confidence: PredicateConfidence
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_value_contract(self) -> AtomicPredicate:
        _require_unique(self.source_ids, "source_ids")
        if self.subject_type == "implementation" and self.predicate_kind != "capability":
            raise ValueError("implementation predicates must use predicate_kind=capability")
        if self.operator in {"in", "not_in"} and not isinstance(self.value, list):
            raise ValueError(f"{self.operator} requires a list value")
        if self.operator in {"in", "not_in"} and not self.value:
            raise ValueError(f"{self.operator} requires a non-empty list value")
        if self.operator in {"lt", "lte", "gt", "gte"}:
            if not _is_number(self.value):
                raise ValueError(f"{self.operator} requires a numeric value")
            if self.value_type != "number":
                raise ValueError(f"{self.operator} requires value_type=number")
        if self.value_type == "controlled_code" and not (
            isinstance(self.value, str)
            or (
                isinstance(self.value, list)
                and bool(self.value)
                and all(isinstance(item, str) and item for item in self.value)
            )
        ):
            raise ValueError("controlled_code requires a string or non-empty string list")
        if self.value_type == "number" and not _is_number(self.value):
            raise ValueError("number value_type requires a numeric value")
        if self.value_type == "string" and not isinstance(self.value, str):
            raise ValueError("string value_type requires a string value")
        if self.value_type == "boolean" and not isinstance(self.value, bool):
            raise ValueError("boolean value_type requires a boolean value")
        if self.value_type == "list" and not isinstance(self.value, list):
            raise ValueError("list value_type requires a list value")
        return self


class PredicateFact(MetadataModel):
    """A problem fact; epistemic/support status is separate from predicate truth."""

    status: FactStatus
    value: object | None = None
    source_ids: list[NonBlank] = Field(default_factory=list)
    reason: NonBlank | None = None

    @model_validator(mode="after")
    def validate_fact(self) -> PredicateFact:
        _require_unique(self.source_ids, "source_ids")
        if self.status == "known":
            if self.value is None:
                raise ValueError("known facts require a value")
            if self.reason is not None:
                raise ValueError("known facts do not accept an unresolved reason")
        else:
            if self.value is not None:
                raise ValueError("non-known facts must not carry a value")
            if self.reason is None:
                raise ValueError(f"{self.status} facts require a reason")
        return self


class PredicateLeaf(MetadataModel):
    kind: Literal["predicate"]
    predicate_id: NonBlank


class AllExpression(MetadataModel):
    kind: Literal["all"]
    items: list[PredicateExpression] = Field(min_length=1)


class AnyExpression(MetadataModel):
    kind: Literal["any"]
    items: list[PredicateExpression] = Field(min_length=1)


class NotExpression(MetadataModel):
    kind: Literal["not"]
    item: PredicateExpression


class WhenExpression(MetadataModel):
    kind: Literal["when"]
    condition: PredicateExpression
    then: PredicateExpression
    otherwise: PredicateExpression | None = None


type PredicateExpression = Annotated[
    PredicateLeaf | AllExpression | AnyExpression | NotExpression | WhenExpression,
    Field(discriminator="kind"),
]

for _expression_model in (AllExpression, AnyExpression, NotExpression, WhenExpression):
    _expression_model.model_rebuild()


class PredicatePolicy(MetadataModel):
    """A subject-level eligibility or exclusion policy composed from atomic predicates."""

    policy_id: NonBlank
    schema_version: Literal["1.0.0"]
    subject_type: PredicateSubjectType
    subject_id: NonBlank
    effect: PolicyEffect
    expression: PredicateExpression | None
    inheritance_mode: InheritanceMode
    override_action: OverrideAction = "add"
    overrides_policy_id: NonBlank | None = None
    rationale_key: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    confidence: PredicateConfidence
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_override(self) -> PredicatePolicy:
        _require_unique(self.source_ids, "source_ids")
        if self.override_action == "add":
            if self.overrides_policy_id is not None:
                raise ValueError("add policies must not name overrides_policy_id")
            if self.expression is None:
                raise ValueError("add policies require an expression")
        else:
            if self.overrides_policy_id is None:
                raise ValueError(f"{self.override_action} requires overrides_policy_id")
            if self.override_action == "replace" and self.expression is None:
                raise ValueError("replace policies require an expression")
            if self.override_action == "suppress":
                if self.expression is not None:
                    raise ValueError("suppress policies must not define an expression")
                if self.inheritance_mode != "local_only":
                    raise ValueError("suppress policies must be local_only")
        return self


class PredicateCoverage(MetadataModel):
    subject_type: Literal["method", "implementation"]
    subject_id: NonBlank
    status: CoverageStatus
    rationale: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_sources(self) -> PredicateCoverage:
        _require_unique(self.source_ids, "source_ids")
        return self


class RuleTargetRetirement(MetadataModel):
    """Retire one method target from one legacy decision rule after policy migration."""

    retirement_id: NonBlank
    rule_id: NonBlank
    method_id: NonBlank
    policy_id: NonBlank
    reason: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_sources(self) -> RuleTargetRetirement:
        _require_unique(self.source_ids, "source_ids")
        return self


class PredicateCatalog(MetadataModel):
    predicates: list[AtomicPredicate] = Field(min_length=1)
    policies: list[PredicatePolicy] = Field(min_length=1)
    coverage: list[PredicateCoverage] = Field(default_factory=list)
    rule_target_retirements: list[RuleTargetRetirement] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_catalog(self) -> PredicateCatalog:
        predicate_ids = [predicate.predicate_id for predicate in self.predicates]
        policy_ids = [policy.policy_id for policy in self.policies]
        coverage_ids = [(row.subject_type, row.subject_id) for row in self.coverage]
        retirement_ids = [row.retirement_id for row in self.rule_target_retirements]
        retired_targets = [(row.rule_id, row.method_id) for row in self.rule_target_retirements]
        _require_unique(predicate_ids, "predicate_id")
        _require_unique(policy_ids, "policy_id")
        _require_unique(coverage_ids, "predicate coverage subject")
        _require_unique(retirement_ids, "retirement_id")
        _require_unique(retired_targets, "retired rule target")
        predicates = self.predicates_by_id()
        policies = self.policies_by_id()
        coverage = self.coverage_by_subject()
        for policy in self.policies:
            if policy.subject_type == "implementation" and policy.effect != "require":
                raise ValueError("implementation policies must use effect=require")
            if policy.expression is not None:
                for predicate_id in _expression_predicate_ids(policy.expression):
                    predicate = predicates.get(predicate_id)
                    if predicate is None:
                        raise ValueError(f"policy references missing predicate: {predicate_id}")
                    if (predicate.subject_type, predicate.subject_id) != (
                        policy.subject_type,
                        policy.subject_id,
                    ):
                        raise ValueError(
                            f"policy {policy.policy_id} references predicate from another subject"
                        )
            if policy.overrides_policy_id is not None:
                overridden = policies.get(policy.overrides_policy_id)
                if overridden is None:
                    raise ValueError(
                        f"policy references missing override: {policy.overrides_policy_id}"
                    )
                if overridden.effect != policy.effect:
                    raise ValueError("policy override cannot change require/exclude effect")
                if (overridden.subject_type, overridden.subject_id) == (
                    policy.subject_type,
                    policy.subject_id,
                ):
                    raise ValueError("policy override must target an inherited policy")
            if (
                policy.effect == "exclude"
                and policy.expression is not None
                and _expression_contains_when(policy.expression)
            ):
                raise ValueError(
                    "exclude policies must express conditional triggers with all/not, not when"
                )
        for retirement in self.rule_target_retirements:
            retired_policy = policies.get(retirement.policy_id)
            if retired_policy is None:
                raise ValueError(
                    f"rule target retirement references missing policy: {retirement.policy_id}"
                )
            if retired_policy.subject_type == "implementation" or (
                retired_policy.subject_type == "method"
                and retired_policy.subject_id != retirement.method_id
            ):
                raise ValueError(
                    "rule target retirement policy must belong to the method or its family"
                )
            method_coverage = coverage.get(("method", retirement.method_id))
            if method_coverage is None or method_coverage.status != "complete":
                raise ValueError("rule targets may retire only after complete predicate coverage")
        return self

    def predicates_by_id(self) -> dict[str, AtomicPredicate]:
        return {predicate.predicate_id: predicate for predicate in self.predicates}

    def policies_by_id(self) -> dict[str, PredicatePolicy]:
        return {policy.policy_id: policy for policy in self.policies}

    def coverage_by_subject(self) -> dict[tuple[str, str], PredicateCoverage]:
        return {(row.subject_type, row.subject_id): row for row in self.coverage}


class EvaluationDetail(MetadataModel):
    predicate_id: NonBlank
    feature_id: NonBlank
    truth: PredicateTruth
    fact_status: FactStatus
    reason_code: ReasonCode
    reason: NonBlank
    expected_value: object
    observed_value: object | None = None
    path: NonBlank
    role: DetailRole


class PredicateEvaluation(MetadataModel):
    truth: PredicateTruth
    reason_code: ReasonCode
    reason: NonBlank
    details: list[EvaluationDetail] = Field(default_factory=list)
    unresolved_fact_statuses: list[Literal["unknown", "unsupported", "not_applicable"]] = Field(
        default_factory=list
    )


class PolicyEvaluation(MetadataModel):
    policy_id: NonBlank
    effect: PolicyEffect
    truth: PredicateTruth
    status: Literal["eligible", "conditional", "excluded"]
    reason_code: ReasonCode
    reason: NonBlank
    details: list[EvaluationDetail]


class EligibilityEvaluation(MetadataModel):
    status: EligibilityStatus
    reason_code: ReasonCode
    reason: NonBlank
    policy_evaluations: list[PolicyEvaluation] = Field(default_factory=list)


def resolve_effective_policies(
    catalog: PredicateCatalog,
    *,
    subject_type: PredicateSubjectType,
    subject_id: str,
    parent_by_subject: Mapping[SubjectKey, SubjectKey | None],
) -> list[PredicatePolicy]:
    """Derive canonical lineage, then apply explicit local add/replace/suppress rows."""

    effective: dict[str, PredicatePolicy] = {}
    subject = (subject_type, subject_id)
    ancestors = _resolve_ancestors(subject, parent_by_subject)
    layers = [*ancestors, subject]
    for layer_type, layer_id in layers:
        is_local = (layer_type, layer_id) == (subject_type, subject_id)
        layer_policies = [
            policy
            for policy in catalog.policies
            if (policy.subject_type, policy.subject_id) == (layer_type, layer_id)
            and (is_local or policy.inheritance_mode == "inheritable")
        ]
        for policy in layer_policies:
            if policy.override_action == "add":
                effective[policy.policy_id] = policy
                continue
            target_id = policy.overrides_policy_id
            if target_id not in effective:
                raise PredicateContractError(
                    f"policy {policy.policy_id} overrides a policy that is not inherited: "
                    f"{target_id}"
                )
            effective.pop(str(target_id))
            if policy.override_action == "replace":
                effective[policy.policy_id] = policy
    return list(effective.values())


def evaluate_expression(
    expression: PredicateExpression,
    catalog: PredicateCatalog,
    facts: Mapping[str, PredicateFact],
) -> PredicateEvaluation:
    """Evaluate one expression with strict strong-Kleene three-valued semantics."""

    return _evaluate(
        expression,
        catalog.predicates_by_id(),
        facts,
        path="$",
        role="operand",
    )


def evaluate_eligibility(
    catalog: PredicateCatalog,
    facts: Mapping[str, PredicateFact],
    *,
    subject_type: PredicateSubjectType,
    subject_id: str,
    parent_by_subject: Mapping[SubjectKey, SubjectKey | None],
) -> EligibilityEvaluation:
    """Resolve catalog-owned coverage and lineage, then enforce exclusion wins."""

    coverage = catalog.coverage_by_subject().get((subject_type, subject_id))
    if coverage is None or coverage.status != "complete":
        coverage_status = "missing" if coverage is None else coverage.status
        return EligibilityEvaluation(
            status="not_evaluated",
            reason_code="coverage_incomplete",
            reason=f"predicate coverage is {coverage_status}; eligibility was not enforced",
        )
    policies = resolve_effective_policies(
        catalog,
        subject_type=subject_type,
        subject_id=subject_id,
        parent_by_subject=parent_by_subject,
    )
    if not policies:
        raise PredicateContractError("complete predicate coverage requires effective policies")
    evaluations: list[PolicyEvaluation] = []
    for policy in policies:
        if policy.override_action == "suppress" or policy.expression is None:
            raise PredicateContractError(
                f"effective policy cannot be evaluated: {policy.policy_id}"
            )
        result = evaluate_expression(policy.expression, catalog, facts)
        evaluations.append(_evaluate_policy(policy, result))

    excluded = next(
        (item for item in evaluations if item.effect == "exclude" and item.status == "excluded"),
        None,
    )
    if excluded is None:
        excluded = next((item for item in evaluations if item.status == "excluded"), None)
    if excluded is not None:
        return EligibilityEvaluation(
            status="excluded",
            reason_code=excluded.reason_code,
            reason=excluded.reason,
            policy_evaluations=evaluations,
        )
    conditional = next((item for item in evaluations if item.status == "conditional"), None)
    if conditional is not None:
        return EligibilityEvaluation(
            status="conditional",
            reason_code="policy_unresolved",
            reason=conditional.reason,
            policy_evaluations=evaluations,
        )
    return EligibilityEvaluation(
        status="eligible",
        reason_code="all_policies_satisfied",
        reason="all required policies are satisfied and no exclusion policy matched",
        policy_evaluations=evaluations,
    )


def _evaluate(
    expression: PredicateExpression,
    predicates: Mapping[str, AtomicPredicate],
    facts: Mapping[str, PredicateFact],
    *,
    path: str,
    role: DetailRole,
) -> PredicateEvaluation:
    if expression.kind == "predicate":
        predicate = predicates.get(expression.predicate_id)
        if predicate is None:
            raise PredicateContractError(
                f"predicate definition is missing from the catalog: {expression.predicate_id}"
            )
        return _evaluate_predicate(predicate, facts, path=path, role=role)
    if expression.kind == "not":
        result = _evaluate(
            expression.item,
            predicates,
            facts,
            path=f"{path}.item",
            role=role,
        )
        truth: PredicateTruth
        if result.truth == "true":
            truth = "false"
        elif result.truth == "false":
            truth = "true"
        else:
            truth = "unknown"
        return PredicateEvaluation(
            truth=truth,
            reason_code="not_expression",
            reason=f"negated expression evaluated as {truth}",
            details=result.details,
            unresolved_fact_statuses=result.unresolved_fact_statuses,
        )
    if expression.kind == "all":
        return _combine(
            expression.items,
            predicates,
            facts,
            mode="all",
            path=path,
            role=role,
        )
    if expression.kind == "any":
        return _combine(
            expression.items,
            predicates,
            facts,
            mode="any",
            path=path,
            role=role,
        )

    condition = _evaluate(
        expression.condition,
        predicates,
        facts,
        path=f"{path}.condition",
        role="condition",
    )
    if condition.truth == "unknown":
        return PredicateEvaluation(
            truth="unknown",
            reason_code="policy_unresolved",
            reason="when condition is unknown",
            details=condition.details,
            unresolved_fact_statuses=condition.unresolved_fact_statuses,
        )
    if condition.truth == "false":
        if expression.otherwise is None:
            return PredicateEvaluation(
                truth="true",
                reason_code="guard_not_applicable",
                reason="when condition is false; guarded requirement does not apply",
                details=condition.details,
                unresolved_fact_statuses=condition.unresolved_fact_statuses,
            )
        branch = _evaluate(
            expression.otherwise,
            predicates,
            facts,
            path=f"{path}.otherwise",
            role="otherwise",
        )
        return _with_details(branch, [*condition.details, *branch.details])
    branch = _evaluate(
        expression.then,
        predicates,
        facts,
        path=f"{path}.then",
        role="then",
    )
    return _with_details(branch, [*condition.details, *branch.details])


def _evaluate_predicate(
    predicate: AtomicPredicate,
    facts: Mapping[str, PredicateFact],
    *,
    path: str,
    role: DetailRole,
) -> PredicateEvaluation:
    fact = facts.get(predicate.feature_id)
    if fact is None:
        return _unknown_detail(
            predicate,
            fact_status="unknown",
            reason_code="missing_fact",
            reason="problem fact is not answered",
            path=path,
            role=role,
        )
    if fact.status != "known":
        reason_codes: dict[FactStatus, ReasonCode] = {
            "known": "matched",
            "unknown": "unknown_fact",
            "unsupported": "unsupported_fact",
            "not_applicable": "not_applicable_fact",
        }
        return _unknown_detail(
            predicate,
            fact_status=fact.status,
            reason_code=reason_codes[fact.status],
            reason=str(fact.reason),
            path=path,
            role=role,
        )
    try:
        matches = _compare(predicate.operator, fact.value, predicate.value)
    except TypeError as exc:
        raise PredicateContractError(
            f"invalid fact value for {predicate.predicate_id}: {exc}"
        ) from exc
    truth: PredicateTruth = "true" if matches else "false"
    reason_code: ReasonCode = "matched" if matches else "mismatch"
    reason = "predicate matches expected value" if matches else "predicate value does not match"
    detail = EvaluationDetail(
        predicate_id=predicate.predicate_id,
        feature_id=predicate.feature_id,
        truth=truth,
        fact_status="known",
        reason_code=reason_code,
        reason=reason,
        expected_value=predicate.value,
        observed_value=fact.value,
        path=path,
        role=role,
    )
    return PredicateEvaluation(
        truth=truth,
        reason_code=reason_code,
        reason=reason,
        details=[detail],
        unresolved_fact_statuses=[],
    )


def _unknown_detail(
    predicate: AtomicPredicate,
    *,
    fact_status: FactStatus,
    reason_code: ReasonCode,
    reason: str,
    path: str,
    role: DetailRole,
) -> PredicateEvaluation:
    detail = EvaluationDetail(
        predicate_id=predicate.predicate_id,
        feature_id=predicate.feature_id,
        truth="unknown",
        fact_status=fact_status,
        reason_code=reason_code,
        reason=reason,
        expected_value=predicate.value,
        path=path,
        role=role,
    )
    return PredicateEvaluation(
        truth="unknown",
        reason_code=reason_code,
        reason=reason,
        details=[detail],
        unresolved_fact_statuses=_unresolved_fact_statuses([detail]),
    )


def _evaluate_policy(policy: PredicatePolicy, result: PredicateEvaluation) -> PolicyEvaluation:
    if result.truth == "unknown":
        return PolicyEvaluation(
            policy_id=policy.policy_id,
            effect=policy.effect,
            truth=result.truth,
            status="conditional",
            reason_code="policy_unresolved",
            reason=f"policy {policy.policy_id} is unresolved: {result.reason}",
            details=result.details,
        )
    if policy.effect == "require":
        satisfied = result.truth == "true"
        return PolicyEvaluation(
            policy_id=policy.policy_id,
            effect=policy.effect,
            truth=result.truth,
            status="eligible" if satisfied else "excluded",
            reason_code=("required_policy_satisfied" if satisfied else "required_policy_violated"),
            reason=(
                f"required policy {policy.policy_id} is satisfied"
                if satisfied
                else f"required policy {policy.policy_id} is violated"
            ),
            details=result.details,
        )
    triggered = result.truth == "true"
    return PolicyEvaluation(
        policy_id=policy.policy_id,
        effect=policy.effect,
        truth=result.truth,
        status="excluded" if triggered else "eligible",
        reason_code="excluded_by_policy" if triggered else "exclusion_not_triggered",
        reason=(
            f"exclusion policy {policy.policy_id} matched"
            if triggered
            else f"exclusion policy {policy.policy_id} did not match"
        ),
        details=result.details,
    )


def _combine(
    expressions: list[PredicateExpression],
    predicates: Mapping[str, AtomicPredicate],
    facts: Mapping[str, PredicateFact],
    *,
    mode: Literal["all", "any"],
    path: str,
    role: DetailRole,
) -> PredicateEvaluation:
    results = [
        _evaluate(
            expression,
            predicates,
            facts,
            path=f"{path}.items[{index}]",
            role=role,
        )
        for index, expression in enumerate(expressions)
    ]
    truths = [result.truth for result in results]
    if mode == "all":
        truth: PredicateTruth = (
            "false" if "false" in truths else "unknown" if "unknown" in truths else "true"
        )
        reason_code: ReasonCode = "all_expression"
    else:
        truth = "true" if "true" in truths else "unknown" if "unknown" in truths else "false"
        reason_code = "any_expression"
    details = [detail for result in results for detail in result.details]
    return PredicateEvaluation(
        truth=truth,
        reason_code=reason_code,
        reason=f"{mode} expression evaluated as {truth}",
        details=details,
        unresolved_fact_statuses=_unresolved_fact_statuses(details),
    )


def _compare(operator: PredicateOperator, observed: object, expected: object) -> bool:
    if operator == "eq":
        return observed == expected
    if operator == "neq":
        return observed != expected
    if operator == "in":
        return bool(observed in _as_sequence(expected))
    if operator == "not_in":
        return bool(observed not in _as_sequence(expected))
    if operator in {"lt", "lte", "gt", "gte"}:
        return _numeric_compare(observed, expected, operator)
    if operator == "contains":
        if not isinstance(observed, (str, list, tuple, set, dict)):
            raise TypeError("contains requires a string or collection fact")
        return bool(expected in observed)
    raise AssertionError(f"unreachable predicate operator: {operator}")


def _as_sequence(value: object) -> Sequence[object]:
    if not isinstance(value, list):
        raise TypeError("membership comparison requires a list predicate value")
    return value


def _numeric_compare(observed: object, expected: object, operator: PredicateOperator) -> bool:
    if not _is_number(observed) or not _is_number(expected):
        raise TypeError("numeric comparison requires numeric values")
    if operator == "lt":
        return observed < expected
    if operator == "lte":
        return observed <= expected
    if operator == "gt":
        return observed > expected
    return observed >= expected


def _expression_predicate_ids(expression: PredicateExpression) -> list[str]:
    if expression.kind == "predicate":
        return [expression.predicate_id]
    if expression.kind == "not":
        return _expression_predicate_ids(expression.item)
    if expression.kind == "all":
        return [
            predicate_id
            for item in expression.items
            for predicate_id in _expression_predicate_ids(item)
        ]
    if expression.kind == "any":
        return [
            predicate_id
            for item in expression.items
            for predicate_id in _expression_predicate_ids(item)
        ]
    result = [*_expression_predicate_ids(expression.condition)]
    result.extend(_expression_predicate_ids(expression.then))
    if expression.otherwise is not None:
        result.extend(_expression_predicate_ids(expression.otherwise))
    return result


def _expression_contains_when(expression: PredicateExpression) -> bool:
    if expression.kind == "when":
        return True
    if expression.kind == "predicate":
        return False
    if expression.kind == "not":
        return _expression_contains_when(expression.item)
    return any(_expression_contains_when(item) for item in expression.items)


def _resolve_ancestors(
    subject: SubjectKey,
    parent_by_subject: Mapping[SubjectKey, SubjectKey | None],
) -> list[SubjectKey]:
    if subject not in parent_by_subject:
        raise PredicateContractError(f"canonical parent row is missing for subject: {subject}")
    ancestors: list[SubjectKey] = []
    seen = {subject}
    current = subject
    while True:
        parent = parent_by_subject.get(current)
        if parent is None:
            break
        if parent in seen:
            raise PredicateContractError(f"predicate inheritance cycle detected at: {parent}")
        if parent not in parent_by_subject:
            raise PredicateContractError(f"canonical parent row is missing for ancestor: {parent}")
        seen.add(parent)
        ancestors.append(parent)
        current = parent
    ancestors.reverse()
    return ancestors


def _with_details(
    result: PredicateEvaluation,
    details: list[EvaluationDetail],
) -> PredicateEvaluation:
    return result.model_copy(
        update={
            "details": details,
            "unresolved_fact_statuses": _unresolved_fact_statuses(details),
        }
    )


def _unresolved_fact_statuses(
    details: Sequence[EvaluationDetail],
) -> list[Literal["unknown", "unsupported", "not_applicable"]]:
    statuses: list[Literal["unknown", "unsupported", "not_applicable"]] = []
    for detail in details:
        if detail.fact_status == "known" or detail.fact_status in statuses:
            continue
        statuses.append(detail.fact_status)
    return statuses


def _is_number(value: object) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_unique(values: Sequence[object], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} values are not allowed")
