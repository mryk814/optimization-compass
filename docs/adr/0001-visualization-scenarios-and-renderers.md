# ADR 0001: Visualization scenarios and renderer families

- Status: Accepted
- Date: 2026-07-15
- Decision owners: Optimization Compass maintainers
- Related: #22, #24, #25, #26, #31

## Context

The Atlas already has deterministic `AlgorithmTrace` playback, a Nelder–Mead theater,
and a first-order comparison. The current metadata joins methods, visualization
profiles, objectives, scenarios, comparisons, and learning edges, but it does not yet
name the educational purpose, artifact kind, comparison eligibility, or renderer
family as one reusable scenario contract.

Adding a bespoke page and payload for each new method would make search-tree and
Bayesian-optimization work duplicate experiment identity, provenance, playback, and
comparison rules. Conversely, forcing every renderer payload and every article body
into SQLite would make the knowledge database an unsuitable binary/event store.

## Decision

We will treat a visualization as six separate identities:

1. A **problem definition** describes the mathematical family and available oracles.
2. A **problem instance** fixes the concrete data, domain, dimension, and known facts.
3. A **visualization scenario** states the lesson, experiment policy, and artifact.
4. A **method run** records one method/implementation/preset execution in a scenario.
5. A **trace or schematic artifact** contains the renderable observations.
6. A **renderer family** interprets a versioned family payload, never a method ID.

The versioned `VisualizationScenario` contract in
[`../visualization-scenarios.md`](../visualization-scenarios.md) is the shared envelope.
It adds metadata around the existing `AlgorithmTrace`; it does not replace or widen the
trace frame contract. Existing trace IDs and deep links remain valid.

### Authority boundaries

| Authority | Owns | Must not own |
|---|---|---|
| Canonical SQLite | Stable entity IDs, method/profile support, problem and scenario catalog metadata, source relations, review dates, coverage status | Article bodies, trace frames, large instance arrays, renderer payloads |
| Markdown frontmatter + body | Educational narrative, prerequisites, related canonical IDs, source IDs | Method/source records, experiment results, renderer state |
| Python generator and registry | Executable problem instances, method adapters, deterministic run generation, artifact validation | UI routing or prose |
| Versioned generated site data | Resolved scenario envelopes, comparison envelopes, artifact index, hashes | Hand-edited authority |
| Trace JSON | Full deterministic execution snapshots under `AlgorithmTrace 1.0.0` | Scenario prose or renderer dispatch rules |
| Renderer registry in TypeScript | `renderer_family` to component mapping and exact family-payload parsing | Method-specific routing or experiment generation |
| Derived media | GIF, video, PNG, and thumbnails generated from a scenario/artifact | Source of truth |

### Extension rule

A new method may reuse an existing renderer when it emits the renderer family's
payload contract. A new renderer is justified only when the observable geometry is
different, not merely because the method ID is new. Renderers dispatch on
`renderer_family` and `renderer_contract_version`, never on `method_id`.

### Executable and schematic distinction

Every artifact carries a visible `artifact_kind` label. `executable_trace` means the
display is generated from a recorded run. `schematic_animation` and `static_diagram`
mean the geometry is explanatory and must not be presented as measured execution.
`result_visualization` may show imported results but must name the producing run or
external source. The UI keeps the label and limitations visible beside playback.

### High-dimensional policy

We do not silently project an n-dimensional path onto its first two coordinates.
Scenarios declare one or more observables: objective/evaluation history, constraint
violation, distance to a known reference, population summary, uncertainty/calibration,
selected named coordinates, or a documented projection. A projection records its
method, fitted-on data, retained variance when meaningful, and limitations. If no
faithful spatial view exists, `generic_metric_history` is the primary renderer.

## Consequences

### Positive

- #25 and #26 share scenario, run, provenance, comparison, and artifact rules.
- #24 can measure coverage by educational purpose and artifact availability rather
  than counting pages or methods.
- Existing theaters can migrate without breaking `AlgorithmTrace 1.0.0`.
- Failure and sensitivity examples become first-class scenarios rather than special UI
  branches.

### Costs

- Site export must eventually resolve catalog metadata and registry metadata into one
  generated contract.
- Each renderer family needs an exact payload parser and contract fixtures.
- Comparison eligibility must be authored explicitly; shared problem IDs alone are
  insufficient.

## Rejected alternatives

- **One page/component per method:** duplicates common playback and makes coverage
  depend on UI file count.
- **Put all payloads in SQLite:** turns a queryable metadata authority into an event and
  media store.
- **Expand `AlgorithmTrace.payload` until it is universal:** weakens the strict common
  trace contract and makes renderer dispatch implicit.
- **Treat every shared problem as directly comparable:** hides differences in oracle,
  budget, initialization, stopping, and tuning policy.

## Migration

1. Keep existing trace, comparison, and deep-link contracts unchanged.
2. Map the current Nelder–Mead and gradient examples to the proposed envelope in
   documentation and add generated scenario data only when #22 touches those exports.
3. Add scenario/comparison fields to canonical metadata in one future migration; do
   not create parallel v2 tables.
4. Introduce a renderer registry with the first genuinely new family in #25. The
   existing pages may register their renderer families at the same time.
5. Build #24 coverage from exported scenario status, including `not_applicable`, before
   using it for prioritization.
6. Use the same contract for #26; do not create a Bayesian-optimization-only scenario
   envelope.

## Issue scope decisions

| Issue | In scope after this decision | Explicitly out of scope |
|---|---|---|
| #22 | Better event explanations, operation highlights, fair gradient comparison, and mapping existing examples to the envelope | A universal renderer framework or trace-contract rewrite |
| #24 | Coverage by purpose × entity × artifact availability with `available / partial / missing / not_applicable` | Treating raw page count as coverage |
| #25 | Search-tree family payload plus scenarios for mechanism and failure contrast | A method-ID-specific page contract |
| #26 | Surrogate/uncertainty family payload plus sensitivity/failure scenarios | A Bayesian-optimization-only experiment model |

