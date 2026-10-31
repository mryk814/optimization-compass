# Practical blind spots in solving optimization problems

- Status: research backlog
- Date: 2026-10-30
- First article: [`content/concepts/solver-evaluation-points.md`](../../content/concepts/solver-evaluation-points.md)

Beginners who solve a real problem often meet failures that no formulation or method article
explains: the objective is numerically rough although it is smooth in theory, a constraint was
never written because it lives inside a simulator, or a solver evaluates points the user never
expected. This document inventories those blind spots, records which ones the canonical failure
mode catalog (`failure_modes`, FM001–FM042, and `diagnostics`, D001–D042) already covers, and
fixes how they enter the Atlas.

It is a planning document, not canonical knowledge. Facts marked *unverified* must be checked
against an official source before an article or a migration states them.

## Where the blind spots live

The inventory is grouped by the layer the reader has to inspect. "Existing" names the FM row that
already covers the item; *none* means the catalog has no row for it.

### Inside the objective

| Blind spot | Symptom a beginner sees | Existing |
|---|---|---|
| Computational noise: an inner iterative solver, adaptive steps, or remeshing makes a deterministic objective jagged | BFGS stops with "precision loss"; a finite-difference gradient changes with the step | none (FM003 covers stochastic noise only) |
| Cancellation and rounding: differences of large values, float32, a large objective offset | progress stalls; `ftol` never triggers | part of FM024 |
| Rounding, table interpolation, or `if` branches inside the model | zero gradient and an immediate stop; staircase values | part of FM018, PA012 |
| Stateful objective: globals, warm start from the previous call, caches | the same x returns different values; results depend on call order | FM042 (nested solves only) |
| The objective mutates x, or returns the wrong type or shape | unexplained divergence | none |

### Constraints and domain

| Blind spot | Symptom | Existing |
|---|---|---|
| Hidden constraints: infeasibility known only after running the simulation | NaN, exceptions | FM004, FM005, PA016 |
| Unwritten domain: log, sqrt, division, quantities that cannot be negative | NaN in the middle of a run, often together with out-of-range evaluation points | part of FM004 |
| A forgotten constraint makes the problem unbounded or trivial | the solution is 0 or infinite; `unbounded` status | none |
| The optimizer exploits the validity range of a fitted or surrogate model (optimizer's curse) | the prediction is excellent, the real system is not | part of FM034 |
| Constraint tolerance and units: kN versus N changes what "feasible" means | reported feasible, fails on the real system | part of FM015 |
| A sharp optimum on a constraint boundary | a small perturbation violates the constraint | none |

### Solver implementation

| Blind spot | Symptom | Existing |
|---|---|---|
| Hidden evaluations: finite differences cost n to 2n calls per gradient, line-search trials, `fun` and `jac` called separately | ten times slower than expected; `nit` and `nfev` differ widely | part of FM023 |
| Only iterates honor bounds: difference points, line-search trials, interior-point bound relaxation, infeasible SQP or penalty iterates, out-of-bound samples in evolutionary methods | NaN at an x that "must" be inside the range | none |
| Defaults that depend on the start or the scale: the Nelder–Mead initial simplex, absolute finite-difference steps | variables of a different scale never move | part of FM007 |
| Internal variable transforms for bounds (for example a sine transform) | vanishing gradient near a bound; distorted covariance | none |
| Default `maxiter` or tolerances stop the run quietly | `success=False` is never read | FM025 |

Reading the result (FM015, FM016, FM025, FM038) is already covered and is out of scope here.

## Decision: three cross-cutting articles with one running example

The blind spots cut across formulations and methods, so they do not fit the formulation or
method skeleton. They enter as three concept articles, one per layer, that share one running
example: estimating the outlet area `a` [m^2] and inflow `q` [m^3/s] of a tank from 31 water-level
readings, by solving `dh/dt = q - a sqrt(2 g h)` with `solve_ivp` and minimizing the sum of
squared differences. The tool fails when the tank runs dry within the 30 minutes. The example
replaced an earlier steel heat-treatment example (2026-10-31) because parameter estimation of an
ODE model is something most readers in science, engineering and data analysis meet, and because
each trap appears without being staged:

- the start `a = q = 1e-4` is physically valid, yet solvers pass impossible or uncomputable points;
- `a` and `q` are about `1e-4`, so a unit step in the raw variables is ten thousand times the value;
- the default `solve_ivp` tolerance `rtol=1e-3` makes the objective rough at small scales;
- the real constraint, "the tank does not run dry", couples `a` and `q` and is not a bound.

Each article peels one layer off the same example, and every article uses the same evaluation
recorder (a wrapper that stores each x passed to the objective), which also connects to the
evaluation ledger in `concept.evaluation-cost`.

| Order | Article | What the running example shows (SciPy 1.18.1) |
|---|---|---|
| 1 | `concept.solver-evaluation-points`: where and how often a solver evaluates (published) | `minimize(f, x0)` passes `(0.979, -0.248)` on its 4th call; `fmin` passes negative `q` from its 13th call and fails on its 15th; bounds `[0, 0.01]` make L-BFGS-B pass the corner `(0.01, 0)` and fail; with bounds `[1e-5, 1e-3]` L-BFGS-B makes 102 calls in 11 iterations, while Nelder–Mead reports success at a point whose fit is 150 times worse because its clipped simplex collapsed onto `q = 1e-5` |
| 2 | Written constraints versus real constraints (planned) | negative inflow is evaluated silently; the run-dry condition couples `a` and `q`; `q > 0` keeps the level above `(q/a)^2/(2g)`; handling a failure as a state instead of a large value |
| 3 | Is the objective really smooth? (planned) | `rtol=1e-3` versus `rtol=1e-8`: L-BFGS-B needs 102 versus 51 evaluations, and its last 12 gradient points sit at the same 3-digit answer |

## Follow-up work

1. **Failure-mode catalog.** Add rows for the items marked *none* above, starting with
   computational noise, out-of-range evaluation points, hidden evaluation counts, and unbounded or
   trivial solutions. This is a dataset migration (high risk) and goes in its own pull request.
2. **Learning path.** A symptom-first path ("it stopped, but is it optimal?", "the evaluation count
   is not what I expected", "NaN inside the range") that orders existing articles and the three new
   ones.
3. **Explorables.** Candidates: the finite-difference error V-curve with added computational noise
   (the minimum becomes shallower and moves to a larger step); an evaluation-point scatter where
   difference points and line-search trials appear outside the bounds.
4. **Diagnose.** Questions such as "does the objective contain an inner solver or adaptive steps?"
   change recommendation behavior (critical) and come last, after the articles and catalog rows.

## Unverified candidates

These were raised during the inventory and need an official source before use.

- Ipopt relaxes variable bounds by a small default factor (`bound_relax_factor`) and projects only
  the final point back into the original bounds (`honor_original_bounds`), so intermediate
  evaluations can lie slightly outside the bounds. Source to check: the Ipopt options reference
  (S017).
- Libraries that implement bounds by a variable transform, such as the sine transform used by
  some least-squares fitting packages.
- Primary sources to add to the source catalog for articles 2 and 3: Moré and Wild, "Estimating
  Computational Noise" (SIAM J. Sci. Comput., 2011); Le Digabel and Wild's taxonomy of constraints
  in simulation-based optimization; Smith and Winkler, "The Optimizer's Curse" (Management
  Science, 2006). Adding a source is a dataset change and follows the source-evidence recipe.
