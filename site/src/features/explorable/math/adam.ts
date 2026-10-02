import { DIVERGENCE_LIMIT, valleyGradient, valleyValue, type ValleyProblem } from "./descent";

export interface AdamOptions {
  eta: number;
  beta1: number;
  beta2: number;
  epsilon: number;
  /** Standard deviation of the Gaussian noise added to each gradient coordinate. */
  noise: number;
  seed: number;
  maxSteps: number;
}

/** One coordinate of one Adam step: what was measured, what was remembered, and how far it moved. */
export interface AdamCoordinate {
  /** Gradient used for this step (noisy when noise > 0). */
  g: number;
  /** Bias-corrected first moment m̂. */
  mHat: number;
  /** √v̂: bias-corrected root mean square of past gradients. */
  rms: number;
  /** m̂ / (√v̂ + ε): the step in units of η. Its magnitude never exceeds about 1 for these betas. */
  ratio: number;
  /** Signed change of the coordinate, −η · ratio. */
  move: number;
}

export interface AdamStep {
  /** 1-based step index t; the point is where the step starts. */
  t: number;
  x: number;
  y: number;
  f: number;
  cx: AdamCoordinate;
  cy: AdamCoordinate;
}

export interface AdamRun {
  steps: AdamStep[];
  /** Points visited: the start, then the point after each step. */
  path: Array<readonly [number, number]>;
  values: number[];
}

export const ADAM_DEFAULTS = { beta1: 0.9, beta2: 0.999, epsilon: 1e-8 } as const;

/** Deterministic uniform numbers in [0, 1) (mulberry32), so a seed always gives the same noise. */
export function seededUniform(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let z = state;
    z = Math.imul(z ^ (z >>> 15), z | 1);
    z ^= z + Math.imul(z ^ (z >>> 7), z | 61);
    return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
  };
}

/** Standard normal numbers by Box–Muller from a seeded uniform source. */
export function seededNormal(seed: number): () => number {
  const uniform = seededUniform(seed);
  return () => {
    const u = Math.max(uniform(), 1e-12);
    const v = uniform();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
}

export function runAdam(
  problem: ValleyProblem,
  start: readonly [number, number],
  options: AdamOptions,
): AdamRun {
  const normal = seededNormal(options.seed);
  const { eta, beta1, beta2, epsilon, noise } = options;
  let [x, y] = start;
  let mx = 0;
  let my = 0;
  let vx = 0;
  let vy = 0;
  const steps: AdamStep[] = [];
  const path: Array<readonly [number, number]> = [[x, y]];
  const values = [valleyValue(problem, x, y)];
  const coordinate = (g: number, m: number, v: number, t: number): AdamCoordinate => {
    const mHat = m / (1 - beta1 ** t);
    const rms = Math.sqrt(v / (1 - beta2 ** t));
    const ratio = mHat / (rms + epsilon);
    return { g, mHat, rms, ratio, move: -eta * ratio };
  };
  for (let t = 1; t <= options.maxSteps; t += 1) {
    const [exactX, exactY] = valleyGradient(problem, x, y);
    // Draw both coordinates every step so the noise sequence does not depend on the settings.
    const nx = normal();
    const ny = normal();
    const gx = exactX + noise * nx;
    const gy = exactY + noise * ny;
    mx = beta1 * mx + (1 - beta1) * gx;
    my = beta1 * my + (1 - beta1) * gy;
    vx = beta2 * vx + (1 - beta2) * gx * gx;
    vy = beta2 * vy + (1 - beta2) * gy * gy;
    const cx = coordinate(gx, mx, vx, t);
    const cy = coordinate(gy, my, vy, t);
    steps.push({ t, x, y, f: valleyValue(problem, x, y), cx, cy });
    x += cx.move;
    y += cy.move;
    path.push([x, y]);
    values.push(valleyValue(problem, x, y));
  }
  return { steps, path, values };
}

/** Plain gradient descent with the same η, for the comparison overlay. Stops once it blows up. */
export function runPlainDescent(
  problem: ValleyProblem,
  start: readonly [number, number],
  eta: number,
  maxSteps: number,
): { path: Array<readonly [number, number]>; diverged: boolean } {
  let [x, y] = start;
  const path: Array<readonly [number, number]> = [[x, y]];
  for (let k = 0; k < maxSteps; k += 1) {
    const [gx, gy] = valleyGradient(problem, x, y);
    x -= eta * gx;
    y -= eta * gy;
    path.push([x, y]);
    if (!Number.isFinite(x + y) || valleyValue(problem, x, y) > DIVERGENCE_LIMIT) {
      return { path, diverged: true };
    }
  }
  return { path, diverged: valleyValue(problem, x, y) > valleyValue(problem, start[0], start[1]) };
}
