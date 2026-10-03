/**
 * Newton's method on f(x) = x⁴/4 − x²/2, the running example of the Newton article.
 * Two valleys at x = ±1 (f'' = 2) and a hill at x = 0 (f'' = −1) show, on one curve,
 * quadratic convergence, a step toward a maximum, and a leap where the curvature is near zero.
 */
export const f = (x: number) => x ** 4 / 4 - x ** 2 / 2;
export const df = (x: number) => x ** 3 - x;
export const d2f = (x: number) => 3 * x * x - 1;

/** The parabola Newton's method fits at x0: value, slope and curvature agree with f. */
export function model(x0: number, x: number): number {
  const d = x - x0;
  return f(x0) + df(x0) * d + 0.5 * d2f(x0) * d * d;
}

export type NewtonMethod = "newton" | "safeguarded";

export interface NewtonStep {
  x: number;
  /** Fraction of the Newton (or fallback) step actually taken; 1 for plain Newton. */
  t: number;
  /** True when the curvature was too small or negative and the step used −f' instead. */
  fallback: boolean;
}

/** Stationary points of f; every run ends near one of them or leaves the plot. */
export const STATIONARY = [-1, 0, 1] as const;
export const ESCAPE = 50;
const CURVATURE_FLOOR = 0.1;

/**
 * Plain Newton: jump to the parabola's stationary point, whatever its curvature.
 * Safeguarded: if f'' ≤ 0.1 move along −f' instead, then halve the step until f decreases
 * enough (Armijo, c = 10⁻⁴). Both stop when |f'| < 10⁻¹³ or after `maxSteps`.
 */
export function newtonRun(x0: number, method: NewtonMethod, maxSteps = 8): NewtonStep[] {
  const steps: NewtonStep[] = [{ x: x0, t: 1, fallback: false }];
  let x = x0;
  for (let k = 0; k < maxSteps; k += 1) {
    if (Math.abs(df(x)) < 1e-13 || Math.abs(x) > ESCAPE) break;
    const h = d2f(x);
    if (method === "newton") {
      if (h === 0) break;
      x -= df(x) / h;
      steps.push({ x, t: 1, fallback: false });
      continue;
    }
    const fallback = h <= CURVATURE_FLOOR;
    const direction = fallback ? -df(x) : -df(x) / h;
    let t = 1;
    while (f(x + t * direction) > f(x) + 1e-4 * t * df(x) * direction && t > 1e-8) t /= 2;
    x += t * direction;
    steps.push({ x, t, fallback });
  }
  return steps;
}

/** Plain gradient descent with a fixed step, for the digits comparison. */
export function gradientRun(x0: number, eta = 0.1, maxSteps = 8): number[] {
  const xs = [x0];
  let x = x0;
  for (let k = 0; k < maxSteps; k += 1) {
    x -= eta * df(x);
    xs.push(x);
  }
  return xs;
}

/** The stationary point a run is heading to (the nearest one to its last iterate). */
export function limitOf(xs: readonly number[]): number {
  const last = xs[xs.length - 1];
  return STATIONARY.reduce((best, s) => (Math.abs(s - last) < Math.abs(best - last) ? s : best), STATIONARY[0]);
}

/**
 * Correct decimal digits −log₁₀|x − x*|, capped at 16 where double precision ends.
 * Zero error (an exact hit in floating point) also counts as 16.
 */
export function correctDigits(x: number, target: number): number {
  const error = Math.abs(x - target);
  if (error === 0) return 16;
  return Math.max(0, Math.min(16, -Math.log10(error)));
}
