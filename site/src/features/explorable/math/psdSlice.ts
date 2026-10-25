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
