# ADR 0004: Atomic method predicates and three-valued eligibility

- Status: Accepted
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

### 2. Atomic predicate record

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
  "status": "required",
  "rationale_key": "RATIONALE_BFGS_SMOOTHNESS",
  "source_ids": ["S001"],
  "confidence": "high",
  "last_verified": "2026-07-15"
}
```

`predicate_kind` distinguishes `assumption`, `capability`,
`incompatibility`, and `recommendation_guard`. The `feature_id`, operator, and
value are machine fields; rationale, source, confidence, and review date are
evidence fields. An atomic predicate has no embedded prose condition.

The controlled operator vocabulary is `eq`, `neq`, `in`, `not_in`, `lt`, `lte`,
`gt`, `gte`, `contains`, `exists`, and `not_exists`. Values refer to
`controlled_vocab` codes or typed numeric values; arbitrary executable
expressions are forbidden.

### 3. Versioned expression semantics

Method eligibility is a versioned expression tree whose leaves are atomic
predicates:

```json
{
  "schema_version": "1.0.0",
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

The evaluator returns `true`, `false`, or `unknown` using strong three-valued
logic:

- `all`: false if any child is false; otherwise unknown if a child is unknown;
  otherwise true.
- `any`: true if any child is true; otherwise unknown if a child is unknown;
  otherwise false.
- `not`: true/false are inverted and unknown remains unknown.
- `when`: an unknown condition produces unknown; it is never silently treated as
  false.

`unknown` means the problem fact is not answered or not evidenced. It is not the
same as `unsupported` (the method/implementation explicitly does not support
the value) or `not_applicable` (the predicate has no meaning for this problem
type). The exported evaluation result preserves all three statuses and a
stable mismatch reason.

### 4. Inheritance and implementation boundary

Method-family predicates are inherited first, then method predicates are applied
as explicit additions or overrides. An override must name the predicate it
replaces and provide its own source and review date; silent weakening is invalid.

Theoretical assumptions describe what the method requires mathematically.
Implementation capabilities describe what a product/version can do. A method is
not made eligible merely because one implementation has a feature, and an
implementation is not rejected merely because a theoretical predicate has no
implementation claim yet.

### 5. Consumer contract

Diagnose, Map, method pages, and comparison eligibility consume the same exported
predicate evaluation. Every excluded or conditional candidate exposes:

- the predicate/expression ID;
- observed value and expected value when available;
- `unknown`, `unsupported`, or `not_applicable` status;
- machine reason and human rationale/source links.

Ranking is not allowed when required predicates are unresolved. A comparison
contract must carry its evaluated predicate context before it may display a
performance difference.

## Migration and validation order

1. Add controlled vocabulary and schema validation with deterministic export.
2. Add the evaluator and golden tests for `true`, `false`, `unknown`,
   `unsupported`, and `not_applicable`.
3. Migrate Gradient Descent, Nelder–Mead, BFGS/L-BFGS, SLSQP/interior-point,
   Branch-and-Bound/CP-SAT, Bayesian Optimization, CMA-ES, and LP/QP/conic
   families.
4. Produce a report for required conditions that still exist only as free text.
5. Re-run recommendation parity and comparison eligibility tests before adding
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
