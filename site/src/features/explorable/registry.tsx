import { lazy, type ComponentType, type LazyExoticComponent } from "react";

/**
 * One entry per id in `src/optimization_compass/resources/explorables.json`.
 * Each figure is its own chunk, so an article without one downloads none of this code.
 */
export const EXPLORABLE_COMPONENTS: Readonly<Record<string, LazyExoticComponent<ComponentType>>> = {
  "branch-bound-proof": lazy(() => import("./BranchBound")),
  "gradient-descent-valley": lazy(() => import("./GradientDescentValley")),
  "lp-vertex-walk": lazy(() => import("./LpVertexWalk")),
  "simplex-pivot": lazy(() => import("./SimplexPivot")),
  "simplex-shadow-price": lazy(() => import("./SimplexShadowPrice")),
  "convexity-chord": lazy(() => import("./ConvexityChord")),
  "least-squares-bowl": lazy(() => import("./LeastSquaresBowl")),
  "adam-step-ratio": lazy(() => import("./AdamStepRatio")),
  "bayes-opt-acquisition": lazy(() => import("./BayesOptAcquisition")),
  "coordinate-descent-walk": lazy(() => import("./CoordinateDescentWalk")),
  "nonlinear-least-squares-landscape": lazy(() => import("./NonlinearFitLandscape")),
  "newton-parabola-jump": lazy(() => import("./NewtonParabola")),
  "cmaes-shape-learning": lazy(() => import("./CmaesShape")),
  "interior-point-barrier-path": lazy(() => import("./BarrierPath")),
  "multiobjective-pareto-weights": lazy(() => import("./ParetoWeights")),
  "proximal-gradient-threshold": lazy(() => import("./ProximalThreshold")),
  "inverse-problem-alpha": lazy(() => import("./InverseProblemAlpha")),
};
