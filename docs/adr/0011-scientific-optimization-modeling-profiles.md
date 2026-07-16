# ADR 0011: Scientific optimization uses explicit modeling profiles and scoped feasibility claims

- Status: proposed
- Date: 2026-07-16
- Issue: #132

## Context

Optimization Compass already distinguishes methods, implementations, problem archetypes, problem
instances, Gallery cases, scenarios, comparisons, sources, and generated artifacts. That model works
well for ordinary finite-dimensional examples, but future scientific and engineering cases introduce
several independent structures that cannot be represented safely by one `variable_domain` or
`constraint_class` field:

- the optimized object may be a vector, field, shape, trajectory, distribution, graph, or matrix;
- the object may live in Euclidean space, a simplex, `SO(3)`, `SE(3)`, a Stiefel manifold, the SPD cone,
  a fixed-rank set, or a mixed discrete/continuous product;
- evaluating an objective may require an algebraic model, ODE, DAE, PDE, FEM/CFD solve, simulator,
  nested optimization, equilibrium solve, or physical experiment;
- derivatives may come from an analytic formula, automatic differentiation, direct sensitivities,
  adjoints, finite differences, a surrogate, or may be unavailable;
- feasibility may hold for every accepted iterate, only for a discretized model, only at convergence,
  after reconstruction, approximately, or with a probabilistic statement.

Compressing those distinctions into domain labels such as `CFD`, `robotics`, or `topology` would make
Diagnose less reusable and would encourage misleading claims. For example, a direct-collocation
solution can satisfy the collocation equations to tolerance while still requiring mesh refinement to
support a continuous-time accuracy claim. A density-based topology optimization solution can satisfy
its volume constraint while remaining a continuous material-density relaxation rather than a binary
layout. An `SO(3)` update may stay on the rotation group by construction, whereas a penalty formulation
may leave the group during optimization and only approach it at convergence.

The Atlas therefore needs a shared modeling vocabulary before domain-specific cases are added.

## Decision

Introduce a **scientific modeling profile** as a separate conceptual layer attached to a canonical
problem definition, problem instance, or Gallery case. A modeling profile does not replace the existing
problem archetype and does not duplicate method or implementation facts. It describes how a particular
problem is represented and evaluated.

The profile is composed from controlled vocabularies along six independent axes:

1. decision objects and variable roles;
2. feasible-set geometry and numerical representation;
3. state/evaluation models;
4. derivative routes;
5. constraint scopes and enforcement strategies;
6. discretization, evaluation regime, and guarantee scope.

The first implementation should use a versioned, Pydantic-validated profile envelope rather than add
many columns to `problem_archetypes`, `methods`, or Gallery rows. Relation-heavy concepts may later be
normalized into dedicated tables after at least two flagship journeys have exercised the contract.

## Entity boundaries

### Problem archetype

Owns the broad mathematical problem family and reusable classification already used by Diagnose and
recommendation rules. It does not own a specific mesh, trajectory transcription, simulator, or
manifold representation.

### Problem definition and problem instance

Own the mathematical family and a reproducible instance. A problem instance may reference one
modeling profile that states its variables, state model, discretization, and known-reference semantics.

### Gallery case

Owns the real-world question, practical assumptions, candidate/conditional/excluded methods, and the
learning journey. A Gallery case may reuse the instance profile or add case-level facts such as an
expensive external experiment, a safety requirement, or unavailable derivatives.

### Method and implementation

Own algorithm theory and concrete API/library behavior respectively. They may declare compatibility
with modeling vocabulary, but they do not redefine the problem profile.

### Scenario and comparison

Own a fixed educational run and a fair comparison. They record the exact profile, discretization,
budget, and feasibility claims used by that run. They must not imply broader guarantees than their
problem instance supports.

## Controlled vocabulary

### 1. Decision object kind

The decision object answers **what is being chosen**, not merely the scalar storage type.

Initial values:

- `scalar`
- `vector`
- `matrix`
- `tensor`
- `field`
- `shape`
- `domain`
- `trajectory`
- `control_policy`
- `probability_distribution`
- `graph`
- `set`
- `mixed_product`

Each variable also has a role:

- `design`
- `control`
- `state`
- `parameter`
- `uncertainty`
- `auxiliary`
- `slack`
- `dual`

State variables are not automatically decision variables. Reduced-space formulations may eliminate the
state through a solver, while full-space formulations may optimize design and state together.

### 2. Feasible-set geometry

The feasible set answers **where a variable is allowed to live**. It is distinct from the chosen
coordinates or parametrization.

Initial values:

