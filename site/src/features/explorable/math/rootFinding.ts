/**
 * The diagonal slice of the root-finding article: both equations reduce to
 * F(t) = t² + t − 1 when x₁ = x₂ = t, with positive root t* = (√5 − 1)/2.
 * Newton's step follows the tangent to its zero; bisection halves a bracket.
 */
export const F = (t: number) => t * t + t - 1;
export const dF = (t: number) => 2 * t + 1;
export const ROOT = (Math.sqrt(5) - 1) / 2;
/** F(t) = (t − t*)(t + 1 + t*): the same value without cancellation, for drawing very near the root. */
export const fStable = (t: number) => (t - ROOT) * (t + 1 + ROOT);

export interface NewtonStep {
  /** Number of steps already taken before this one. */
  k: number;
  t: number;
  residual: number;
  slope: number;
  /** Zero of the tangent line at t: the next iterate's position on the axis F = 0. */
  next: number;
  nextResidual: number;
}

/** `count` Newton steps from t0 on F (valid while t0 > −1/2, where the slope is positive). */
export function newtonSteps(t0: number, count = 3): NewtonStep[] {
  const steps: NewtonStep[] = [];
  let t = t0;
  for (let k = 0; k < count; k += 1) {
    const slope = dF(t);
    const next = t - F(t) / slope;
    steps.push({ k, t, residual: fStable(t), slope, next, nextResidual: fStable(next) });
    t = next;
  }
  return steps;
}

export interface BisectionStep {
  k: number;
  lo: number;
  hi: number;
  mid: number;
  midResidual: number;
  /** Bracket kept after looking at the sign of F(mid). */
  nextLo: number;
  nextHi: number;
}

/** `count` bisection steps on a bracket with F(lo) < 0 < F(hi). */
export function bisectionSteps(lo0 = 0, hi0 = 1, count = 8): BisectionStep[] {
  const steps: BisectionStep[] = [];
  let lo = lo0;
  let hi = hi0;
  for (let k = 0; k < count; k += 1) {
    const mid = (lo + hi) / 2;
    const midResidual = F(mid);
    const nextLo = midResidual < 0 ? mid : lo;
    const nextHi = midResidual < 0 ? hi : mid;
    steps.push({ k, lo, hi, mid, midResidual, nextLo, nextHi });
    lo = nextLo;
    hi = nextHi;
  }
  return steps;
}

/** Correct decimal digits −log₁₀|x|, capped at 16 where double precision ends. */
export function digits(magnitude: number): number {
  const m = Math.abs(magnitude);
  if (m === 0) return 16;
  return Math.max(0, Math.min(16, -Math.log10(m)));
}

export interface Window {
  /** Domain window centre and half-width on the t axis. */
  center: number;
  half: number;
  /** Vertical half-range, symmetric around F = 0. */
  yHalf: number;
}

/** Fixed window that holds the whole bracket [0, 1] and every start t0 the slider allows. */
export const WIDE_WINDOW: Window = { center: 0.6, half: 0.7, yHalf: 1.8 };

/** Window around the root that keeps this step's tangent and its landing point in view. */
export function newtonWindow(step: NewtonStep): Window {
  const reach = Math.max(Math.abs(step.t - ROOT), Math.abs(step.next - ROOT));
  return { center: ROOT, half: reach * 1.5, yHalf: Math.abs(step.residual) * 1.3 };
}

/** Window around a bracket: a little wider than the bracket, tall enough for both ends. */
export function bracketWindow(lo: number, hi: number): Window {
  const half = (hi - lo) * 0.75;
  return { center: (lo + hi) / 2, half, yHalf: Math.max(Math.abs(F(lo)), Math.abs(F(hi)), 1e-12) * 1.3 };
}

/** Interpolates two windows with the width on a log scale, so zooming looks even. */
export function blendWindow(a: Window, b: Window, u: number): Window {
  const mixLog = (x: number, y: number) => Math.exp(Math.log(x) * (1 - u) + Math.log(y) * u);
  return {
    center: a.center + (b.center - a.center) * u,
    half: mixLog(a.half, b.half),
    yHalf: mixLog(a.yHalf, b.yHalf),
  };
}

export const smooth = (u: number) => u * u * (3 - 2 * u);

/** The article's two-variable system: F₁ = x₁² + x₂ − 1, F₂ = x₁ + x₂² − 1. */
export const residual2 = (x1: number, x2: number): [number, number] => [x1 * x1 + x2 - 1, x1 + x2 * x2 - 1];
/** Jacobian determinant 4·x₁·x₂ − 1: zero on the curve where the pure Newton step is undefined. */
export const jacobianDet2 = (x1: number, x2: number) => 4 * x1 * x2 - 1;

/** The point on the diagonal where the Jacobian is [[1, 1], [1, 1]] and has no inverse. */
export const SINGULAR_POINT = { x1: 0.5, x2: 0.5 } as const;

/** The four roots of the system (the diagonal ones are (−1 ± √5)/2). */
export const PLANE_ROOTS: ReadonlyArray<readonly [number, number]> = [
  [ROOT, ROOT], [1, 0], [0, 1], [-(1 + Math.sqrt(5)) / 2, -(1 + Math.sqrt(5)) / 2],
];

export interface PlanePath {
  points: Array<readonly [number, number]>;
  /** True when a step could not be taken because the Jacobian is singular there. */
  stuck: boolean;
}

/** Pure Newton steps J p = −F on the two-variable system, stopping where det J = 0. */
export function planeNewtonPath(x1: number, x2: number, count = 3): PlanePath {
  const points: Array<readonly [number, number]> = [[x1, x2]];
  let a = x1;
  let b = x2;
  for (let k = 0; k < count; k += 1) {
    const det = jacobianDet2(a, b);
    if (Math.abs(det) < 1e-9) return { points, stuck: true };
    const [f1, f2] = residual2(a, b);
    // J = [[2a, 1], [1, 2b]], so J⁻¹ = [[2b, −1], [−1, 2a]] / det.
    const p1 = -(2 * b * f1 - f2) / det;
    const p2 = -(-f1 + 2 * a * f2) / det;
    a += p1;
    b += p2;
    points.push([a, b]);
  }
  return { points, stuck: false };
}
