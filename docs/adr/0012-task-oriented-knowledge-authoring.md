# ADR 0012: Knowledge authoring is task-oriented, declarative where appropriate, and compiled into the released database

- Status: proposed
- Date: 2026-07-16
- Issue: #145
- Related: PR #144, PR #146

## Context

Optimization Compass has strong runtime and release boundaries:

- the released SQLite database owns canonical runtime knowledge;
- SQL migrations and validated seeds are auditable build inputs;
- Markdown owns human-readable educational prose;
- Python registries and generators own executable behavior;
- site indexes, distributions, Trace payloads, and release files are generated artifacts.

The boundaries protect identity and deterministic releases, but the authoring experience is difficult.
A contributor adding one concept may need to discover whether the change belongs in a SQL migration,
JSON seed, Markdown frontmatter, Python registry, generated fixture, or release workflow. Ordinary
knowledge additions can require hand-written SQL. Migrations are wired individually. Validation is a
long command list. Scaffolding does not exist. Generated release counts and parity fixtures have
occasionally required coordinated updates.

The problem is not that all information should live in one file. Prose, structured facts, executable
behavior, and rendering genuinely have different owners. The problem is that common tasks lack one
discoverable entry point and one validated authoring contract.

## Decision

Adopt a **task-oriented authoring architecture** with four preserved authority families:

1. human-readable content;
2. declarative structured knowledge;
3. executable behavior;
4. generated outputs.

Ordinary structured knowledge additions will move from SQL data migrations into versioned,
Pydantic-validated catalogs compiled into SQLite during the deterministic staged build. SQL migrations
will be reserved for schema evolution and exceptional transformations. Specialized authoring inputs,
such as Gallery cases, comparisons, problem suites, and visualization scenarios, remain separate until
there is demonstrated value in moving them.

The repository will expose task-oriented validation and scaffold commands. Those commands orchestrate
existing validation logic; they do not create a second implementation of repository rules.

This ADR is an architecture proposal. It does not authorize an immediate all-at-once migration.

## Goals

- make a prose correction and an existing-entity Gallery addition discoverable from the repository root;
- allow a new canonical source, method, implementation, mapping, and evidence relation to be authored
  without embedding ordinary row data in a schema migration;
- preserve stable IDs, evidence, explicit unknown states, deterministic builds, and atomic releases;
- give humans and agents the same task-specific commands and machine-readable failures;
- reduce generated-file and release-golden hand coordination;
- enable incremental migration with byte/row-equivalent output checks.

## Non-goals

- one monolithic YAML/JSON file for the entire product;
- making generated SQLite, site data, Trace, or release artifacts editable;
- moving executable objective, solver, simulator, or renderer code into data files;
- weakening source, evidence, licensing, or release requirements;
- automatically allocating stable IDs without review;
- automatically publishing a dataset from an ordinary contribution;
- replacing specialized Gallery/Comparison/Problem/Scenario contracts before their current pain is
  measured.

## Authority model

| Information | Authoring authority after this ADR | Compiled/generated target |
|---|---|---|
| Educational prose and article metadata | `content/**/*.md` | content/search/retrieval/site indexes |
| Canonical source/method/implementation facts | `data/catalog/**` | released SQLite and all distributions |
| Hierarchy, implementation mappings, evidence, aliases, learning relations | `data/catalog/**` | released SQLite and relation indexes |
| Versioned implementation claims | claim catalog with validity windows | SQLite claim tables and audits |
| Gallery cases | existing validated Gallery input | Gallery/journey/search/Coverage outputs |
| Comparisons | existing validated comparison input | comparison/site/journey outputs |
| Problem definitions and instances | existing problem-suite input | SQLite/site/Trace metadata |
| Executable objectives and gradients | Python registry | generated traces and runtime evaluation |
| Scenario/generator/renderer behavior | specialized Python/TypeScript contracts | visualization artifacts and UI |
| Schema evolution | ordered schema migration manifest | database schema |
| Released database and site/distribution artifacts | generated only | immutable release tree |

A catalog does not own long-form explanation or executable code. A Markdown page does not own a method's
canonical family, implementation mapping, or versioned API default.

## Proposed repository layout

The initial catalog should prefer deterministic JSON and one reviewable record per file. JSON avoids
implicit YAML scalar coercion and uses the repository's existing JSON/Pydantic tooling.

```text
data/
  build-manifest.json
  schema-migrations/
    003_atlas_metadata.sql
    ...
  catalog/
    catalog-manifest.json
    sources/
      S096.json
    methods/
      M_TRUST_REGION_REFLECTIVE.json
    implementations/
      I_SCIPY_LEAST_SQUARES_TRF.json
    relations/
      method-hierarchy/
        MH_TRUST_REGION_REFLECTIVE.json
      method-implementation/
        MIM_SCIPY_TRF.json
      evidence/
        EV_SCIPY_TRF_DEFAULT.json
      learning/
        LEARN_TRF_LEAST_SQUARES.json
    claims/
      CLAIM_SCIPY_LEAST_SQUARES_DEFAULT_TRF.json
```

