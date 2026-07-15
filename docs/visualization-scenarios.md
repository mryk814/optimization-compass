# Visualization scenario contract

This document defines the shared vocabulary published in
`site/public/data/visualization-scenarios.json`. `AlgorithmTrace 1.0.0` remains the execution
contract for trajectory-based families; renderer-specific payloads use the same scenario envelope
and their own exact family contract.

## Identity model

```text
ProblemDefinition
  └─ ProblemInstance
       └─ VisualizationScenario
            ├─ MethodRun ──> AlgorithmTrace or result artifact
            └─ Schematic artifact
                         └─ RendererFamily
```

- `ProblemDefinition`: mathematical structure and oracle capabilities; for example,
  unconstrained continuous minimization or mixed-integer scheduling.
- `ProblemInstance`: concrete coefficients/data/domain/dimension and known reference
  values. A procedural generator plus parameters may define it without storing large
  arrays in SQLite.
- `VisualizationScenario`: the educational question, fixed experiment conditions,
  expected phenomenon, artifact kind, and renderer request.
- `MethodRun`: one method, implementation mapping, parameter preset, seed, budget, and
  stopping policy applied within the scenario.
- `AlgorithmTrace`: immutable full-snapshot execution observations. It is an output of
  a run, not the scenario definition.
- `RendererFamily`: an exact parser and component for an observable geometry. It is
  selected by family metadata, not inferred from a method ID.

## Minimum `VisualizationScenario 1.0.0`

The generated contract uses stable IDs and exact enums. Unknown contract versions and
unknown core fields fail parsing; there is no legacy fallback.

```json
{
  "contract_version": "1.0.0",
  "dataset_version": "0.3.0",
  "scenario_id": "SCENARIO_NM_QUADRATIC",
  "title_ja": "二次関数で単体操作を学ぶ",
  "title_en": "Learn simplex operations on a quadratic",
  "purpose": "mechanism",
  "problem_definition_id": "PROBLEM_CONTINUOUS_UNCONSTRAINED",
  "problem_instance_id": "OBJECTIVE_QUADRATIC_2D",
  "lesson": {
    "expected_phenomenon_ja": "反射・拡大・収縮で単体が移動する",
    "expected_phenomenon_en": "The simplex moves by reflection, expansion, and contraction",
    "limitations_ja": "2次元の教育用決定論的実行",
    "limitations_en": "A deterministic two-dimensional educational run"
  },
  "experiment": {
    "oracle_policy": ["objective_value"],
    "initial_condition": {"point": [-2.5, 2.0]},
    "parameter_preset_id": "NM_EDUCATIONAL_DEFAULT",
    "seed": {"status": "not_applicable", "value": null},
    "budget": {"metric": "oracle_evaluations", "value": 80},
    "stopping": {"max_oracle_evaluations": 80, "simplex_tolerance": 0.0001},
    "tuning_policy": "fixed_preset"
  },
  "runs": [
    {
      "run_id": "RUN_NM_QUADRATIC_DEFAULT",
      "method_id": "M_NELDER_MEAD",
      "profile_id": "PROFILE_NELDER_MEAD_2D",
      "implementation_mapping_status": "not_applicable",
      "implementation_id": null,
      "artifact_id": "nelder-mead-quadratic"
    }
  ],
  "artifact": {
    "artifact_kind": "executable_trace",
    "artifact_contract": "AlgorithmTrace",
    "artifact_contract_version": "1.0.0",
    "renderer_family": "simplex_geometry",
    "renderer_contract_version": "1.0.0",
    "observable_ids": ["objective_value", "simplex_vertices", "accepted_operation"],
    "payload_path": "traces/nelder-mead-quadratic.json",
    "payload_bytes": 12345,
    "payload_sha256": "<64 lowercase hex characters>"
  },
  "source_ids": ["S001", "S070"],
  "last_verified": "2026-07-15"
}
```

