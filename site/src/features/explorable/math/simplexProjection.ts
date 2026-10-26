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

/** The projected point of the article: θ = 0.1 gives (0.8, 0.2, 0). */
export const PROJECTED = [0.8, 0.2, 0] as const;

/**
 * Triangle (ternary) drawing of the three-activity simplex. Vertex 0 (調査) is at the origin,
 * vertex 1 (制作) at (1, 0), vertex 2 (確認) at (1/2, √3/2). A point with total 1 sits at its
 * barycentric position; a point whose total is not 1 is drawn at its shadow on the plane Σ = 1.
 */
export const TRIANGLE_VERTICES: ReadonlyArray<readonly [number, number]> = [[0, 0], [1, 0], [0.5, Math.sqrt(3) / 2]];

/** Orthogonal projection of v onto the plane Σ = 1 (move along (1, 1, 1)). */
export function planeShadow(v: readonly number[]): number[] {
  const shift = (v.reduce((a, b) => a + b, 0) - 1) / v.length;
  return v.map((value) => value - shift);
}

/** Barycentric coordinates (total 1) to triangle drawing coordinates. */
export function triangleXY(b: readonly number[]): [number, number] {
  let x = 0;
  let y = 0;
  b.forEach((w, i) => {
    x += w * TRIANGLE_VERTICES[i][0];
    y += w * TRIANGLE_VERTICES[i][1];
  });
  return [x, y];
}

/** Drawing coordinates of any 3-vector's shadow on the plane Σ = 1. */
export const shadowXY = (v: readonly number[]) => triangleXY(planeShadow(v));

/** Euclidean distance between two 3-vectors (the distance the objective ½‖x − y‖² measures). */
export const distance3 = (a: readonly number[], b: readonly number[]) =>
  Math.hypot(...a.map((v, i) => v - b[i]));