Exact names may change, but the following properties are required:

- file paths are stable and derive from stable IDs where practical;
- one file has one primary review identity;
- collection-wide ordering is canonicalized by ID, never filesystem enumeration order;
- duplicate primary IDs across files fail validation;
- every file declares a model/schema version;
- all catalog paths are registered and protected deterministic inputs;
- unregistered files under managed catalog directories fail validation rather than being silently ignored.

## Build manifests

### Schema migration manifest

Schema migration ordering must be explicit and validated. Directory discovery by filename alone is not
sufficient, and individual Python constants do not scale.

A proposed `data/build-manifest.json` owns an ordered sequence such as:

```json
{
  "manifest_version": "1.0.0",
  "schema_migrations": [
    {"id": "003", "path": "data/schema-migrations/003_atlas_metadata.sql", "sha256": "..."},
    {"id": "004", "path": "data/schema-migrations/004_learning_coverage.sql", "sha256": "..."}
  ],
  "catalog_manifest": "data/catalog/catalog-manifest.json",
  "specialized_inputs": [
    "data/seeds/site_gallery.json",
    "data/seeds/site_comparisons.json",
    "src/optimization_compass/resources/problem-suite.json"
  ]
}
```

The manifest must reject:

- duplicate or non-monotonic migration IDs;
- missing files or hash mismatches;
- migration files present in the managed directory but absent from the manifest;
- manifest entries outside approved repository paths;
- data-changing SQL in migrations declared `schema_only` unless explicitly allowed for a transition;
- an authoring input omitted from protected-input and deterministic-tree checks.

Release authority continues to own target/base version and pinned base hash. The build manifest does not
duplicate release identity.

### Catalog manifest

The catalog manifest owns dependency order and model versions, not factual records.

```json
{
  "catalog_version": "1.0.0",
  "collections": [
    {"kind": "source", "path": "data/catalog/sources", "model_version": "1.0.0"},
    {"kind": "method", "path": "data/catalog/methods", "model_version": "1.0.0"},
    {"kind": "implementation", "path": "data/catalog/implementations", "model_version": "1.0.0"},
    {"kind": "relation", "path": "data/catalog/relations", "model_version": "1.0.0"},
    {"kind": "claim", "path": "data/catalog/claims", "model_version": "1.0.0"}
  ]
}
```

Sources load before entities, entities before relations, and entities/relations before claims and audits.
The compiler derives a stable dependency graph and rejects cycles where cycles are semantically invalid.

## Catalog record semantics

### Full records, not embedded SQL

A catalog entity is a complete validated representation of the fields the project owns for that entity.
The compiler maps it to SQLite. Catalog files may not contain arbitrary SQL fragments, table names, or
unvalidated column maps.

### Explicit operation

Each record declares one operation:

- `add`: ID must not exist in the pinned base or earlier catalog phase;
- `replace`: ID must exist and the replacement is a complete project-owned record;
- `retire`: ID remains resolvable with explicit replacement/deprecation semantics;
- `assert`: validate a legacy/base row without changing it during staged migration work.

Generic upsert is prohibited because it hides accidental identity collisions.

### Drift protection for replacements

A `replace` record includes an expected prior fingerprint computed from the canonical subset of the base
row. The compiler fails when the pinned base no longer matches that fingerprint. This prevents a stale
catalog replacement from silently overwriting a newer upstream correction.

During initial migration, an `assert` record can verify row equivalence before ownership moves to the
catalog.

### Evidence and field ownership

Every factual entity record includes:

- stable ID and aliases;
- explicit status/confidence/last-verified fields;
- source IDs;
- controlled-vocabulary values;
- explicit `unknown`, `not_applicable`, or `unsupported` states where applicable.

Claims whose truth depends on version, API, condition, or time remain separate claim records with
validity windows. Evidence records identify the supported target and field/claim rather than relying only
on a broad source list.

### Canonical serialization

The compiler:

- parses JSON into frozen Pydantic models;
- normalizes only fields whose normalization is part of the contract;
- sorts records and unordered relation sets deterministically;
- preserves authored display order only where display order is semantically owned;
- emits canonical JSON for hashes and diagnostics;
- reports file path and JSON pointer for every validation error.

## Compilation pipeline

The staged release becomes:

```text
pinned base database
  → validate build/catalog manifests and protected inputs
  → apply ordered schema migrations
  → compile declarative catalogs in dependency order
  → apply specialized validated seeds and executable-registry metadata
  → compute live integrity/evidence/coverage/release checks
  → export SQLite / JSON / JSONL / CSV / Excel / report / site data
  → rebuild independently and compare deterministic tree hashes
  → publish atomically only through the existing publish gate
```