- `euclidean`
- `box`
- `integer_lattice`
- `binary_hypercube`
- `categorical_product`
- `permutation`
- `simplex_closed`
- `simplex_interior`
- `sphere`
- `stiefel`
- `grassmann`
- `SO2`
- `SO3`
- `SE2`
- `SE3`
- `SPD`
- `PSD_fixed_rank`
- `low_rank_fixed`
- `function_space`
- `shape_space`
- `mixed_product`
- `other_structured`
- `unknown`

Representation is stored separately, for example:

- rotation matrix, unit quaternion, Lie-algebra coordinates;
- direct simplex coordinates, softmax/log-ratio coordinates;
- Cholesky factor, matrix exponential, or direct SPD matrix;
- voxel density, finite-element coefficients, level set, spline, CAD parameters;
- knot values, shooting controls, collocation polynomials.

This separation is required because representations have different singularities, boundary access, and
feasibility behavior even when they describe the same mathematical set.

### 3. State/evaluation model

The state model answers **what must be solved or executed to evaluate the objective and constraints**.

Initial values:

- `closed_form`
- `algebraic_system`
- `linear_system`
- `eigenproblem`
- `ODE`
- `DAE`
- `elliptic_PDE`
- `parabolic_PDE`
- `hyperbolic_PDE`
- `steady_multiphysics`
- `transient_multiphysics`
- `rigid_body_simulator`
- `contact_simulator`
- `stochastic_simulator`
- `nested_optimization`
- `equilibrium_problem`
- `physical_experiment`
- `surrogate_only`
- `none`
- `unknown`

Additional controlled fields describe:

- formulation: `reduced_space`, `full_space`, `simultaneous`, `black_box`;
- time structure: `static`, `steady`, `transient`, `periodic`, `multi_stage`;
- coupling: `none`, `one_way`, `two_way`, `multidisciplinary`, `multiphysics`;
- solve status: deterministic, stochastic, failure-prone, timeout-prone, or unknown.

### 4. Derivative route

Derivative availability is recorded per target relation rather than as one global boolean. A problem may
have an analytic objective gradient but only finite-difference constraint sensitivities.

Initial routes:

- `analytic`
- `automatic_differentiation`
- `direct_sensitivity`
- `continuous_adjoint`
- `discrete_adjoint`
- `implicit_differentiation`
- `finite_difference`
- `complex_step`
- `stochastic_estimator`
- `surrogate_gradient`
- `subgradient`
- `unavailable`
- `unknown`

The profile records derivative target (`objective`, `constraint`, `state`, `inner_solution`), fidelity,
approximation status, and cost relative to a state evaluation.

### 5. Constraint scope

Constraint scope answers **what the condition acts on**:

- `design`
- `state`
- `control`
- `path`
- `initial`
- `terminal`
- `boundary`
- `integral`
- `pointwise_field`
- `global_aggregate`
- `chance`
- `robust`
- `complementarity`
- `equilibrium`
- `topology_manufacturing`
- `geometry_validity`
- `mesh_quality`

Enforcement strategy is separate:

- `elimination`
- `parametrization`
- `projection`
- `normalization`
- `retraction`
- `exact_subproblem`
- `active_set`
- `barrier`
- `augmented_lagrangian`
- `penalty`
- `repair`
- `relaxation`
- `scenario_approximation`
- `sampling_estimate`
- `unknown`

### 6. Discretization and evaluation regime

Discretization values include:

- `none`
- `finite_difference_grid`
- `finite_element_mesh`
- `finite_volume_mesh`
- `spectral`
- `voxel`
- `particle`
- `boundary_element`
- `shooting`
- `multiple_shooting`
- `direct_transcription`
- `collocation`
- `pseudospectral`
- `time_stepping`
- `CAD_parameterization`
- `level_set_grid`
- `sample_average`
- `scenario_set`
- `other`

Evaluation regime records:

- cost class and optional unit-normalized cost;
- serial, batch-parallel, asynchronous, distributed, or real-time policy;
- noise and repeatability;
- failure, timeout, censoring, and retry behavior;
- single, discrete multi-fidelity, or continuous-fidelity levels;
- state, derivative, and high-fidelity-equivalent evaluation counts.

## Feasibility semantics

A single `feasible: true` field is prohibited for scientific profiles. A feasibility claim is a scoped
statement with four required dimensions.

### Point scope

- `all_evaluated_points`
- `accepted_iterates`
- `reported_solution`
- `reconstructed_trajectory`
- `sampled_scenarios`

### Model scope

- `authored_mathematical_model`
- `relaxed_model`
- `discretized_model`
- `reconstructed_continuous_model`
- `physical_system`
- `statistical_population`

### Strength

