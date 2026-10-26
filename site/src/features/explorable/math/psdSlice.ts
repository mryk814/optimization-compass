/**
 * The SDP article's slice X = [[1, r], [r, 4]]: diagonal fixed at 1 and 4, covariance r free.
 * X is positive semidefinite exactly when both eigenvalues are ≥ 0, i.e. when det = 4 − r² ≥ 0.
 */
export const X11 = 1;
export const X22 = 4;
/** Largest |r| that keeps the slice positive semidefinite: √(X11·X22). */
export const R_LIMIT = Math.sqrt(X11 * X22);
const ON_BOUNDARY = 1e-9;

export function determinant(r: number, a = X11, c = X22): number {
  return a * c - r * r;
}

/** Eigenvalues of [[a, r], [r, c]], smaller first. */
export function eigenvalues(r: number, a = X11, c = X22): [number, number] {
  const centre = (a + c) / 2;
  const spread = Math.hypot((a - c) / 2, r);
  return [centre - spread, centre + spread];
}

export type PsdState = "inside" | "boundary" | "outside";

export function psdState(r: number): PsdState {
  const d = determinant(r);
  if (Math.abs(d) < ON_BOUNDARY) return "boundary";
  return d > 0 ? "inside" : "outside";
}

/** Smallest X22 = s that keeps [[1, r], [r, s]] semidefinite: the parabola s = r². */
export const boundaryS = (r: number) => r * r;

/** The article's objective −r, to be minimized. */
export const objective = (r: number) => -r;

/** Playback: r climbs 0 → 2 at 0.05 per step, rests on the boundary for HOLD steps, then goes on to 3. */
export const SWEEP_RATE = 0.05;
export const SWEEP_HOLD_STEPS = 10;
const SWEEP_REACH_STEPS = Math.round(R_LIMIT / SWEEP_RATE);
export const SWEEP_LENGTH = SWEEP_REACH_STEPS + SWEEP_HOLD_STEPS + Math.round((3 - R_LIMIT) / SWEEP_RATE);

export function sweepR(position: number): number {
  if (position <= SWEEP_REACH_STEPS) return position * SWEEP_RATE;
  if (position <= SWEEP_REACH_STEPS + SWEEP_HOLD_STEPS) return R_LIMIT;
  return R_LIMIT + (position - SWEEP_REACH_STEPS - SWEEP_HOLD_STEPS) * SWEEP_RATE;
}

/** λ₁·λ₂ equals the determinant 4 − r², and λ₁ + λ₂ equals the trace 5. */
export const eigenProduct = (r: number) => {
  const [low, high] = eigenvalues(r);
  return low * high;
};
export const eigenSum = (r: number) => {
  const [low, high] = eigenvalues(r);
  return low + high;
};

/** A weighted difference a − c·b has variance 1 − 2cr + 4c²; c = r/4 makes it smallest: 1 − r²/4. */
export const weightedDifferenceVariance = (r: number, c: number) => X11 - 2 * c * r + X22 * c * c;
export const smallestWeightedVariance = (r: number) => weightedDifferenceVariance(r, r / X22);
