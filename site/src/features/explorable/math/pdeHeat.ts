/**
 * The PDE article's two-interior-point rod: −u″ = q, u(0) = u(1) = 0, h = 1/3, so K u = q with
 * K = 9·[[2, −1], [−1, 2]]. The objective is J = ½‖u − (1, 1)‖² + ‖q‖²/162.
 */
export const H = 1 / 3;
export const TARGET = 1;
const PENALTY_WEIGHT = 1 / 162;

/** u = K⁻¹ q, with K⁻¹ = (1/27)·[[2, 1], [1, 2]]. */
export function state(q1: number, q2: number): [number, number] {
  return [(2 * q1 + q2) / 27, (q1 + 2 * q2) / 27];
}

export const misfitTerm = (u: readonly [number, number]) =>
  0.5 * ((u[0] - TARGET) ** 2 + (u[1] - TARGET) ** 2);

export const penaltyTerm = (q1: number, q2: number) => PENALTY_WEIGHT * (q1 * q1 + q2 * q2);

export interface HeatBalance {
  q: number;
  u: [number, number];
  misfit: number;
  penalty: number;
  total: number;
}

/** Both heaters set to the same strength q (the diagonal of the article's table). */
export function balanceAt(q: number): HeatBalance {
  const u = state(q, q);
  const misfit = misfitTerm(u);
  const penalty = penaltyTerm(q, q);
  return { q, u, misfit, penalty, total: misfit + penalty };
}

/** The strength where the two terms are equal, which for this quadratic is also the minimum of J. */
export const BEST_Q = 4.5;

/** K·u for the two interior points: 9·(2u₁ − u₂, −u₁ + 2u₂). */
export const applyK = (u: readonly [number, number]): [number, number] => [
  9 * (2 * u[0] - u[1]),
  9 * (-u[0] + 2 * u[1]),
];

/** The state residual ‖K u − q‖: zero exactly when u really is the temperature that q produces. */
export function stateResidual(u: readonly [number, number], q1: number, q2: number): number {
  const ku = applyK(u);
  return Math.hypot(ku[0] - q1, ku[1] - q2);
}

export interface FreeBalance extends HeatBalance {
  /** ‖K u − q‖ */
  residual: number;
  /** The heat source that would make u consistent: K u = 9u at each point. */
  required: number;
}

/**
 * "Free u" contrast: u is chosen by hand (both points the same) and q is chosen separately,
 * so the heat equation is not enforced. The objective can look better than the true optimum.
 */
export function freeBalance(u: number, q: number): FreeBalance {
  const pair: [number, number] = [u, u];
  const misfit = misfitTerm(pair);
  const penalty = penaltyTerm(q, q);
  return {
    q, u: pair, misfit, penalty, total: misfit + penalty,
    residual: stateResidual(pair, q, q),
    required: applyK(pair)[0],
  };
}

/** Playback: q climbs RATE per step, rests HOLD steps at `restAt`, then goes on to the maximum. */
export const SWEEP_RATE = 0.25;
export const SWEEP_HOLD_STEPS = 8;
export const Q_MAX = 12;
export const SWEEP_LENGTH = Q_MAX / SWEEP_RATE + SWEEP_HOLD_STEPS;

export function sweepQ(position: number, restAt: number): number {
  const reach = restAt / SWEEP_RATE;
  if (position <= reach) return position * SWEEP_RATE;
  if (position <= reach + SWEEP_HOLD_STEPS) return restAt;
  return restAt + (position - reach - SWEEP_HOLD_STEPS) * SWEEP_RATE;
}
