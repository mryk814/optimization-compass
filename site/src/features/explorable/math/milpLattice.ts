import { feasibleVertices, isFeasible, objectiveValue, type HalfPlane, type Vec2 } from "./lp2d";

/** Profit per unit of product A and B in the MILP article: max 5x1 + 4x2. */
export const MILP_PROFIT: Vec2 = [5, 4];

/** Resource use per unit: 6x1 + 4x2 <= b1 and x1 + 2x2 <= b2. */
export const MILP_USE: readonly [Vec2, Vec2] = [[6, 4], [1, 2]];

/** The article's resource limits. */
export const MILP_ARTICLE_LIMITS: Vec2 = [24, 6];

export const MILP_LIMIT_RANGE = {
  b1: { min: 12, max: 36, step: 1 },
  b2: { min: 3, max: 12, step: 1 },
} as const;

/** Largest coordinate the plot ever needs: x1 <= min(b1/6, b2) <= 6 and x2 <= min(b1/4, b2/2) <= 6. */
export const LATTICE_MAX = 7;

export function milpConstraints(b1: number, b2: number): HalfPlane[] {
  return [
    { a: MILP_USE[0], b: b1, label: "資源1" },
    { a: MILP_USE[1], b: b2, label: "資源2" },
    { a: [-1, 0], b: 0, label: "x₁ ≥ 0", unlabeled: true },
    { a: [0, -1], b: 0, label: "x₂ ≥ 0", unlabeled: true },
  ];
}

export interface LatticePoint {
  x: number;
  y: number;
  /** Inside the LP relaxation (every integer point inside is a feasible plan). */
  inside: boolean;
}

export interface MilpSolution {
  vertices: Vec2[];
  lpPoint: Vec2;
  /** Profit at the LP optimum: an upper bound on every integer plan. */
  lpValue: number;
  lpIsInteger: boolean;
  /** The LP optimum with each coordinate rounded to the nearest integer (halves go up). */
  rounded: Vec2;
  roundedFeasible: boolean;
  roundedValue: number;
  /** How much each resource limit is exceeded by the rounded point (0 when it fits). */
  roundedExcess: Vec2;
  /** Every integer point of the plot window, flagged by whether the LP relaxation contains it. */
  lattice: LatticePoint[];
  insideCount: number;
  integerBest: Vec2;
  integerValue: number;
  /** Number of integer plans that tie for the best profit. */
  integerTies: number;
  /** lpValue - integerValue, never negative. */
  gap: number;
}

export function roundHalfUp(value: number): number {
  return Math.floor(value + 0.5 + 1e-9);
}

/**
 * Exact LP optimum by vertex enumeration, the integer optimum by listing every lattice point.
 * Both use the same constraint rows, so the bound and the plan can never disagree.
 */
export function solveMilp(b1: number, b2: number): MilpSolution {
  const constraints = milpConstraints(b1, b2);
  const vertices = feasibleVertices(constraints);
  const lpPoint = vertices.reduce((best, vertex) => (
    objectiveValue(MILP_PROFIT, vertex) > objectiveValue(MILP_PROFIT, best) + 1e-9 ? vertex : best
  ));
  const lpValue = objectiveValue(MILP_PROFIT, lpPoint);
  const rounded: Vec2 = [roundHalfUp(lpPoint[0]), roundHalfUp(lpPoint[1])];
  const roundedFeasible = isFeasible(constraints, rounded);

  const lattice: LatticePoint[] = [];
  let integerBest: Vec2 = [0, 0];
  let integerValue = -Infinity;
  let integerTies = 0;
  for (let x = 0; x <= LATTICE_MAX; x += 1) {
    for (let y = 0; y <= LATTICE_MAX; y += 1) {
      const inside = isFeasible(constraints, [x, y]);
      lattice.push({ x, y, inside });
      if (!inside) continue;
      const value = objectiveValue(MILP_PROFIT, [x, y]);
      if (value > integerValue) {
        integerValue = value;
        integerBest = [x, y];
        integerTies = 1;
      } else if (value === integerValue) {
        integerTies += 1;
      }
    }
  }

  const excess = (row: Vec2, limit: number) => Math.max(0, row[0] * rounded[0] + row[1] * rounded[1] - limit);
  return {
    vertices,
    lpPoint,
    lpValue,
    lpIsInteger: Math.abs(lpPoint[0] - Math.round(lpPoint[0])) < 1e-9
      && Math.abs(lpPoint[1] - Math.round(lpPoint[1])) < 1e-9,
    rounded,
    roundedFeasible,
    roundedValue: objectiveValue(MILP_PROFIT, rounded),
    roundedExcess: [excess(MILP_USE[0], b1), excess(MILP_USE[1], b2)],
    lattice,
    insideCount: lattice.filter((point) => point.inside).length,
    integerBest,
    integerValue,
    integerTies,
    gap: Math.max(0, lpValue - integerValue),
  };
}
