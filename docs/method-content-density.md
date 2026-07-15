# Method content density

Optimization Compass separates structured method facts from human-facing educational prose.

## Authority

- `methods` and related canonical tables own stable IDs, short summaries, assumptions, capabilities, implementations, sources, and relations.
- `content/methods/*.md` owns explanatory prose, mathematics, examples, interpretation, and teaching order.
- generated `content.json`, `entity-links.json`, and Coverage assets are exporter outputs and must not be edited by hand.

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

## Initial expanded tranche

Issue #87 raises coverage across:

- smooth local and curvature methods
- composite / nonsmooth convex methods
- population and derivative-free methods
- structure-first discrete algorithms
- LP / MILP algorithms
- trajectory optimization

The tranche adds guides for BFGS, L-BFGS-B, Newton, trust-region Newton-CG, ADMM, proximal gradient, FISTA, differential evolution, genetic algorithms, particle swarm optimization, MADS, dynamic programming, Dijkstra / A*, branch-and-cut, dual simplex, and direct collocation.

## Review checklist

- The first paragraph exactly matches frontmatter `summary`.
- `method_id` and every `source_id` resolve to canonical data.
- Local and global claims are distinguished.
- Heuristic results are not described as certificates.
- Method theory and implementation behavior are not conflated.
- Unknown facts remain explicit.
- Examples are syntactically valid and clearly scoped as educational or executable.
- Comparison claims state budget, initialization, seed, tolerance, and implementation context.
- Generated site data is regenerated from the latest validated database and content tree.
