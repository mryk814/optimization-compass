# Issue #140 method, implementation, and source backlog

Reviewed: 2026-07-19

## Audit result

The released canonical database was searched before adding the Issue #140 Theater and Compare slice.
No method or implementation name currently resolves to a dedicated bilevel, MPEC,
complementarity, equilibrium, contact, friction, or hybrid solver. Existing IDs such as
`M_SLSQP`, `M_INTERIOR_POINT_NLP`, `M_DIRECT_COLLOCATION`, `I_SCIPY_SLSQP`, and `I_IPOPT`
describe reusable ordinary NLP or optimal-control machinery; this work does not repurpose them
as dedicated nested or contact methods.

The source catalog likewise has no dedicated primary record for bilevel differentiation, MPEC
stationarity/regularization, contact-implicit trajectory optimization, or mode-discovery methods.
The executable slice therefore reuses only already-cataloged background sources and labels every
trace as a deterministic teaching ledger, not a solver execution. It adds canonical problem
definition and instance IDs for the fixed bilevel and hybrid lessons, plus one exact benchmark
context for the bilevel contrast. It does not add or repurpose method, implementation, or source
IDs, and it introduces no schema field or renderer family.

## Candidate canonical additions

| Priority | Candidate | Needed authority | Primary source to review | Acceptance boundary |
| --- | --- | --- | --- | --- |
| 1 | implicit differentiation through a converged inner solution map | method, implementation mapping, sources, evidence | Franceschi et al., 2018, [PMLR 80](https://proceedings.mlr.press/v80/franceschi18a.html); Lorraine et al., 2020, [PMLR 108](https://proceedings.mlr.press/v108/lorraine20a.html); Ji et al., 2021, [PMLR 139](https://proceedings.mlr.press/v139/ji21c.html) | Separate solution-map differentiation from differentiating a finite solver trace; record inner accuracy and regularity assumptions. |
| 2 | MPEC stationarity and relaxation | method/family vocabulary, sources, evidence | Scheel and Scholtes, 2000, [doi:10.1287/moor.25.1.1.15213](https://doi.org/10.1287/moor.25.1.1.15213); Scholtes, 2001, [doi:10.1137/S1052623499361233](https://doi.org/10.1137/S1052623499361233) | Name the stationarity notion and constraint-qualification assumptions; finite relaxation must not be presented as exact complementarity. |
| 3 | hyperparameter optimization with active-set sensitivity | method, implementation, source, executable case | Bertrand et al., 2020, [PMLR 119](https://proceedings.mlr.press/v119/bertrand20a.html) | Record active-set changes and gradient-check policy rather than claiming a globally smooth solution map. |
| 4 | contact-implicit trajectory optimization | method, implementation, problem instance, source, executable artifact | Posa, Cantu, and Tedrake, 2014, [doi:10.1177/0278364913506757](https://doi.org/10.1177/0278364913506757) | Model gap, normal force, friction cone, complementarity residual, discretization, and contact-mode semantics explicitly. |

## Deferred contracts

The existing `generic_metric_history` renderer honestly supports outer/inner residual histories and
a synthetic chattering ledger. A dedicated nested-solve timeline, contact-state renderer, physical
contact model, or hybrid solver trace would require a reviewed scenario/artifact contract and is
outside this closure slice. Contact/friction remains a named, source-backed backlog item rather than
being simulated with labels on an ordinary NLP trace.
