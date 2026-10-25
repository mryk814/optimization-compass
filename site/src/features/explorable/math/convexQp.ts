import type { Vec2 } from "./lp2d";

/**
 * The convex QP of the article: the point of the triangle {x1 + x2 <= b, x >= 0} nearest to a target p,
 * that is min (x1-p1)^2 + (x2-p2)^2. Q = 2I, so every active-set KKT system is a 1x1 or 2x2 solve.
 */
export const QP_ARTICLE_TARGET: Vec2 = [3, 2];
export const QP_ARTICLE_LIMIT = 3;

export const QP_RANGE = {
  target: { min: -1, max: 5, step: 0.5 },
  limit: { min: 1, max: 5, step: 0.5 },
} as const;

export interface QpConstraint {
  /** g(x) = a·x - h <= 0 */
  a: Vec2;
  label: string;
}

/** Constraint 0 is the sum limit; 1 and 2 are the non-negativity bounds. */
export function qpConstraints(): QpConstraint[] {
  return [
    { a: [1, 1], label: "x₁ + x₂ ≤ b" },
    { a: [-1, 0], label: "x₁ ≥ 0" },
    { a: [0, -1], label: "x₂ ≥ 0" },
  ];
}

function rhs(limit: number): number[] {
  return [limit, 0, 0];
}

const TOL = 1e-9;

export interface QpSolution {
  target: Vec2;
  limit: number;
  x: Vec2;
  /** (x1-p1)^2 + (x2-p2)^2 at x */
  value: number;
  /** Lagrange multiplier of each constraint (0 for the ones not in the active set). */
  multipliers: [number, number, number];
  /** Constraints used as equalities in the KKT system that was accepted. */
  activeSet: number[];
  /** Constraints satisfied with equality at x, including ones whose multiplier is 0. */
  tight: number[];
  targetInside: boolean;
  /** Distance from the target to x: the radius of the level circle through x. */
  radius: number;
  vertices: Vec2[];
  vertexValues: number[];
  bestVertex: Vec2;
  bestVertexValue: number;
  /** bestVertexValue - value: what comparing vertices alone would miss. */
  vertexGap: number;
  /** x is one of the vertices of the triangle. */
  atVertex: boolean;
}

function subsets(): number[][] {
  return [[], [0], [1], [2], [0, 1], [0, 2], [1, 2]];
}

/** Solves 2(x-p) + G^T λ = 0, G x = h for the rows in `set`; undefined when G is singular. */
function kktForSet(p: Vec2, limit: number, set: number[]): { x: Vec2; lambda: number[] } | undefined {
  const cons = qpConstraints();
  const h = rhs(limit);
  if (set.length === 0) return { x: [p[0], p[1]], lambda: [] };
  const rows = set.map((index) => cons[index].a);
  const heights = set.map((index) => h[index]);
  // λ = 2 (G G^T)^{-1} (G p - h), then x = p - G^T λ / 2.
  const gp = rows.map((row, i) => row[0] * p[0] + row[1] * p[1] - heights[i]);
  const gram = rows.map((r1) => rows.map((r2) => r1[0] * r2[0] + r1[1] * r2[1]));
  let inv: number[][];
  if (set.length === 1) {
    if (Math.abs(gram[0][0]) < TOL) return undefined;
    inv = [[1 / gram[0][0]]];
  } else {
    const det = gram[0][0] * gram[1][1] - gram[0][1] * gram[1][0];
    if (Math.abs(det) < TOL) return undefined;
    inv = [
      [gram[1][1] / det, -gram[0][1] / det],
      [-gram[1][0] / det, gram[0][0] / det],
    ];
  }
  const lambda = inv.map((row) => 2 * row.reduce((sum, value, j) => sum + value * gp[j], 0));
  const x: Vec2 = [
    p[0] - 0.5 * lambda.reduce((sum, value, i) => sum + value * rows[i][0], 0),
    p[1] - 0.5 * lambda.reduce((sum, value, i) => sum + value * rows[i][1], 0),
  ];
  return { x, lambda };
}

function distanceSquared(a: Vec2, b: Vec2): number {
  return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;
}

export function solveConvexQp(target: Vec2, limit: number): QpSolution {
  const cons = qpConstraints();
  const h = rhs(limit);
  const slack = (x: Vec2) => cons.map((c, i) => c.a[0] * x[0] + c.a[1] * x[1] - h[i]);

  // Smaller active sets are tried first, so a target that sits exactly on the boundary is reported
  // with an empty active set (multiplier 0) instead of a tie.
  let found: { x: Vec2; lambda: number[]; set: number[] } | undefined;
  for (const set of subsets()) {
    const candidate = kktForSet(target, limit, set);
    if (!candidate) continue;
    const feasible = slack(candidate.x).every((value) => value <= TOL);
    const dual = candidate.lambda.every((value) => value >= -TOL);
    if (feasible && dual) {
      found = { ...candidate, set };
      break;
    }
  }
  if (!found) throw new Error("no KKT point found for a convex QP over a non-empty triangle");

  const x: Vec2 = [found.x[0], found.x[1]];
  const multipliers: [number, number, number] = [0, 0, 0];
  found.set.forEach((index, i) => {
    multipliers[index] = Math.max(0, found.lambda[i]);
  });
  const tight = slack(x).flatMap((value, i) => (Math.abs(value) <= 1e-7 ? [i] : []));
  const vertices: Vec2[] = [[0, 0], [limit, 0], [0, limit]];
  const vertexValues = vertices.map((v) => distanceSquared(v, target));
  const best = vertexValues.indexOf(Math.min(...vertexValues));
  const value = distanceSquared(x, target);
  return {
    target,
    limit,
    x,
    value,
    multipliers,
    activeSet: found.set,
    tight,
    targetInside: found.set.length === 0 && distanceSquared(x, target) === 0
      && slack(target).every((s) => s < -1e-7),
    radius: Math.sqrt(value),
    vertices,
    vertexValues,
    bestVertex: vertices[best],
    bestVertexValue: vertexValues[best],
    vertexGap: vertexValues[best] - value,
    atVertex: tight.length >= 2,
  };
}

export interface RelaxResult {
  amount: number;
  /** λ₁ · amount: the first-order prediction of the improvement. */
  predicted: number;
  /** Exact v(b) - v(b + amount). */
  actual: number;
}

/** Loosening the sum limit b by `amount`: the multiplier's prediction against the exact re-solve. */
export function relaxSumLimit(target: Vec2, limit: number, amount: number): RelaxResult {
  const now = solveConvexQp(target, limit);
  const relaxed = solveConvexQp(target, limit + amount);
  return { amount, predicted: now.multipliers[0] * amount, actual: now.value - relaxed.value };
}
