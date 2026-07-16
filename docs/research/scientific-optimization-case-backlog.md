# Scientific optimization Case backlog

- Status: research backlog
- Date: 2026-07-16
- Issue: #142
- Modeling vocabulary: ADR 0011 / #132

This document is a reviewed queue for future Optimization Compass cases. It is not a promise to
implement every item. Promotion into an implementation Issue requires a complete source trail, a
small reproducible teaching instance or static-data plan, explicit feasibility/guarantee language, and
a plausible Case → Theater → Compare → Method/Source journey.

## How to read the backlog

Scores are relative planning aids, not scientific rankings.

- **Learning value (V)**: how many important optimization ideas the case can teach, 1–5.
- **Primitive reuse (R)**: how much canonical data/renderer infrastructure later cases can reuse, 1–5.
- **Visualization value (X)**: how strongly the case benefits from Theater/Compare, 1–5.
- **Implementation effort (E)**: expected repository effort for a deterministic first slice, 1–5.
- **Readiness**:
  - `ready-after-platform`: can start once shared contracts/renderers exist;
  - `research-ready`: sources and a small formulation are clear, but a contract decision remains;
  - `later`: depends on several earlier primitives or has a high modeling burden.

A low effort score does not mean the scientific problem is easy. It means a deliberately small Atlas
example can be built without embedding a production solver stack.

## Recommended implementation sequence

| Order | Candidate | Issue | V | R | X | E | Readiness | Primary reason |
|---:|---|---:|---:|---:|---:|---:|---|---|
| 1 | Cantilever minimum-compliance topology optimization | #133 | 5 | 5 | 5 | 3 | ready-after-platform | Introduces field variables, state solves, adjoints, filtering, and failure modes in one compact loop. |
| 2 | Rotation averaging on `SO(3)` | #136 | 5 | 5 | 5 | 3 | ready-after-platform | Establishes constraint geometry, representation, retraction/projection, and scoped feasibility. |
| 3 | Robot-arm or pendulum direct collocation | #137 | 5 | 5 | 5 | 4 | research-ready | Establishes trajectory variables, dynamics constraints, discretization, and path feasibility. |
| 4 | Synthetic multi-fidelity expensive simulator | #138 | 4 | 5 | 5 | 3 | ready-after-platform | Establishes cost-aware comparison, failures, uncertainty, and fidelity accounting without a heavy solver. |
| 5 | Diffuser/nozzle shape optimization | #134 | 5 | 5 | 5 | 4 | research-ready | Separates parameter, geometry, mesh, state, and shape sensitivity. |
| 6 | Compact PDE inverse/design problem | #135 | 5 | 5 | 4 | 4 | research-ready | Generalizes state/adjoint/cost accounting beyond topology. |
| 7 | Simplex allocation with CVaR/scenarios | #139 | 4 | 4 | 4 | 3 | research-ready | Adds uncertainty, finite-sample versus population claims, and simplex geometry. |
| 8 | Small bilevel regression or complementarity problem | #140 | 4 | 4 | 4 | 4 | later | Adds inner-solve policy, implicit differentiation, residuals, and nonstandard stationarity. |

The sequence deliberately alternates new problem structure with reusable visualization/data
infrastructure. It does not place all PDE cases before all geometry/control cases.

## Backlog grouped by problem structure

### Field- and domain-valued design

- cantilever/MBB minimum compliance;
- stress- or buckling-constrained topology;
- compliant mechanism;
- heat conduction and heat-sink topology;
- fluid-channel topology;
- photonic/acoustic inverse design;
- additive-manufacturing constraints;
- fixed-topology shape optimization;
- level-set shape/topology evolution.

Shared primitives: field-valued decision objects, mesh/discretization metadata, state equations,
adjoint sensitivities, filtering/regularization, geometry validity, field renderers, and refinement claims.

### Trajectory- and policy-valued design

- pendulum swing-up;
- robot-arm obstacle avoidance;
- quadrotor trajectory;
- autonomous racing MPC;
- spacecraft attitude maneuver;
- orbital transfer;
- swarm coverage/formation;
- contact-aware legged motion.

Shared primitives: state/control trajectories, path and terminal constraints, transcription/collocation,
control timelines, defect/refinement views, disturbances, warm starts, and real-time budgets.

### Manifold- and matrix-valued design

- rotation averaging;
- pose-graph optimization;
- spacecraft attitude estimation/control;
- orthogonal/Stiefel embedding;
- SPD covariance estimation;
- fixed-rank matrix completion;
- low-rank synchronization.

