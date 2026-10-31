/**
 * Exponential-decay fit y = a·exp(−k t) to five readings: the running example of the
 * Gauss–Newton and Levenberg–Marquardt articles. Cost is ½Σr² with r = model − observation.
 * One trial solves (JᵀJ + λI) p = −Jᵀr; Gauss–Newton is λ = 0 and always moves.
 */
export const EXP_T: readonly number[] = [0, 1, 2, 3, 4];
export const EXP_Y: readonly number[] = [5.1, 3.0, 1.9, 1.1, 0.7];

export interface FitPoint {
  a: number;
  k: number;
}

export type FitMode = "gn" | "lm";

/** Rule used by the articles' teaching LM: accept → λ/3, reject → λ×10. */
export const LM_ACCEPT_FACTOR = 1 / 3;
export const LM_REJECT_FACTOR = 10;
/** A trial whose predicted decrease is below this ends the run: nothing left to gain. */
export const CONVERGED_PREDICTED = 1e-9;
export const MAX_TRIALS = 14;

export function residuals({ a, k }: FitPoint): number[] {
  return EXP_T.map((t, index) => a * Math.exp(-k * t) - EXP_Y[index]);
}

export function cost(p: FitPoint): number {
  return 0.5 * residuals(p).reduce((total, r) => total + r * r, 0);
}

/** Rows of the Jacobian: ∂r/∂a = e^(−kt), ∂r/∂k = −a t e^(−kt). */
export function jacobian({ a, k }: FitPoint): Array<readonly [number, number]> {
  return EXP_T.map((t) => {
    const e = Math.exp(-k * t);
    return [e, -a * t * e] as const;
  });
}

/** Model value at time t, for drawing the fitted curve. */
export function modelAt({ a, k }: FitPoint, t: number): number {
  return a * Math.exp(-k * t);
}

export interface Trial {
  from: FitPoint;
  lambda: number;
  step: FitPoint;
  candidate: FitPoint;
  stepLength: number;
  /** Angle in degrees between the step and the steepest-descent direction −Jᵀr. */
  descentAngleDeg: number;
  /** Unit vector of the steepest-descent direction −Jᵀr (zero when the gradient vanishes). */
  gradDir: FitPoint;
  costBefore: number;
  costAfter: number;
  /** Decrease the damping-free linear model predicts: ½‖r‖² − ½‖r + Jp‖². */
  predicted: number;
  /** Decrease actually obtained: ½‖r(x)‖² − ½‖r(x+p)‖². */
  actual: number;
  /** actual / predicted. */
  rho: number;
  accepted: boolean;
}

export type Outcome = "converged" | "budget" | "singular";

export interface Run {
  trials: Trial[];
  outcome: Outcome;
}

/** One trial from `from` with damping `lambda`; `mode` decides whether it is kept. */
export function trialAt(from: FitPoint, lambda: number, mode: FitMode): Trial | undefined {
  const r = residuals(from);
  const rows = jacobian(from);
  let m11 = lambda;
  let m22 = lambda;
  let m12 = 0;
  let g1 = 0;
  let g2 = 0;
  rows.forEach(([ja, jk], index) => {
    m11 += ja * ja;
    m12 += ja * jk;
    m22 += jk * jk;
    g1 += ja * r[index];
    g2 += jk * r[index];
  });
  const det = m11 * m22 - m12 * m12;
  if (!Number.isFinite(det) || Math.abs(det) < 1e-14) return undefined;
  const step = { a: (-g1 * m22 + g2 * m12) / det, k: (-g2 * m11 + g1 * m12) / det };
  const candidate = { a: from.a + step.a, k: from.k + step.k };
  const costBefore = cost(from);
  const costAfter = cost(candidate);
  const linear = rows.reduce((total, [ja, jk], index) => total + (r[index] + ja * step.a + jk * step.k) ** 2, 0) / 2;
  const predicted = costBefore - linear;
  const actual = costBefore - costAfter;
  const rho = predicted > 0 ? actual / predicted : Number.NaN;
  const stepLength = Math.hypot(step.a, step.k);
  const gradLength = Math.hypot(g1, g2);
  const cosine = stepLength > 0 && gradLength > 0 ? (-(g1 * step.a + g2 * step.k)) / (stepLength * gradLength) : 1;
  const descentAngleDeg = (Math.acos(Math.min(1, Math.max(-1, cosine))) * 180) / Math.PI;
  const accepted = mode === "gn" ? Number.isFinite(costAfter) : Number.isFinite(costAfter) && rho > 0;
  const gradDir = gradLength > 0 ? { a: -g1 / gradLength, k: -g2 / gradLength } : { a: 0, k: 0 };
  return { from, lambda, step, candidate, stepLength, descentAngleDeg, gradDir, costBefore, costAfter, predicted, actual, rho, accepted };
}