No catalog compiler writes published repository artifacts directly. It writes only into the staged
working database/output tree.

## Compatibility strategy

### Do not migrate everything at once

Existing SQL migrations remain immutable historical inputs until a planned dataset release replaces or
absorbs them. The catalog compiler is added alongside the current pipeline.

### Pilot with one complete slice

The first catalog pilot should migrate one representative addition that includes:

- one source;
- one method;
- one implementation or mapping;
- one hierarchy relation;
- one evidence relation;
- one content link;
- focused tests.

The Trust Region Reflective addition is a useful equivalence fixture because its current migration
contains all of those elements, but migration must happen only in an intentional release and must prove
row/snapshot equivalence before deleting or bypassing historical SQL.

### Snapshot equivalence

For every migrated collection, tests compare:

- table schema and row content;
- stable IDs and aliases;
- evidence/relationship closure;
- recommendation projection;
- search/retrieval/entity-link outputs;
- release report and format round trips;
- deterministic tree hash, except for explicitly versioned release changes.

### Dual-authority prohibition

An ID may not be actively owned by both SQL data migration and catalog. The manifest/compiler reports
duplicate ownership. Transitional `assert` records may verify legacy rows but do not author them.

## Task-oriented validation commands

Add one stable CLI surface:

```bash
uv run optimization-compass validate content
uv run optimization-compass validate gallery
uv run optimization-compass validate comparison
uv run optimization-compass validate problem
uv run optimization-compass validate catalog
uv run optimization-compass validate visualization
uv run optimization-compass validate release
uv run optimization-compass validate all
```

### Implementation requirements

- commands call shared Python validation functions, not shell-script copies of logic;
- CI and local usage use the same functions;
- each task has `--format human|json`;
- each task returns a stable nonzero exit code on failure;
- output names the authority file, stable ID, rule code, and suggested next action;
- `--changed-from <ref>` may narrow expensive checks only when dependency analysis proves safety;
- `validate all` remains the authoritative full gate;
- aliases print the underlying checks they ran.

A proposed machine-readable result:

```json
{
  "contract_version": "1.0.0",
  "task": "gallery",
  "status": "fail",
  "checks": [
    {
      "code": "gallery.unknown_method",
      "status": "fail",
      "path": "data/seeds/site_gallery.json",
      "pointer": "/cases/4/candidate_method_ids/0",
      "entity_id": "example-case",
      "message": "unknown method M_EXAMPLE",
      "next_action": "add or correct the canonical method ID; do not edit generated gallery.json"
    }
  ]
}
```

Validation task composition should be documented and tested so that a shorter command never silently
omits a required integrity check.

## Scaffolding commands

Scaffolds reduce blank-page friction but may not invent facts.

```bash
uv run optimization-compass scaffold content method --id M_EXAMPLE
uv run optimization-compass scaffold gallery-case --id example-case
uv run optimization-compass scaffold problem-instance --id INSTANCE_EXAMPLE
uv run optimization-compass scaffold comparison --id COMPARE_EXAMPLE
uv run optimization-compass scaffold method --id M_EXAMPLE
uv run optimization-compass scaffold scenario --id SCENARIO_EXAMPLE
```

### Safety rules

- `--id` is required; the scaffold may suggest naming rules but does not silently allocate an ID;
- existing IDs and aliases are searched before output;
- default mode prints a plan/diff; writing requires `--write`;
- output contains explicit placeholders or `unknown`, never fabricated sources, claims, dates, or
  performance statements;
- generated/release paths are never scaffold targets;
- every scaffold prints editable files, forbidden generated files, required sources, validation task,
  and PR checklist path;
- overwrite requires an explicit flag and is refused for canonical IDs by default;
- content starts as draft unless publication requirements are already supplied and validated;
- method/implementation scaffolds remain high-risk and require an Issue reference.

### Scaffold output manifest

Each scaffold emits a small plan:

```json
{
  "contract_version": "1.0.0",
  "task": "gallery-case",
  "requested_id": "example-case",
  "files_to_create": ["data/seeds/site_gallery.json#planned-entry"],
  "editable_authorities": ["data/seeds/site_gallery.json"],
  "forbidden_outputs": ["site/public/data/gallery.json"],
  "required_inputs": ["problem_archetype_id", "source_ids", "method dispositions"],
  "validation": "optimization-compass validate gallery"
}
```

## Release and generated-golden simplification

### Derive non-contract counts

Raw page, row, source, and coverage counts should not be hard-coded in tests unless the count is itself a
published compatibility contract. Prefer minimum thresholds, set equality against canonical inputs, or
manifest-derived expectations.

### Regenerate parity from post-build authority

