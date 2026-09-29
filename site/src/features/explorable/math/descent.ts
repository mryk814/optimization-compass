export type DescentMethod = "gd" | "momentum";

/** f(x, y) = (x - cx)^2 + kappa (y - cy)^2. A valley whose steepness ratio is kappa. */
export interface ValleyProblem {
  readonly cx: number;
  readonly cy: number;
  readonly kappa: number;
}

export interface DescentOptions {
  eta: number;
  method: DescentMethod;
  /** Momentum coefficient; ignored by plain gradient descent. */
  beta: number;
  maxSteps: number;
}

export interface DescentPoint {
  k: number;
  x: number;
  y: number;
  f: number;
  gx: number;
  gy: number;
  gradNorm: number;
}

export type DescentOutcome = "converged" | "diverged" | "unfinished";

export interface DescentRun {
  points: DescentPoint[];
  outcome: DescentOutcome;
}

export interface AxisRate {
  /** Signed per-step multiplier of the error along the axis (dominant root for momentum). */
  factor: number;
  /** Magnitude of the multiplier: below 1 the error shrinks, above 1 it grows. */
  rate: number;
  /** True when the error changes sign each step (or spirals, for momentum). */
  oscillates: boolean;
}

export const GRADIENT_TOLERANCE = 1e-3;
export const DIVERGENCE_LIMIT = 1e9;

export function valleyValue(problem: ValleyProblem, x: number, y: number): number {
  return (x - problem.cx) ** 2 + problem.kappa * (y - problem.cy) ** 2;
}

export function valleyGradient(problem: ValleyProblem, x: number, y: number): [number, number] {
  return [2 * (x - problem.cx), 2 * problem.kappa * (y - problem.cy)];
}

/** Hessian eigenvalues: `gentle` along x, `steep` along y. `steep / gentle` is the condition number. */
export function valleyCurvatures(problem: ValleyProblem): { gentle: number; steep: number } {
  return { gentle: 2, steep: 2 * problem.kappa };
}

/** Largest eta for which the quadratic model stays stable; beyond it the iterates grow. */
export function stabilityLimit(problem: ValleyProblem, method: DescentMethod, beta: number): number {
  const { gentle, steep } = valleyCurvatures(problem);
  const largest = Math.max(gentle, steep);
  return method === "gd" ? 2 / largest : (2 * (1 + beta)) / largest;
}

export function axisRate(
  method: DescentMethod,
  curvature: number,
  eta: number,
  beta: number,
): AxisRate {
  if (method === "gd") {
    const factor = 1 - eta * curvature;
    return { factor, rate: Math.abs(factor), oscillates: factor < 0 };
  }
  // Heavy ball on one eigen-direction: z^2 - (1 + beta - eta*curvature) z + beta = 0.
  const trace = 1 + beta - eta * curvature;
  const discriminant = trace * trace - 4 * beta;
  if (discriminant < 0) {
    const rate = Math.sqrt(beta);
    return { factor: rate, rate, oscillates: true };
  }
  const root = Math.sqrt(discriminant);
  const first = (trace + root) / 2;
  const second = (trace - root) / 2;
  const dominant = Math.abs(first) >= Math.abs(second) ? first : second;
  return { factor: dominant, rate: Math.abs(dominant), oscillates: dominant < 0 };
}

export function runDescent(
  problem: ValleyProblem,
  start: readonly [number, number],
  options: DescentOptions,
): DescentRun {
  const points: DescentPoint[] = [];
  let [x, y] = start;
  let vx = 0;
  let vy = 0;
  for (let k = 0; k <= options.maxSteps; k += 1) {
    const [gx, gy] = valleyGradient(problem, x, y);
    const f = valleyValue(problem, x, y);
    const gradNorm = Math.hypot(gx, gy);
    if (!Number.isFinite(f) || f > DIVERGENCE_LIMIT) return { points, outcome: "diverged" };
    points.push({ k, x, y, f, gx, gy, gradNorm });
    if (gradNorm < GRADIENT_TOLERANCE) return { points, outcome: "converged" };
    if (options.method === "gd") {
      x -= options.eta * gx;
      y -= options.eta * gy;
    } else {
      vx = options.beta * vx - options.eta * gx;
      vy = options.beta * vy - options.eta * gy;
      x += vx;
      y += vy;
    }
  }
  return { points, outcome: "unfinished" };
}
