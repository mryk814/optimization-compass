/**
 * Constant fit to observations (0, 0, 0, m) under the squared loss and the Huber loss.
 * It is the article's "same four observations" example (robust-regression.md): the model is one
 * constant x, so each residual's derivative with respect to x is 1 and an observation's
 * contribution to the objective's gradient is exactly the loss slope ψ(r).
 */
export const BASE_OBSERVATIONS: readonly number[] = [0, 0, 0, 10];

/** Squared loss r²/2 (the article's convention) and its slope. */
export const squaredLoss = (r: number): number => 0.5 * r * r;
export const squaredSlope = (r: number): number => r;

/** Huber loss ρ_δ: quadratic up to δ, then linear with the same value and slope at |r| = δ. */
export function huberLoss(r: number, delta: number): number {
  const a = Math.abs(r);
  return a <= delta ? 0.5 * r * r : delta * (a - 0.5 * delta);
}

/** ψ_δ(r) = ρ'_δ(r): r inside [−δ, δ], otherwise ±δ. */
export function huberSlope(r: number, delta: number): number {
  return Math.min(delta, Math.max(-delta, r));
}

/** The squared-loss minimiser of a constant is the mean. */
export function fitSquared(ys: readonly number[]): number {
  return ys.reduce((total, y) => total + y, 0) / ys.length;
}

/**
 * The Huber minimiser of a constant: the root of Σ ψ_δ(x − y_i), which is non-decreasing in x.
 * Bisection on [min y, max y] (the root always lies there) to machine precision.
 */
export function fitHuber(ys: readonly number[], delta: number): number {
  let low = Math.min(...ys);
  let high = Math.max(...ys);
  for (let i = 0; i < 200 && high - low > 1e-15; i += 1) {
    const mid = 0.5 * (low + high);
    const slope = ys.reduce((total, y) => total + huberSlope(mid - y, delta), 0);
    if (slope > 0) high = mid;
    else low = mid;
  }
  return 0.5 * (low + high);
}

/**
 * Closed form for the data (0, 0, 0, m), m ≥ 0: x⋆ = min(m/4, δ/3).
 * The explorable computes with `fitHuber`; this is the article's formula, pinned against it in tests.
 */
export function articleClosedForm(m: number, delta: number): number {
  return Math.min(m / 4, delta / 3);
}

export type LossKind = "squared" | "huber";

export interface ConstantFit {
  x: number;
  residuals: number[];
  /** ψ(r_i): each observation's contribution to the objective's gradient. */
  slopes: number[];
  /** Σ ρ(r_i). */
  objective: number;
  /** Σ ψ(r_i): zero at the minimiser. */
  slopeSum: number;
  /** How many residuals sit past δ (always 0 for the squared loss). */
  capped: number;
}

export function evaluateConstant(ys: readonly number[], x: number, loss: LossKind, delta: number): ConstantFit {
  const residuals = ys.map((y) => x - y);
  const slopes = residuals.map((r) => (loss === "squared" ? squaredSlope(r) : huberSlope(r, delta)));
  const objective = residuals.reduce((t, r) => t + (loss === "squared" ? squaredLoss(r) : huberLoss(r, delta)), 0);
  return {
    x,
    residuals,
    slopes,
    objective,
    slopeSum: slopes.reduce((t, s) => t + s, 0),
    capped: loss === "squared" ? 0 : residuals.filter((r) => Math.abs(r) > delta).length,
  };
}

export interface RobustComparison {
  ys: number[];
  delta: number;
  squared: ConstantFit;
  huber: ConstantFit;
}

/** Both fits for the observations (0, 0, 0, m) at Huber scale δ. */
export function compareFits(m: number, delta: number): RobustComparison {
  const ys = [0, 0, 0, m];
  return {
    ys,
    delta,
    squared: evaluateConstant(ys, fitSquared(ys), "squared", delta),
    huber: evaluateConstant(ys, fitHuber(ys, delta), "huber", delta),
  };
}