Recommendation and browser parity fixtures must be generated from the staged post-migration engine/site
projection. Textual insertion into one fixture is prohibited. Python and TypeScript parity consume one
canonical generated case set.

### Atomic generated commit

When a release workflow commits generated outputs, it commits runtime database, distributions, site
data, fixtures, release identity, and documentation in one final commit. Actor guards must not skip the
only workflow capable of completing that atomic set.

### No ordinary-PR publish

Ordinary content/catalog PRs run stage validation. Publishing remains an explicit maintainer/release
operation.

## Incremental implementation plan

### Phase 1 — exercise and inventory

Use the documented recipes for at least:

- one prose correction;
- one existing-entity content page;
- one Gallery case;
- one comparison;
- one problem instance;
- one canonical method/implementation addition.

For each, record touched authorities, repeated commands, manual count/fixture changes, unclear ownership,
and unexpected generated diffs. This evidence can adjust later phases.

### Phase 2 — validation aliases first

Implement `validate content`, `gallery`, and `all` by wrapping existing functions. This improves the
human/agent path without changing dataset authority. Add JSON output and stable rule codes.

### Phase 3 — build and migration manifests

Introduce manifests and protected-input validation while retaining current migrations. Fail on
unregistered inputs. Do not move data yet.

### Phase 4 — source and method catalog pilot

Add Pydantic catalog models and compile a representative complete slice into the staged database. Prove
snapshot/recommendation/export equivalence.

### Phase 5 — relation and claim catalogs

Move hierarchy, implementation mapping, evidence, aliases, learning relations, and typed versioned claims
after entity catalogs are stable.

### Phase 6 — scaffolds

Add low-risk content, Gallery, comparison, and problem scaffolds first. Add canonical method/scenario
scaffolds only after catalog and visualization contracts are stable.

### Phase 7 — release-golden automation

Remove non-contract count assertions, unify parity generation, and prove atomic bot/release behavior.

### Phase 8 — consider specialized-input migration

Only after measured use should the project decide whether Gallery, comparisons, failure metadata, or
problem profiles benefit from one-file-per-entity catalogs. They must not be moved merely for visual
uniformity.

## Validation requirements for the architecture work

Every implementation phase must include:

- focused Pydantic/model tests;
- duplicate/unregistered/missing/dependency-cycle failure tests;
- protected-input and deterministic-rebuild tests;
- row and generated-output equivalence tests for migrated records;
- recommendation parity and source/evidence closure;
- Windows/path-order independence where filesystem traversal is used;
- machine-readable CLI output contract tests;
- no-write/dry-run and overwrite-refusal scaffold tests;
- release rollback and atomicity tests when publish behavior changes.

## Risks and mitigations

### Catalog becomes a second database

Mitigation: catalogs are authoring inputs compiled into SQLite; no runtime reads them directly. The
released SQLite remains runtime authority.

### Full records duplicate pinned-base data

Mitigation: migrate only project-owned additions/overrides; use `assert` and prior fingerprints; keep
historical base ownership explicit.

### Too many small files

Mitigation: one file per primary identity for conflict-prone entities, with optional reviewed grouping
only when records are inseparable. Validate filename/ID correspondence.

### Manifest maintenance becomes another manual step

Mitigation: validation fails on unregistered files and a safe command can propose, but not silently
commit, manifest additions.

### Validation aliases diverge from CI

Mitigation: commands and workflows call the same Python functions and publish the executed check list.

### Scaffolds encourage low-quality factual additions

Mitigation: scaffolds create placeholders/drafts only, require explicit IDs, and never invent evidence or
publication status.

### Migration changes release hashes unexpectedly

Mitigation: perform catalog migration only in an intentional release, compare canonical snapshots, and
review every non-identity diff.

## Consequences

- common tasks gain a discoverable and testable entry point;
- new canonical knowledge no longer requires ordinary row data embedded in DDL-oriented migrations;
- repository responsibilities remain separate instead of being flattened into one universal format;
- agents receive stable rule codes and stop conditions rather than inferring workflow from filenames;
- initial implementation adds catalog/compiler/manifest code and transitional compatibility tests;
- migration is deliberately slower than a one-shot rewrite, but each phase remains reviewable and
  preserves release integrity.

## Open review questions

1. Should initial catalogs use JSON per entity, or a tightly restricted YAML subset? This ADR recommends
   JSON for deterministic parsing and existing-tool reuse.
2. Which legacy records are project-owned overrides versus immutable pinned-base facts?
3. Is a prior-row fingerprint sufficient for `replace`, or should replacements also name the release in
   which ownership transferred?
4. Which validation tasks can safely support changed-file narrowing?
5. Should manifest hashes be authored or generated/verified by a dedicated command?
6. Which representative method should be the first catalog pilot if TRF is considered too release-coupled?
7. When should Gallery and comparison collections move from single collection files to one file per
   identity?
