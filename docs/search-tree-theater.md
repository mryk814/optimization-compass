# Search-tree Theater

Issue #25 adds the first renderer-family implementation described by
[`visualization-scenarios.md`](visualization-scenarios.md). It is an executable,
deterministic educational Branch-and-Bound run for a four-variable 0-1 knapsack.

## Published artifacts

- `data/search-trees/index.json`: strict `SearchTreeIndex 1.0.0` with mechanism and
  failure-contrast artifact entries. It references scenario IDs but does not own
  scenario titles, lessons, purpose, experiment policy, or provenance.
- `data/search-trees/<artifact-id>.json`: `SearchTreeArtifact 1.0.0`. The artifact
  contains an unchanged `AlgorithmTrace 1.0.0`; each frame payload is a full
  `SearchTreeFramePayload 1.0.0` snapshot.
- `data/search-trees/<artifact-id>.svg`: deterministic static fallback generated from
  the final validated snapshot.
- `data/traces/<trace-id>.json`: the same `AlgorithmTrace`, also published in the
  shared trace index so Map, Gallery, content, methods, and sources can use the
  canonical entity-relation graph.

The site manifest owns the search-tree index path, byte count, and SHA-256. Python and
TypeScript parsers reject unknown core fields, unknown renderer versions, inconsistent
gap values, broken node references, and trace/artifact identity mismatches.
`data/visualization-scenarios.json` is the single scenario authority. The page resolves
the artifact's `scenario_id` against that shared `VisualizationScenario 1.0.0` envelope
before rendering.

## Deterministic experiment

The fixed instance is:

```text
maximize 9A + 6B + 4D + 5C
subject to 4A + 3B + 2D + 3C <= 7
A, B, C, D in {0, 1}
```

Both scenarios use seed `0`, `depth_first_include_first`, a fractional-knapsack upper
bound, and the same initial heuristic incumbent. The mechanism scenario completes the
tree. The failure-contrast scenario stops after four explored nodes. Repeating the same
problem, seed, strategy, and node budget produces byte-equivalent trace content.

The renderer shows partial assignments, feasibility, incumbent, global upper bound,
absolute/relative gap, and the reason for every prune. `capacity_exceeded` and
`bound_not_better` are distinct contract values with Japanese and English explanations.

## Terminal semantics

- `optimality_proven`: no open node can improve the incumbent; best feasible and
  global bound agree and gap is zero.
- `budget_exhausted`: a feasible incumbent remains a candidate, but open nodes and a
  positive gap remain. The UI must not call it optimal.

Naive enumeration would inspect all 16 assignments. This example skips whole subtrees
using infeasibility and bounds. It does not claim to reproduce production solver
performance. MIP Branch-and-Cut may add continuous relaxations, cuts, and presolve;
CP-SAT combines SAT/CP propagation and learning. A shared tree vocabulary does not make
their internal mechanisms equivalent.

## Keyboard and fallback behavior

The common playback controls remain keyboard-operable. Within the tree, Up/Down moves
through visible nodes, Right moves to the first child, Left moves to the parent, and
Home/End moves to the first/last node. A textual tree summary exposes every node and
prune explanation without relying on geometry. The SVG fallback remains linked beside
the executable artifact.

## Integration seams

- **#22 scenario envelope:** mechanism and failure-contrast metadata are emitted only
  through the shared generated `VisualizationScenario`. The search-tree artifact keeps
  only its scenario ID, renderer payload, unchanged `AlgorithmTrace`, and static fallback.
- **#24 coverage:** count the mechanism and failure-contrast tuples only after the
  exported scenario, renderer, sources, route, and artifacts all validate.
- **#18 E2E framework:** desktop search-tree journeys live in `e2e/search-tree.spec.ts`;
  the shared `responsive.spec.ts` owns the 375 px journey under the common projects.
