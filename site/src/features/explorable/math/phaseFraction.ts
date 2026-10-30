/**
 * The external-solver article's two-phase alloy A–B at a fixed temperature. The stand-in "tool"
 * gets the B fraction x and returns the phase combination with the lowest Gibbs energy, using
 * the teaching parabolas g_α = (x − 0.1)² and g_β = (x − 0.6)² + 0.1. Their common tangent
 * touches at x_α = 0.2 and x_β = 0.7: G = 0.2x − 0.03.
 */
export const X_ALPHA = 0.2;
export const X_BETA = 0.7;
export const TARGET = 0.3;
/** Where the outer objective J = (f_β − 0.30)² is zero. */
export const BEST_X = X_ALPHA + TARGET * (X_BETA - X_ALPHA);
/** Where the equilibrium Gibbs energy itself is lowest (the pitfall of minimizing G outside). */
export const LOWEST_G_X = 0.1;

export const gAlpha = (x: number) => (x - 0.1) ** 2;
export const gBeta = (x: number) => (x - 0.6) ** 2 + 0.1;
export const tangent = (x: number) => 0.2 * x - 0.03;

export type Phases = "α" | "β" | "α+β";

export interface Candidate {
  phases: Phases;
  fBeta: number;
  g: number;
}

export interface Equilibrium {
  /** α alone, β alone, and α+β when x lies strictly between the tangent points. */
  candidates: Candidate[];
  chosen: Candidate;
}

/** What the stand-in tool compares and returns for one composition. */
export function equilibrium(x: number): Equilibrium {
  const candidates: Candidate[] = [
    { phases: "α", fBeta: 0, g: gAlpha(x) },
    { phases: "β", fBeta: 1, g: gBeta(x) },
  ];
  if (x > X_ALPHA && x < X_BETA) {
    candidates.push({ phases: "α+β", fBeta: (x - X_ALPHA) / (X_BETA - X_ALPHA), g: tangent(x) });
  }
  // The first lowest wins, as Python's min does in the article's code.
  const chosen = candidates.reduce((best, c) => (c.g < best.g ? c : best));
  return { candidates, chosen };
}

export const betaFraction = (x: number) => equilibrium(x).chosen.fBeta;
export const equilibriumG = (x: number) => equilibrium(x).chosen.g;
export const objectiveJ = (x: number) => (betaFraction(x) - TARGET) ** 2;

/** dJ/dx: zero where β is absent or alone, 8(x − 0.35) on the two-phase range. */
export function objectiveSlope(x: number): number {
  if (x <= X_ALPHA || x >= X_BETA) return 0;
  return (2 * (betaFraction(x) - TARGET)) / (X_BETA - X_ALPHA);
}
