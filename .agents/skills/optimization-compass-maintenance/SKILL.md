---
name: optimization-compass-maintenance
description: Safely correct or extend Optimization Compass knowledge, content, Gallery cases, comparisons, problem instances, scenarios, and release inputs without editing generated artifacts or breaking canonical identity.
---

# Optimization Compass maintenance skill

Use this skill for repository tasks involving knowledge correction, educational content, canonical data, Gallery cases, comparisons, problem instances, visualization scenarios, recommendation relations, or dataset releases.

## Mandatory first reads

Read these before editing:

1. `/AGENTS.md`
2. `/docs/adding-knowledge.md`
3. `/CONTRIBUTING.md`
4. the nearest existing file and one recent merged PR for the same change type

For source or copied-material changes, also read:

- `/docs/licensing.md`
- `/NOTICE`
- `/THIRD_PARTY_SOURCE_AUDIT.md`

## Task classification

Classify the request into exactly one primary class before editing.

### A. Existing prose/content correction

Examples:

- fix an explanation, typo, formula wording, limitation, or example;
- update an existing source or review date;
- improve an article without adding a canonical entity.

Primary authority: `content/**/*.md`.

### B. Existing-entity content addition

Examples:

- add a method article for an existing `M_*` ID;
- add a concept article linked to an existing canonical entity;
- add prerequisites or related content links.

Primary authority: `content/**/*.md`.

### C. Gallery case

Examples:

- add a real-world application using existing methods, problems, implementations, and sources;
- promote an existing canonical example case into Gallery.

Primary authority: `data/seeds/site_gallery.json`.

### D. Comparison

Examples:

- add a method contrast, sensitivity comparison, failure contrast, or result trade-off using existing artifacts.

Primary authority: `data/seeds/site_comparisons.json`.

### E. Problem definition or executable instance

Examples:

- add a benchmark/problem instance;
- add an objective evaluator or gradient;
- add display/reference metadata.

Primary authorities:

- `src/optimization_compass/resources/problem-suite.json`
- `src/optimization_compass/problem_registry.py`

### F. Canonical method, implementation, source, evidence, or vocabulary

Examples:

- add a new `M_*`, `I_*`, `S*`, hierarchy relation, implementation mapping, predicate, or evidence claim.

Primary authority: registered dataset migration/build inputs, plus content and tests.

This is a high-risk class.

### G. Visualization scenario, generator, artifact, or renderer

Examples:

- add a canonical scenario;
- add a Trace generator;
- add a renderer family or visualization payload contract.

Primary authorities span Python contracts/generators, data seeds, and site code.

This is a high-risk class.

### H. Recommendation, schema, release, or publishing

Examples:

- change decision rules or Diagnose vocabulary;
- add a schema migration;
- change dataset version or publish generated artifacts.

This is a critical class. Require an explicit issue/design context and complete validation.

## Non-negotiable invariants

Before making a patch, preserve all of these:

1. Do not hand-edit generated authority outputs:
   - `src/optimization_compass/resources/knowledge.sqlite`
   - `src/optimization_compass/resources/DATASET_VERSION`
   - `site/public/data/**`
   - `data/optimization_method_selection_database_v*`
   - generated Trace/media/search/retrieval/Coverage/release files
2. Do not silently repurpose a stable ID.
3. Search for aliases and near-duplicate entities before creating an ID.
4. Keep method theory separate from library/API implementation.
5. Keep `unknown`, `not_applicable`, and `unsupported` distinct.
6. Attach authoritative sources to factual knowledge additions.
7. Do not use Qiita or Zenn as evidence.
8. Do not convert a library default into a universal ranking.
9. Do not claim continuous feasibility or safety solely from discretized constraints.
10. Do not add entity-specific router/UI crosswalks when canonical relations can generate links.
11. Do not manually reconcile generated JSON conflicts; regenerate from current canonical inputs.
12. Do not change release identity in a content-only change.

## Standard operating procedure

### Step 1 — Resolve scope

Write down internally:

- primary task class;
- canonical entity IDs involved;
- editable authority;
- generated outputs that may change;
- recommendation/route/Coverage/release impact;
- validation tier.

If the request mixes multiple primary classes, split the work or make the dependency order explicit.

### Step 2 — Inspect existing identity

Search the repository/database-facing inputs for:

- exact ID;
- English and Japanese names;
- common aliases and abbreviations;
- family/parent entity;
- implementation mapping;
- existing content, case, scenario, comparison, and source links.

Do not infer that a missing article means a missing canonical method.

### Step 3 — Resolve evidence

For every material claim:

- prefer official docs/repository, original paper, standard, or specification;
- record source identity and supported claim;
- separate historical primary sources from current implementation behavior;
- record version/date for implementation defaults or release claims;
- review licensing when copying anything beyond a factual paraphrase.

If no suitable source exists, stop or store an explicit unknown instead of inventing a value.

### Step 4 — Modify the smallest authority

Follow the matching recipe below. Do not patch a downstream representation if an upstream authority owns the value.

### Step 5 — Add focused tests

Tests should prove the new invariant, identity, relation, recommendation behavior, generated route, or renderer contract. Avoid brittle raw count assertions unless the count is itself a documented release contract.

### Step 6 — Validate incrementally

