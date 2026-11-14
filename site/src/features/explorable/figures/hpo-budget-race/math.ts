import fixture from "./fixture.json";

/**
 * The 30-point example of content/concepts/hyperparameter-optimization.md. Every score here was
 * computed in Python (`hpo_race_data` in scripts/lesson_figures/hyperparameter_optimization.py):
 * the data, the 12 ways of splitting it, the random settings and the 5000 fresh points all depend
 * on Python's random numbers, so this file never re-creates them. It only counts over the scores
 * and fits the curves that are drawn (a ridge fit on the 30 points, checked against Python's).
 */
export const BUDGET = 16;
export const SPLITS: number = fixture.map.cv.length;
export const SEEDS: number = fixture.runs.random.length;
export const DEGREES: readonly number[] = fixture.space.degrees;
export const LOG_LAMS: readonly number[] = fixture.space.log_lam;
export const DATA_X: readonly number[] = fixture.data.x;
export const DATA_Y: readonly number[] = fixture.data.y;
/** Best score of 16 random settings, for 200 random seeds (split 0). */
export const RANDOM_BESTS: readonly number[] = fixture.random_bests_200;

export type Placement = "edge" | "center";
/** Which data a score was measured on: the 5-fold cross-validation, or the 5000 fresh points. */
export type Score = "cv" | "fresh";

export interface RacePoint {
  d: number;
  log_lam: number;
  /** Cross-validation error, one per split. */
  cv: readonly number[];
  /** Error on the fresh points of the curve fitted on all 30 points. */
  fresh: number;
}

export const gridRun = (placement: Placement): readonly RacePoint[] => (
  placement === "edge" ? fixture.runs.grid : fixture.runs.grid_mid
);
export const randomRun = (seed: number): readonly RacePoint[] => fixture.runs.random[seed];

export const scoreOf = (point: RacePoint, score: Score, split: number): number => (
  score === "cv" ? point.cv[split] : point.fresh
);

/** Score of a cell of the settings map; indices into DEGREES and LOG_LAMS. */
export const mapScore = (degreeIndex: number, lamIndex: number, score: Score, split: number): number => (
  score === "cv" ? fixture.map.cv[split][degreeIndex][lamIndex] : fixture.map.fresh[degreeIndex][lamIndex]
);

/** Index of the nearest lattice value of log10 λ. */
export const lamIndexOf = (logLam: number): number => (
  Math.min(LOG_LAMS.length - 1, Math.max(0, Math.round((logLam - LOG_LAMS[0]) / 0.5)))
);

/**
 * The setting a search would report after `count` evaluations: the lowest cross-validation score
 * so far (the first one on a tie). Settings are always chosen by cross-validation; the fresh
 * points are only ever used to re-measure what was chosen. -1 before the first evaluation.
 */
export function bestIndex(points: readonly RacePoint[], count: number, split: number): number {
  let best = -1;
  for (let index = 0; index < Math.min(count, points.length); index += 1) {
    if (best === -1 || points[index].cv[split] < points[best].cv[split]) best = index;
  }
  return best;
}

/** Lowest cross-validation score after each evaluation 1..16. */
export function bestSoFar(points: readonly RacePoint[], split: number): number[] {
  let low = Infinity;
  return points.map((point) => {
    low = Math.min(low, point.cv[split]);
    return low;
  });
}

/** How many different values of λ the first `count` evaluations tried. */
export const distinctLambdas = (points: readonly RacePoint[], count: number): number => (
  new Set(points.slice(0, count).map((point) => point.log_lam)).size
);

function legendreRow(x: number, degree: number): number[] {
  const row = [1, x];
  for (let n = 2; n <= degree; n += 1) row.push(((2 * n - 1) * x * row[n - 1] - (n - 1) * row[n - 2]) / n);
  return row.slice(0, degree + 1);
}

/** Gaussian elimination with partial pivoting, as `_solve_linear` in the Python module. */
function solve(matrix: number[][], rhs: number[]): number[] {
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

const DATA_ROWS = DATA_X.map((x) => legendreRow(x, DEGREES[DEGREES.length - 1]));
const fits = new Map<string, readonly number[]>();

/**
 * Legendre coefficients of the ridge fit on all 30 points: (AᵀA + nλI) w = Aᵀy. This is the curve
 * a setting stands for; its scores come from the fixture.
 */
export function fitCoefficients(degree: number, logLam: number): readonly number[] {
  const key = `${degree}|${logLam}`;
  const cached = fits.get(key);
  if (cached) return cached;
  const size = degree + 1;
  const penalty = DATA_X.length * 10 ** logLam;
  const gram = Array.from({ length: size }, (_, i) => Array.from({ length: size }, (_, j) => {
    let sum = i === j ? penalty : 0;
    for (const row of DATA_ROWS) sum += row[i] * row[j];
    return sum;
  }));
  const rhs = Array.from({ length: size }, (_, i) => DATA_ROWS.reduce((sum, row, k) => sum + row[i] * DATA_Y[k], 0));
  const coefficients = solve(gram, rhs);
  fits.set(key, coefficients);
  return coefficients;
}

export function curveValue(coefficients: readonly number[], x: number): number {
  const row = legendreRow(x, coefficients.length - 1);
  return coefficients.reduce((sum, c, i) => sum + c * row[i], 0);
}

/** The curve the data was drawn around. Known here only because the example is synthetic. */
export const truth = (x: number): number => Math.sin(3 * x) + 0.5 * x;

/** Position in [0, 1] of a score on the grey ramp of the map: pale at 0.13 or less, dark at 1 or more. */
export function shadeLevel(value: number): number {
  const t = (Math.log10(Math.max(value, 0.13)) - Math.log10(0.13)) / (0 - Math.log10(0.13));
  return Math.min(1, Math.max(0, t));
}
