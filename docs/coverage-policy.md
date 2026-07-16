# Atlas coverage policy

Coverage is a learning-contract audit, not a page-count score. It follows
[ADR-0001](adr/0001-visualization-scenarios-and-renderers.md): the canonical database owns the
expectation and the generated artifacts provide observed evidence.

## Two separate layers

1. The **artifact inventory** lists every method, problem archetype, and feature family. Its
   eight dimensions are map, recommendation, content, visualization, comparison, gallery,
   implementation, and source. Inventory states are `connected`, `absent`, or `broken`.
2. A **coverage expectation** is an explicit tuple of subject, educational purpose, artifact
   kind, and renderer family. A missing inventory connection is not automatically a missing
   expectation.

The observed expectation status is derived on every export:

- `available`: an expected scenario and its explicit artifact, renderer, route, and sources pass.
- `partial`: a candidate exists but its contract or a required reference is incomplete.
- `missing`: an expectation exists and no candidate scenario has been built.
- `not_applicable`: policy explicitly marks the tuple out of scope and records a rationale.

Renderer families are never inferred from a method or visualization profile. New scenario
contracts become visible automatically when their explicit subject, purpose, artifact kind, and
renderer family match an expectation. Method-family expectations include child methods through
the canonical `method_family_id` relationship.

## Prioritization

Priority uses four scored factors (0–3): classification representation, misconception risk,
visualization effect, and practical demand. The total is ordered descending; ties use `slice_id`.
Popularity is deliberately not a factor, and equal content depth is not a goal.

The initial five slices are discrete/search trees, expensive black-box/surrogate optimization,
constrained continuous optimization, multi-objective optimization, and optimal control/manifold
problems. Their factor-specific reasons and proposed scope are canonical database rows.

## Generated artifacts and release delta

- `coverage.json` is the exact versioned UI contract.
- `coverage.md` is a human-readable snapshot from the same report object.
- `#/coverage` is the public/maintainer view.

The first snapshot states `baseline: not_provided`; it never fabricates a comparison with v0.2.
Release notes must pass two explicit snapshots:

```powershell
optimization-compass coverage-diff --before old-coverage.json --after new-coverage.json --format markdown
```

The diff reports status transitions, added/removed expectations, subject inventory deltas, and
the available-count delta.

## Language scope

Current Coverage audits the Japanese primary-language learning contract. A subject needs complete
Japanese explanatory copy where its learning surface requires prose. `title_en`, English aliases, and
abbreviations are terminology and retrieval metadata; they do not make a Japanese learning asset
bilingual and do not satisfy a missing explanation.

Optional translated fragments neither raise nor lower the current status. `coverage.json` does not add
locale fields for this policy. Per-language completeness requires a separately versioned contract when a
future full-i18n initiative defines an additional publication surface, review responsibility, and
missing-translation behavior. See [ADR 0013](adr/0013-japanese-first-language-strategy.md).
