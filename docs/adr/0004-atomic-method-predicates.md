# ADR 0004: Atomic method predicates and three-valued eligibility

- Status: Accepted (revised after design review)
- Date: 2026-07-15
- Decision owners: Optimization Compass maintainers
- Related: #43, #48, #49, #64

## Context

The canonical database currently mixes machine-relevant method conditions with
free-text fields such as `required_conditions`, `exclusion_conditions`, and
`claim_summary`. That is useful for reading, but it cannot reliably answer
whether a method is eligible for a concrete problem, why a candidate was
excluded, or whether the evidence is simply missing.

The same condition must be usable by Diagnose, Map, method pages, comparison
eligibility, and future failure-mode relations. A predicate must therefore be
small enough to evaluate, versioned independently from prose, and traceable to
the feature/value and source that support it.

## Decision

### 1. Canonical authority

SQLite owns the stable predicate definitions, controlled vocabulary, method
family inheritance, method overrides, and problem-feature connections. The
deterministic site exporter resolves these rows into JSON; the browser never
infers predicates from labels or free text.

Long-form rationale remains Markdown/content-owned. Trace values remain owned by
the trace or comparison artifact. Implementation-specific capabilities remain
separate from theoretical method assumptions and are joined only by an explicit
implementation claim.

There is one predicate model. A parallel `v2` table or compatibility evaluator
is not introduced.

### 2. Atomic predicates and subject policies

The implementation contract uses the following logical shape. The final SQL
column names may follow the existing repository naming convention, but the
exported field meanings are fixed here.

```json
{
  "predicate_id": "PRED_GRADIENT_SMOOTH",
  "schema_version": "1.0.0",
  "subject_type": "method",
  "subject_id": "M_BFGS",
  "predicate_kind": "assumption",
  "feature_id": "F_SMOOTHNESS",
  "operator": "in",
  "value": ["smooth", "piecewise_smooth"],
  "value_type": "controlled_code",
  "rationale_key": "RATIONALE_BFGS_SMOOTHNESS",
  "source_ids": ["S001"],
  "confidence": "high",
  "last_verified": "2026-07-15"
}
```

`predicate_kind` distinguishes `assumption`, `capability`,
`incompatibility`, and `recommendation_guard`. The `feature_id`, operator, and
value are machine fields; rationale, source, confidence, and review date are
evidence fields. An atomic predicate has no embedded prose condition and does
not decide by itself whether a method is eligible.

One or more atomic predicates are composed by a subject policy:

```json
{
  "policy_id": "POLICY_BFGS_BASE_REQUIREMENTS",
  "schema_version": "1.0.0",
  "subject_type": "method",
  "subject_id": "M_BFGS",
  "effect": "require",
  "expression": {"kind": "predicate", "predicate_id": "PRED_GRADIENT_SMOOTH"},
  "inheritance_mode": "local_only",
  "override_action": "add",
  "overrides_policy_id": null,
  "rationale_key": "RATIONALE_BFGS_BASE_REQUIREMENTS",
  "source_ids": ["S001"],
  "confidence": "high",
  "last_verified": "2026-07-15"
}
```

Policy `effect` is deliberately limited to `require` and `exclude`. Candidate
promotion and ranking remain owned by `decision_rules`; predicates constrain
the candidates those rules produce. This prevents method assumptions from
becoming a second recommendation system.

The controlled operator vocabulary is `eq`, `neq`, `in`, `not_in`, `lt`, `lte`,
`gt`, `gte`, and `contains`. Values refer to `feature_values`,
`controlled_vocab` codes, or typed numeric values; arbitrary executable
expressions are forbidden. `exists` and `not_exists` are intentionally absent:
a missing fact is `unknown`, not evidence that a feature does not exist.

### 3. Versioned expression semantics

Method eligibility is a versioned expression tree whose leaves are atomic
predicates. The policy's `schema_version` versions the complete tree; nested
nodes do not repeat it:

```json
{
  "kind": "all",
  "items": [
    {"kind": "predicate", "predicate_id": "PRED_GRADIENT_SMOOTH"},
    {"kind": "any", "items": [
      {"kind": "predicate", "predicate_id": "PRED_HAS_GRADIENT"},
      {"kind": "predicate", "predicate_id": "PRED_AUTODIFF_AVAILABLE"}
    ]}
  ]
}
```

The evaluator returns only `true`, `false`, or `unknown` using strong
three-valued logic:

- `all`: false if any child is false; otherwise unknown if a child is unknown;
  otherwise true.
- `any`: true if any child is true; otherwise unknown if a child is unknown;
  otherwise false.
- `not`: true/false are inverted and unknown remains unknown.
- `when`: an unknown condition produces unknown; it is never silently treated as
  false. A false condition evaluates the `otherwise` branch when present, or
  returns true when omitted because the guarded requirement does not apply.

