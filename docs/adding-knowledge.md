# Adding and correcting Optimization Compass knowledge

This guide explains where information is owned, which files to edit, and how to validate common changes.
It is designed both for maintainers and for contributors making their first small correction or addition.

For the concise repository rules, read [`../AGENTS.md`](../AGENTS.md). For an AI-agent procedure, read [`.agents/skills/optimization-compass-maintenance/SKILL.md`](../.agents/skills/optimization-compass-maintenance/SKILL.md).

## 1. The mental model

Optimization Compass has several kinds of authority because the same concept may have structured facts, human explanation, executable behavior, and generated visual output.

```text
Auditable editable inputs
  ├─ SQL migrations / validated data seeds
  ├─ Markdown content
  ├─ Python executable registries and generators
  └─ frontend renderer contracts
             │
             ▼
Deterministic staged build
             │
             ├─ released SQLite runtime authority
             ├─ JSON / JSONL / CSV / Excel distributions
             ├─ site/public/data indexes
             ├─ search / retrieval / Coverage artifacts
             └─ Trace and visualization payloads
```

The released SQLite database is the runtime authority. It is **not** an authoring interface. Change its build inputs and regenerate it.

## 2. Where each kind of information lives

| Information | Editable authority | Notes |
|---|---|---|
| Method, family, implementation, source, evidence, hierarchy, support scope | Dataset migration/build inputs | A knowledge addition may require a SQL migration until a declarative catalog exists. |
| Method or concept explanation | `content/**/*.md` | Frontmatter links prose to canonical entities and sources. |
| Gallery case | `data/seeds/site_gallery.json` | Uses existing canonical IDs and is validated against Diagnose questions and features. |
| Comparison | `data/seeds/site_comparisons.json` | Must state fairness, caveats, synchronization, and members. |
| Problem definition and instance metadata | `src/optimization_compass/resources/problem-suite.json` | Defines mathematical family, domain, parameters, reference, display, and sources. |
| Executable objective/gradient | `src/optimization_compass/problem_registry.py` | `registry_key` values must match the problem-suite instances exactly. |
| View presets and method visualization profiles | `data/seeds/atlas_metadata.json` and canonical database rows | Do not hard-code entity routing in the UI. |
| Formulation terminology | `data/seeds/formulation_primer_terms.json` | Shared by Case, Diagnose, and Map. |
| Atomic predicates | `data/seeds/atomic_predicates.json` and related migration tables | Changes may affect recommendation behavior. |
| Structured failure relations | Existing failure rows plus `src/optimization_compass/failure_modes.py` | Current authoring is partly code-backed; treat changes as canonical-data work. |
| Implementation claims and benchmark contexts | Canonical implementation data plus `src/optimization_compass/versioned_claims.py` | Defaults and release claims are versioned facts, not rankings. |
| Visualization scenario contracts | `src/optimization_compass/visualization_scenarios.py` and scenario generation code | Includes learning metadata, experiment policy, run identity, artifact, and sources. |
| Release download catalog | `data/releases/catalog.json` via the validated publish command | Compact immutable metadata; complete bundles are prepared outside Git. |
| Site indexes, release data, Coverage, search, retrieval, Trace JSON | Generated output | Never fix by hand. |

## 3. Files that must not be edited by hand

These files and directories are products of the build or release process:

```text
src/optimization_compass/resources/knowledge.sqlite
src/optimization_compass/resources/DATASET_VERSION
site/public/data/**
data/optimization_method_selection_database_v*
generated Trace, media, search, retrieval, Coverage, manifest, and release artifacts
```

Complete versioned release bundles are also generated outside the repository. After dataset 0.12.0,
do not add a new JSON/JSONL/CSV/Excel/site-data distribution tree under `data/`. The Git tree retains
only current compact release metadata plus the runtime and build inputs defined by
[`adr/0014-release-retention-and-external-bundles.md`](adr/0014-release-retention-and-external-bundles.md).

A generated file may be committed as part of a validated release. It must be produced from canonical inputs, not manually patched.

When a generated page is wrong, trace the value backward:

```text
visible page
  → generated site payload
  → exporter / relation index
  → Markdown, seed, migration, registry, or generator authority
```

## 4. Choose a safe change level

### Green: suitable for a first contribution

- fix prose, spelling, terminology, limitations, or practical notes;
- improve an existing example without changing canonical behavior;
- add or improve a method/concept article for an existing entity;
- add aliases or links using existing valid IDs;
- add a Gallery case that only references existing canonical entities.

### Yellow: agent-assisted or maintainer-reviewed

