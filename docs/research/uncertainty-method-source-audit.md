# Optimization under uncertainty: canonical method and source audit

**Issue:** #139  
**Audited:** 2026-07-19  
**Scope:** robust, stochastic, chance-constrained, CVaR, and distributionally robust optimization

This audit records what the Atlas can publish through the current content and visualization contracts,
and what still needs a dataset release. It is a backlog, not a substitute for canonical method or source
records.

## Current authority boundary

The published Atlas has two feature-backed concept pages, the `portfolio-cvar-allocation` Case, and the
`MF_LP_QP_CONIC` / `I_CVXPY` route needed to explain the fixed finite-scenario formulation. It does not
have dedicated canonical method IDs for robust optimization, two- or multistage stochastic programming,
sample-average approximation, chance-constrained optimization, CVaR optimization, or DRO.

The 0.18.8 release slice stages `S103`, the original Rockafellar–Uryasev CVaR paper, for the CVaR
representation used by the Case. The catalog still has no primary sources for robust optimization,
SAA, chance-constraint guarantees, two-/multistage stochastic programming, or DRO. `S054` is a general
problem-type guide; `S055` and `S056` are broad textbooks and should not be presented as direct evidence
for those missing guarantee claims.

Adding the missing method or source records changes the released SQLite authority. Do that in a versioned dataset migration and release PR, not in an ordinary content journey.

## Canonical method backlog

| Priority | Proposed scope | Keep distinct from | Minimum canonical claims before publication | Candidate implementation evidence |
| --- | --- | --- | --- | --- |
| P0 | CVaR risk formulation / epigraph | chance constraint; worst-case objective | loss direction, tail level, sample weights, objective versus constraint placement, finite-sample claim scope | CVXPY official examples and supported cone/linear forms; solver-specific support recorded separately |
| P0 | sample-average approximation / finite scenarios | stochastic gradient; scenario feasibility guarantee | sampling law, weighting, seed, train/evaluation split, convergence assumptions, stopping policy | Pyomo or JuMP stochastic-programming examples only after official support is verified |
| P1 | robust optimization | DRO; chance constraints | uncertainty-set element, geometry, radius/budget, robust-feasibility scope, counterpart/reformulation assumptions | modeling-system support must identify uncertainty-set and reformulation behavior |
| P1 | chance-constrained optimization | empirical scenario satisfaction; CVaR objective | violation event, probability target, confidence statement, distribution assumptions, approximation and sample-size conditions | implementation must report whether the chance constraint is native, approximated, or user reformulated |
| P1 | two-stage stochastic programming | a flat scenario objective | first-stage variables, recourse variables, nonanticipativity, scenario tree/probabilities, decomposition assumptions | Pyomo/JuMP/PySP-like support requires current official documentation |
| P2 | multistage stochastic programming | MPC disturbance replay | information filtration, nonanticipativity, policy representation, stagewise assumptions, scenario-tree reduction | record modeling and algorithm support independently |
| P2 | distributionally robust optimization | parameter uncertainty set | ambiguity-set elements, distance/divergence, radius calibration, tractable reformulation assumptions, out-of-sample theorem conditions | package support must name ambiguity family and supported reformulation |

`robust`, `stochastic`, `chance`, and `DRO` are formulations or modeling families. CVaR is a risk
measure that can occur in an objective or constraint. SAA is an approximation/estimation procedure.
They should not be forced into one flat method ranking.

## Primary-source backlog

Each candidate source needs a new source ID, supported-claim text, quality/currentness metadata, and
claim-level relations in the dataset release that introduces it.

