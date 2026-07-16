# ADR 0010: Learning journeys are derived, case-rooted bundles

- Status: accepted
- Date: 2026-07-16
- Issue: #116

## Context

Gallery cases, `VisualizationScenario`, comparison sets, content, implementations, and sources
already own their respective facts. Re-authoring those facts in a journey seed would create a second
authority and allow the Case, Theater, and Compare surfaces to drift apart.

The product nevertheless needs one stable unit that answers: for this case, what is being formulated,
which scenario should be watched, which comparison is fair, which methods and implementations are
relevant, and what evidence supports the path?

## Decision

`GalleryCase` is the root authority. The exporter derives `learning-journeys.json` version `1.0.0`
from the existing Gallery, VisualizationScenario, Comparison, content, and repository contracts.
There is no authored journey seed and no parallel v2 contract.

### Identity and routes

- `journey_id` is exactly `case_id`. A separate alias namespace is not introduced.
- The journey's canonical product destination is generated as `/gallery/{case_id}`.
- Scenario and comparison destinations are generated from renderer family and stable IDs. UI code
  consumes these destinations and does not maintain case- or scenario-specific route maps.
- Every journey row repeats `dataset_version`; it must equal the index and all source artifacts.

### Derived relations

- A Gallery `visualization_id` matches a scenario by `scenario_id` or by a run `artifact_id`.
- One matching scenario is selected as primary by purpose: mechanism, application result, schematic,
  failure contrast, sensitivity, then comparison. Canonical identity wins ties.
- Other scenarios retain explicit `failure_contrast`, `sensitivity`, or `alternate` roles.
- `comparison_ids` remain authored on Gallery cases because selecting a fair comparison is a product
  judgment. The journey only resolves and routes those IDs.
- Candidate, conditional, and excluded methods; implementations; formulation text; and sources come
  from the case. Method content is derived by matching the case's candidate and conditional methods.
- Multiple problem instances, scenarios, comparisons, implementations, and content pages are lists;
  the contract does not collapse them to one hidden choice.

### Completeness

- `complete`: a published case has one primary scenario, at least one comparison, implementation,
  and source.
- `partial`: a published case is missing one or more of those connections. Stable reason codes explain
  each missing connection.
- `draft`: the source Gallery case is draft. The missing connections are still reported.

`orphan_scenario_ids` and `orphan_comparison_ids` report assets not reached by any case-rooted journey.
They are backlog signals, not export failures.

### Validation and downstream exports

Export fails on duplicate journey or relation IDs, dangling case/problem/scenario/comparison/method/
implementation/content/source references, cross-version rows, missing prerequisite journeys, or a
circular prerequisite graph. Output ordering is stable.

Journey and scenario nodes are added to `EntityLinkIndex`. Search and retrieval documents are derived
from that graph, and Coverage exposes a `journey` inventory dimension. The site manifest advertises
the generated journey asset.

## Consequences

The initial `constrained-design` pilot resolves its formulation, `SCENARIO_CONSTRAINED_DISK`, methods,
implementations, content, and sources. It is intentionally `partial` until a fair comparison is authored;
the contract makes that missing product work visible instead of inventing a misleading comparison.

Later Case, Theater, and Compare UI issues can share one generated route-and-relation contract. Adding
a new complete journey normally means improving existing Gallery/Scenario/Comparison authorities, not
editing a fourth copy of the content.