Run focused validation first. Then run the required tier. Inspect generated diffs before claiming completion.

### Step 7 — Prepare the PR

Use `/docs/knowledge-change-checklist.md`. Include:

- change category;
- changed IDs;
- source/evidence;
- prior and new behavior;
- recommendation/View/journey/Coverage/release impact;
- generated outputs and command used;
- exact test results;
- limitations and follow-up.

Every commit requires DCO sign-off.

## Recipes

### Recipe A — Correct existing prose

1. Open the matching `content/**/*.md` page.
2. Preserve canonical frontmatter identity.
3. Keep frontmatter `summary` identical to the first body paragraph.
4. Update sources and `last_reviewed` only when factually reviewed.
5. Run content, licensing, and site tests.
6. Escalate if the correction reveals incorrect canonical structured data.

### Recipe B — Add content for an existing entity

1. Confirm the canonical entity exists.
2. Add a Markdown page with validated frontmatter.
3. Start with `status: draft` when evidence or relations are incomplete.
4. Explain intuition, inputs, constraints, guarantee scope, diagnostics, switch signals, and limitations.
5. Link existing cases, visualizations, comparisons, family guidance, and sources where valid.
6. Run content validation and a staged build if indexes/relations change.

### Recipe C — Add a Gallery case

1. Choose an existing problem archetype and canonical entities.
2. Copy the nearest case in `data/seeds/site_gallery.json`.
3. Replace every copied ID after independent review.
4. Supply valid feature values and Diagnose answers.
5. Keep candidate/conditional/excluded method sets disjoint.
6. Give concrete reasons for conditional and excluded methods.
7. Make `map_node_id` derivable from an answer.
8. Include a minimal compilable Python example.
9. Explain real-world assumptions and distinguish them from the educational instance.
10. Run content/data/site-export/stage/site-build validation.

### Recipe D — Add a comparison

1. Reuse existing traces/artifacts and renderer families when possible.
2. Define canonical or derived identity.
3. State question, fixed factors, changed factors, budget, stopping, seed, tuning, synchronization, metrics, fairness, caveat, and comparability.
4. Mark failure/sensitivity comparisons non-ranking.
5. Require complete benchmark context for ranking eligibility.
6. Validate parity, site contracts, build, and relevant E2E.

### Recipe E — Add an executable problem instance

1. Add definition/instance metadata in `problem-suite.json`.
2. Add exactly one matching `registry_key` implementation in `problem_registry.py`.
3. Validate dimensions and parameters.
4. State oracle availability and infeasible-result behavior.
5. Distinguish known reference from optimizer-visible information.
6. Add focused evaluator/gradient tests.
7. Run full Python and staged-build validation.

### Recipe F — Add a canonical method or implementation

1. Confirm identity, family placement, aliases, and method-versus-implementation boundary.
2. Add source rows before dependent knowledge.
3. Add canonical rows, hierarchy, mappings, evidence, and relations in a dedicated migration/build input.
4. Register the migration in `dataset_release.py`; a file in `data/migrations/` is not auto-applied.
5. Add or update content and source links.
6. Add focused identity, relation, recommendation, and release tests.
7. Update release authority/docs only within an intentional dataset release.
8. Run complete validation.

Do not execute this recipe as a hidden side effect of a small article or Gallery request.

### Recipe G — Add a visualization scenario

1. Confirm or add a canonical problem instance.
2. Reuse an existing profile, artifact contract, and renderer family when possible.
3. Define scenario identity, purpose, experiment, runs, budget, seed, tuning, stopping, observables, success/failure signals, sources, static summary, text alternative, and limitations.
4. Add deterministic generator output.
5. Connect through canonical relations to Case/Method/Compare rather than hard-coded UI switches.
6. Add contract tests, artifact tests, frontend tests, accessibility/static-summary tests, and E2E.
7. Run complete validation.

## Validation tiers

### Tier A

For prose or an existing-content correction:

```bash
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
npm --prefix site test -- --run
```

### Tier B

For Gallery, comparison, existing-contract structured data, or problem metadata:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run optimization-compass verify-data
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
uv run python scripts/rebuild_dataset.py --stage
npm --prefix site run parity
npm --prefix site test -- --run
npm --prefix site run build
```

### Tier C

For executable scenarios, renderer changes, recommendation behavior, schema, or release changes, run Tier B plus:

```bash
npm --prefix site run typecheck
npm --prefix site run test:e2e
```

Use focused tests during iteration, but do not substitute them for the required final tier.

## Stop conditions

Stop and report the unresolved decision when:

- a new ID namespace or schema field is needed;
- the entity may duplicate an existing method, variant, implementation, problem, or source;
- an authoritative source is unavailable;
- recommendation output changes without a regression case;
- continuous/discrete feasibility semantics are ambiguous;
- a new renderer or artifact contract version is required;
- migration ordering or release bump policy is unclear;
- only generated files appear to offer an edit point;
- validation generates broad unrelated changes;
- publishing would be required but was not explicitly part of the task.

## Completion criteria

A task is complete only when:

- the correct authority was edited;
- identities and sources are valid;
- generated output was not manually patched;
- required tests pass or failures are reported precisely;
- the PR description contains the evidence and impact summary;
- no hidden release or recommendation change remains.
