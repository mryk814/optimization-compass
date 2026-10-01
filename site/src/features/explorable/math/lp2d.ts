export type Vec2 = readonly [number, number];

/** The half-plane a . p <= b. */
export interface HalfPlane {
  a: Vec2;
  b: number;
  label: string;
}

const EPSILON = 1e-9;

/** The LP used in the primal simplex article: max 3x + 2y s.t. x + y <= 4, 2x + y <= 5, x, y >= 0. */
export const ARTICLE_LP: readonly HalfPlane[] = [
  { a: [1, 1], b: 4, label: "x + y ≤ 4" },
  { a: [2, 1], b: 5, label: "2x + y ≤ 5" },
  { a: [-1, 0], b: 0, label: "x ≥ 0" },
  { a: [0, -1], b: 0, label: "y ≥ 0" },
];

export function isFeasible(constraints: readonly HalfPlane[], point: Vec2, tolerance = EPSILON): boolean {
  return constraints.every((row) => row.a[0] * point[0] + row.a[1] * point[1] <= row.b + tolerance);
}

export function objectiveValue(cost: Vec2, point: Vec2): number {
  return cost[0] * point[0] + cost[1] * point[1];
}

/** Vertices of the bounded feasible polygon, counter-clockwise. */
export function feasibleVertices(constraints: readonly HalfPlane[]): Vec2[] {
  const found: Vec2[] = [];
  for (let i = 0; i < constraints.length; i += 1) {
    for (let j = i + 1; j < constraints.length; j += 1) {
      const [a1, a2] = constraints[i].a;
      const [b1, b2] = constraints[j].a;
      const determinant = a1 * b2 - a2 * b1;
      if (Math.abs(determinant) < EPSILON) continue;
      const x = (constraints[i].b * b2 - a2 * constraints[j].b) / determinant;
      const y = (a1 * constraints[j].b - constraints[i].b * b1) / determinant;
      const candidate: Vec2 = [x, y];
      if (
        isFeasible(constraints, candidate, 1e-7)
        && !found.some((seen) => Math.hypot(seen[0] - x, seen[1] - y) < 1e-7)
      ) {
        found.push(candidate);
      }
    }
  }
  const centerX = found.reduce((sum, point) => sum + point[0], 0) / found.length;
  const centerY = found.reduce((sum, point) => sum + point[1], 0) / found.length;
  return found.sort(
    (left, right) => Math.atan2(left[1] - centerY, left[0] - centerX)
      - Math.atan2(right[1] - centerY, right[0] - centerX),
  );
}

/** Indices of every vertex that attains the best objective value (an edge when there are two). */
export function optimalVertices(vertices: readonly Vec2[], cost: Vec2): number[] {
  const best = Math.max(...vertices.map((vertex) => objectiveValue(cost, vertex)));
  return vertices.flatMap((vertex, index) => (
    objectiveValue(cost, vertex) >= best - 1e-9 ? [index] : []
  ));
}

/**
 * Educational vertex walk: from the start vertex, keep moving to the adjacent vertex with the
 * larger objective value until no neighbour improves. Real simplex codes pick the entering
 * variable by reduced cost and pivot rule instead.
 */
export function greedyVertexWalk(vertices: readonly Vec2[], cost: Vec2, start: number): number[] {
  const path = [start];
  let current = start;
  for (let guard = 0; guard < vertices.length; guard += 1) {
    const here = objectiveValue(cost, vertices[current]);
    const neighbours = [
      (current + vertices.length - 1) % vertices.length,
      (current + 1) % vertices.length,
    ];
    const best = neighbours.reduce((winner, candidate) => (
      objectiveValue(cost, vertices[candidate]) > objectiveValue(cost, vertices[winner])
        ? candidate
        : winner
    ));
    if (objectiveValue(cost, vertices[best]) <= here + 1e-9) break;
    path.push(best);
    current = best;
  }
  return path;
}

/** The chord of the line `cost . p = value` inside a rectangle, or undefined when it misses. */
export function levelLine(
  cost: Vec2,
  value: number,
  box: { xMin: number; xMax: number; yMin: number; yMax: number },
): [Vec2, Vec2] | undefined {
  const [c1, c2] = cost;
  const hits: Vec2[] = [];
  if (Math.abs(c2) > EPSILON) {
    for (const x of [box.xMin, box.xMax]) {
      const y = (value - c1 * x) / c2;
      if (y >= box.yMin - EPSILON && y <= box.yMax + EPSILON) hits.push([x, y]);
    }
  }
  if (Math.abs(c1) > EPSILON) {
    for (const y of [box.yMin, box.yMax]) {
      const x = (value - c2 * y) / c1;
      if (x >= box.xMin - EPSILON && x <= box.xMax + EPSILON) hits.push([x, y]);
    }
  }
  if (hits.length < 2) return undefined;
  const first = hits[0];
  const far = hits.reduce((winner, candidate) => (
    Math.hypot(candidate[0] - first[0], candidate[1] - first[1])
      > Math.hypot(winner[0] - first[0], winner[1] - first[1])
      ? candidate
      : winner
  ));
  return [first, far];
}

/** Pull `target` toward `inside` until it is feasible, so a dragged probe stays in the polygon. */
export function pullIntoPolygon(
  constraints: readonly HalfPlane[],
  inside: Vec2,
  target: Vec2,
): Vec2 {
  if (isFeasible(constraints, target)) return target;
  let low = 0;
  let high = 1;
  for (let iteration = 0; iteration < 40; iteration += 1) {
    const middle = (low + high) / 2;
    const candidate: Vec2 = [
      inside[0] + (target[0] - inside[0]) * middle,
      inside[1] + (target[1] - inside[1]) * middle,
    ];
    if (isFeasible(constraints, candidate)) low = middle;
    else high = middle;
  }
  return [inside[0] + (target[0] - inside[0]) * low, inside[1] + (target[1] - inside[1]) * low];
}

/** Position along a vertex path at a fractional step, interpolating along the edge. */
export function pathPoint(vertices: readonly Vec2[], path: readonly number[], position: number): Vec2 {
  const clamped = Math.min(Math.max(position, 0), path.length - 1);
  const index = Math.min(Math.floor(clamped), path.length - 2);
  if (index < 0) return vertices[path[0]];
  const t = clamped - index;
  const from = vertices[path[index]];
  const to = vertices[path[index + 1]];
  return [from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t];
}
