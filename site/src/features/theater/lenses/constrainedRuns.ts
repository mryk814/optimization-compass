/**
 * Three ways of seeing one constraint, on the Case `constrained-design` teaching problem:
 *   minimise f(x, y) = x² + y²  subject to  g(x, y) = (x − 1)² + (y − 1)² − 1 ≤ 0.
 * The constrained optimum is on the circle at (1 − 1/√2, 1 − 1/√2).
 *
 * Each instrument runs the same number of iterations from the same feasible start. Each
 * snapshot keeps only what that method holds after k iterations — the algorithm's view — so
 * the page can show that only one of them "sees" the feasible region at all.
 *
 * In-browser teaching computation, not a canonical Trace, and not a ranking.
 */
export type Vec2 = readonly [number, number];

export const CONSTRAINED_ITERATIONS = 12;
export const CONSTRAINED_START: Vec2 = [1.5, 1.7];
export const DISC_CENTER: Vec2 = [1, 1];
export const DISC_RADIUS = 1;
export const CONSTRAINED_BOUNDS = { xMin: -0.6, xMax: 2.4, yMin: -0.6, yMax: 2.4 } as const;
export const CONSTRAINED_OPTIMUM: Vec2 = [1 - Math.SQRT1_2, 1 - Math.SQRT1_2];

export const objective2 = ([x, y]: Vec2) => x * x + y * y;
export const gradient2 = ([x, y]: Vec2): Vec2 => [2 * x, 2 * y];
/** Constraint value: feasible when ≤ 0. */
export const constraint2 = ([x, y]: Vec2) => (x - DISC_CENTER[0]) ** 2 + (y - DISC_CENTER[1]) ** 2 - DISC_RADIUS ** 2;
const constraintGradient = ([x, y]: Vec2): Vec2 => [2 * (x - DISC_CENTER[0]), 2 * (y - DISC_CENTER[1])];

export const FEASIBILITY_TOLERANCE = 1e-9;
export const isFeasible = (point: Vec2) => constraint2(point) <= FEASIBILITY_TOLERANCE;

export type ConstrainedLensId = "objective-only" | "penalty" | "projection";

export interface ConstrainedStep {
  /** Iteration index; 0 is the start. */
  k: number;
  point: Vec2;
  value: number;
  violation: number;
}

export type ConstrainedView =
  | { kind: "objective-only"; direction: Vec2 }
  | { kind: "penalty"; direction: Vec2; mu: number; penaltyPull: Vec2 }
  | { kind: "projection"; direction: Vec2; trial: Vec2; projected: boolean };

export interface ConstrainedSnapshot {
  steps: ConstrainedStep[];
  /** What the method used to choose the next point, if there is a next point. */
  view: ConstrainedView | null;
}

export interface ConstrainedRun {
  id: ConstrainedLensId;
  snapshots: ConstrainedSnapshot[];
}

const step = (k: number, point: Vec2): ConstrainedStep => ({
  k,
  point,
  value: objective2(point),
  violation: Math.max(0, constraint2(point)),
});

export const OBJECTIVE_ONLY_STEP = 0.15;

/** Gradient descent on f alone: the constraint is never read. */
export function runObjectiveOnly(): ConstrainedRun {
  let point = CONSTRAINED_START;
  const steps = [step(0, point)];
  const snapshots: ConstrainedSnapshot[] = [];
  for (let k = 1; k <= CONSTRAINED_ITERATIONS; k += 1) {
    const g = gradient2(point);
    snapshots.push({ steps: [...steps], view: { kind: "objective-only", direction: [-g[0], -g[1]] } });
    point = [point[0] - OBJECTIVE_ONLY_STEP * g[0], point[1] - OBJECTIVE_ONLY_STEP * g[1]];
    steps.push(step(k, point));
  }
  snapshots.push({ steps: [...steps], view: null });
  return { id: "objective-only", snapshots };
}

/** Quadratic penalty: F = f + μ·max(0, g)², μ multiplied each iteration, one gradient step. */
export const PENALTY_SETTINGS = { mu0: 1, growth: 1.8, step: 0.12 } as const;

export function runPenalty(): ConstrainedRun {
  let point = CONSTRAINED_START;
  let mu: number = PENALTY_SETTINGS.mu0;
  const steps = [step(0, point)];
  const snapshots: ConstrainedSnapshot[] = [];
  for (let k = 1; k <= CONSTRAINED_ITERATIONS; k += 1) {
    const g = gradient2(point);
    const c = constraint2(point);
    const cg = constraintGradient(point);
    const scale = c > 0 ? 2 * mu * c : 0;
    const pull: Vec2 = [-scale * cg[0], -scale * cg[1]];
    const total: Vec2 = [g[0] + scale * cg[0], g[1] + scale * cg[1]];
    // Keep the step stable as μ grows: a step that is safe for the steepest curvature.
    const curvature = 2 + (c > 0 ? 2 * mu * (1 + 4 * (c + 1)) : 0);
    const eta = Math.min(PENALTY_SETTINGS.step, 1 / curvature);
    snapshots.push({ steps: [...steps], view: { kind: "penalty", direction: [-total[0], -total[1]], mu, penaltyPull: pull } });
    point = [point[0] - eta * total[0], point[1] - eta * total[1]];
    steps.push(step(k, point));
    mu *= PENALTY_SETTINGS.growth;
  }
  snapshots.push({ steps: [...steps], view: null });
  return { id: "penalty", snapshots };
}

export const PROJECTION_STEP = 0.15;

export function projectOntoDisc(point: Vec2): Vec2 {
  const dx = point[0] - DISC_CENTER[0];
  const dy = point[1] - DISC_CENTER[1];
  const distance = Math.hypot(dx, dy);
  if (distance <= DISC_RADIUS) return point;
  return [DISC_CENTER[0] + (DISC_RADIUS * dx) / distance, DISC_CENTER[1] + (DISC_RADIUS * dy) / distance];
}

/** Projected gradient: step on f, then return to the disc by the closed-form projection. */
export function runProjection(): ConstrainedRun {
  let point = CONSTRAINED_START;
  const steps = [step(0, point)];
  const snapshots: ConstrainedSnapshot[] = [];
  for (let k = 1; k <= CONSTRAINED_ITERATIONS; k += 1) {
    const g = gradient2(point);
    const trial: Vec2 = [point[0] - PROJECTION_STEP * g[0], point[1] - PROJECTION_STEP * g[1]];
    const projected = projectOntoDisc(trial);
    snapshots.push({ steps: [...steps], view: { kind: "projection", direction: [-g[0], -g[1]], trial, projected: projected !== trial } });
    point = projected;
    steps.push(step(k, point));
  }
  snapshots.push({ steps: [...steps], view: null });
  return { id: "projection", snapshots };
}

export function runConstrainedLenses(): Record<ConstrainedLensId, ConstrainedRun> {
  return { "objective-only": runObjectiveOnly(), penalty: runPenalty(), projection: runProjection() };
}

export function constrainedSnapshotAt(run: ConstrainedRun, k: number): ConstrainedSnapshot {
  return run.snapshots[Math.min(Math.max(k, 0), run.snapshots.length - 1)];
}
