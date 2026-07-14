# Optimization Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver GitHub Issues #1〜#11 as four independently releasable vertical slices and close the Issue #12 Optimization Atlas MVP checklist.

**Architecture:** Keep Python and SQLite canonical, export deterministic versioned JSON, and render it with a static Vite/React/TypeScript app. Shared contracts isolate map, recommendation, URL state, algorithm trace, and content so each slice can be tested without a running API.

**Tech Stack:** Python 3.12, Pydantic 2, SQLite, Typer, pytest, Vite 8, React 19, TypeScript, React Router HashRouter, Vitest, Testing Library.

## Global Constraints

- FastAPI UI, Python API, CLI, and deterministic recommendation engine remain supported.
- GitHub Pages base path is exactly `/optimization-compass/` and direct navigation must not require server rewrites.
- SQLite IDs and canonical answer values never change for presentation convenience.
- `unknown`, unanswered, `not_applicable`, and `unsupported` are distinct states.
- Generated JSON is deterministic for the same database and contract version.
- No legacy/v2 parallel implementation or fallback route is introduced.
- Long-form content and full trace frames are not stored in canonical SQLite.
- Comparison claims use the same evaluation budget and never present a universal ranking.

---

## Execution Order

`Task 2 → Task 1 → Task 5 state kernel → Task 3/4 → Task 5 integration → Task 11 foundation → Task 6 → Task 7/8 → Task 9/10 → Task 11 release finalization → Task 12` の順で進める。Task 3と4、Task 7と8、Task 9と10は共有contractが固定された後だけ並行化する。

---

### Task 1: Static application and Pages delivery (#1)

**Files:**
- Create: `site/package.json`, `site/package-lock.json`, `site/index.html`, `site/tsconfig*.json`, `site/vite.config.ts`
- Create: `site/src/main.tsx`, `site/src/App.tsx`, `site/src/styles.css`, `site/src/test/setup.ts`, `site/src/App.test.tsx`
- Create: `.github/workflows/pages.yml`
- Modify: `.github/workflows/ci.yml`, `README.md`, `.gitignore`

**Interfaces:**
- Produces: HashRouter routes `/`, `/map`, `/diagnose`, `/methods/:methodId`, `/compare/:comparisonId`, `/gallery`, `/gallery/:caseId`.
- Produces: `npm run test`, `npm run build`, and a `dist/` deploy artifact rooted at `/optimization-compass/`.

- [ ] Write routing and layout tests that assert all seven route families render and the mobile navigation remains reachable.
- [ ] Run `npm.cmd test -- --run` and confirm failure before the application files exist.
- [ ] Implement the smallest shared shell, compact navigation, error route, and placeholder route components.
- [ ] Configure Vite base and HashRouter, then run `npm.cmd test -- --run` and `npm.cmd run build`.
- [ ] Add PR build and main Pages deployment jobs; update local commands in README.
- [ ] Commit as `feat: add static atlas application shell`.

### Task 2: Versioned ViewSpec and deterministic exporter (#2)

**Files:**
- Create: `src/optimization_compass/view_spec.py`, `src/optimization_compass/site_export.py`
- Create: `tests/test_viewspec.py`, `tests/test_site_export.py`
- Modify: `src/optimization_compass/db.py`, `src/optimization_compass/cli.py`
- Generate: `site/public/data/views/problem-structure.json`, `site/public/data/manifest.json`

**Interfaces:**
- Produces: `ViewSpec`, `ViewNode`, `ViewEdge`, `AnswerBinding` Pydantic models.
- Produces: `export_site_data(output_dir: Path, repository: KnowledgeRepository) -> SiteManifest`.
- CLI: `optimization-compass export-site-data --output site/public/data`.
- `ViewSpec` includes `root_node_ids`; `ViewNode.answer_bindings` contains exact `{question_id, answer_value}` pairs.
- `ViewSpec` includes title/description. Every node includes summary, display order, initial collapsed state, and emphasis. Every edge includes an explanation.
- Answer nodes resolve related method/problem/feature/alternative IDs from matching `decision_rules`; entity records carry display label, summary, source IDs, and source URLs where applicable.

