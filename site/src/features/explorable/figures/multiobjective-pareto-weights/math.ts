/**
 * The bracket example of the multiobjective article: thickness x₁ and a needless ornament x₂,
 * both in [0, 1]. Weight f₁ = x₁ grows with thickness; deflection f₂ = h(x₁) + x₂ falls with
 * thickness and grows with the ornament. The Pareto set is the edge x₂ = 0 and the front is
 * f₂ = h(f₁): concave for h = 1 − x² and convex for h = 1 − √x.
 */
export type FrontShape = "concave" | "convex";
export type Design = readonly [number, number];

export const deflectionDrop = (x1: number, shape: FrontShape) => (shape === "concave" ? 1 - x1 * x1 : 1 - Math.sqrt(x1));

export function objectives([x1, x2]: Design, shape: FrontShape): readonly [number, number] {
  return [x1, deflectionDrop(x1, shape) + x2];
}

/** A design is Pareto optimal exactly when it carries no ornament. */
export const isParetoOptimal = ([, x2]: Design) => x2 < 1e-9;

/**
 * Minimizer of w f₁ + (1 − w) f₂ over the square. With a concave front the sum is concave in
 * x₁, so only an end of the front can win; with a convex front the minimizer slides along it.
 * Ties at the switching weight go to the thin end.
 */
export function weightedSumChoice(w: number, shape: FrontShape): Design {
  if (shape === "concave") return w < 0.5 ? [1, 0] : [0, 0];
  if (w <= 0) return [1, 0];
  const x1 = Math.min(1, ((1 - w) / (2 * w)) ** 2);
  return [x1, 0];
}

/** Minimizer of f₂ subject to f₁ ≤ ε: the thickest bracket the weight cap allows. */
export function epsilonChoice(epsilon: number): Design {
  return [Math.min(Math.max(epsilon, 0), 1), 0];
}

export function weightedSum([f1, f2]: readonly [number, number], w: number): number {
  return w * f1 + (1 - w) * f2;
}