- add a comparison using existing traces and renderer families;
- add a problem instance under an existing problem contract;
- add a family guide or learning relation;
- extend a structured failure mode inside the current schema;
- add source/evidence records without changing recommendation semantics.

### Red: dedicated design and release work

- introduce a new method, implementation, source namespace, or controlled vocabulary;
- change recommendation rules or Diagnose questions;
- add a new problem/trace/artifact/renderer contract;
- change the SQLite schema or migration order;
- publish a dataset version;
- alter release identity or generated artifact structure.

A red change is not forbidden. It should not be discovered accidentally inside a small content PR.

## 5. General preparation

Before editing:

1. Search for an existing canonical entity or alias. Do not create a near-duplicate ID.
2. Identify the primary or authoritative source for each factual claim.
3. Decide whether recommendation output, a public route, Coverage, or release identity changes.
4. Find one recent merged PR with the same change type and inspect its complete file set.
5. Keep the PR focused. Avoid mixing schema, content, renderer, and unrelated UI cleanup.

### Source policy

Preferred sources, in order:

1. official documentation;
2. official repository or release notes;
3. original paper;
4. RFC, standard, or specification;
5. official issue/discussion from maintainers;
6. a trustworthy technical publication when no primary source exists.

Qiita and Zenn are not accepted as sources.

For third-party quotations, diagrams, screenshots, logos, or copied examples, also follow [`licensing.md`](licensing.md), `NOTICE`, and `THIRD_PARTY_SOURCE_AUDIT.md`.

## 6. Recipe: correct an existing article

Use this for prose, examples, limitations, terminology, or citation corrections where the canonical entity already exists.

### Usually edit

```text
content/methods/<content-id>.md
content/concepts/<content-id>.md
```

### Required checks

- Keep `content_id`, `method_id`, or canonical entity identity stable unless correcting a proven identity error.
- Keep the frontmatter `summary` exactly equal to the first body paragraph.
- Keep `source_ids`, `related_ids`, `visualization_ids`, and `comparison_ids` unique and valid.
- Update `last_reviewed` when the factual review has actually been performed.
- Do not turn an implementation default into a general method recommendation.

### Validate

```bash
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
npm --prefix site test -- --run
```

If a relation or generated index changes, also run a staged dataset build and site build.

## 7. Content Golden Path: add an article for an existing method

Ordinary content publication has one canonical lane. It does **not** publish a dataset version.

```text
author canonical draft
  → write and run the short content checks
  → promote frontmatter to published
  → ready regenerates public indexes and runs the owning gate
  → open and merge the PR
  → main deploys GitHub Pages
  → verify the reported public routes
```

Create a parseable draft directly in the editable authority. The command refuses unknown method
IDs and existing content IDs:

```bash
uv run optimization-compass author content method \
  --id example-method \
  --method-id M_EXAMPLE
```

While writing, keep `status: draft` and use the short iteration loop:

```bash
uv run optimization-compass validate content example-method
```

Fill every placeholder, source, relation, limitation, success/failure signal, and Python example;
update `last_reviewed`, then change the status to `published`. The handoff command owns generation
and readiness:

```bash
uv run optimization-compass ready content example-method
```

The target-specific iteration check parses only the named article and verifies its canonical method,
source, and content-relation IDs; it intentionally allows a draft and placeholders. `ready content`
replaces generated indexes from canonical inputs, validates the canonical method and
source IDs, rejects placeholders and future review dates, enforces the published method density
floor, regenerates `site/public/data`, refreshes the density report, proves the content/search/
retrieval/entity-link entries and routes, runs `content-ready`, and prints the exact files, PR gate,
and post-merge URLs. If it is green, do not additionally run dataset staging or dataset publish for
an ordinary existing-entity article.

Draft pages are not public inputs: site export, search, retrieval, and entity links include only
`status: published` content. A draft-only PR therefore remains a Tier A change without generated
artifact churn.

## 8. Recipe: add an article for an existing method or concept

Use this when the canonical entity exists in the database but has no published explanatory page.

### Add

```text
content/methods/<content-id>.md
# or
content/concepts/<content-id>.md
```

A method page frontmatter normally includes:

```yaml
---
content_id: example-method
kind: method
method_id: M_EXAMPLE
title_ja: 例示手法
title_en: Example Method
summary: 最初の本文段落と完全に一致する短い説明です。
source_ids: [S001]
prerequisites: []
related_ids: []
visualization_ids: []
comparison_ids: []
status: draft
last_reviewed: 2026-07-16
---
```

Replace every placeholder and verify the entity and source IDs before committing.