- `exact_by_representation`
- `exact_by_elimination`
- `enforced_to_tolerance`
- `asymptotic_under_refinement`
- `probabilistic_under_assumptions`
- `empirical_only`
- `heuristic`
- `unknown`
- `not_applicable`

### Evidence context

Every nontrivial claim states, where applicable:

- tolerance and norm;
- discretization or sample size;
- confidence level and assumptions;
- solver termination/status mapping;
- reconstruction or validation procedure;
- source IDs and last verified date.

Product-facing labels may summarize these claims, but the underlying scope must remain available.

Examples:

- A Lie-group update on `SO(3)` may claim `accepted_iterates` × `authored_mathematical_model` ×
  `exact_by_representation`.
- A unit quaternion parametrization may preserve unit norm while still requiring a separate note that
  `q` and `-q` represent the same rotation.
- Softmax coordinates may claim membership in `simplex_interior`, not access to the closed-simplex
  boundary or exact zero components.
- Cholesky coordinates may claim SPD membership, not arbitrary PSD boundary access.
- Direct collocation may claim `reported_solution` × `discretized_model` × `enforced_to_tolerance`;
  a continuous-time claim requires reconstruction and error/refinement evidence.
- SIMP may satisfy a volume constraint on the discretized relaxed problem while the binary topology
  interpretation remains a relaxation/continuation claim.
- A scenario approximation may report empirical scenario satisfaction; a chance-constraint guarantee
  requires its statistical assumptions and confidence statement.

## Representative mappings

| Case | Decision object / space | State model | Derivative route | Key constraint scope | Feasibility statement |
|---|---|---|---|---|---|
| Existing constrained design | vector / Euclidean box | closed form | analytic | design nonlinear inequality | converged solution to tolerance |
| Existing nonlinear parameter estimation | parameter vector / box | residual model | Jacobian / finite difference | design bounds | accepted iterates may stay within bounds; local stationarity only |
| Existing HPO case | mixed vector / product bounds | external experiment or black box | unavailable / surrogate | resource and box constraints | evaluated configurations only; noisy empirical result |
| Existing binary allocation | binary vector | algebraic model | not applicable | budget and logic | reported integer solution; certificate depends on solver status |
| Cantilever topology | density field / box-relaxed field | linear-elastic FEM | discrete adjoint | volume, optional manufacturing | discretized relaxed problem; binary interpretation requires projection/continuation |
| Rotation averaging | rotations / `SO(3)^n` | algebraic residual graph | analytic or AD on manifold | group membership | representation-dependent iterate feasibility; local/global claim stated separately |
| Robot-arm direct collocation | state/control trajectories | nonlinear ODE | AD or analytic Jacobians | dynamics, path, boundary | collocation constraints to tolerance; continuous path requires refinement checks |
| Expensive multi-fidelity simulator | vector / box or mixed product | simulator hierarchy | surrogate / unavailable | black-box feasibility | observed and modeled feasibility separated; failures/censoring explicit |
| Shape optimization | shape/domain | PDE/CFD/FEM | shape derivative / adjoint | geometry, mesh, state | mesh/discrete feasibility separated from geometry and physical-model validity |
| CVaR allocation | simplex vector | scenario loss model | analytic/subgradient | simplex and risk | finite-sample optimization distinguished from population risk statement |

## Candidate Diagnose questions

Diagnose should ask about computational and mathematical bottlenecks rather than domain names.

1. What is being chosen: a finite vector, field, shape, trajectory, matrix, distribution, graph, or mixed object?
2. Does the variable have geometry that a naive Euclidean update would violate?
3. Does each evaluation require solving an ODE, DAE, PDE, simulator, nested optimization, equilibrium, or experiment?
4. Can that state solve fail, time out, or return censored/invalid values?
5. Which derivatives are available, for which outputs, and at what relative cost?
6. Is the design dimension small, large, field-scale, sparse, distributed, or unknown?
7. Are constraints on design variables, states, paths, terminal values, boundaries, integrals, uncertainty, or complementarity?
8. Must accepted iterates remain feasible, or is feasibility at convergence sufficient?
9. Is the guarantee about a discretized model, reconstructed continuous model, physical system, or probability distribution?
10. Is one evaluation cheap, expensive, noisy, batchable, multi-fidelity, real-time, or failure-prone?
11. Is the problem solved once, repeatedly with warm starts, online, or as part of a control loop?
12. Is a local stationary point sufficient, or is a bound, certificate, safety invariant, Pareto set, or statistical guarantee required?

`unknown` must remain an answer for every question whose value has not been established. Questions that do
not apply to a profile use `not_applicable`; known but unsupported Atlas capabilities use `unsupported`.

