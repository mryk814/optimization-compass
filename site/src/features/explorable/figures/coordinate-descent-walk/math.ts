/** f = a(x-1)^2 + 2b(x-1)(y+2) + d(y+2)^2; a,d>0 and ad>b². */
export interface CoordinateQuadratic {
  a: number;
  b: number;
  d: number;
}

export type Coordinate = "x" | "y";
export interface CoordinatePoint {
  x: number;
  y: number;
  f: number;
  gx: number;
  gy: number;
  gradNorm: number;
}
export const COORDINATE_TOLERANCE = 1e-6;
export const COORDINATE_BUDGET = 200;
export const ARTICLE_QUADRATIC: CoordinateQuadratic = { a: 1, b: 2, d: 20 };

export function coordinatePoint(q: CoordinateQuadratic, x: number, y: number): CoordinatePoint {
  const u = x - 1;
  const v = y + 2;
  const gx = 2 * (q.a * u + q.b * v);
  const gy = 2 * (q.b * u + q.d * v);
  return { x, y, f: q.a * u * u + 2 * q.b * u * v + q.d * v * v, gx, gy, gradNorm: Math.hypot(gx, gy) };
}

export function coordinateUpdate(q: CoordinateQuadratic, p: CoordinatePoint, axis: Coordinate): CoordinatePoint {
  return axis === "x"
    ? coordinatePoint(q, 1 - q.b * (p.y + 2) / q.a, p.y)
    : coordinatePoint(q, p.x, -2 - q.b * (p.x - 1) / q.d);
}

/** Check the whole gradient after a complete sweep, never just the updated partial derivative. */
export function runCoordinateDescent(q: CoordinateQuadratic, start: readonly [number, number], budget = COORDINATE_BUDGET) {
  if (![q.a, q.b, q.d, ...start].every(Number.isFinite) || q.a <= 0 || q.d <= 0 || q.a * q.d <= q.b * q.b) {
    throw new Error("Coordinate descent requires a finite positive-definite quadratic.");
  }
  const points = [coordinatePoint(q, ...start)];
  if (points[0].gradNorm < COORDINATE_TOLERANCE) return { points, outcome: "converged" as const };
  for (let k = 0; k < budget; k += 1) {
    const axis = k % 2 === 0 ? "x" : "y";
    const p = coordinateUpdate(q, points[points.length - 1], axis);
    points.push(p);
    if (k % 2 === 1 && p.gradNorm < COORDINATE_TOLERANCE) return { points, outcome: "converged" as const };
  }
  return { points, outcome: "budget" as const };
}

/** The gentle principal direction is angle degrees from x; curvatures are 2m and 2mκ. */
export function rotatedQuadratic(gentle: number, kappa: number, angle: number): CoordinateQuadratic {
  const theta = angle * Math.PI / 180;
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  return {
    a: gentle * (c * c + kappa * s * s),
    b: gentle * (1 - kappa) * s * c,
    d: gentle * (s * s + kappa * c * c),
  };
}

export function coordinateGeometry(q: CoordinateQuadratic) {
  const gap = Math.hypot(q.a - q.d, 2 * q.b);
  const gentle = (q.a + q.d - gap) / 2;
  const steep = (q.a + q.d + gap) / 2;
  const angle = gap < 1e-12 ? 0 : Math.atan2(-2 * q.b, q.d - q.a) * 90 / Math.PI;
  const rho = q.b / Math.sqrt(q.a * q.d);
  return { gentle, kappa: steep / gentle, angle, rho, sweepFactor: rho * rho };
}

/** Exact level ellipse, sampled only for drawing; update calculations do not use this sampling. */
export function coordinateEllipse(q: CoordinateQuadratic, level: number): Array<readonly [number, number]> {
  const { gentle, kappa, angle } = coordinateGeometry(q);
  const theta = angle * Math.PI / 180;
  const r = Math.sqrt(level / gentle);
  const t = Math.sqrt(level / (gentle * kappa));
  return Array.from({ length: 129 }, (_, i) => {
    const phi = i * Math.PI / 64;
    const u = r * Math.cos(phi);
    const v = t * Math.sin(phi);
    return [1 + u * Math.cos(theta) - v * Math.sin(theta), -2 + u * Math.sin(theta) + v * Math.cos(theta)] as const;
  });
}
