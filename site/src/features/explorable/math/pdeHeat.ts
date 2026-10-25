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