`when` is implication syntax and is valid only in `require` policies. An
`exclude` policy expresses a conditional trigger with `all` and `not`; allowing
`when` there would turn a false guard into true and incorrectly exclude the
subject.

Problem facts carry a separate status axis: `known`, `unknown`, `unsupported`,
or `not_applicable`. The latter three produce logical `unknown` while preserving
their exact fact status, expression path, active branch role, and a stable reason
code in evaluation detail. Composite results expose the distinct unresolved fact
statuses without inserting them into AND/OR/NOT as extra truth values.

A missing predicate definition, unknown schema version, invalid controlled
value, or type mismatch is a contract error. It is not converted into epistemic
`unknown`, because doing so would hide broken canonical data.

### 4. Eligibility, exclusion wins, and recommendation authority

For a `require` policy, true is eligible, false is excluded, and unknown is
conditional. For an `exclude` policy, true is excluded, false is eligible, and
unknown is conditional. Any definitive exclusion wins over support from other
policies or `decision_rules`. Required policies that remain unresolved cannot
produce a first-choice ranking.

`decision_rules` continue to map questionnaire answers to candidate methods,
alternatives, problems, warnings, and follow-up questions. Predicate policies
then gate those method candidates. Once a method reaches complete predicate
coverage, duplicate hard exclusions and hand-written compatibility checks for
that method are removed rather than run in parallel. Because current
`decision_rules.action_target_ids` contains several methods in one row, this
handoff is recorded per `rule_id × method_id × policy_id`; the repository omits
only that retired target while preserving unrelated rule targets.

### 5. Inheritance, migration coverage, and implementation boundary

Method-family policies are inherited first, then method policies are applied as
explicit `add`, `replace`, or `suppress` rows. `replace` and `suppress` must name
the inherited policy they override and provide their own source and review date;
silent weakening is invalid. `methods.parent_method_id` is the inheritance
authority. `method_hierarchy` must agree with it but is not a second inheritance
source. The repository derives the complete parent chain from that column; an
arbitrary caller-provided ancestor list is not accepted by the evaluator.

Every method has explicit predicate migration coverage: `complete`, `partial`,
`not_started`, or `not_applicable`. Only `complete` policies affect eligibility.
Partial rows may be displayed and audited, but are never mixed with free-text
fallback logic at runtime. Evaluation resolves coverage from the canonical
catalog by subject; callers cannot pass or promote a coverage status.

Theoretical assumptions describe what the method requires mathematically.
Implementation capabilities describe what a product/version can do. A method is
not made eligible merely because one implementation has a feature, and an
implementation is not rejected merely because a theoretical predicate has no
implementation claim yet.

An implementation subject may define only `capability` predicates and `require`
policies. Version validity and supersession remain owned by the implementation
claim model introduced in #49.

### 6. Consumer contract

Diagnose, Map, method pages, and comparison eligibility consume the same exported
predicate evaluation. Every excluded or conditional candidate exposes:

- the predicate/expression ID;
- observed value and expected value when available;
- three-valued truth plus the exact fact status (`unknown`, `unsupported`, or
  `not_applicable`);
- machine reason and human rationale/source links.

Ranking is not allowed when required predicates are unresolved. A comparison
contract must carry its evaluated predicate context before it may display a
performance difference.

## Migration and validation order

1. Add controlled vocabulary, policy, override, and coverage schema validation
   with deterministic export.
2. Add the evaluator and golden tests for three-valued truth, separate fact
   status, inheritance, explicit override, and exclusion precedence.
3. Migrate Gradient Descent, Nelder–Mead, BFGS/L-BFGS, SLSQP/interior-point,
   Branch-and-Bound/CP-SAT, Bayesian Optimization, CMA-ES, and LP/QP/conic
   families.
4. Produce a report for required conditions that still exist only as free text,
   duplicate decision-rule exclusions, and incomplete migration coverage.
5. Replace duplicate compatibility paths for complete methods and re-run
   recommendation parity and comparison eligibility tests before adding
   versioned claims in #49 or failure triggers in #64.

The migration preserves canonical IDs and the existing recommendation golden
answers. If a condition cannot be evaluated, the result is `unknown` with a
traceable reason; it is not converted into an optimistic match.

## Consequences

Positive:

- one machine-evaluable contract can explain recommendations, exclusions, and
  comparison eligibility;
- missing evidence remains visible instead of becoming a false negative;
- method assumptions and implementation claims can evolve independently;
- #49 and #64 have a stable foreign-key target.

Costs:

- existing free-text conditions require an explicit migration or a report;
- every predicate override needs source and review metadata;
- exporter and browser contracts must reject unknown schema versions.

## Rejected alternatives

- Parsing English/Japanese free text at runtime: non-deterministic and not
  auditable.
- Treating unknown as false: hides missing evidence and changes recommendation
  behavior.
- One large boolean expression string: cannot provide stable mismatch reasons or
  validate references.
- Storing implementation capability directly on a method assumption: confuses
  theory with product/version support.
