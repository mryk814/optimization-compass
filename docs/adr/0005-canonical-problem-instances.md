# ADR 0005: Canonical problem definitions and instances

- Status: Accepted
- Date: 2026-07-15
- Related: #45, #49, #50, #62

## Context

The former `demo_objectives` table mixed a mathematical family, one concrete
parameterization, display metadata, and an executable generator. Search Tree and
Bayesian Optimization then used separate in-code problem descriptions. Known optima,
axis bounds, and comparison context could therefore disagree between renderers.

## Decision

Problem identity is split into two versioned entities:

- `problem_definitions` owns mathematical family, variable domain, objective form and
  direction, available oracles, constraint class, dimensionality policy, reference
  semantics, related archetypes/features, provenance, and review date.
- `problem_instances` owns concrete parameters, dimension, bounds, constraints,
  initialization candidates, seed policy, known-reference status and payload, display
  metadata, intended phenomena, limitations, provenance, and review date.

The authority flow is one-way:

```text
problem-suite.json
  ├─> SQLite problem tables and relation tables
  ├─> Python registry validation and executable functions
  └─> generated problems.json
         ├─> visual goal cues
         ├─> comparison context
         └─> constrained / multiobjective renderers
```

SQLite never evaluates an expression. The versioned resource contains stable,
reviewable metadata and small instance data. `problem_registry.py` owns callable
objective/gradient implementations and validates that every registry key is present
exactly once. Generated site data resolves both sides and is never hand edited.

`demo_objectives` is removed rather than kept as a compatibility authority.
`demo_scenarios` and `comparison_sets` now reference `problem_instance_id`. The
`AlgorithmTrace 1.0.0` field remains named `objective_id` for trace-contract stability,
but its value is the canonical problem-instance ID.

## Known-reference semantics

Every instance states one of `known_exact`, `known_reference`, `best_known`, `unknown`,
or `not_meaningful`. The first three require a reference payload and source IDs; the
last two forbid a reference payload. Multiobjective references may identify a Pareto
set/front instead of one point.

## Consequences

- Nelder–Mead, first-order traces, Search Tree, and Bayesian Optimization resolve their
  problem data through the same registry.
- #45 goal cues receive optimum and display metadata from canonical instances.
- #49 and #50 can consume `problems.json` without adding renderer-local constants.
- Adding an instance requires metadata, registry resolution, provenance, and
  round-trip validation, but no new renderer contract by default.