### Content expectations

- explain the method's intuition before advanced detail;
- state variable type, available information, constraints, evaluation cost, and guarantee scope;
- state success signals, failure/switch signals, and limitations;
- distinguish method theory from implementation-specific behavior;
- link to existing family guidance and application cases when possible.

Start as `draft` if relations or sources are incomplete. Publication should not be used to bypass Coverage or evidence requirements.

For an existing method, prefer the Golden Path above. Concept authoring and uncertain/high-risk
work may still start from a review pack until their canonical author command exists.

## 9. Task-oriented scaffolds: review before authoring

Phase 5 provides review-first scaffolds for each concrete authoring path. Every
command requires an author-supplied ID, prints a machine-readable plan without
writing by default, and can optionally write draft files outside canonical and
generated paths.

```bash
# Existing-entity method article (content authority).
uv run optimization-compass scaffold content method --id example-article

# Existing-entity Gallery case.
uv run optimization-compass scaffold gallery-case --id example-case

# Coordinated metadata + executable behavior for a problem instance.
uv run optimization-compass scaffold problem-instance --id example-instance

# Comparison using existing traces and renderer families.
uv run optimization-compass scaffold comparison --id example-comparison

# New canonical method (maintainer-reviewed, high risk).
uv run optimization-compass scaffold method --id M_EXAMPLE

# Visualization scenario using an existing artifact contract where possible.
uv run optimization-compass scaffold scenario --id SCENARIO_EXAMPLE
```

To write a review pack, use `--write`; choose a separate empty directory with
`--output` when the default `scaffolds/<task>/<id>/` location is not suitable:

```bash
uv run optimization-compass scaffold gallery-case --id example-case --write
uv run optimization-compass scaffold content method --id example-article --write --output path/to/article-draft
```

The shared scaffold contract remains the review-first lane when identity or authority is not yet
settled. It never allocates a stable ID, fabricates sources,
claims, relations, defaults, or benchmark results, overwrites a non-empty draft
directory, or writes an authority or generated output. Replace every `TODO`,
independently review all IDs and sources, then copy the reviewed material into the
authority named in the plan. The generated README lists required inputs, forbidden
outputs, the focused validation task, and the PR gate/checklist.

| Command | Editable authority | Focused validation | PR gate |
| --- | --- | --- | --- |
| `scaffold content method` | `content/methods/<content-id>.md` | `validate content` | `tier-a` |
| `scaffold gallery-case` | `data/seeds/site_gallery.json` | `validate gallery` | `tier-b` |
| `scaffold problem-instance` | `problem-suite.json` + `problem_registry.py` | `validate problem` | `tier-c` |
| `scaffold comparison` | `data/seeds/site_comparisons.json` | `validate comparison` | `tier-b` |
| `scaffold method` | registered canonical build inputs | `validate tier-c` | `tier-c` |
| `scaffold scenario` | scenario contract/generator inputs | `validate tier-c` | `tier-c` |

The focused command is an iteration subset only when the registry provides one;
the README and manifest always state the required PR gate. A scaffold is not a
substitute for evidence review, canonical identity checks, or the full release
workflow.

## 10. Recipe: add a Gallery case using existing entities

This is the recommended first structured-data contribution.

### Edit

```text
data/seeds/site_gallery.json
```

### Before adding

Confirm that the following IDs already exist:

- `problem_archetype_id`;
- every `feature_id` and value;
- every Diagnose `question_id` and answer;
- candidate, conditional, and excluded method IDs;
- implementation IDs;
- source IDs;
- visualization and comparison IDs, when used.

### Required semantics

- Candidate, conditional, and excluded method sets must not overlap.
- Every candidate, conditional, and excluded method needs a concrete reason.
- `map_node_id` must be backed by the case's question answers.
- Canonical `EC...` cases must match their database example-case/problem relation.
- The Python example must be nonblank and syntactically compilable.
- `limitations` must explicitly bound what the fixed educational case does not establish.
- Practical notes must state the checks needed when applying the case in practice; they do not replace
  `limitations`.
- Do not imply that the example's fixed educational run guarantees performance on the real problem.

### Suggested workflow

1. Copy the closest existing case.
2. Change the identity and prose first.
3. Re-evaluate every copied method, implementation, source, visualization, and comparison ID.
4. Add complete Diagnose answers when promoting a canonical `EC...` case.
5. Run validation before touching UI code. The Gallery is generated from data.

### Validate

