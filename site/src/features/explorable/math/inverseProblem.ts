import fixture from "./inverseProblem.fixture.json";

/**
 * Rod example of content/concepts/inverse-problem.md: 40 blurred, noisy readings of a two-bump
 * temperature profile. The matrix, the truth and the noisy data are exported from Python
 * (`scripts/generate_lesson_figures.py`), so this file never re-creates the example; it only solves
 * the Tikhonov normal equations (GᵀG + αI) m = Gᵀd for a given α.
 */
export const INVERSE_N: number = fixture.n;
export const INVERSE_SIGMA: number = fixture.sigma;
/** Discrepancy level δ = σ√n: the size of the noise in the whole observation vector. */
export const INVERSE_DELTA = INVERSE_SIGMA * Math.sqrt(INVERSE_N);
export const INVERSE_ALPHA_MIN_LOG10 = -10;
export const INVERSE_ALPHA_MAX_LOG10 = 0;

const blur: readonly (readonly number[])[] = fixture.blur;
export const INVERSE_TRUTH: readonly number[] = fixture.truth;
export const INVERSE_DATA: readonly number[] = fixture.data;
/** Cell centres on [0, 1]. */
export const INVERSE_X: readonly number[] = Array.from({ length: INVERSE_N }, (_, i) => (i + 0.5) / INVERSE_N);

const norm = (v: readonly number[]) => Math.sqrt(v.reduce((sum, a) => sum + a * a, 0));

const gram: number[][] = Array.from({ length: INVERSE_N }, (_, i) => Array.from({ length: INVERSE_N }, (_, j) => {
  let sum = 0;
  for (let k = 0; k < INVERSE_N; k += 1) sum += blur[k][i] * blur[k][j];
  return sum;
}));
const gtd: number[] = Array.from({ length: INVERSE_N }, (_, i) => {
  let sum = 0;
  for (let k = 0; k < INVERSE_N; k += 1) sum += blur[k][i] * INVERSE_DATA[k];
  return sum;
});
const TRUTH_NORM = norm(INVERSE_TRUTH);

/** Gaussian elimination with partial pivoting (the same method as the Python figure generator). */
function solveLinear(matrix: number[][], rhs: number[]): number[] {
  const size = rhs.length;
  const a = matrix.map((row, i) => [...row, rhs[i]]);
  for (let col = 0; col < size; col += 1) {
    let pivot = col;
    for (let r = col + 1; r < size; r += 1) if (Math.abs(a[r][col]) > Math.abs(a[pivot][col])) pivot = r;
    [a[col], a[pivot]] = [a[pivot], a[col]];
    for (let r = col + 1; r < size; r += 1) {
      const factor = a[r][col] / a[col][col];
      for (let c = col; c <= size; c += 1) a[r][c] -= factor * a[col][c];
    }
  }
  const solution = new Array<number>(size).fill(0);
  for (let r = size - 1; r >= 0; r -= 1) {
    let tail = 0;
    for (let c = r + 1; c < size; c += 1) tail += a[r][c] * solution[c];
    solution[r] = (a[r][size] - tail) / a[r][r];
  }
  return solution;
}

export interface InverseReading {
  alpha: number;
  /** Reconstructed profile m_α. */
  m: number[];
  /** ‖m_α − m_true‖ / ‖m_true‖. Needs the truth, which a real problem does not have. */
  relativeError: number;
  /** ‖G m_α − d‖. */
  residual: number;
  /** ‖m_α‖. */
  length: number;
}

export function tikhonov(alpha: number): InverseReading {
  const shifted = gram.map((row, i) => row.map((v, j) => (i === j ? v + alpha : v)));
  const m = solveLinear(shifted, gtd);
  const error = norm(m.map((v, i) => v - INVERSE_TRUTH[i])) / TRUTH_NORM;
  const residual = norm(blur.map((row, k) => row.reduce((sum, a, j) => sum + a * m[j], 0) - INVERSE_DATA[k]));
  return { alpha, m, relativeError: error, residual, length: norm(m) };
}

/** Largest α in [1e-10, 1] whose residual reaches δ (discrepancy principle), by bisection on log10 α. */
export function discrepancyAlpha(): number {
  let lo = INVERSE_ALPHA_MIN_LOG10, hi = INVERSE_ALPHA_MAX_LOG10;
  for (let i = 0; i < 50; i += 1) {
    const mid = (lo + hi) / 2;
    if (tikhonov(10 ** mid).residual < INVERSE_DELTA) lo = mid; else hi = mid;
  }
  return 10 ** ((lo + hi) / 2);
}

/** Relative error on a log10 α grid, for locating the best α (answer check only). */
export function bestAlphaOnGrid(steps = 120): { alpha: number; relativeError: number } {
  let best = { alpha: 1, relativeError: Infinity };
  for (let i = 0; i <= steps; i += 1) {
    const alpha = 10 ** (-12 + (12 * i) / steps);
    const { relativeError } = tikhonov(alpha);
    if (relativeError < best.relativeError) best = { alpha, relativeError };
  }
  return best;
}
