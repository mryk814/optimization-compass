# Optimization Compass agent instructions

This file is the first entry point for humans and automated agents changing this repository.
For detailed recipes, read [`docs/adding-knowledge.md`](docs/adding-knowledge.md). Automated agents should also read [`.agents/skills/optimization-compass-maintenance/SKILL.md`](.agents/skills/optimization-compass-maintenance/SKILL.md).

Task-shaped authoring skills for growing the dataset live in [`.claude/skills/`](.claude/skills/) (Claude Code loads them automatically): `grow-data` (triage/routing), `add-content-article`, `add-gallery-case`, `add-comparison`, and `add-problem-instance`. They are thin wrappers: rules stay in this file, `docs/adding-knowledge.md`, and the maintenance skill; validation runs through the cross-platform `uv run optimization-compass validate <task>` CLI.

## Product boundary

Optimization Compass is a versioned, data-driven Optimization Atlas. Keep these responsibilities separate:

| Responsibility | Authority / editable input |
|---|---|
| Stable IDs, structured relations, support scope, evidence, canonical knowledge | SQL migrations and validated seed/catalog inputs used to build the released SQLite database |
| Human-readable method and concept explanations | `content/**/*.md` frontmatter and Markdown body |
| Gallery cases | `data/seeds/site_gallery.json` |
| Comparison definitions | `data/seeds/site_comparisons.json` |
| Problem definitions and instances | `src/optimization_compass/resources/problem-suite.json` |
| Executable problem behavior | `src/optimization_compass/problem_registry.py` |
| View and visualization metadata | validated seeds and Python contracts under `data/seeds/` and `src/optimization_compass/` |
| Generated site indexes and distributions | generated from the inputs above; never treated as editable authority |

The released SQLite database is the runtime authority, but contributors do **not** edit it directly. They edit auditable inputs and regenerate a deterministic staged release.

## Never edit generated artifacts directly

Do not hand-edit these paths to fix a visible result:

- `src/optimization_compass/resources/knowledge.sqlite`
- `src/optimization_compass/resources/DATASET_VERSION`
- `site/public/data/**`
- `data/optimization_method_selection_database_v*`
- generated Trace, media, search, retrieval, Coverage, manifest, or release artifacts

Find and change the canonical input instead. Generated artifacts may appear in a final release commit only after the repository's generation workflow has produced them.

## Route the change before editing

| Requested change | Start here | Risk |
|---|---|---:|
| Correct prose, examples, limitations, or citations on an existing page | `content/**/*.md` | low |
| Add a method or concept article for an existing canonical entity | `content/**/*.md` | low |
| Add a Gallery case using existing problem/method/implementation/source IDs | `data/seeds/site_gallery.json` | low–medium |
| Add or revise a comparison using existing traces and entities | `data/seeds/site_comparisons.json` | medium |
| Add a problem instance with executable evaluation | `problem-suite.json` and `problem_registry.py` | medium |
| Add a new method, implementation, source, evidence relation, or controlled vocabulary | dataset migration/build inputs plus content | high |
| Add a scenario, generator, artifact contract, or renderer family | Python contracts/generators plus site implementation | high |
| Change recommendation behavior, schema, release identity, or publishing | dedicated design and release flow | critical |

For high or critical changes, inspect similar merged work and document the authority boundary before coding.

## Core invariants

- Stable IDs are never silently repurposed.
- `method` and `implementation` remain distinct.
- `unknown`, `not_applicable`, and `unsupported` remain distinct explicit states.
- Every factual knowledge addition has a source/evidence trail.
- Official documentation, official repositories, original papers, standards, and specifications are preferred.
- Qiita and Zenn are not accepted as sources.
- A library default is not presented as a universal recommendation or ranking.
- Comparisons state fixed factors, changed factors, budget, synchronization, metrics, fairness, caveats, and ranking eligibility.
- Continuous-model guarantees are not inferred from a discretized solve without qualification.
- Published explanatory prose uses Japanese as the sentence language; English remains for canonical terms, proper names, APIs, source titles, code, formulas, and identifiers.
- PDE-constrained data keeps decision variables, derived state, residual constraints, evaluation failures, and solver cost distinguishable. Detailed modeling guidance belongs in the PDE article and ADR, not in this entry point.
- UI code does not gain per-entity routing crosswalks when canonical relations can generate the route.
- Generated JSON is regenerated from the latest branch state; it is not manually merged.

## Lightweight workflow

1. Classify the change using the routing table above.
2. Read the matching recipe only when adding a new entity or changing a contract.
3. Edit the canonical input, preserve IDs and sources, and run the smallest focused validation.
4. For prose or small seed corrections, inspect the rendered Pages result in the PR or after deploy.
5. Use the complete release validation only for schema, recommendation, generator, executable-problem, or release changes.

## Validation policy

Use the smallest task exposed by `optimization-compass validate`. The local content tasks check parsing, relations, licensing, and the focused authoring contract. They do not run the full Python suite, site build, or browser suite.

CI and main-branch Pages still run the broader artifact and release gates. Do not weaken generated-data identity, canonical data integrity, stable IDs, or deployment identity merely to shorten local feedback.

For an existing canonical method article, `ready content <content-id>` exports public data and runs the focused content contract. It no longer regenerates review reports as a side effect; report scripts remain available when a report is explicitly needed.

A staged build is read-only with respect to published repository artifacts. Publishing is a separate atomic operation and must not be improvised in an ordinary content edit.

## Stop and escalate conditions

Stop and document the uncertainty instead of guessing when any of these is true:

- a new stable-ID namespace or schema field appears necessary;
- an apparently new entity may duplicate an existing method, family, implementation, problem, or source;
- a primary or authoritative source cannot be found;
- recommendation output changes without an explicit regression case;
- a new renderer or artifact contract version is required;
- a release version bump or migration ordering decision is unclear;
- the requested change would require editing generated artifacts only;
- validation creates widespread unrelated diffs.

## Pull request shape

Prefer one reviewable concern per PR. Separate when practical:

- canonical structured data;
- human-readable content;
- executable generators/engine behavior;
- frontend renderer or UX;
- generated release artifacts.

Every commit must include a DCO sign-off. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/adding-knowledge.md`](docs/adding-knowledge.md).

## Lessons from issue-scale maintenance

- When the release catalog contains historical entries, staging tests must use an unpublished target
  version; reusing an already-published version correctly fails identity validation.
- Site exports for a not-yet-published staged release embed a predecessor-only catalog snapshot. The
  published site may include the new current entry only after the external bundle and catalog update.
- After changing a test or generated-data policy, run both `ruff check .` and `ruff format --check .`
  before relying on the longer Pages smoke job; a focused test pass alone is not sufficient.
- A change to `resources/problem-suite.json` is a release-boundary change: update the release
  authority, build and publish the staged SQLite/site tree, then regenerate `CITATION.cff` and the
  dataset card. The normal site export intentionally rejects a seed/runtime SQLite mismatch.
- For browser diagnosis, prefer `CI=1` with a unique `PLAYWRIGHT_PORT` so Playwright uses one worker;
  a many-worker local run can turn existing route failures into resource/timeout noise. Record new
  focused E2E results separately from the repository's pre-existing full-suite failures.
