# Method content density

Optimization Compass separates structured method facts from human-facing educational prose.

## Authority

- `methods` and related canonical tables own stable IDs, short summaries, assumptions, capabilities, implementations, sources, and relations.
- `content/methods/*.md` owns explanatory prose, mathematics, examples, interpretation, and teaching order.
- generated `content.json`, `entity-links.json`, search, and Coverage assets are exporter outputs and must not be edited by hand.

## Content levels

A method does not need every possible artifact, but a public Method page should not appear empty.

### Level 0 — Registered

- canonical method ID
- name
- short summary
- at least one source

### Level 1 — Structured

- assumptions and incompatibilities
- variable / constraint / oracle scope
- implementation relations
- diagnostic or failure relations where available

### Level 2 — Explained

A published Markdown guide provides:

- what the method updates or searches
- suitable and unsuitable conditions
- important parameters and diagnostics
- stopping / budget interpretation
- a copyable example or explicit educational pseudocode
- common failures and checks
- sources and related content

### Level 3 — Demonstrated

- Gallery case, comparison, or executable scenario
- fair comparison context
- known limitations

### Level 4 — Visualized

- canonical visualization scenario
- educational metadata and text alternative
- interactive or derived media artifact

Level 4 is selective. Level 2 is the target for representative methods that users are likely to encounter directly.

## Beginner-first reading order

The first reader is assumed to be learning the method rather than implementing a solver from scratch. A guide may contain advanced material, but the main path should answer these questions before entering detailed theory:

1. What is the method trying to accomplish?
2. What information does it observe?
3. What state does it move or update?
4. What counts as progress?
5. Under which conditions should it be considered or avoided?
6. Which observable indicates that another method should be tried?

Mathematics is retained, but the prose explains what each expression represents before relying on it. Proof assumptions, implementation differences, numerical linear algebra, and historical details may appear under a clearly named `コラム` or deeper section.

## Family choice guides

A family guide uses a canonical `MF_*` row and groups methods with overlapping prerequisites. It does not create a context-free ranking.

Families may overlap from a learner's point of view. A method can appear in more than one guide when the surrounding decision question is different; the canonical method identity remains single and the guide explains why the method is being compared in that context.

Each family guide provides:

- `30秒でつかむ`: the family's motivation or “feeling”
- `まず確認すること`: variable, oracle, constraint, cost, and guarantee questions
- `条件付きの選び分け`: method roles and the conditions that change the preferred candidate
- `うまくいったサインと切替サイン`: method-specific observables
- a small comparison or problem-brief contract
- an advanced `コラム`
- related family and method routes

Priority is expressed as a role, not a universal score:

- a simple default starting point when its assumptions hold
- preferred under a stated condition
- fallback after a stated failure or unavailable oracle
- contrast-only for learning
- avoid when assumptions conflict
- switch when diagnostics show a specific failure mode

## Initial expanded tranche

Issue #87 raises coverage across:

- smooth local and curvature methods
- composite / nonsmooth convex methods
- population and derivative-free methods
- structure-first discrete algorithms
- LP / MILP algorithms
- trajectory optimization

The tranche adds guides for BFGS, L-BFGS-B, Newton, trust-region Newton-CG, ADMM, proximal gradient, FISTA, differential evolution, genetic algorithms, particle swarm optimization, MADS, dynamic programming, Dijkstra / A*, branch-and-cut, dual simplex, and direct collocation.

The first tranche moves the published content baseline from 12 to at least 28 pages. This is a review floor for representative coverage, not a target to give all 98 methods identical page length.

## High-use method tranche

Issue #92 adds guides for methods that already appear frequently in implementation libraries, comparisons, or adjacent Atlas content but lacked dedicated explanations:

- Momentum SGD, Adam, coordinate descent, subgradient, and mirror descent
- SLSQP, nonlinear interior-point, augmented Lagrangian, projected gradient, and active-set methods
- Powell, pattern search, and COBYLA
- SHGO, DIRECT, and dual annealing

This raises the published method-guide baseline to 42. The remaining registered methods continue to retain structured summaries, predicates, implementations, relations, and sources even where a full guide has not yet been authored.

## Beginner family tranche

Issue #97 adds beginner-first choice guides for:

- smooth local optimization
- constrained nonlinear programming
- local derivative-free optimization
- global and multimodal search
- expensive black-box optimization and HPO
- composite and nonsmooth convex optimization
- discrete and combinatorial optimization
- stochastic-gradient and machine-learning optimization

This raises the published method-guide baseline to 50 and provides a reusable pattern for future family and method tranches.

## Second beginner method tranche

Issue #101 fills the most visible gaps exposed by the family guides:

- nonlinear CG, Newton-CG, trust-krylov, and Gauss–Newton
- bundle method, SPSA, COBYQA, and basin hopping
- TPE, Hyperband / ASHA, and AdamW
- epsilon-constraint, NSGA-III, MOEA/D, direct shooting, and outer approximation for MINLP

These guides are the first individual-method tranche to require the beginner-first structure directly: `30秒でつかむ`, prerequisite questions, a plain-language mechanism, suitable and unsuitable conditions, observable switch signals, a syntax-valid example, and an advanced column.

This raises the published method-guide baseline to 66. It still does not require every registered method to have the same amount of prose or a visualization.

## Default-method pilot

Issue #111 adds a dedicated Trust Region Reflective guide because it is selected implicitly by a high-use SciPy API. This raises the published method-guide baseline to 67 while keeping library defaults separate from recommendation priority.

## Audit report

`scripts/method_content_density_report.py` generates [`method-content-density-report.md`](method-content-density-report.md) from the authored Markdown tree. The report records summary length, body length, table-of-contents entries, Python blocks, and syntax status for every published method guide.

After the second beginner method tranche, all 66 published method guides must meet the Level 2 floor. This does not imply that all 98 registered methods have full guides; it makes the remaining content gap measurable and prevents already-published guides from becoming visibly empty again.

The same canonical export rebuilds search and retrieval documents, so added explanations become available through human search and future external retrieval without a second hand-maintained corpus. `search-index.json` uses deterministic compact JSON serialization to preserve its 2 MiB browser asset budget without removing searchable fields; human-oriented generated reports remain pretty-printed.

## Review checklist

- The first paragraph exactly matches frontmatter `summary`.
- `method_id` and every `source_id` resolve to canonical data.
- Each source directly supports the page claim; an adjacent method's paper is not used as a substitute merely because it is in the same family.
- Local and global claims are distinguished.
- Heuristic results are not described as certificates.
- Method theory and implementation behavior are not conflated.
- Unknown facts remain explicit.
- Examples are syntactically valid and clearly scoped as educational or executable.
- Comparison claims state budget, initialization, seed, tolerance, and implementation context.
- Family guides describe conditional roles rather than a universal ranking.
- Beginner-first method guides explain what is observed, what is updated, and which diagnostic triggers a switch.
- Generated site data is regenerated from the latest validated database and content tree.
