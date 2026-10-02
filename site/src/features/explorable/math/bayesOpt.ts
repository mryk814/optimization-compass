/**
 * One-dimensional Bayesian optimisation small enough to compute exactly in the browser:
 * a Gaussian process with a fixed RBF kernel on standardised observations, and an acquisition
 * minimised over a fixed grid. Everything is deterministic, so a setting always gives one run.
 */

export type Acquisition = "lcb" | "ei";

export const BO_DOMAIN: readonly [number, number] = [0, 1];
export const BO_GRID_SIZE = 201;
export const BO_INITIAL: readonly number[] = [0.1, 0.45, 0.6];
export const BO_ITERATIONS = 10;
const JITTER = 1e-6;

/** The hidden objective: a broad shallow basin near 0.35 and a narrow deeper one near 0.84. */
export function boObjective(x: number): number {
  return 1
    - 0.7 * Math.exp(-(((x - 0.35) / 0.12) ** 2))
    - Math.exp(-(((x - 0.84) / 0.05) ** 2))
    + 0.15 * Math.sin(13 * x);
}

export const BO_GRID: readonly number[] = Array.from(
  { length: BO_GRID_SIZE },
  (_, index) => BO_DOMAIN[0] + ((BO_DOMAIN[1] - BO_DOMAIN[0]) * index) / (BO_GRID_SIZE - 1),
);

export interface Posterior {
  mean: number[];
  sd: number[];
}

const rbf = (a: number, b: number, lengthScale: number) => Math.exp(-0.5 * ((a - b) / lengthScale) ** 2);

/** Lower-triangular L with L Lᵀ = K. */
function cholesky(matrix: number[][]): number[][] {
  const n = matrix.length;
  const lower = matrix.map(() => new Array<number>(n).fill(0));
  for (let i = 0; i < n; i += 1) {
    for (let j = 0; j <= i; j += 1) {
      let sum = matrix[i][j];
      for (let k = 0; k < j; k += 1) sum -= lower[i][k] * lower[j][k];
      lower[i][j] = i === j ? Math.sqrt(Math.max(sum, 1e-18)) : sum / lower[j][j];
    }
  }
  return lower;
}

function forward(lower: number[][], rhs: number[]): number[] {
  const out = new Array<number>(rhs.length).fill(0);
  for (let i = 0; i < rhs.length; i += 1) {
    let sum = rhs[i];
    for (let k = 0; k < i; k += 1) sum -= lower[i][k] * out[k];
    out[i] = sum / lower[i][i];
  }
  return out;
}

function backward(lower: number[][], rhs: number[]): number[] {
  const n = rhs.length;
  const out = new Array<number>(n).fill(0);
  for (let i = n - 1; i >= 0; i -= 1) {
    let sum = rhs[i];
    for (let k = i + 1; k < n; k += 1) sum -= lower[k][i] * out[k];
    out[i] = sum / lower[i][i];
  }
  return out;
}

/**
 * GP posterior on `at` given observations. Outputs are standardised by the sample mean and
 * standard deviation before fitting and mapped back, so the prior band matches the data's spread.
 */
export function posterior(
  xs: readonly number[],
  ys: readonly number[],
  lengthScale: number,
  at: readonly number[] = BO_GRID,
): Posterior {
  const n = xs.length;
  const mu = ys.reduce((total, y) => total + y, 0) / n;
  const variance = ys.reduce((total, y) => total + (y - mu) ** 2, 0) / n;
  const scale = n > 1 && variance > 1e-18 ? Math.sqrt(variance) : 1;
  const z = ys.map((y) => (y - mu) / scale);
  const kernel = xs.map((a, i) => xs.map((b, j) => rbf(a, b, lengthScale) + (i === j ? JITTER : 0)));
  const lower = cholesky(kernel);
  const alpha = backward(lower, forward(lower, z));
  const mean: number[] = [];
  const sd: number[] = [];
  for (const point of at) {
    const k = xs.map((x) => rbf(point, x, lengthScale));
    const w = forward(lower, k);
    const explained = w.reduce((total, value) => total + value * value, 0);
    mean.push(mu + scale * k.reduce((total, value, i) => total + value * alpha[i], 0));
    sd.push(scale * Math.sqrt(Math.max(1 - explained, 1e-12)));
  }
  return { mean, sd };
}

