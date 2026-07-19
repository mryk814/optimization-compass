# Constraint Geometry Atlas contract and audit

Reviewed: 2026-07-19 (JST)
Issue: #136
Dataset boundary: cumulative 0.18.9 staging; ordinary content publication must not publish it alone.

## Canonical proposal

The Atlas keeps three identities separate:

1. a canonical feature describes the kind of variable or constraint;
2. a problem definition and fixed instance own an executable teaching contract;
3. a method describes how an update is constructed and returned to the feasible set.

An article, Case, renderer, or implementation must reference those identities rather than inventing a UI-only crosswalk. `F_VARIABLE_MANIFOLD` remains the canonical feature for smooth manifold-valued variables. `concept.manifold`, `concept.so3-rotation-representation`, and `concept.spd-matrix-geometry` are distinct explanations of that feature; their content IDs are not new stable feature IDs.

## Common geometry page contract

Every geometry explanation must state all of the following before it is published:

| Required field | Question answered |
| --- | --- |
| set and degrees of freedom | What is the feasible set, ambient dimension, and intrinsic dimension? |
| naive Euclidean failure | Which invariant does an unrestricted update break? |
| representations | Which matrix, factor, quaternion, chart, or quotient represents one point? |
| feasibility map | Is the operation a projection, normalization, retraction, or exponential map? |
| boundary and non-uniqueness | Where do singularities, sign aliases, quotient aliases, or rank changes appear? |
| guarantee scope | Are iterates feasible, approximately feasible, or only feasible after convergence? |
| methods and implementations | Which canonical method and versioned implementation support the geometry? |
| diagnostics | Which structure residual, step, objective, and stopping quantities are recorded? |

The contract deliberately forbids using “projection”, “retraction”, and “exponential map” as interchangeable labels.

## Feasibility-strategy relation matrix

| Geometry | Feasibility strategy | What it guarantees per iterate | What it does not guarantee |
| --- | --- | --- | --- |
| simplex with boundary | Euclidean projection | nonnegative entries and sum one after projection | mirror geometry, differentiability at corners, or an exact zero through softmax |
| simplex interior | mirror map / softmax-like parametrization | positive interior entries under the declared map | exact zeros or the same update as Euclidean projection |
| sphere / Stiefel / SO(3) | normalization, QR, or polar projection | declared norm or orthogonality invariant after repair | an intrinsic tangent step or exact geodesic |
| smooth manifold | tangent step plus retraction | a feasible local update for the chosen retraction | equality with the exponential map or global convergence |
| SO(3) | Lie-algebra step plus exponential map | a proper rotation when evaluated accurately | a globally nonsingular log chart at angle pi |
| SPD interior | Cholesky or matrix exponential | positive definiteness for finite valid parameters | direct representation of the PSD boundary |
| fixed-rank PSD | factor or quotient representation | declared rank while the factor remains full rank | rank changes or a unique factor |

The versioned learning graph connects `F_VARIABLE_MANIFOLD` to Riemannian gradient and trust-region methods, and connects the SO(3) Case, scenarios, comparison, and supported implementations. Projected gradient is retained as a contrast, not silently relabeled as a Riemannian method.

## SO(3) flagship contract

The flagship uses `PROBLEM_SO3_ATTITUDE_ALIGNMENT` and `INSTANCE_SO3_ATTITUDE_FIXED_3`.

- fixed target: axis `(1, 2, 3) / sqrt(14)`, angle `2.8` radians;
- fixed observations: three noiseless basis correspondences;
- initial rotation: identity;
- objective: chordal squared residual;
- diagnostic distance: geodesic angle;
- budget: 12 updates;
- comparison: ambient step plus QR projection versus Lie-algebra step plus exponential map;
- renderer: existing `generic_metric_history` and `AlgorithmTrace` contracts;
- ranking: forbidden; this is a feasibility-strategy contrast.

The initial angle is close enough to pi to make chart scope visible without placing the deterministic log computation at the singular point itself. This is not evidence that either update is generally robust near pi.

## SPD secondary contract

`concept.spd-matrix-geometry` supplies the secondary example around a fixed 2-by-2 covariance matrix. It distinguishes Cholesky, matrix-exponential, eigenvalue-projection, and Riemannian contracts and requires minimum eigenvalue and condition-number diagnostics. An executable SPD Case is intentionally not implied by the SO(3) trace; it needs its own canonical problem instance and fixed metric before publication.

## Method, source, and implementation audit

| Concern | Canonical method | Current primary or official sources | Current implementation mappings | Result |
| --- | --- | --- | --- | --- |
| Euclidean projection | `M_PROJECTED_GRADIENT` | S017, S029, S030, S055, S056, S064 | JAXopt, PETSc TAO | available; projection operator remains problem-specific |
| simplex mirror geometry | `M_MIRROR_DESCENT` | S055, S061, S066, S067 | no direct implementation mapping | content is available; implementation mapping remains follow-up |
| first-order manifold update | `M_RIEMANNIAN_GRADIENT` | S044, S045, S071 | Pymanopt, Manopt, Manopt.jl | available |
| second-order manifold update | `M_RIEMANNIAN_TRUST_REGION` | S044, S045, S071 | Pymanopt, Manopt, Manopt.jl | available; Hessian convention must be checked |
| rotation averaging and distances | SO(3) flagship | S107, Hartley et al. | same manifold toolkits | staged in 0.18.9 |
| SPD geometry | SPD secondary | S108, Pennec et al.; S044 official manifold catalog | Pymanopt SPD manifold through I_PYMANOPT | content staged; executable Case remains follow-up |

Official Pymanopt 2.2.1 documentation exposes both `SpecialOrthogonalGroup` and `SymmetricPositiveDefinite`. Official Manopt documentation records the tangent representation used by `rotationsfactory` and warns that tangent and ambient matrices must not be confused. The primary rotation-averaging paper distinguishes chordal, geodesic/angular, and quaternion distances. The SPD paper provides the geometric basis for tensor-valued SPD processing. These sources support contracts and distinctions, not performance rankings for the fixed Atlas traces.

## Follow-up map

| Slice | Current state | Next canonical input | Stop condition |
| --- | --- | --- | --- |
| SO(3) flagship | Case, Theater, Compare, problem instance, exact context staged | integrate common comparison validator and cumulative 0.18.9 release | context, problem, profile, and generated artifact must resolve together |
| simplex | concept and projected/mirror method content already published | add a boundary-focused executable Case only if it does not duplicate portfolio allocation | exact-zero and interior-only claims must remain distinct |
| SPD | secondary concept and source audit staged | add a fixed covariance-mean or covariance-fit problem definition, instance, Theater, and Compare | metric and PSD-boundary policy must be fixed first |
| Stiefel / Grassmann | listed in manifold overview | choose one subspace-estimation Case and quotient-aware diagnostic | basis distance must not substitute for subspace distance |
| SE(3) | not yet executable | define rotation/translation units, metric weights, and fixed registration Case | no mixed-unit distance without an explicit scale |
| fixed-rank / low-rank | not yet executable | define rank-fixed instance and quotient representation | rank changes require a different contract |
| mirror implementation | method content only | verify and add one official maintained implementation mapping | do not infer support from a generic autodiff library |

Generated site data, release identity, and publication are deliberately left to the cumulative release workflow.