### Required enums

`purpose` is exactly one of:

- `mechanism`: reveal the method's internal operation.
- `comparison`: compare runs under an authored comparison contract.
- `failure_contrast`: explain a known mismatch or failure mode.
- `sensitivity`: vary one declared condition or hyperparameter.
- `application_result`: explain inputs, constraints, and results of an application.
- `schematic`: explain a concept that is not faithfully represented by an execution
  trace.

`artifact_kind` is exactly one of:

- `executable_trace`
- `schematic_animation`
- `static_diagram`
- `result_visualization`

The contract does not infer either enum from the renderer or method.

## Method run and renderer payload boundary

The common run identity owns method/implementation references and reproducibility
conditions. The common artifact envelope owns kind, contract, renderer family, and
observable IDs. A renderer-specific payload owns only geometry needed by that family.

For example, `search_tree` may define nodes, parent edges, bounds, incumbent changes,
and pruning reasons. `surrogate_uncertainty` may define observations, posterior mean,
uncertainty bands, acquisition values, and selected candidates. Neither payload repeats
scenario title, method ID, budget, provenance, or limitations.

Executable families should consume `AlgorithmTrace` points/vectors/metrics where those
fields suffice. A family extension uses a namespaced, versioned renderer payload rather
than teaching the common player method-specific keys.

## Comparison contract

Sharing a problem instance does not imply a meaningful comparison. A comparison
envelope must declare pairwise or group eligibility:

```json
{
  "comparison_contract_version": "1.0.0",
  "comparison_id": "COMPARE_GRADIENT_FAMILY",
  "scenario_ids": ["SCENARIO_GD_QUADRATIC", "SCENARIO_MOMENTUM_QUADRATIC"],
  "comparability": "directly_comparable",
  "caveat_ja": null,
  "caveat_en": null,
  "fairness": {
    "problem_instance_id": "OBJECTIVE_ROSENBROCK_2D",
    "oracle_policy": ["objective_value", "gradient"],
    "initial_condition_policy": "identical",
    "budget": {"metric": "oracle_evaluations", "value": 200},
    "stopping_policy": "identical",
    "parameter_tuning_policy": "fixed_documented_preset",
    "seed_policy": "not_applicable"
  },
  "synchronization": "oracle_evaluations"
}
```

`comparability` is one of:

- `directly_comparable`: the fairness block is satisfied without qualification.
- `comparable_with_caveat`: a visible caveat names the unavoidable difference.
- `contrast_only`: co-display is educational, but rank/performance language is barred.
- `not_meaningful`: the UI must not build a synchronized performance comparison.

The comparison records initial conditions, available oracles, budget metric/value,
stopping policy, tuning policy, and seed policy. The UI may show a comparison only when
this authored contract exists. `contrast_only` and `not_meaningful` never produce a
winner or ranking.

## Renderer families

| Family | Minimum payload | Typical purpose |
|---|---|---|
| `continuous_trajectory` | named coordinates, path points, objective values | mechanism, comparison |
| `simplex_geometry` | simplex vertices, operation, accepted/rejected candidate | mechanism, failure contrast |
| `population_distribution` | population members, generation, fitness summaries | mechanism, sensitivity |
| `surrogate_uncertainty` | observations, predictive summary, acquisition, selected point | mechanism, sensitivity |
| `search_tree` | nodes, parent edges, bounds, incumbent, branch/prune reason | mechanism, failure contrast |
| `pareto_front` | objective vectors, dominance state, selected solutions | mechanism, application result |
| `feasible_region` | constraints, boundary/violation observations, candidates | mechanism, application result |
| `schedule_timeline` | resources, tasks, intervals, violations | application result |
| `route_map` | locations, edges, route order/cost | application result |
| `generic_metric_history` | named metric series against declared progress axis | comparison, high-dimensional fallback |

