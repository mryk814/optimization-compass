# ADR 0016: Renderer taxonomy and shared observables

- Status: Proposed
- Date: 2026-07-19
- Issue: #141
- Related: #119, #120, #133–#140, ADR 0001, `visualization-scenarios.md`, `trace-contract.md`, PR #210

## Context

Theater and Compare already have a shared `VisualizationScenario 1.2.0` envelope,
`AlgorithmTrace 1.0.0`, and renderer-family labels. The remaining #141 work needs to
cover fields, geometry, trajectories, manifolds, expensive evaluations, uncertainty,
and nested solves without creating a page or payload for every method. The current
contracts already own scenario identity, run conditions, observable IDs, static
summary, text alternative, artifact identity, and payload hashes. This ADR defines
the next implementation seam; it does not change those contracts or canonical data.

## Decision

### 1. Taxonomy

Renderer dispatch is always `renderer_family` plus
`renderer_contract_version`. It never dispatches on `method_id`, case ID, or a page
index. The following names are stable or reserved:

| Family | Status | Visual semantic | Minimum family payload |
|---|---|---|---|
| `continuous_trajectory` | existing | points, phase/state/control paths | named paths, progress, values |
| `simplex_geometry` | existing | simplex operations and candidate decisions | vertices, candidate, operation, decision |
| `generic_metric_history` | existing | high-dimensional or non-spatial fallback | named series and progress axis |
| `search_tree` | existing | branching, bounds, incumbent, pruning | nodes, edges, bounds, prune reason |
| `surrogate_uncertainty` | existing | observations, posterior, acquisition | samples, predictive summary, acquisition |
| `feasible_region` | existing | finite-dimensional feasibility and margins | constraints, boundary/violation, candidates |
| `pareto_front` | existing | objective vectors and dominance | objective vectors, dominance, selection |
| `field_evolution` | existing | scalar/vector fields on a fixed or declared mesh/grid | field snapshots, mesh/grid identity, range |
| `geometry_evolution` | reserved | shape/domain/boundary and mesh validity changes | geometry snapshots, boundary, mesh-quality state |
| `manifold_geometry` | reserved | tangent steps, representations, retractions, geodesic residuals | representation, tangent/retraction, invariant residual |
| `evaluation_timeline` | reserved | simulator calls, fidelity, cost, timeout/failure | call ledger, fidelity, cost unit, outcome |
| `distribution_summary` | reserved | scenario/ensemble outcomes and risk | scenario summaries, violation status, risk measure |
| `nested_solve_timeline` | reserved | outer/inner solves, equilibrium, complementarity, modes | solve tree, residuals, mode intervals, derivative route |

`field_evolution` is for a field over a domain; `geometry_evolution` is for the
domain or mesh itself. `continuous_trajectory` may render state and control paths,
but a mesh/refinement or contact-mode lesson uses the corresponding overlay family
or `nested_solve_timeline`. `generic_metric_history` is the honest primary family
when no faithful spatial view exists. Names such as `population_distribution`,
`schedule_timeline`, and `route_map` in older planning prose are not registered
families; reserve them until a concrete contract and scenario justify them.

### 2. Shared payload boundary

The existing scenario envelope remains the authority for title, lesson, purpose,
problem IDs, run/method identity, seed, budget, stopping, provenance, limitations,
`observable_ids`, `static_summary`, and `text_alternative`. A renderer payload must
not repeat any of those fields or contain canonical method/entity routing.

Every new family contract uses the following conceptual shared envelope before its
family body. Existing `AlgorithmTrace`, search-tree, and surrogate payloads remain
valid; migration is additive and happens only when a family is next implemented.