- [ ] Write failing model tests for duplicate IDs, missing roots, broken parent/edge/entity references, unknown answer bindings, invalid display order/emphasis, and incomplete related entities.
- [ ] Write a failing exporter golden test asserting required five branches and byte-identical repeated output.
- [ ] Implement Pydantic validation and repository queries without exposing SQLite layout to TypeScript.
- [ ] Export matching decision-rule targets as typed related entities so the map never derives method/problem links from node names.
- [ ] Use latest dataset release date at UTC 00:00 for `generated_at`; never use wall-clock time.
- [ ] Implement the CLI and generate the committed `problem-structure` artifact.
- [ ] Run focused tests, `optimization-compass export-site-data`, and a second byte comparison.
- [ ] Commit as `feat: export deterministic atlas view specs`.

### Task 3: Interactive Compass Map (#3)

**Files:**
- Create: `site/src/contracts/viewspec.ts`
- Create: `site/src/features/map/MapPage.tsx`, `MapTree.tsx`, `MapDetail.tsx`, `map-state.ts`, `MapPage.test.tsx`
- Modify: `site/src/App.tsx`, `site/src/styles.css`

**Interfaces:**
- Consumes: `/data/views/problem-structure.json` only.
- Produces: selected node ID and its exact `answer_bindings`; does not infer state from node naming.

- [ ] Write failing tests for three-level expansion, breadcrumb updates, related method/source rendering, keyboard movement, empty data, broken references, and unknown entity types.
- [ ] Implement an accessible semantic tree with 5〜7 top branches, ancestor emphasis, compact detail panel, zoom controls, and focus-current action.
- [ ] Add the 375px layout where map and detail switch without losing selection.
- [ ] Run map tests, full site tests, production build, and a browser smoke at desktop and 375px.
- [ ] Commit as `feat: add interactive optimization map`.

### Task 4: Browser recommendation data and parity engine (#4)

**Files:**
- Create: `src/optimization_compass/site_recommendation.py`
- Create: `tests/fixtures/recommendation_cases.json`, `tests/test_site_recommendation.py`
- Create: `site/src/contracts/site-data.ts`, `site/src/features/diagnose/recommend.ts`, `recommend.test.ts`, `DiagnosePage.tsx`
- Modify: `src/optimization_compass/site_export.py`, `site/src/App.tsx`, `.github/workflows/ci.yml`
- Generate: `site/public/data/recommendation/site-data.json`

**Interfaces:**
- Produces: `SiteData 1.0.0` with questions, rules, methods, implementations, compatibility metadata, source IDs, and dataset version.
- Produces: `recommend(siteData, canonicalAnswers): RecommendationResult` matching Python result bands and trace rule IDs.

- [ ] Convert current Python golden cases into shared JSON fixtures and verify Python expected output.
- [ ] Write failing TypeScript tests for exact validation, alternatives, domain gate, certificate gate, exclusion precedence, unknown semantics, and dataset mismatch.
- [ ] Implement deterministic exporter and TypeScript evaluator by porting the existing contract completely, not by adding a reduced second rule path.
- [ ] Add a parity command that compares the four result bands and fired rule/source IDs for every fixture.
- [ ] Build the Diagnose page and run Python tests, TypeScript tests, parity, and build.
- [ ] Commit as `feat: add offline diagnosis with python parity`.

### Task 5: Canonical AtlasState and deep links (#5)

**Files:**
- Create: `site/src/state/atlas-state.ts`, `atlas-state.test.ts`, `useAtlasState.ts`
- Modify: map, diagnose, method-link components
- Create: `docs/atlas-state-url-contract.md`

**Interfaces:**
- Produces: `AtlasStateV1 { version: 1; datasetVersion; viewVersion; selectedNodeId?; answers }`.
- Produces: `encodeAtlasState`, `decodeAtlasState`, and history-aware `useAtlasState`.