/**
 * Up to `maxTrials` trials. Gauss–Newton ignores `lambda0` and takes every step.
 * Levenberg–Marquardt starts at `lambda0`, keeps a step only when ρ > 0, and moves λ by the rule above.
 */
export function runTrials(mode: FitMode, start: FitPoint, lambda0: number, maxTrials = MAX_TRIALS): Run {
  const trials: Trial[] = [];
  let p = start;
  let lambda = mode === "gn" ? 0 : lambda0;
  let outcome: Outcome = "budget";
  for (let n = 0; n < maxTrials; n += 1) {
    const trial = trialAt(p, lambda, mode);
    if (!trial) { outcome = "singular"; break; }
    trials.push(trial);
    if (trial.predicted < CONVERGED_PREDICTED) { outcome = "converged"; break; }
    if (trial.accepted) {
      p = trial.candidate;
      if (mode === "lm") lambda *= LM_ACCEPT_FACTOR;
    } else {
      lambda *= LM_REJECT_FACTOR;
    }
  }
  return { trials, outcome };
}

/** The current point after the first `count` trials. */
export function pointAfter(run: Run, start: FitPoint, count: number): FitPoint {
  let p = start;
  for (const trial of run.trials.slice(0, count)) if (trial.accepted) p = trial.candidate;
  return p;
}

/**
 * Cost along the step direction: the true cost at from + s·p, and the damping-free linear
 * model ½‖r + s·J p‖² that Gauss–Newton trusts. At s = 1 they are costAfter and costBefore − predicted.
 */
export function alongStep(trial: Trial, s: number): { actual: number; model: number } {
  const point = { a: trial.from.a + s * trial.step.a, k: trial.from.k + s * trial.step.k };
  const r = residuals(trial.from);
  const model = jacobian(trial.from).reduce(
    (total, [ja, jk], index) => total + (r[index] + s * (ja * trial.step.a + jk * trial.step.k)) ** 2,
    0,
  ) / 2;
  return { actual: cost(point), model };
}

export interface ObservationReading {
  t: number;
  observed: number;
  /** y + (r + J p): where the linearized model says the curve will pass after the whole step. */
  linearized: number;
  /** y + r(x + p): where the curve really passes after the whole step. */
  actual: number;
}

/** Per observation: the linearized prediction against the real value at the end of a trial's step. */
export function observationReadings(trial: Trial): ObservationReading[] {
  const r = residuals(trial.from);
  const after = residuals(trial.candidate);
  return jacobian(trial.from).map(([ja, jk], index) => ({
    t: EXP_T[index],
    observed: EXP_Y[index],
    linearized: EXP_Y[index] + r[index] + ja * trial.step.a + jk * trial.step.k,
    actual: EXP_Y[index] + after[index],
  }));
}

/** The parameter points a run has visited: the start, then every accepted candidate among the first `count` trials. */
export function acceptedPath(run: Run, start: FitPoint, count = run.trials.length): FitPoint[] {
  const path = [start];
  for (const trial of run.trials.slice(0, count)) if (trial.accepted) path.push(trial.candidate);
  return path;
}

export interface CostHistory {
  /** Cost of the current point after 0..count trials; it stays flat across a rejected trial. */
  current: Array<{ n: number; cost: number }>;
  /** Cost a rejected trial reached at its candidate, which never became the current point. */
  rejected: Array<{ n: number; cost: number }>;
}

/** Splits the cost record into the accepted line and the rejected candidates, which must not be mixed. */
export function costHistory(run: Run, start: FitPoint, count: number): CostHistory {
  const current = [{ n: 0, cost: cost(start) }];
  const rejected: Array<{ n: number; cost: number }> = [];
  let p = start;
  run.trials.slice(0, count).forEach((trial, index) => {
    if (trial.accepted) p = trial.candidate;
    else rejected.push({ n: index + 1, cost: trial.costAfter });
    current.push({ n: index + 1, cost: cost(p) });
  });
  return { current, rejected };
}
