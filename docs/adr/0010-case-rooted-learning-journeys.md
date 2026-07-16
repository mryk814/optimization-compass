# ADR 0010: Learning journeys are derived, case-rooted bundles

- Status: accepted
- Date: 2026-07-16
- Issues: #116, #123

## Context

Gallery cases, `VisualizationScenario`, comparison sets, content, implementations, and sources
already own their respective facts. Re-authoring those facts in a journey seed would create a second
authority and allow the Case, Theater, and Compare surfaces to drift apart.

The product nevertheless needs one stable unit that answers: for this case, what is being formulated,
which scenario should be watched, which comparison is fair, which methods and implementations are
relevant, and what evidence supports the path?

## Decision

`GalleryCase` version `2.0.0` is the root authority. Candidate methods are authored as reason-bearing
rows and limitations remain distinct from operational notes. The exporter derives
`learning-journeys.json` version `1.1.0`
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

The exporter evaluates thirteen explicit dimensions: formulation, canonical problem instance,
primary and alternate scenarios, canonical comparison, method roles, implementation, source review,
terminology prerequisite, static/text alternative, cross-surface links, route reachability, and
reference validation. Each dimension publishes its state, target IDs, and stable reason codes.

- `complete`: every dimension is connected and valid.
- `partial`: a published case has one or more missing or broken dimensions.
- `draft`: the source Gallery case is draft. Its missing dimensions are still reported separately.

The index summary publishes the target of five complete journeys and derives the current milestone
state from the rows. Assets not reached by a journey use an explicit orphan policy. Identity such as
`derived` or `generated_only` does not prove that standalone publication was intentional, so the
exporter reports unlinked scenarios, comparisons, run artifacts, and published content as `warning`
until `data/seeds/learning_journey_asset_policy.json` explicitly declares another policy. An `error`
policy is rejected during export.

Comparison completeness uses the validated fairness contract, including canonical identity,
case/journey ownership, fixed and changed factors, aligned budget, metrics, fairness note, caveat,
limitations, and members. Method-role completeness also requires authored candidate, conditional,
and exclusion reasons. Source review combines the direct sources of the Case, every linked Scenario,
Comparison, and published method guide; it checks type-specific freshness, currentness, claim text,
and source quality as well as the Case review date. Route reachability is checked against actual case, scenario, run artifact, comparison,
method, and source inventories rather than URL prefixes.

### Validation and downstream exports

Export fails on duplicate journey or relation IDs, dangling case/problem/scenario/comparison/method/
implementation/content/source references, cross-version rows, missing prerequisite journeys, or a
circular prerequisite graph. Output ordering is stable.

Journey and scenario nodes are added to `EntityLinkIndex`. Search and retrieval documents are derived
from that graph, and Coverage exposes a `journey` inventory dimension. The site manifest advertises
the generated journey asset.

## Consequences

The initial `constrained-design` pilot resolves its formulation, `SCENARIO_CONSTRAINED_DISK`, fair
comparison, methods, implementations, content, and sources. It remains `partial` until an alternate
failure-contrast or sensitivity scenario is connected; the contract makes that missing product work
visible instead of weakening the completion definition.

Later Case, Theater, and Compare UI issues can share one generated route-and-relation contract. Adding
a new complete journey normally means improving existing Gallery/Scenario/Comparison authorities, not
editing a fourth copy of the content.