## Validation rules

A future profile validator must reject or report:

- duplicate profile and variable IDs;
- unknown controlled-vocabulary values;
- references to missing problem, case, source, implementation, or scenario IDs;
- a state variable marked as eliminated while also declared as an independent decision variable without
  an explicit simultaneous/full-space formulation;
- derivative claims without target, route, source, and approximation status;
- feasibility claims missing point scope, model scope, or strength;
- continuous/physical guarantees inferred only from a discretized termination status;
- `exact_by_representation` without an identified representation and preserved set;
- chance/probabilistic claims without assumptions, sample/confidence context, or explicit unknowns;
- ranking-eligible comparisons whose members use incompatible model scopes, fidelities, budgets, or
  feasibility interpretations;
- scenarios that omit discretization, state-solve, or reconstruction limitations relevant to the lesson;
- blank values used to imply `unknown`, `not_applicable`, or `unsupported`.

Warnings should report representation singularities, non-uniqueness, inaccessible boundaries, mesh or
sample dependence, and missing refinement/held-out validation without automatically rejecting draft
research profiles.

## Migration plan

### Phase 0 — documentation and mapping

Adopt this ADR, map current and proposed flagship cases, and identify vocabulary collisions. No schema or
release change is required.

### Phase 1 — validated profile envelope

Add a versioned `ProblemModelingProfile` Pydantic model and an authoring seed/catalog. Profiles reference
existing problem definitions, instances, cases, and sources. Export a machine-readable profile index for
Coverage and research use, but do not alter recommendation behavior.

A profile envelope should initially own nested variable, state-model, derivative, constraint, evaluation,
and feasibility records. This limits premature schema proliferation while keeping every field validated.

### Phase 2 — two flagship pilots

Use one field/PDE case and one manifold or trajectory case to test the contract. Recommended pilots are:

- cantilever minimum-compliance topology optimization;
- rotation averaging on `SO(3)` or robot-arm direct collocation.

Only after both profiles are expressible should relation-heavy concepts be normalized.

### Phase 3 — normalized query surfaces

Normalize stable, reusable vocabularies and many-to-many relations into SQLite tables where SQL/API
queries, Diagnose, comparison eligibility, or Coverage require them. Keep representation-specific
configuration in versioned JSON where normalization would create sparse, unstable columns.

### Phase 4 — Diagnose and Coverage integration

Add bottleneck-oriented questions, profile completeness dimensions, and validation. Recommendation
rules may consume profile predicates only after explicit regression cases demonstrate unchanged or
intended behavior.

## Consequences

- Scientific applications can share one vocabulary without pretending that domains are equivalent.
- Constraint geometry, simulation dependency, discretization, and guarantee scope remain independently
  queryable.
- The Atlas can explain why two apparently similar optimization problems require different methods.
- Case, Theater, Compare, and Coverage can expose modeling limitations rather than only final objective
  values.
- The initial cost is a new profile contract and more explicit unknown states.
- The design deliberately postpones a large database migration until representative cases prove which
  relationships require normalization.

## Primary and official references

- DTU TopOpt Apps/Software, educational minimum-compliance, level-set, large-scale, buckling, and
  photonics examples: https://www.topopt.mek.dtu.dk/apps-and-software
- Ferrari and Sigmund, *A new generation 99 line Matlab code for compliance Topology Optimization and
  its extension to 3D*: https://arxiv.org/abs/2005.05436
- Manopt official manifold catalog, including sphere, Stiefel, rotations, `SE(n)`, fixed-rank, SPD, and
  simplex-like manifolds: https://www.manopt.org/manifolds.html
- MIT Underactuated Robotics, trajectory optimization and direct collocation:
  https://underactuated.mit.edu/trajopt.html
- MOOSE Optimization Module, PDE-constrained optimization through PETSc/TAO:
  https://mooseframework.inl.gov/modules/optimization/
- Blauth, *cashocs: A Computational, Adjoint-Based Shape Optimization and Optimal Control Software*:
  https://arxiv.org/abs/2010.02048
- Blauth, *cashocs 2.0*, including space mapping, level-set topology optimization, state constraints,
  and MPI: https://arxiv.org/abs/2306.09828
- Balandat et al., *BoTorch: A Framework for Efficient Monte-Carlo Bayesian Optimization*:
  https://arxiv.org/abs/1910.06403
- Dellaert et al., *Shonan Rotation Averaging: Global Optimality by Surfing SO(p)^n*:
  https://arxiv.org/abs/2008.02737
- PowerModels official documentation, separating power-network problem specifications from AC/DC and
  relaxation formulations: https://lanl-ansi.github.io/PowerModels.jl/stable/