Shared primitives: variable-space identity, numerical representation, tangent/retraction operations,
quotient/non-uniqueness notes, eigenvalue/conditioning views, and representation-specific feasibility.

### Expensive, noisy, or failure-prone evaluation

- synthetic multi-fidelity simulator;
- experiment-in-the-loop tuning;
- wind-farm layout;
- CFD/aerodynamic design;
- chemical-process flowsheet optimization;
- hardware or scientific-instrument tuning.

Shared primitives: evaluation ledger, high-fidelity-equivalent cost, batch/asynchronous policy, failure and
timeout semantics, surrogate uncertainty, and budget-aligned Compare contracts.

### Uncertain and nested models

- simplex/CVaR allocation;
- scenario production or inventory planning;
- robust engineering design;
- chance-constrained control;
- bilevel hyperparameter selection;
- market/network equilibrium design;
- complementarity-based contact;
- hybrid mode scheduling.

Shared primitives: uncertainty model, risk measure, sample/confidence scope, inner-solve policy,
complementarity residuals, mode timelines, and relaxation/continuation claims.

## Priority candidate cards

### 1. Cantilever minimum-compliance topology optimization

**Linked Issue:** #133  
**Domain:** structural design  
**Modeling profile:** density field in a box-relaxed function space; linear-elastic FEM state equation;
compliance objective; global volume constraint; discrete adjoint sensitivity.

**Smallest useful deterministic example**

- 2D rectangular cantilever or MBB beam;
- structured low-resolution finite-element mesh;
- one load case and one volume fraction;
- SIMP interpolation, density filter, and optional projection;
- OC update as the first executable path; MMA may be a comparison or later implementation.

**What it teaches**

- design field versus displacement state field;
- state solve versus optimization update;
- direct versus adjoint sensitivity cost;
- continuous density relaxation versus binary topology interpretation;
- volume feasibility, local stationarity, and mesh dependence;
- why filtering/projection changes the lesson rather than merely improving appearance.

**Theater/Compare**

- synchronized density, projected density, displacement/strain-energy, and sensitivity fields;
- objective, volume, grayness, and maximum-change histories;
- no-filter checkerboard failure;
- mesh-resolution and projection-continuation sensitivity;
- OC versus MMA only with aligned state/gradient-solve accounting.

**Promotion blockers**