| Claim family | Primary source candidate | What it may support | What it does not support by itself |
| --- | --- | --- | --- |
| CVaR representation | `S103` (staged): Rockafellar and Uryasev, [*Optimization of Conditional Value-at-Risk*](https://uryasev.ams.stonybrook.edu/wp-content/uploads/2019/03/optimization_cvar.pdf) | CVaR optimization representation and portfolio motivation | arbitrary out-of-sample superiority of a CVaR portfolio |
| SAA | Kleywegt, Shapiro, and Homem-de-Mello, [*The Sample Average Approximation Method for Stochastic Discrete Optimization*](https://doi.org/10.1137/S1052623499363220) | sample-average construction, convergence/complexity under stated assumptions | a guarantee for the Atlas fixed 8/4 sample |
| scenario feasibility | Campi and Garatti, [*The Exact Feasibility of Randomized Solutions of Uncertain Convex Programs*](https://doi.org/10.1137/07069821X) | scenario-program feasibility results under the paper's convexity and sampling conditions | treating any finite scenario count as a distribution-free chance guarantee |
| robust optimization | Bertsimas and Sim, [*The Price of Robustness*](https://doi.org/10.1287/opre.1030.0065) | budgeted uncertainty and a tractable robust counterpart in the paper's setting | all uncertainty-set geometries or distributional robustness |
| Wasserstein DRO | Mohajerin Esfahani and Kuhn, [*Data-driven Distributionally Robust Optimization Using the Wasserstein Metric*](https://doi.org/10.1007/s10107-017-1172-1) | Wasserstein ambiguity sets, tractable reformulations, and stated finite-sample results | other ambiguity families or guarantees without the theorem assumptions |
| two-/multistage modeling | Birge and Louveaux, [*Introduction to Stochastic Programming*](https://doi.org/10.1007/978-1-4614-0237-4) | recourse, scenario trees, nonanticipativity, and sampling background | implementation-version claims |

## Implemented journey contract

The `portfolio-cvar-allocation` journey deliberately stays narrower than the backlog:

- one four-asset capped simplex;
- eight fixed training returns and four disjoint fixed held-out returns;
- a nominal mean-loss objective and a mean-plus-CVaR objective;
- the same scenario order, uniform weights, tail level `0.75`, decision grid, and 12 loss evaluations;
- a `contrast_only` Compare with ranking disabled;
- mean loss, empirical CVaR, worst loss, and best loss reported separately for training and held-out;
- no chance constraint, robust-feasibility, population-risk, confidence-interval, or DRO claim.

The `0.75` value is a CVaR tail/quantile level. It is not a statistical confidence level. The comparison's
confidence target is explicitly `not_applicable` because this fixed teaching contrast does not make a
probabilistic guarantee.

## Visualization and comparison requirements

The current journey uses `AlgorithmTrace` plus `generic_metric_history`; no new renderer family or schema
is required. The two frames that contain results are synchronized at eight and twelve loss evaluations:
training first, then held-out. Individual fixed losses remain in each trace frame payload while the UI reads
the four shared summaries.

Future scenario-cloud, tail-highlight, efficient-frontier, uncertainty-set-growth, or confidence-sensitivity
views should not be simulated with unrelated renderer semantics. Promote a new renderer contract only
after its observables, static alternative, comparison synchronization, and responsive behavior are specified.

Any future Compare must align, or explicitly mark as not comparable:

- uncertainty source and uncertainty model;
- train/evaluation sample generation, weights, order, and seed;
- risk or violation target and its mathematical definition;
- confidence target and theorem assumptions, when a confidence statement is made;
- objective, constraints, feasible set, and decision representation;
- oracle, sample, compute, and wall-clock budgets;
- implementation versions, tolerance, stopping, and tuning policy.

## Statistical-claim gate

Before publishing a statistical or guarantee claim, the PR should answer all of the following:

1. Is the displayed value in-sample, held-out empirical, or a population quantity?
2. Is `alpha` a violation probability, a quantile/tail level, or a confidence level?
3. What sampling, independence, stationarity, convexity, and support assumptions are required?
4. Does the cited theorem apply to the implemented formulation and sample policy?
5. Is the confidence statement simultaneous or pointwise, and what is its evaluation unit?
6. Were model/tuning choices frozen before the held-out data were inspected?
7. Are uncertainty-set and ambiguity-set radii defined and calibrated?
8. Are empirical feasibility, probabilistic feasibility, and robust feasibility named separately?

If these answers are missing, use empirical language only: “on these fixed scenarios,” not “with 95%
confidence,” “safe,” “robust,” or “guaranteed.”

## Simplex and manifold link

The Case's decision domain is the closed capped simplex, so exact zero weights and boundary solutions are
valid. A strict-simplex/softmax or multinomial-manifold representation excludes exact zeros and changes the
numerical problem. Keep the [Simplex concept](../../content/concepts/simplex.md) as the representation
authority; do not attribute uncertainty guarantees to the choice of simplex coordinates.