/** Error function, Abramowitz–Stegun 7.1.26 (absolute error below 1.5e−7). */
function erf(x: number): number {
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x);
  const t = 1 / (1 + 0.3275911 * ax);
  const poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
  return sign * (1 - poly * Math.exp(-ax * ax));
}

const normalCdf = (z: number) => 0.5 * (1 + erf(z / Math.SQRT2));
const normalPdf = (z: number) => Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);

/** Expected improvement below `best` for a Gaussian prediction (mean, sd). */
export function expectedImprovement(mean: number, sd: number, best: number): number {
  if (sd < 1e-12) return Math.max(best - mean, 0);
  const z = (best - mean) / sd;
  return (best - mean) * normalCdf(z) + sd * normalPdf(z);
}

/**
 * Acquisition as a score to minimise, so both kinds read the same way in the figure:
 * LCB is μ − βσ; EI is negated.
 */
export function acquisitionScores(
  post: Posterior,
  kind: Acquisition,
  beta: number,
  best: number,
): number[] {
  return post.mean.map((mean, index) => (
    kind === "lcb" ? mean - beta * post.sd[index] : -expectedImprovement(mean, post.sd[index], best)
  ));
}

export interface BoState {
  /** Observations available when choosing (initial design plus earlier choices). */
  xs: number[];
  ys: number[];
  post: Posterior;
  scores: number[];
  /** Grid index and position of the next evaluation. */
  nextIndex: number;
  nextX: number;
  /** Best observed value so far (before evaluating nextX). */
  best: number;
  bestX: number;
}

export interface BoSettings {
  acquisition: Acquisition;
  beta: number;
  lengthScale: number;
}

/** Suggest from available observations only; never evaluate an unobserved point here. */
export function suggestBayesOpt(xs: readonly number[], ys: readonly number[], settings: BoSettings): BoState {
  const post = posterior(xs, ys, settings.lengthScale);
  let bestIndex = 0;
  for (let i = 1; i < ys.length; i += 1) if (ys[i] < ys[bestIndex]) bestIndex = i;
  const best = ys[bestIndex];
  const scores = acquisitionScores(post, settings.acquisition, settings.beta, best);
  let nextIndex = 0;
  for (let i = 1; i < scores.length; i += 1) if (scores[i] < scores[nextIndex]) nextIndex = i;
  return { xs: [...xs], ys: [...ys], post, scores, nextIndex, nextX: BO_GRID[nextIndex], best, bestX: xs[bestIndex] };
}

/** Each state is one decision: fit the posterior, score the grid, pick the minimum. */
export function runBayesOpt(settings: BoSettings, iterations = BO_ITERATIONS): BoState[] {
  const xs = [...BO_INITIAL];
  const ys = xs.map(boObjective);
  const states: BoState[] = [];
  for (let n = 0; n <= iterations; n += 1) {
    const state = suggestBayesOpt(xs, ys, settings);
    const nextIndex = state.nextIndex;
    states.push(state);
    if (n < iterations) {
      xs.push(BO_GRID[nextIndex]);
      ys.push(boObjective(BO_GRID[nextIndex]));
    }
  }
  return states;
}

/** Location and value of the objective's minimum on the grid, for the answer key. */
export function gridMinimum(): { x: number; value: number } {
  let index = 0;
  for (let i = 1; i < BO_GRID.length; i += 1) if (boObjective(BO_GRID[i]) < boObjective(BO_GRID[index])) index = i;
  return { x: BO_GRID[index], value: boObjective(BO_GRID[index]) };
}