```json
{
  "payload_contract_version": "1.0.0",
  "artifact_id": "<artifact>",
  "scenario_id": "<scenario>",
  "renderer_family": "<family>",
  "renderer_contract_version": "1.0.0",
  "progress_axis": {"id": "oracle_evaluations", "unit": "evaluations"},
  "observables": [{
    "observable_id": "constraint_violation",
    "kind": "scalar_series",
    "label_ja": "制約違反量",
    "label_en": "constraint violation",
    "unit": null
  }, {
    "observable_id": "state_field",
    "kind": "field",
    "label_ja": "状態field",
    "label_en": "state field",
    "unit": null
  }, {
    "observable_id": "objective_value",
    "kind": "scalar_series",
    "label_ja": "目的関数値",
    "label_en": "objective value",
    "unit": null
  }],
  "event_markers": [{
    "marker_id": "state-solve-3",
    "position": {"axis": "oracle_evaluations", "value": 12},
    "event_type": "state_solve",
    "severity": "info",
    "decision": "not_applicable",
    "observable_ids": ["state_field", "constraint_violation"],
    "label_ja": "状態方程式を解く",
    "label_en": "solve state equation",
    "explanation_key": "state_solve"
  }],
  "static_fallback": {
    "title_ja": "静的な要点",
    "title_en": "Static summary",
    "facts": [
      {"observable_id": "constraint_violation", "value": "0.0", "status": "observed"},
      {"observable_id": "objective_value", "value": "12.4", "status": "observed"}
    ],
    "event_marker_ids": ["state-solve-3"],
    "limitations_ja": "離散化した教育用モデル",
    "limitations_en": "A discretized educational model"
  },
  "family_payload": {}
}
```

The exact family parser owns `family_payload`; it may not move family data into the
shared envelope merely to avoid defining a family contract. `observables` must cover
the artifact's declared IDs exactly, and `lesson` observables/signals may only select
from them. Observable IDs are lowercase stable slugs, not method IDs. Recommended
cross-family IDs are `objective_value`, `constraint_violation`, `gradient_norm`,
`residual_norm`, `incumbent_gap`, `oracle_evaluations`, `state_solves`,
`design_field`, `state_field`, `sensitivity_field`, `geometry`, `mesh_quality`,
`state_trajectory`, `control_trajectory`, `tangent_step`, `retraction_residual`,
`simulation_call`, `fidelity`, `scenario_outcome`, `risk_measure`, `inner_solve`,
`complementarity_residual`, and `mode_sequence`. A family may add namespaced IDs
when none of these semantics fit.

Event markers are semantic annotations, not a second playback clock. `position.axis`
must be a deterministic declared axis such as `frame_index`, `optimizer_iterations`,
`oracle_evaluations`, `state_solves`, or `cost_units`; raw wall-clock time is not an
alignment axis. `event_type` is a lowercase stable slug, `severity` is `info`,
`warning`, or `failure`, and `decision` is `accepted`, `rejected`, or
`not_applicable`. Markers may reference only emitted observables. For an
`AlgorithmTrace`, existing frame `event_type` remains unchanged and an adapter may
project it to these markers; it must not reinterpret method-specific payload keys in
the common player. Compare may align markers only when its authored synchronization
axis matches the marker axis.

`lesson.static_summary` and `lesson.text_alternative` remain the human-readable
authority. `static_fallback` is the deterministic family-side data needed to render
the same lesson without animation: at least two observable facts, the important
success/failure marker IDs, and limitations. It must be generated from the same
payload as the visual view, include artifact kind and execution/result status, and
never imply a continuous-model guarantee from a discretized result.

### 3. Candidate journey mapping

This is a routing proposal, not a claim that any issue is implemented or complete.