Renderer-family payloads are separately versioned discriminated unions. A new payload
version is added only for a semantic change; adding a scenario or method does not bump
the renderer version.

Issue #26 の実装・生成方法・公平性と限界は
[`bayesian-optimization-theater.md`](bayesian-optimization-theater.md) を参照する。

## Executable and schematic display rules

- Always display the artifact-kind badge and limitations adjacent to the visualization.
- An executable trace names its generator, generator version, run conditions, sources,
  and terminal status.
- A schematic uses labels such as `模式図 / Schematic`; controls must not imply measured
  iteration time or objective evaluations unless those values are authored examples.
- A result visualization names its run artifact or external source and whether data was
  imported or generated.
- Derived GIF/video/static images link back to the scenario and artifact identity.
- A schematic and an executable trace may share a renderer family but never share an
  ambiguous artifact label.

## High-dimensional visualization

Each scenario declares its observable strategy:

1. Prefer invariant metrics: objective, oracle evaluations, constraint violation,
   gradient norm, incumbent/bound gap, hypervolume, or calibration.
2. Use domain observables when they are the lesson: schedule timelines, routes,
   population summaries, or surrogate slices.
3. Show named coordinate slices only when the fixed coordinates and slice definition
   are explicit.
4. A projection must record method, fitted-on dataset, parameters, retained variance
   when defined, and a visible limitation. It is never the sole performance evidence.
5. If no faithful spatial representation exists, use `generic_metric_history`; do not
   silently render the first two dimensions.

## Existing mapping examples

### Nelder–Mead theater

- Purpose: `mechanism`; separate scenarios may use `failure_contrast` or `sensitivity`.
- Problem definition: continuous unconstrained derivative-free minimization.
- Problem instances: current quadratic and Rosenbrock objectives.
- Runs: current deterministic Nelder–Mead generators and presets.
- Artifact: `executable_trace`, `AlgorithmTrace 1.0.0`.
- Renderer: `simplex_geometry`.
- Existing deep links and trace IDs remain unchanged.

### Gradient comparison

- Purpose: `comparison`.
- Problem instance: the current shared ill-conditioned quadratic instance.
- Runs: GD, Momentum, and Adam under the current authored presets.
- Artifact: one trace per run, grouped by the comparison envelope.
- Renderer: `continuous_trajectory` plus `generic_metric_history`.
- Comparability: `comparable_with_caveat` unless the oracle accounting includes both
  objective and gradient work consistently; the caveat must be visible rather than
  implied by a generic fairness sentence.

## Coverage semantics for #24

Coverage is evaluated on a tuple, not a page count:

```text
(entity or problem family, educational purpose, artifact kind, renderer family)
```

Each expected tuple has exactly one state:

- `available`: validated scenario, artifact, renderer, sources, and route exist.
- `partial`: a scenario exists but a required artifact/source/renderer/lesson field is
  missing or only schematic coverage exists where execution coverage is expected.
- `missing`: the tuple is valuable and expected, but no scenario exists.
- `not_applicable`: the tuple is intentionally inapplicable and includes a rationale.

The dashboard reports missing and partial reasons and can prioritize a learning slice;
it must not collapse these states into a single percentage.

## Minimum migration plan

1. Keep `AlgorithmTrace 1.0.0`, current generated paths, and deep links.
2. During #22, export a scenario envelope for the existing two experiences and display
   artifact kind/limitations. No universal framework is required there.
3. Add purpose, instance, artifact, renderer, and comparability metadata to the existing
   canonical tables in one migration when implementation begins. Do not add parallel
   `*_v2` tables.
4. Validate the generated envelope in Python and TypeScript with shared fixtures.
5. In #25, add the renderer registry and `search_tree` family as the first new renderer.
6. In #26, reuse the envelope and registry, adding only `surrogate_uncertainty` family
   payloads.
7. Generate #24 coverage from validated envelopes and explicit expected/not-applicable
   policy records.

