export const THEATER_ROUTES = {
  index: "/theater",
  nelderMead: "/traces/nelder-mead-quadratic",
  searchTree: "/theater/search-tree/binary-knapsack-bnb-complete",
  bayesianOptimization: "/theater/bayesian-optimization",
  constrainedContinuous: "/theater/learning/SCENARIO_CONSTRAINED_DISK",
  multiObjective: "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC",
  algorithmLenses: "/theater/lenses/hyperparameter-search",
} as const;

/** Cases that have an algorithm-view stage (/theater/lenses/:caseId). */
export const ALGORITHM_LENS_CASES = ["hyperparameter-search", "constrained-design"] as const;

export function algorithmLensRoute(caseId: string): string | undefined {
  return (ALGORITHM_LENS_CASES as readonly string[]).includes(caseId) ? `/theater/lenses/${caseId}` : undefined;
}