```bash
uv run python scripts/verify_content.py
uv run optimization-compass verify-data
uv run pytest tests/test_site_export.py
uv run python scripts/rebuild_dataset.py --stage
npm --prefix site test -- --run
npm --prefix site run build
```

## 11. Recipe: add or revise a comparison

### Edit

```text
data/seeds/site_comparisons.json
```

Until the generalized comparison contract is complete, stay inside the existing validated fields and renderer families.

### A comparison must explain

- the comparison question;
- what is fixed;
- what changes;
- initial condition and seed policy;
- budget and stopping rule;
- synchronization axis;
- metrics and status interpretation;
- member parameters;
- fairness note;
- caveat and ranking eligibility;
- canonical versus derived identity.

A failure contrast is not a ranking. A comparison with incomplete benchmark context must not be marked ranking-eligible.

### Validate

```bash
uv run python scripts/verify_content.py
uv run pytest tests/test_site_export.py
uv run python scripts/rebuild_dataset.py --stage
npm --prefix site run parity
npm --prefix site test -- --run
npm --prefix site run build
```

## 12. Recipe: add a problem definition or instance

A problem instance has two coordinated parts.

### Metadata

```text
src/optimization_compass/resources/problem-suite.json
```

This owns:

- definition and instance IDs;
- mathematical family and variable domain;
- objective direction and available oracles;
- constraint class;
- dimension and parameters;
- initialization candidates and seed policy;
- known-reference status;
- display range, expression, units, and limitations;
- source IDs and review date.

### Executable behavior

```text
src/optimization_compass/problem_registry.py
```

The instance's `registry_key` must have exactly one corresponding registry entry. The problem-suite key set and Python registry key set must match exactly.

### Rules

- Keep display expressions descriptive; do not evaluate SQLite or display expressions as code.
- Return objective vectors only for explicitly multi-objective definitions.
- Validate dimensions and parameter types before evaluating.
- Make constraints and infeasible-result policy explicit.
- Separate hidden educational reference data from information available to the optimizer.
- State when a reference is exact, best-known, approximate, unknown, or not meaningful.

