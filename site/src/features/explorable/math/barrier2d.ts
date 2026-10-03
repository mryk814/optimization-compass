/**
 * The log-barrier view of an interior-point method on
 *   minimize (x − 2)² + 4(y − 1)²  subject to  x² + y² ≤ 1,
 * the running example of the nonlinear interior-point article. The barrier problem
 *   φ_μ(p) = f(p) − μ log s(p),  s = 1 − x² − y²
 * is minimized by damped Newton steps that never leave the disk; its minimizer x(μ) traces the
 * central path to the constrained solution as μ → 0.
 */
export type Point = readonly [number, number];

export const f = ([x, y]: Point) => (x - 2) ** 2 + 4 * (y - 1) ** 2;
export const slack = ([x, y]: Point) => 1 - x * x - y * y;

export function barrier(p: Point, mu: number): number {
  const s = slack(p);
  return s <= 0 ? Number.POSITIVE_INFINITY : f(p) - mu * Math.log(s);
}

function gradient(p: Point, mu: number): Point {
  const s = slack(p);
  return [2 * (p[0] - 2) + (2 * mu * p[0]) / s, 8 * (p[1] - 1) + (2 * mu * p[1]) / s];
}

function hessian(p: Point, mu: number): readonly [number, number, number] {
  const s = slack(p);
  const outer = (4 * mu) / (s * s);
  return [2 + (2 * mu) / s + outer * p[0] * p[0], outer * p[0] * p[1], 8 + (2 * mu) / s + outer * p[1] * p[1]];
}

/** Constrained solution, from a high-accuracy solve (see the article's Python section). */
export const SOLUTION: Point = [0.721110, 0.692820];
export const F_STAR = 2.012996;
export const LAMBDA_STAR = 1.773501;

export interface Center {
  mu: number;
  p: Point;
  /** Newton steps spent to reach this center from the previous one. */
  newtonSteps: number;
}

/**
 * Minimizes φ_μ from `start` with Newton steps. Each step is first halved until the point stays
 * strictly inside the disk, then until φ decreases enough (Armijo, c = 10⁻⁴).
 */
export function centerFor(mu: number, start: Point, tolerance = 1e-9, maxSteps = 50): Center {
  let p = start;
  let steps = 0;
  while (steps < maxSteps) {
    const g = gradient(p, mu);
    if (Math.hypot(g[0], g[1]) < tolerance) break;
    const [a, b, c] = hessian(p, mu);
    const det = a * c - b * b;
    const d: Point = [-(c * g[0] - b * g[1]) / det, -(a * g[1] - b * g[0]) / det];
    let t = 1;
    while (slack([p[0] + t * d[0], p[1] + t * d[1]]) <= 0) t /= 2;
    const slope = g[0] * d[0] + g[1] * d[1];
    while (barrier([p[0] + t * d[0], p[1] + t * d[1]], mu) > barrier(p, mu) + 1e-4 * t * slope) t /= 2;
    p = [p[0] + t * d[0], p[1] + t * d[1]];
    steps += 1;
  }
  return { mu, p, newtonSteps: steps };
}

/** Centers for a decreasing sequence of μ, each warm-started from the previous center. */
export function centralPath(mus: readonly number[], start: Point = [0, 0]): Center[] {
  const centers: Center[] = [];
  let p = start;
  for (const mu of mus) {
    const center = centerFor(mu, p);
    centers.push(center);
    p = center.p;
  }
  return centers;
}

/** μ from 10 down to 10⁻⁴ in steps of a tenth of a decade: index 0 … 50. */
export const MU_STEPS = 50;
export const muAt = (index: number) => 10 ** (1 - index / 10);
