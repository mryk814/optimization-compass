/**
 * Euclidean projection onto the probability simplex, the way the simplex article draws it:
 * subtract one common amount θ from every wish, clip negatives to 0, and pick θ so the total is 1.
 */
export const WISH = [0.9, 0.3, 0.05] as const;

export const shiftedValues = (y: readonly number[], theta: number) => y.map((v) => v - theta);
export const clippedValues = (y: readonly number[], theta: number) => y.map((v) => Math.max(v - theta, 0));
export const clippedSum = (y: readonly number[], theta: number) => clippedValues(y, theta).reduce((a, b) => a + b, 0);

/** The θ that makes the clipped total exactly 1 (sort, then the largest prefix that stays positive). */
export function projectionTheta(y: readonly number[]): number {
  const sorted = [...y].sort((a, b) => b - a);
  let running = 0;
  let theta = 0;
  sorted.forEach((value, index) => {
    running += value;
    const candidate = (running - 1) / (index + 1);
    if (value - candidate > 0) theta = candidate;
  });
  return theta;
}

export interface ThetaProbe {
  lo: number;
  hi: number;
  mid: number;
  /** Total of the clipped values at `mid`; above 1 means θ is still too small. */
  sum: number;
}

/** Bisection on θ in [0, max y]: the clipped total only falls as θ grows, so look at the middle. */
export function bisectTheta(y: readonly number[], count: number): ThetaProbe[] {
  let lo = 0;
  let hi = Math.max(...y);
  const probes: ThetaProbe[] = [];
  for (let i = 0; i < count; i += 1) {
    const mid = (lo + hi) / 2;
    const sum = clippedSum(y, mid);
    probes.push({ lo, hi, mid, sum });
    if (sum > 1) lo = mid;
    else hi = mid;
  }
  return probes;
}

/** θ at each whole step: 0 before the search, then each probe's middle. */
export function thetaPath(y: readonly number[], count: number): number[] {
  return [0, ...bisectTheta(y, count).map((p) => p.mid)];
}

/** Dividing by the total: also sums to 1, but it is a different point. */
export const divideBySum = (y: readonly number[]) => {
  const total = y.reduce((a, b) => a + b, 0);
  return y.map((v) => v / total);
};

/** The article's objective ½‖x − y‖². */
export const halfSquaredDistance = (x: readonly number[], y: readonly number[]) =>
  0.5 * x.reduce((acc, v, i) => acc + (v - y[i]) ** 2, 0);