- [ ] Write failing round-trip, unknown/unanswered/N/A, invalid node, stale version, reload, and popstate tests.
- [ ] Before Task 3/4, implement the state type, stable key ordering, omission of unanswered values, and URL codec; document the 1800-character size limit and version policy.
- [ ] Wire map → diagnose, diagnose → map, and method → map without duplicate state stores.
- [ ] Run unit tests and browser reload/share/back-forward smoke.
- [ ] Commit as `feat: unify map and diagnosis state`.

### Task 6: AlgorithmTrace contract and reusable playback (#6)

**Files:**
- Create: `src/optimization_compass/trace_models.py`, `src/optimization_compass/traces/base.py`
- Create: `tests/test_trace_contract.py`
- Create: `site/src/contracts/trace.ts`, `site/src/features/playback/usePlayback.ts`, `PlaybackControls.tsx`, `PlaybackControls.test.tsx`
- Create: `docs/trace-contract.md`

**Interfaces:**
- Produces: `AlgorithmTrace`, `TraceBundle`, `TraceFrame`, `TracePoint`, `TraceVector`, `TraceMetric` and deterministic JSON serialization.
- Produces: player state with play/pause/step ±/speed/seek and unknown-event label fallback.

- [ ] Write failing Python validation, determinism, standalone snapshot, frame/evaluation monotonicity, size-limit, bundle fairness, finite-number, and unknown extension tests.
- [ ] Write failing React player tests for stepping, seeking, reversing, speed, and unknown events.
- [ ] Implement contracts and player, then export and replay a minimal dummy trace.
- [ ] Document hard limits and deterministic downsampling.
- [ ] Run both suites and build.
- [ ] Commit as `feat: add versioned optimization trace playback`.

### Task 7: Nelder–Mead Method Theater (#7)

**Files:**
- Create: `src/optimization_compass/traces/objectives.py`, `nelder_mead.py`
- Create: `tests/test_nelder_mead_trace.py`
- Create: `site/src/features/theater/NelderMeadPage.tsx`, `NelderMeadCanvas.tsx`, tests
- Generate: `site/public/data/traces/nelder-mead/*.json`

**Interfaces:**
- Produces events: `initialize`, `order`, `reflect`, `expand`, `outside_contract`, `inside_contract`, `shrink`, `stop`.
- Produces deterministic convex-quadratic and Rosenbrock presets with evaluation counts and role-labelled simplex vertices.

- [ ] Add failing event decision tests for reflection, expansion, both contractions, shrink, and stop.
- [ ] Implement pure objective and generator functions with finite-value guards.
- [ ] Add contour/simplex/candidate rendering and connect common playback controls.
- [ ] Add initial-simplex presets, method/source links, and local-search warning.
- [ ] Run tests, build, and browser playback smoke.
- [ ] Commit as `feat: visualize nelder mead steps`.

### Task 8: Gradient Compare Lab (#8)

**Files:**
- Create: `src/optimization_compass/traces/gradient_methods.py`
- Create: `tests/test_gradient_traces.py`
- Create: `site/src/features/compare/GradientComparePage.tsx`, `TrajectoryChart.tsx`, `MetricChart.tsx`, tests
- Generate: `site/public/data/traces/gradient-compare/*.json`

**Interfaces:**
- Produces GD, Momentum, Adam traces under an identical evaluation budget and objective/initial state.
- Supports ill-conditioned quadratic, Rosenbrock, oscillation, and safe-divergence presets.

- [ ] Write failing update-rule, shared-budget, determinism, divergence cap, and status tests.
- [ ] Implement three pure generators and preset exporter.
- [ ] Render synchronized trajectories, updates, objective history, parameters, and final statuses on one timeline.
- [ ] Add the non-ranking caveat and method/source links.
- [ ] Run tests, build, and synchronized playback smoke.
- [ ] Commit as `feat: compare gradient methods on shared budgets`.

### Task 9: Method and concept content system (#9)

