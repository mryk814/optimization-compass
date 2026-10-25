import { feasibleVertices, objectiveValue, type HalfPlane, type Vec2 } from "./lp2d";

/** The production example of the variable-domain article: max 5x1 + 4x2, 6x1+4x2 <= 24, x1+2x2 <= 6. */
export const VD_PROFIT: Vec2 = [5, 4];
export const VD_USE: readonly [Vec2, Vec2] = [[6, 4], [1, 2]];
export const VD_LIMITS: Vec2 = [24, 6];

export type Domain = "continuous" | "integer" | "binary";

export const DOMAIN_LABEL: Record<Domain, string> = {
  continuous: "連続",
  integer: "整数",
  binary: "0か1",
};

/** The largest value an integer variable can take here: x1 <= 4 and x2 <= 3, so 0..6 never misses a plan. */
const INTEGER_MAX = 6;
const EPS = 1e-9;

export function baseConstraints(): HalfPlane[] {
  return [
    { a: VD_USE[0], b: VD_LIMITS[0], label: "資源1" },
    { a: VD_USE[1], b: VD_LIMITS[1], label: "資源2" },
    { a: [-1, 0], b: 0, label: "x₁ ≥ 0", unlabeled: true },
    { a: [0, -1], b: 0, label: "x₂ ≥ 0", unlabeled: true },
  ];
}

/** The continuous relaxation keeps the bound of a 0/1 variable (x <= 1) and drops integrality. */
export function relaxedConstraints(d1: Domain, d2: Domain): HalfPlane[] {
  const rows = baseConstraints();
  if (d1 === "binary") rows.push({ a: [1, 0], b: 1, label: "x₁ ≤ 1", unlabeled: true });
  if (d2 === "binary") rows.push({ a: [0, 1], b: 1, label: "x₂ ≤ 1", unlabeled: true });
  return rows;
}

export type FeasibleSet =
  | { kind: "region"; vertices: Vec2[] }
  | { kind: "segments"; segments: Array<[Vec2, Vec2]> }
  | { kind: "points"; points: Vec2[] };

export interface DomainSolution {
  d1: Domain;
  d2: Domain;
  /** The set of plans the reader may choose from. */
  feasible: FeasibleSet;
  /** The polygon of the continuous relaxation (same as `feasible` when both are continuous). */
  relaxedVertices: Vec2[];
  relaxedPoint: Vec2;
  relaxedValue: number;
  best: Vec2;
  bestValue: number;
  /** relaxedValue - bestValue, never negative. */
  gap: number;
  /** Candidate points or candidate slices; 0 when the set is a region. */
  candidateCount: number;
  /** True when the best point has a non-integer coordinate (only possible for a continuous variable). */
  bestHasFraction: boolean;
}

function discreteValues(domain: Domain): number[] {
  const top = domain === "binary" ? 1 : INTEGER_MAX;
  return Array.from({ length: top + 1 }, (_, value) => value);
}

function inside(point: Vec2): boolean {
  return VD_USE.every((row, index) => row[0] * point[0] + row[1] * point[1] <= VD_LIMITS[index] + EPS);
}

function argmax(points: readonly Vec2[]): Vec2 {
  return points.reduce((best, point) => (
    objectiveValue(VD_PROFIT, point) > objectiveValue(VD_PROFIT, best) + EPS ? point : best
  ));
}

/**
 * Exact optimum for every pair of domains: vertex enumeration for the relaxation and the all-continuous
 * case, a full list of plans when both variables are discrete, and a full list of slices (one value fixed,
 * the other continuous, whose best end is a closed form) when exactly one is.
 */
export function solveDomains(d1: Domain, d2: Domain): DomainSolution {
  const relaxedVertices = feasibleVertices(relaxedConstraints(d1, d2));
  const relaxedPoint = argmax(relaxedVertices);
  const relaxedValue = objectiveValue(VD_PROFIT, relaxedPoint);

  let feasible: FeasibleSet;
  let best: Vec2;
  let candidateCount = 0;

  if (d1 === "continuous" && d2 === "continuous") {
    feasible = { kind: "region", vertices: relaxedVertices };
    best = relaxedPoint;
  } else if (d1 !== "continuous" && d2 !== "continuous") {
    const points: Vec2[] = [];
    for (const x of discreteValues(d1)) {
      for (const y of discreteValues(d2)) {
        if (inside([x, y])) points.push([x, y]);
      }
    }
    feasible = { kind: "points", points };
    best = argmax(points);
    candidateCount = points.length;
  } else if (d2 === "continuous") {
    // x1 fixed at k: x2 may rise until the first resource runs out, and profit grows with x2.
    const segments: Array<[Vec2, Vec2]> = [];
    for (const k of discreteValues(d1)) {
      const top = Math.min(
        (VD_LIMITS[0] - VD_USE[0][0] * k) / VD_USE[0][1],
        (VD_LIMITS[1] - VD_USE[1][0] * k) / VD_USE[1][1],
      );
      if (top >= -EPS) segments.push([[k, 0], [k, Math.max(0, top)]]);
    }
    feasible = { kind: "segments", segments };
    best = argmax(segments.map((segment) => segment[1]));
    candidateCount = segments.length;
  } else {
    const segments: Array<[Vec2, Vec2]> = [];
    for (const m of discreteValues(d2)) {
      const top = Math.min(
        (VD_LIMITS[0] - VD_USE[0][1] * m) / VD_USE[0][0],
        (VD_LIMITS[1] - VD_USE[1][1] * m) / VD_USE[1][0],
      );
      if (top >= -EPS) segments.push([[0, m], [Math.max(0, top), m]]);
    }
    feasible = { kind: "segments", segments };
    best = argmax(segments.map((segment) => segment[1]));
    candidateCount = segments.length;
  }

  const bestValue = objectiveValue(VD_PROFIT, best);
  return {
    d1,
    d2,
    feasible,
    relaxedVertices,
    relaxedPoint,
    relaxedValue,
    best,
    bestValue,
    gap: Math.max(0, relaxedValue - bestValue),
    candidateCount,
    bestHasFraction: best.some((value) => Math.abs(value - Math.round(value)) > 1e-7),
  };
}
