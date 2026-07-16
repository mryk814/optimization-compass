# Product direction: build a problem-first Optimization Atlas

- Status: working product direction
- Date: 2026-07-16
- Inputs: current repository audit and external product review
- Related: #43, #115, #122, #123, #149–#155

## Purpose

Optimization Compass has already built an unusually disciplined foundation: a canonical released
SQLite database, deterministic recommendation rules, explicit sources/evidence, immutable release
identity, structured failure data, generated site artifacts, ADRs, and Coverage that records missing as
well as available learning assets.

The next product risk is no longer insufficient infrastructure. It is that the infrastructure becomes
more complete than the user-facing knowledge and journeys it exists to serve.

This document records a working direction:

> Optimization Compass should be experienced primarily as a collection of optimization problems and
> complete learning/decision journeys. Methods, implementations, visualizations, comparisons, and
> sources are answers and evidence attached to those problems—not six equal products competing for the
> user's first click.

This direction does not discard method content or the canonical database. It changes what the product
optimizes for and what appears first.

## Current diagnosis

### 1. The foundation is ahead of the public content

The current dataset release contains 99 methods, 56 problem archetypes, 28 example cases, 64
implementations, 96 sources, and 4,193 evidence links. The public Gallery currently exposes 11 cases,
and only a smaller subset has a complete Case → Theater → Compare journey.

The gap is not a reason to add another universal abstraction first. It is a reason to use the existing
contracts repeatedly until users can traverse the knowledge already present.

### 2. The natural unit of value is a problem journey

A user normally arrives with a question such as:

- how should I allocate a limited budget?
- how do I estimate nonlinear physical parameters?
- how do I schedule staff under hard and soft constraints?
- how do I optimize a shape, trajectory, or field through a simulator?

A method name is usually a candidate answer, not the initial question. The product's primary unit should
therefore be a Case rooted in a real question and connected to:

```text
question
  → formulation
  → alternatives before generic optimization
  → candidate / conditional / excluded methods
  → representative implementation
  → one mechanism or run in Theater
  → one fair comparison
  → diagnostics, failure modes, limitations, and switch signals
  → sources and evidence
```

A method page remains valuable as a reusable hub, but it is most understandable when reached from a
problem context.

### 3. Negative knowledge is a core differentiator

The Atlas does not only say what may work. It stores:

- exclusions with problem-specific reasons;
- failure triggers and observable symptoms;
- diagnostics and mitigations;
- conditional candidates and switch signals;
- explicit unknown, unsupported, and not-applicable states.

This is rarer and more useful than another catalog of algorithm descriptions. The `exclusion wins`
principle should be visible in the product, not only in the recommendation engine and database.

### 4. Home currently explains the taxonomy before demonstrating the product

Home currently presents Map, Diagnose, Methods, Theater, Compare, and Gallery as six equal cards and
places a full orientation block before the cards. That structure is internally coherent, but it makes a
new visitor choose among product surfaces before seeing a concrete optimization problem.

The Home experience should show one real Case or short diagnosis immediately, with one dominant next
action. Other surfaces remain available as secondary navigation.

### 5. Public release facts must come from generated authority

The README currently reports dataset v0.5.1 and stale table/method/source counts while the release
authority and generated report identify dataset 0.11.0. This contradicts the project's traceable and
deterministic identity.

Public version and count facts must be generated or checked against the validated release tree. They
must never become another hand-maintained authority.

### 6. The language position is implicit

The public product is primarily Japanese, while stable IDs, technical terms, metadata, and English titles
are also maintained. This can be a strength: Japanese-first optimization education with canonical
English terminology is a distinct and useful position.

The project should state that contract explicitly rather than appear to promise incomplete full
bilingual coverage.

### 7. Immutable releases need a sustainable storage policy

Keeping an immutable release is correct. Keeping every complete historical distribution bundle in the
ordinary Git working tree indefinitely may not be. Complete bundles can remain immutable and
hash-verifiable as release assets and external archives while the source tree keeps build inputs,
current runtime needs, and compact release metadata.

The project should stop future repository growth before considering any disruptive history rewrite.

## Product thesis

### Problem-first, not method-first

The main product question is:

> What kind of problem do I have, what must I clarify, what should I try, what should I avoid, and how do
> I verify the result?

The Atlas should not be positioned primarily as a database with 99 methods. It should be positioned as a
place where diverse real questions are translated into optimization formulations and evidence-backed
choices.

### Complete journeys over raw asset counts

The project should optimize for:

- public Cases with complete formulation;
- complete Case → Theater → Compare → Method/Source journeys;
- explicit exclusions and failure paths;
- journey completeness and route reachability;
- evidence freshness and limitations;
- reusable primitives proven by real Cases.

Raw method, page, table, or renderer counts remain release facts, not product-success scores.

### Infrastructure follows representative Cases

New schema, renderer, scientific profile, or authoring infrastructure should be justified by one or more
representative Cases. A generic abstraction without a flagship journey is provisional.

This applies especially to scientific expansion:

- topology optimization should prove field/state/adjoint and field-renderer contracts;
- rotation averaging should prove manifold representation and scoped-feasibility contracts;
- direct collocation should prove trajectory, dynamics, path constraints, and reconstruction accuracy;
- multi-fidelity simulation should prove evaluation-cost and failure-aware comparison.

## Priorities

## P0 — repair public trust and the first experience

### Generate release facts (#149)

Make README and public release identity derive from canonical release metadata and fail CI when stale.
This is a correctness issue, not cosmetic documentation work.

### Make Home problem-first (#150)