**Files:**
- Create: `content/methods/*.md`, `content/concepts/*.md`
- Create: `scripts/validate_content.py`, `tests/test_content.py`
- Create: `site/src/content/content-index.ts`, `site/src/features/content/ContentPage.tsx`, `ContentIndexPage.tsx`, tests
- Modify: `src/optimization_compass/site_export.py`, `site/package.json`

**Interfaces:**
- Content frontmatter validates exact entity/source IDs, status, review date, dataset version, related visualization/comparison IDs.
- Initial pages: Nelder–Mead, Gradient Descent, convexity, derivative-free optimization.

- [ ] Write failing frontmatter, broken DB reference, Japanese text, math/code, and index tests.
- [ ] Add four complete pages with intuition, assumptions, one update/math step, links, Python example, and sources.
- [ ] Export a search index and render math, syntax-highlighted code, warnings, related routes, and SEO title/description.
- [ ] Run content validation, tests, and build.
- [ ] Commit as `feat: add method and concept learning pages`.

### Task 10: Problem Gallery (#10)

**Files:**
- Create: `content/cases/*.md`
- Extend: content validation and index export
- Create: `site/src/features/gallery/GalleryPage.tsx`, `CasePage.tsx`, tests

**Interfaces:**
- Initial cases: binary knapsack/budget, shift scheduling, HPO, portfolio allocation.
- Each case binds exact map answers, candidate/conditional/excluded methods, implementation versions, source IDs, and reproducible Python.

- [ ] Write failing schema/reference/filter/preload tests.
- [ ] Add four complete cases and validate every DB ID.
- [ ] Implement domain filter, detail sections, map link, and diagnose preload through AtlasState.
- [ ] Add avoid/conditional rationale and the no-universal-best disclaimer.
- [ ] Execute each minimal Python example in CI, then run site tests/build.
- [ ] Commit as `feat: add real world problem gallery`.

### Task 11: Canonical visualization and learning metadata foundation/finalization (#11)

**Files:**
- Create: `docs/metadata-responsibilities.md`
- Modify: canonical dataset DDL and all distributed data formats
- Extend: `src/optimization_compass/db.py`, `site_export.py`, `scripts/verify_data.py`, data maintenance docs/tests

**Interfaces:**
- Tables: `view_presets`, `method_visualization_profiles`, `demo_objectives`, `demo_scenarios`, `comparison_sets`, `comparison_set_members`, `learning_edges`.
- Seed records cover Nelder–Mead, gradient family, quadratic/Rosenbrock, Nelder–Mead scenarios, GD/Momentum/Adam comparison, and initial learning edges.

- [ ] Before Task 6, write the authority ADR and a reproducible release pipeline that recalculates checks instead of trusting stored `release_checks` rows.
- [ ] Write migration/rebuild tests for PK, FK, enum, unknown/N/A/unsupported semantics and release checks.
- [ ] Add tables and seed records to canonical SQL/JSON/JSONL/CSV/XLSX/SQLite distributions without storing article bodies or trace frames.
- [ ] Extend exporter indexes to consume these tables.
- [ ] Add cross-format row/key consistency checks and new release checks.
- [ ] After Tasks 6〜10 confirm the required fields, bump dataset version, version history, manifest hashes, preview/report, and runtime resource atomically.
- [ ] Run `verify-data`, cross-format validation, full Python/site suites, and build.
- [ ] Commit as `data: add atlas visualization metadata`.

### Task 12: Whole-product verification and Issue #12 closure

**Files:**
- Modify: `README.md`, relevant architecture/data/trace/state docs

**Interfaces:**
- Produces: one public Pages URL and traceable completion evidence for each #12 MVP checkbox.

- [ ] Run Python lint/format/type/test/verify and record exact counts.
- [ ] Run site tests, parity, content checks, example execution, and production build.
- [ ] Run browser smoke for map, diagnose deep link, Nelder–Mead, compare, four pages, four cases, desktop, keyboard, and 375px.
- [ ] Review the full diff against every Issue #1〜#12 acceptance checkbox.
- [ ] Push branch, open a PR listing `Closes #1` through `Closes #11` and the #12 checklist evidence, wait for required checks, merge, verify Pages, and confirm issues closed.