### Validate

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run python scripts/rebuild_dataset.py --stage
npm --prefix site test -- --run
npm --prefix site run build
```

## 13. Recipe: add a new method, implementation, or source

This is currently a maintainer flow because canonical knowledge additions are partly expressed as SQL migrations.

### Expected change areas

Depending on scope:

```text
data/migrations/<next-migration>.sql
src/optimization_compass/dataset_release.py
src/optimization_compass/resources/release-authority.json
content/methods/<content-id>.md
tests/**
docs/releases/**
docs/migrations/**
```

Generated release and site files may also change after a validated publish step.

### Required work

1. Prove the entity is not an alias, variant, implementation, or duplicate of an existing entity.
2. Add authoritative source records first.
3. Add the method/implementation row and relationships with stable IDs.
4. Add method-family hierarchy and implementation mapping where applicable.
5. Add direct evidence for material claims.
6. State first-choice, avoid, and switch conditions without a context-free ranking.
7. Add or update human-readable content.
8. Add focused tests for identity, relations, counts only where counts are genuine contract boundaries, and affected recommendation behavior.
9. Register the migration in the deterministic build input sequence.
10. Update release identity and release documentation only as part of an intentional dataset release.

### Important warning

Creating `data/migrations/<file>.sql` is not sufficient by itself. Add the migration to
`data/build-manifest.json` with its ordered three-digit ID and SHA-256, then run
`uv run optimization-compass validate manifest`. The staged builder validates the manifest before
applying any migration and rejects missing, unregistered, reordered, or changed files.

### Validate

Run `uv run optimization-compass validate manifest`, followed by the full Python, data, licensing,
parity, frontend, build, and browser suites. A new canonical method is not a content-only change.

## 14. Recipe: add a visualization scenario

A complete visualization is not just an animation. It combines:

```text
canonical problem definition and instance
  + method/profile identity
  + experiment policy and budget
  + executable or static artifact generator
  + observable contract
  + learning objective and failure/success signals
  + renderer family
  + static summary and text alternative
  + source trail and limitations
```

### Likely change areas

```text
src/optimization_compass/resources/problem-suite.json
src/optimization_compass/problem_registry.py
src/optimization_compass/visualization_scenarios.py
src/optimization_compass/traces/** or another generator module
src/optimization_compass/site_export.py
site/src/** renderer and contract code
data/seeds/atlas_metadata.json
data/seeds/site_gallery.json
data/seeds/site_comparisons.json
tests/**
site/e2e/**
```

### Rules

- Prefer an existing renderer family and artifact contract.
- Add a new renderer contract only through explicit design work.
- Use stable canonical scenario identity; mark derived or generated-only scenarios honestly.
- Make budget, seed, tuning, stopping, and available-oracle policy explicit.
- Provide a static summary and text alternative equivalent to the visual lesson.
- Expose failure modes, not only a successful final frame.
- Do not use a two-dimensional educational trace to imply general high-dimensional performance.

### Validate

Run full Python tests, deterministic stage, frontend parity, frontend tests/build, and browser E2E.

## 15. Two publication lanes

### Publish an article to the Atlas

An ordinary article for an existing canonical entity uses `ready content`, a pull request, and a
merge to `main`. The main workflow builds the exact validated Pages artifact, runs browser and
accessibility gates, deploys it, and performs remote smoke checks. The contributor verifies the
routes printed by `ready content`. There is no dataset version bump and no local `--publish` step.

### Publish a dataset version

Dataset publication changes runtime/release authority and is a separate maintainer operation. It
requires an explicit version decision, deterministic staged bundle, GitHub Release/catalog/hash/
citation work, and release-specific verification. Never use this lane merely to publish prose.

## 16. Deterministic dataset staging and publishing

### Staging

```bash
uv run python scripts/rebuild_dataset.py --stage
```

Stage mode:

- starts from the pinned base database;
- validates `data/build-manifest.json` and its declared specialized inputs, then applies its ordered migrations;
- exports all distributions and site data;
- validates cross-format and release identity;
- builds twice and compares deterministic tree hashes;
- does not modify published repository artifacts.

Use `--output <new-directory>` when the staged files need inspection. The output directory must not already exist and must not overlap protected inputs.

### Publishing

Publishing is a separate atomic operation using a previously validated staged directory. It replaces the data release, runtime database, version file, and site data as one unit, restoring backups if replacement fails.

Do not publish as an incidental step in a prose, Gallery, or ordinary content PR. Follow the current release issue/workflow and release documentation.

## 17. Validation matrix

| Change | Minimum focused checks | Full stage | Site parity/build | Browser E2E |
|---|---|---:|---:|---:|
| Prose correction | content + licensing | when generated relations change | tests | no |
| Existing-entity draft | `validate content` / Tier A | no | tests | no |
| Existing-entity published article | `ready content <id>` / `content-ready` | no | generated indexes + tests/build | critical journeys in PR |
| Gallery case | content + data + site export tests | yes | tests/build | journey changes |
| Comparison | content + site export tests | yes | parity/tests/build | route/interaction changes |
| Problem instance | ruff + mypy + pytest | yes | tests/build | scenario changes |
| Method/implementation/source | full Python/data/licensing | yes | parity/tests/build | public journey changes |
| Scenario/generator/renderer | full Python/data/licensing | yes | parity/tests/build | yes |
| Release/schema/recommendation | complete repository validation | yes | yes | yes |

The validation tiers from `AGENTS.md` are runnable as single cross-platform commands: `uv run optimization-compass validate tier-a` (likewise `tier-b`, `tier-c`). Focused iteration subsets exist per task (`validate content`, `validate gallery`, `validate comparison`, `validate problem`, `validate manifest`). Published content uses the complete `ready content <id>` handoff and its `content-ready` gate. `--list` shows a task's checks, `--format json` emits stable rule codes.

Common commands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run optimization-compass verify-data
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
uv run python scripts/rebuild_dataset.py --stage
npm --prefix site run typecheck
npm --prefix site run parity
npm --prefix site test -- --run
npm --prefix site run build
npm --prefix site run test:e2e
```

## 18. Pull request expectations

Use [`knowledge-change-checklist.md`](knowledge-change-checklist.md) when preparing a PR.

At minimum, state:

- change category;
- changed canonical IDs;
- source and evidence basis;
- previous versus new behavior;
- recommendation, View, Coverage, route, or release impact;
- generated files and how they were produced;
- exact validation commands and results;
- known limitations and follow-up work.

Keep canonical data, prose, executable behavior, UI, and generated release output separable when practical.

## 19. Known authoring friction

The Content Golden Path is unified, but higher-risk structured authoring entry points remain distributed:

- knowledge rows may require SQL;
- Gallery and comparisons use separate JSON seeds;
- executable problems require JSON plus Python;
- some failure and versioned-claim metadata is code-backed;
- migration inputs are declared and hash-checked in `data/build-manifest.json`;
- release identity and generated artifacts must move atomically.

This guide makes the current workflow explicit. Declarative catalogs and broader release-golden automation remain future work; do not hide these boundaries by manually editing generated output.