Show one concrete problem and one primary action above the fold. Reduce the cost of understanding the
internal surface taxonomy. Do not imply that all surfaces have equal depth.

## P1 — turn existing knowledge into visible journeys

### Complete representative journeys (#122)

Continue the five representative slices, one Case per PR where practical. Each slice must include at
least one negative or sensitivity lesson, not only a successful run.

Recommended order remains:

1. constrained engineering design;
2. nonlinear parameter estimation / least squares;
3. expensive noisy black box;
4. discrete allocation/search tree;
5. multi-objective trade-off.

### Measure journey completeness (#123)

Coverage should report complete, partial, draft, missing, and orphaned journeys. The milestone is not
"more pages" but a minimum set of fully traversable problem journeys.

### Promote canonical example cases

The canonical dataset has 28 example cases while the public Gallery has 11. Promotion should be a
reviewed pipeline, not bulk exposure:

1. verify the real question and formulation;
2. confirm candidate/conditional/excluded reasons;
3. connect sources and implementations;
4. identify or create a canonical problem instance;
5. add a primary and failure/sensitivity scenario where appropriate;
6. add a fair comparison only when the context is complete;
7. require journey Coverage before declaring the case complete.

### Make failures and exclusions discoverable (#151)

Provide a route from symptom or violated assumption to diagnostics, mitigations, Cases, Methods, and
failure Theater. Reuse canonical failure and exclusion data rather than authoring a second prose-only
knowledge base.

## Decision track — language and publication contract

### Declare Japanese-first positioning (#152)

The recommended provisional contract is:

- Japanese is the primary explanatory language;
- canonical English terms, aliases, source titles, API names, and stable IDs remain visible/searchable;
- English metadata does not imply a complete English article;
- a future full bilingual product requires an explicit i18n initiative and per-language Coverage.

This is a decision to review, not an instruction to translate or remove English fields immediately.

## Research tracks — valuable, but not blockers for the next content milestone

### MCP integration (#153)

Investigate a read-only MCP boundary over the same deterministic service used by CLI/API. MCP responses
must preserve rule IDs, exclusions, evidence, dataset version, and unknown states. An LLM must not become
a second recommendation authority.

### Citable dataset publication (#154)

Evaluate external archival/citation platforms using current official guidance. Deposit only validated
release artifacts whose hashes match the canonical manifest. External services remain distribution and
citation surfaces, not authoring authority.

### Historical release retention (#155)

Measure repository and release sizes, define an artifact retention matrix, and move future complete
historical bundles to release/archive storage while preserving normal offline build/test behavior.

## Home information architecture target

A future Home should be closer to:

```text
A real optimization question
  "I need to allocate limited resources under hard constraints."

What is being chosen?
What is optimized?
What must be respected?

Candidate: CP-SAT / MIP family
Excluded example: unconstrained local continuous method
Why excluded: variable and guarantee mismatch

[Start from this Case]  [Describe my problem]

Secondary paths:
Map · Learn · Theater · Compare · Search · Sources · Data/Coverage
```

The exact Case and CTA can change. The principle is to demonstrate the product before presenting its
internal navigation categories.

## Failure-first information architecture target

A failure/exclusion surface should support:

```text
Observed symptom
  → possible trigger or violated assumption
  → affected method / implementation / problem structure
  → diagnostic checks
  → mitigation or switch signal
  → related failure scenario
  → source and limitation
```

The product must distinguish:

- method excluded before solving;
- warning or conditional use;
- observed failure symptom;
- implementation-specific failure;
- unsupported capability;
- unknown diagnosis.

## Product metrics

Prefer these milestone metrics:

- complete public journeys;
- public Gallery cases with complete formulation and evidence;
- percentage of public Cases with explicit candidate/conditional/excluded reasons;
- Cases with a primary and failure/sensitivity scenario;
- fair canonical comparisons with complete context;
- orphan scenarios/comparisons/content;
- structured failure profiles with public diagnostic routes;
- stale source/claim counts;
- generated public-fact drift incidents;
- repository/release growth per dataset version.

Do not optimize primarily for:

- total method count;
- total Markdown page count;
- total view/renderer count;
- a single Coverage score;
- a universal algorithm ranking.

## Work ordering

The recommended near-term sequence is:

```text
#149 README/release truth
#122 first complete Case slice
#123 completeness report foundation
#150 problem-first Home using a real/near-complete journey
#122 remaining representative slices
#123 Coverage UI and CI gate
#151 failure/exclusion discovery
#152 language decision

parallel research:
#153 MCP
#154 citable dataset publication
#155 historical release retention
```

#149 may run independently because it repairs public release truth. #150 should use a real complete or
near-complete journey rather than inventing a Home-only demo. #151 should follow enough journey and
failure links to prove a generated discovery surface.

## Non-goals

- discarding method pages or Diagnose;
- hiding the canonical dataset;
- making every Case animated;
- exposing all 28 canonical cases without editorial review;
- adding a universal method score or leaderboard;
- building MCP before the deterministic service boundary is clear;
- promising complete English localization;
- moving release artifacts before a verified retention and recovery plan exists;
- adding infrastructure whose first representative Case is unspecified.

## Next milestone definition

A meaningful next product milestone is complete when:

- README release facts cannot drift from the canonical release;
- at least five representative Cases have complete traversable journeys;
- Coverage reports journey completeness and rejects broken public complete journeys;
- Home demonstrates one real Case and one primary problem-first action;
- exclusions and limitations are visible throughout each journey;
- the language position is explicit;
- future release growth has a documented, measurable storage policy;
- research decisions for MCP and citable publication are recorded without blocking content delivery.
