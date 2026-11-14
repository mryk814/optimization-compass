/** A data point (t, y) and a line y = a + b t, the smallest linear least-squares problem. */
export interface DataPoint {
  t: number;
  y: number;
}

export interface Line {
  /** Intercept. */
  a: number;
  /** Slope. */
  b: number;
}

export interface LineFit {
  residuals: number[];
  /** Sum of squared residuals: the total area of the squares in the figure. */
  sse: number;
  /** Σ r_i and Σ t_i r_i. Both vanish exactly at the least-squares line. */
  residualSum: number;
  residualMoment: number;
  /** Gradient of the sum of squares with respect to (a, b): (−2 Σ r, −2 Σ t r). */
  gradient: readonly [number, number];
}

/** Residual r_i = y_i − (a + b t_i): positive when the point sits above the line. */
export function evaluateLine(points: readonly DataPoint[], line: Line): LineFit {
  const residuals = points.map((p) => p.y - (line.a + line.b * p.t));
  const sse = residuals.reduce((total, r) => total + r * r, 0);
  const residualSum = residuals.reduce((total, r) => total + r, 0);
  const residualMoment = residuals.reduce((total, r, index) => total + points[index].t * r, 0);
  return { residuals, sse, residualSum, residualMoment, gradient: [-2 * residualSum, -2 * residualMoment] };
}

/** Entries of the normal equations AᵀA x = Aᵀb for A = [1, t]. */
export interface NormalEquations {
  n: number;
  sumT: number;
  sumTT: number;
  sumY: number;
  sumTY: number;
}

export function normalEquations(points: readonly DataPoint[]): NormalEquations {
  return points.reduce<NormalEquations>(
    (acc, p) => ({
      n: acc.n + 1,
      sumT: acc.sumT + p.t,
      sumTT: acc.sumTT + p.t * p.t,
      sumY: acc.sumY + p.y,
      sumTY: acc.sumTY + p.t * p.y,
    }),
    { n: 0, sumT: 0, sumTT: 0, sumY: 0, sumTY: 0 },
  );
}

/**
 * The least-squares line from the 2×2 normal equations. With two parameters and well-spread t
 * this is exact and well conditioned; returns undefined when every t is the same.
 */
export function fitLine(points: readonly DataPoint[]): Line | undefined {
  const { n, sumT, sumTT, sumY, sumTY } = normalEquations(points);
  const det = n * sumTT - sumT * sumT;
  if (Math.abs(det) < 1e-12) return undefined;
  return { a: (sumTT * sumY - sumT * sumTY) / det, b: (n * sumTY - sumT * sumY) / det };
}

/** Sum of squares as a function of (a, b), for drawing the bowl in parameter space. */
export function sseAt(points: readonly DataPoint[], a: number, b: number): number {
  return points.reduce((total, p) => total + (p.y - a - b * p.t) ** 2, 0);
}
