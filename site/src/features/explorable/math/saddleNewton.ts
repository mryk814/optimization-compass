/**
 * Pure Newton's method on the running example of the smooth unconstrained article (PA006):
 * f(x) = (x1² − 1)² + x1·x2 + 2·x2², with a saddle at the origin (f = 1) and two valley
 * bottoms at ±(√17/4, −√17/16) (f = −33/256). The same iteration as
 * `landscape_newton_path` in scripts/generate_lesson_figures.py.
 */
export type Point2 = readonly [number, number];

export const START_A: Point2 = [0.5, 1.0];
export const START_B: Point2 = [0.2, 0.1];
export const VALLEY_X1 = Math.sqrt(17) / 4;
export const VALLEYS: readonly Point2[] = [[VALLEY_X1, -VALLEY_X1 / 4], [-VALLEY_X1, VALLEY_X1 / 4]];
export const SADDLE: Point2 = [0, 0];
/** The Hessian is singular on the lines x1 = ±√(17/48): Newton's step is undefined there. */
export const SINGULAR_X1 = Math.sqrt(17 / 48);

export const TOLERANCE = 1e-8;
export const MAX_STEPS = 50;
/** A step that leaves this box is reported as "escaped" instead of drawn. */
export const ESCAPE = 6;

export function value([x1, x2]: Point2): number {
  return (x1 * x1 - 1) ** 2 + x1 * x2 + 2 * x2 * x2;
}

export function gradient([x1, x2]: Point2): Point2 {
  return [4 * x1 * (x1 * x1 - 1) + x2, x1 + 4 * x2];
}

/** Entries (h11, h12, h22) of the symmetric 2×2 Hessian. */
export function hessian([x1]: Point2): readonly [number, number, number] {
  return [12 * x1 * x1 - 4, 1, 4];
}

/** Eigenvalues of the Hessian, smallest first: the curvatures along its two principal axes. */
export function curvatures(point: Point2): readonly [number, number] {
  const [a, b, d] = hessian(point);
  const mean = (a + d) / 2;
  const radius = Math.hypot((a - d) / 2, b);
  return [mean - radius, mean + radius];
}

export type Stop = "converged" | "singular" | "escaped" | "budget";

export interface NewtonRun {
  points: Point2[];
  stop: Stop;
}

export function newtonRun(start: Point2): NewtonRun {
  const points: Point2[] = [start];
  let [x1, x2] = start;
  while (points.length <= MAX_STEPS) {
    const [g1, g2] = gradient([x1, x2]);
    if (Math.hypot(g1, g2) < TOLERANCE) return { points, stop: "converged" };
    const [h11, h12, h22] = hessian([x1, x2]);
    const det = h11 * h22 - h12 * h12;
    if (Math.abs(det) < 1e-12) return { points, stop: "singular" };
    x1 -= (h22 * g1 - h12 * g2) / det;
    x2 -= (-h12 * g1 + h11 * g2) / det;
    if (!Number.isFinite(x1) || !Number.isFinite(x2) || Math.abs(x1) > ESCAPE || Math.abs(x2) > ESCAPE) {
      return { points, stop: "escaped" };
    }
    points.push([x1, x2]);
  }
  return { points, stop: "budget" };
}

export type PointKind = "valley" | "saddle" | "peak" | "undecided" | "not-stationary";

/** What the second-order test says at a point: only meaningful where the gradient is ~0. */
export function classify(point: Point2, gradientTolerance = 1e-6): PointKind {
  if (Math.hypot(...gradient(point)) >= gradientTolerance) return "not-stationary";
  const [low, high] = curvatures(point);
  if (Math.abs(low) < 1e-9 || Math.abs(high) < 1e-9) return "undecided";
  if (low > 0) return "valley";
  if (high < 0) return "peak";
  return "saddle";
}