| Issue | Primary family | Supporting observables/family | Minimum payload lesson and markers |
|---|---|---|---|
| #133 topology | `field_evolution` | `generic_metric_history` | density/design, state, sensitivity, compliance/volume; `state_solve`, `sensitivity`, `filter`, `update`, checkerboard/failure |
| #134 shape | `geometry_evolution` | `field_evolution`, `generic_metric_history` | boundary/domain, mesh cells and quality, validity, objective; `geometry_update`, `remesh`, `invalid_geometry`, `accepted_update` |
| #135 PDE/simulation | `evaluation_timeline` | `field_evolution`, `generic_metric_history` | design iteration, state/adjoint calls, residual, feasibility, failed evaluation and cost; `state_solve`, `adjoint_solve`, `failed_evaluation`, `tolerance_change` |
| #136 manifolds | `manifold_geometry` | `generic_metric_history` | representation, tangent step, projection/retraction, invariant/geodesic residual; `retraction`, `projection`, `chart_boundary`, `sign_ambiguity`, `infeasible_iterate` |
| #137 control/robotics | `continuous_trajectory` | `generic_metric_history`, `evaluation_timeline` | state/control path, phase portrait, defect, path/terminal margins, mesh; `dynamics_solve`, `constraint_check`, `mesh_refinement`, `disturbed_rollout` |
| #138 expensive/multi-fidelity | `surrogate_uncertainty` | `evaluation_timeline` | observations, posterior/acquisition, fidelity and call cost, timeout/failure; `candidate_selected`, `fidelity_switch`, `failed_evaluation`, `budget_exhausted` |
| #139 uncertainty/risk | `distribution_summary` | `generic_metric_history`, `pareto_front` | scenario outcomes, violation distribution, risk measure, held-out status; `scenario_batch`, `constraint_threshold`, `risk_update`, `out_of_sample_check` |
| #140 nested/equilibrium | `nested_solve_timeline` | `generic_metric_history`, `continuous_trajectory` | outer/inner progress, inner tolerance, complementarity residual, active mode; `inner_solve`, `derivative_route`, `mode_switch`, `smoothing_update`, `inner_failure` |

The first implementation pilot should be one non-2D family attached to the existing
#119/#120 Theater/Compare seams, preferably #133 `field_evolution` if its current
topology artifact can satisfy this boundary. The pilot must prove the shared parser,
event-marker projection, static fallback, and Compare synchronization before adding
the other reserved families.

## Accessibility, determinism, and limits

- Every scenario exposes a static summary, text alternative, artifact-kind label,
  execution/result status, and limitations beside the visual player.
- Event markers are available as labelled text/table entries; color, motion, mesh
  texture, or spatial position is never the only encoding of a decision or failure.
- New payloads inherit the existing deterministic canonical JSON rules and the
  `AlgorithmTrace` ceiling of 1,000 snapshots and 2 MiB raw JSON unless a dedicated
  contract explicitly documents a stricter limit. Oversize data is downsampled or
  reduced to a static/result artifact; it is never silently truncated.
- A field/geometry projection records mesh/domain, coordinates, normalization, and
  limitations. A trajectory does not imply continuous-time feasibility between
  nodes. A distribution does not imply a probabilistic guarantee without authored
  assumptions and evidence.

## Implementation and remaining #141 work

1. Add shared Python/TypeScript payload types and exact fixtures for one pilot; keep
   `VisualizationScenario`, `AlgorithmTrace`, and `ComparisonSet` versions unchanged.
2. Add a renderer registry entry and deterministic generator for the pilot, including
   event-marker projection, static fallback, text alternative, size checks, and E2E/
   accessibility coverage.
3. Connect the pilot through canonical scenario relations and Compare synchronization;
   do not add entity-specific page-index routing.
4. Add Failure Theater scenarios for the failure markers in #133–#140, then add the
   remaining reserved families only when a concrete Case, source trail, and payload
   contract exist.

This ADR completes the #141 design slice only. The pilot, canonical scenario/data
connections, Failure Theater content, renderer implementations, browser coverage, and
the #133–#140 journey completion remain open follow-up work. PR #210's Compare Lab IA
slice is complete and is not reopened here.

## Rejected alternatives

- One renderer per method or issue: duplicates geometry and makes coverage depend on
  component count.
- A universal `payload` object with method-specific keys: makes exact parsing and
  accessibility impossible.
- Putting field arrays, event logs, or media in SQLite: turns canonical metadata into
  an event/blob store.
- Aligning all comparisons by optimizer iteration: hides simulator, fidelity, and
  inner-solve cost differences.
