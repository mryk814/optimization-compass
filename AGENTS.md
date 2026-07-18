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
- UI code does not gain per-entity routing crosswalks when canonical relations can generate the route.
- Generated JSON is regenerated from the latest branch state; it is not manually merged.

## Minimum workflow

1. Classify the change using the routing table above.
2. Read the matching recipe in `docs/adding-knowledge.md`.
3. Identify the existing canonical IDs and sources before creating new IDs.
4. Change the smallest editable authority that owns the information.
5. Add or update focused tests for new behavior and validation rules.
6. Run the smallest applicable validation tier below.
7. Inspect generated diffs. Unexpected unrelated generated changes are a stop signal.
8. In the PR, state changed IDs, sources, behavioral impact, generated artifacts, and validation results.

## Release sequencing lessons

These are recurring operational rules, not topology-specific exceptions:

- Treat a published dataset version as immutable. Decide and bump the version before the first `--publish`; if the generated artifact changes after publication, use a new patch version rather than trying to republish the old one.
- Finalize generator and serialization code before preparing the release bundle. Regenerate `site/public/data` with the same CLI used by CI, and make numeric payload serialization platform-stable when `math`/libm output is hashed.
- Record the exact source commit used to build the staged release. Do not make output-affecting generator, migration, fixture, or content changes after preparing the bundle without rebuilding the release metadata and bundle.
- When the dataset version changes, search the repository for the previous version and update parity fixtures and other committed expectations before pushing. PR CI is the fastest place to catch stale version literals.
- A green PR is not the publication finish line: after merge, verify the main-branch Pages workflow, browser/accessibility job, deploy smoke, public `deployment.json`, public `data/release.json`, release asset digest, and issue state.

## Validation tiers

Each tier is runnable as one cross-platform command: `uv run optimization-compass validate tier-a` (likewise `tier-b`, `tier-c`; tier C = tier B plus site typecheck and browser E2E). `--list` prints a tier's checks without running them; `--format json` emits machine-readable results with stable rule codes. The composition is owned by `src/optimization_compass/validation_tasks.py` and tested against the lists below. POSIX users may call the same commands through `make tier-a` etc.

### Tier A — prose or existing-content correction

```bash
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
npm --prefix site test -- --run
```

### Tier B — Gallery, comparison, relations, or canonical data using existing contracts

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run optimization-compass verify-data
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
uv run pytest
uv run python scripts/rebuild_dataset.py --stage
npm --prefix site run parity
npm --prefix site test -- --run
npm --prefix site run build
```

### Tier C — executable problem, scenario, generator, renderer, schema, or release change

Run Tier B plus the applicable browser and focused contract tests:

```bash
npm --prefix site run test:e2e
```

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