- define field payload and mesh metadata (#141);
- adopt ADR 0011 feasibility language;
- choose whether the first generator includes a full FEM implementation or checked-in deterministic
  trace generation from a small reference routine.

**Primary/official sources**

- DTU TopOpt educational software collection: https://www.topopt.mek.dtu.dk/apps-and-software
- Ferrari and Sigmund, compact 2D/3D compliance codes: https://arxiv.org/abs/2005.05436
- Ferrari, Sigmund, and Guest, buckling extension for a later slice:
  https://arxiv.org/abs/2101.02973

### 2. Rotation averaging on `SO(3)`

**Linked Issue:** #136  
**Domain:** robotics, vision, estimation  
**Modeling profile:** product of rotation groups; relative-rotation residual graph; local manifold or lifted
relaxation methods; robust loss/outlier policy as an optional later dimension.

**Smallest useful deterministic example**

- 4–8 rotations arranged in a loop or small pose graph;
- fixed synthetic relative rotations with a controlled noise/outlier variant;
- compare rotation-matrix projection, unit quaternion representation, and Lie-group update conceptually;
- use one canonical residual and state clearly whether it is chordal or geodesic.

**What it teaches**

- mathematical set versus numerical representation;
- why a naive Euclidean matrix step leaves `SO(3)`;
- projection versus retraction/exponential-map update;
- quaternion unit norm and double-cover non-uniqueness;
- local stationarity versus certified/global approaches;
- residual geometry and initialization sensitivity.

**Theater/Compare**

- orientation frames and relative-residual edges;
- tangent step followed by projection/retraction;
- orthogonality and determinant diagnostics;
- geodesic/chordal residual history;
- near-π and quaternion-sign failure demonstrations.

**Promotion blockers**

- define a manifold renderer slice (#141);
- choose canonical residual and representation-neutral source identity;
- avoid presenting an `SO(3)` feasibility statement as a global-optimality claim.

**Primary/official sources**

- Manopt official manifold catalog and rotation-group implementation:
  https://www.manopt.org/manifolds.html
- Dellaert et al., Shonan rotation averaging and lifted manifold optimization:
  https://arxiv.org/abs/2008.02737

### 3. Robot-arm or pendulum direct collocation

**Linked Issue:** #137  
**Domain:** control and robotics  
**Modeling profile:** state and control trajectories; nonlinear ODE; direct transcription/collocation;
initial, terminal, bound, path, and optional obstacle constraints.

**Smallest useful deterministic example**

- start with torque-limited pendulum swing-up if implementation simplicity is the priority;
- use a planar two-link arm with one circular obstacle if path-constraint visualization is the priority;
- fixed knot count, deterministic initial guess, and one local NLP solution;
- reconstruct the piecewise-polynomial trajectory and report between-knot validation.

**What it teaches**

- trajectory values as decision variables;
- dynamics as constraints rather than a hidden simulator;
- shooting versus transcription/collocation;
- node/collocation feasibility versus reconstructed continuous-time behavior;
- local nonconvex optimization, initialization, control saturation, and mesh refinement.

**Theater/Compare**

- physical trajectory or phase portrait;
- state and control timelines;
- path/obstacle margins and control saturation;
- collocation residual and between-knot validation;
- coarse versus refined mesh;
- shooting sensitivity versus multiple-shooting/collocation structure.

**Promotion blockers**

- trajectory and defect renderer slice (#141);
- profile contract for state/control roles and path/terminal scopes;
- explicit decision on whether browser artifacts are generated from an in-repository solver or a pinned
  offline trace generator.

**Primary/official sources**

- MIT Underactuated Robotics trajectory optimization and direct collocation:
  https://underactuated.mit.edu/trajopt.html
- Hargraves and Paris, *Direct Trajectory Optimization Using Nonlinear Programming and Collocation*,
  the classical formulation cited by the MIT notes.

### 4. Synthetic multi-fidelity expensive simulator

**Linked Issue:** #138  
**Domain:** simulation optimization, experimental design  
**Modeling profile:** bounded continuous or mixed design; low/high-fidelity black boxes; optional noise,
bias, failure region, and timeout/censoring; surrogate-guided evaluation policy.

**Smallest useful deterministic example**

- one- or two-dimensional hidden truth;
- a biased cheap fidelity and an expensive accurate fidelity;
- fixed cost ratio and total high-fidelity-equivalent budget;
- seeded observations and a deterministic artifact-generation policy;
- one explicit failure or invalid region.

**What it teaches**

- optimizer iteration is not the correct comparison axis;
- uncertainty model versus observed truth;
- acquisition decision versus final recommendation;
- cost/fidelity trade-off and low-fidelity bias;
- failed evaluation policies and why failure is not automatically a large objective value;
- recommendation uncertainty and held-out truth used only for educational evaluation.

**Theater/Compare**

- surrogate mean, uncertainty, acquisition, and observations;
- fidelity-selection and simulator-call timeline;
- successful, failed, and censored calls;
- best-observed, incumbent recommendation, and hidden-truth regret;
- single-fidelity versus multi-fidelity under aligned equivalent cost.

**Promotion blockers**

- comparison cost-accounting extension after #119;
- evaluation/fidelity/failure contract;
- select a GP implementation or generate validated static artifacts without making a library the
  canonical method identity.

**Primary/official sources**

- Balandat et al., BoTorch framework: https://arxiv.org/abs/1910.06403
- BoTorch official tutorials and documentation: https://botorch.org/tutorials/

### 5. Diffuser/nozzle shape optimization

**Linked Issue:** #134  
**Domain:** fluids or PDE-constrained design  
**Modeling profile:** parameterized boundary/shape; mesh/domain representation; steady state equation;
parameter or shape derivative; geometry and state constraints.

**Smallest useful deterministic example**

Preferred first slice: a 2D diffuser/nozzle with a compact boundary parameterization and a lightweight
potential-flow, Poisson, or reduced flow model. A full RANS CFD stack is explicitly not required.

**What it teaches**

- design parameters versus geometry versus mesh versus physical state;
- parameter derivative versus shape derivative;
- fixed-topology parameterization versus topology-changing level set;
- mesh motion/remeshing and invalid-geometry failure;
- discrete objective improvement versus physical-model credibility.

**Theater/Compare**

- geometry and mesh evolution;
- pressure/velocity/state and shape-sensitivity overlays;
- minimum cell quality and geometry-validity events;
- finite difference versus adjoint gradient check;
- coarse versus refined model or low versus high fidelity.

**Promotion blockers**

- choose a small state model that is pedagogically honest;
- define geometry/mesh payloads (#141);
- state how topology change is excluded or represented.

**Primary/official sources**

- Blauth, cashocs adjoint-based shape optimization: https://arxiv.org/abs/2010.02048
- cashocs 2.0, including space mapping and level-set topology:
  https://arxiv.org/abs/2306.09828

### 6. Compact PDE inverse or design problem

**Linked Issue:** #135  
**Domain:** heat transfer, diffusion, inverse problems  
**Modeling profile:** finite-dimensional parameter or distributed control; elliptic/transient PDE;
reduced-space or full-space formulation; direct/adjoint derivatives.

**Smallest useful deterministic example**

- infer a small spatial coefficient field from synthetic observations, or optimize a distributed heat
  source to match a target temperature;
- 1D or small 2D finite-difference/FEM discretization;
- explicit regularization and observation noise;
- direct sensitivity for a tiny parameterization and adjoint sensitivity for a field-scale variant.

**What it teaches**

- design/control versus state;
- inverse ill-posedness and regularization;
- one state solve versus many parameter sensitivities;
- adjoint cost scaling;
- state-solver tolerance and gradient consistency;
- discretized inverse result versus physical truth.

**Theater/Compare**

- parameter/control, state, residual, and adjoint fields;
- observation mismatch and regularization histories;
- direct versus adjoint derivative cost;
- mesh/noise/regularization sensitivity;
- intentionally inaccurate state solve causing an inconsistent gradient.

**Promotion blockers**

- reusable state/evaluation profile from ADR 0011;
- field renderer slice (#141);
- cost ledger that separates state and adjoint solves.

**Primary/official sources**

- MOOSE Optimization Module: https://mooseframework.inl.gov/modules/optimization/
- cashocs adjoint-based optimal control and shape optimization:
  https://arxiv.org/abs/2010.02048

### 7. Simplex allocation with CVaR or scenarios

**Linked Issue:** #139  
**Domain:** allocation, planning, risk  
**Modeling profile:** simplex decision vector; finite scenario set or sampled loss model; expectation/CVaR
objective; optional chance or robust constraints.

**Smallest useful deterministic example**

- 3–6 allocation weights summing to one;
- fixed training and held-out loss scenarios;
- compare expected loss, worst case, and CVaR formulations;
- expose direct simplex coordinates and optionally a mirror/softmax representation caveat.

**What it teaches**

- closed versus interior simplex;
- empirical scenario objective versus population claim;
- expectation, worst case, quantile, and CVaR differences;
- performance/robustness trade-off;
- sample size and held-out validation;
- exact zero allocations and representation limitations.

**Theater/Compare**

- weight movement on a simplex;
- scenario loss distribution and tail highlighting;
- held-out violation/performance distribution;
- efficient frontier between nominal performance and tail risk;
- sample-size and confidence sensitivity.

**Promotion blockers**

- uncertainty/risk vocabulary;
- statistical-claim validation policy;
- simplex renderer shared with #136.

**Primary/official sources**

- Rockafellar and Uryasev, *Optimization of Conditional Value-at-Risk*:
  https://www.ise.ufl.edu/uryasev/files/2011/11/CVaR1_JOR.pdf
- Manopt official strict-simplex/multinomial manifold entries for representation comparison:
  https://www.manopt.org/manifolds.html

### 8. Small bilevel regression or complementarity problem

**Linked Issue:** #140  
**Domain:** hyperparameter selection, equilibrium, contact  
**Modeling profile:** outer decision plus inner optimization/equilibrium; explicit inner tolerance and
solution policy; implicit/unrolled derivatives or complementarity residual.

**Smallest useful deterministic example**

Start with regularization selection for a tiny linear/ridge model because it makes inner-solve accuracy
and implicit differentiation observable without a contact simulator. Follow later with a two-variable
complementarity example before any robotics contact case.

**What it teaches**

- outer iteration versus hidden inner work;
- exact versus truncated inner solve;
- derivative of an algorithm versus derivative of the solution map;
- optimistic/pessimistic or solution-selection assumptions;
- complementarity residual and smoothing/penalty continuation;
- nonstandard stationarity and constraint-qualification limitations.

**Theater/Compare**

- outer and inner objectives on separate axes;
- inner residual/tolerance versus outer progress;
- exact/implicit versus truncated/unrolled derivative error;
- complementarity residual and smoothing parameter timeline;
- incorrect outer direction from an under-solved inner problem.

**Promotion blockers**

- nested-solve profile and accounting;
- clear stationarity/caveat language;
- avoid coupling the first slice to contact, hybrid dynamics, and renderer work simultaneously.

## Secondary domain candidates

These are valuable after the first eight cases establish reusable primitives.

| Candidate | Structure | Reuse from | Main distinctive lesson | Suggested sources |
|---|---|---|---|---|
| AC optimal power flow | nonlinear network physics, relaxations | #135, #139 | one problem specification under AC, DC, SOC, and relaxation formulations | PowerModels: https://lanl-ansi.github.io/PowerModels.jl/stable/ |
| Bundle adjustment | sparse nonlinear least squares with poses and landmarks | #136 | gauge freedom, Schur complement, robust loss, initialization | Triggs et al., *Bundle Adjustment — A Modern Synthesis* |
| Pose-graph SLAM | `SE(3)` graph optimization | #136 | gauge, loop closure, outliers, manifold residuals | GTSAM and Shonan references |
| Photonic splitter | PDE topology/inverse design | #133, #135 | wave physics, complex fields, fabrication constraints | DTU TopOpt photonics resources |
| Buckling topology | eigenvalue/state constraints | #133 | mode switching, aggregation, sensitivity | https://arxiv.org/abs/2101.02973 |
| Wind-farm layout | expensive wake simulation, discrete/continuous siting | #138, #139 | fidelity, uncertainty, spacing constraints | official wake-model/project sources required before promotion |
| Water-network operation/design | nonlinear network simulation and discrete choices | #135, #139 | pressure/flow feasibility, scenario demand | official EPANET sources required before promotion |
| Quantum pulse control | trajectory/control under Schrödinger/Lindblad dynamics | #135, #137 | complex state, pulse parameterization, adjoint/GRAPE, fidelity | https://arxiv.org/abs/2205.15044 |
| Experiment-in-the-loop material/process tuning | physical experiment, noise, failures | #138 | no hidden truth, repeatability, batch policy | application-specific primary source required |
| Molecular geometry | nonconvex geometry with symmetries | #136, #138 | invariance, local minima, expensive energy models | application-specific primary source required |

## Duplicate and ownership rules

- #133 owns the first topology implementation; this backlog does not duplicate its acceptance criteria.
- #134 owns shape representation and geometry/mesh failures.
- #135 owns reusable state/simulation/adjoint abstractions.
- #136 owns constraint geometry and the first `SO(3)` journey.
- #137 owns optimal-control/robotics contracts and the first trajectory journey.
- #138 owns evaluation/fidelity/failure semantics for expensive simulators.
- #139 owns uncertainty/risk/guarantee vocabulary.
- #140 owns nested/equilibrium/complementarity semantics.
- #141 owns reusable renderer families; individual case Issues own only case-specific payloads and lesson
  metadata.
- #142 remains the curation and promotion queue.

A candidate appearing in two domains is one canonical case with multiple domain tags, not duplicate
Gallery rows. For example, spacecraft attitude is both control and manifold optimization; its primary
modeling profile should reference both structures.

## Promotion process

A candidate can move from this backlog to a dedicated implementation Issue only after the following
review.

### 1. Identity and scope

- define the real-world question and the smallest educational problem;
- identify whether an existing Gallery case, problem definition, method, source, or scenario already
  covers the same identity;
- assign one owning Issue and list related platform Issues.

### 2. Modeling profile

- complete the ADR 0011 axes;
- distinguish design, state, control, uncertainty, and auxiliary variables;
- state representation, state/evaluation model, derivative route, discretization, and evaluation regime;
- write scoped feasibility and guarantee claims.

### 3. Evidence

- include at least one primary paper or official specification for the mathematical/application claim;
- include official implementation documentation when an API/library behavior is discussed;
- separate historical primary sources from current versioned implementation facts;
- record licensing/attribution implications for datasets, meshes, screenshots, and copied examples.

### 4. Teaching journey

- state the learning objective and misconception;
- define a primary scenario and at least one failure/sensitivity scenario;
- define a fair comparison question, fixed/changed factors, budget, metrics, caveat, and ranking eligibility;
- include static summary and text alternative requirements.

### 5. Reproducibility and cost

- define the deterministic generator or static-data provenance;
- set runtime/artifact-size limits;
- state whether a heavyweight external solver is required for generation but not runtime;
- define validation for known references, residuals, constraints, and hashes.

### 6. Value/effort review

Promote when the case either adds a reusable primitive or closes a meaningful coverage gap, and when the
first slice can be reviewed independently. Split advanced constraints, multi-physics, contact, robust,
or large-scale variants into follow-up Issues.

## Research maintenance

When adding a backlog candidate:

1. map it to ADR 0011;
2. add an owning or prospective Issue;
3. add a primary/official source shortlist;
4. identify the smallest deterministic example;
5. record expected reusable primitives and renderer needs;
6. score value, reuse, visualization, and effort;
7. state why it is not already covered by an existing case;
8. avoid promising implementation until promotion criteria are met.
