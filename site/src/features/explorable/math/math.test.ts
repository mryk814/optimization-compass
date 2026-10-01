import { describe, expect, it } from "vitest";

import { contourSegments } from "./contours";
import {
  CURVE_FUNCTIONS,
  chordReading,
  descendFrom,
  globalMinimum,
  violationIntervals,
} from "./convexity";
import {
  axisRate,
  runDescent,
  stabilityLimit,
  valleyGradient,
  valleyValue,
  type ValleyProblem,
} from "./descent";
import {
  ARTICLE_LP,
  feasibleVertices,
  greedyVertexWalk,
  isFeasible,
  levelLine,
  objectiveValue,
  optimalVertices,
  pathPoint,
  pullIntoPolygon,
} from "./lp2d";

const valley: ValleyProblem = { cx: 1, cy: -2, kappa: 20 };

describe("contourSegments", () => {
  it("traces a circle whose points all sit on the requested level", () => {
    const circle = (x: number, y: number) => x * x + y * y;
    const segments = contourSegments(circle, { xMin: -2, xMax: 2, yMin: -2, yMax: 2 }, 1, 80, 80);

    expect(segments.length).toBeGreaterThan(60);
    for (const [x1, y1, x2, y2] of segments) {
      expect(Math.hypot(x1, y1)).toBeCloseTo(1, 1);
      expect(Math.hypot(x2, y2)).toBeCloseTo(1, 1);
    }
  });

  it("returns nothing when the level is outside the sampled range", () => {
    const flat = () => 3;
    expect(contourSegments(flat, { xMin: 0, xMax: 1, yMin: 0, yMax: 1 }, 10, 8, 8)).toEqual([]);
  });
});

describe("gradient descent on the valley", () => {
  const start: [number, number] = [4, 3];

  it("has the analytic gradient of the objective", () => {
    const [gx, gy] = valleyGradient(valley, 4, 3);
    expect(gx).toBeCloseTo(6);
    expect(gy).toBeCloseTo(200);
    const h = 1e-6;
    expect((valleyValue(valley, 4 + h, 3) - valleyValue(valley, 4 - h, 3)) / (2 * h)).toBeCloseTo(gx, 4);
  });

  it("puts the stability limit at 2 over the largest curvature", () => {
    expect(stabilityLimit(valley, "gd", 0)).toBeCloseTo(0.05);
    expect(stabilityLimit({ ...valley, kappa: 1 }, "gd", 0)).toBeCloseTo(1);
    expect(stabilityLimit(valley, "momentum", 0.5)).toBeCloseTo(0.075);
  });

  it("converges just below the limit and diverges just above it", () => {
    const below = runDescent(valley, start, { eta: 0.045, method: "gd", beta: 0, maxSteps: 400 });
    const above = runDescent(valley, start, { eta: 0.055, method: "gd", beta: 0, maxSteps: 400 });

    expect(below.outcome).toBe("converged");
    expect(above.outcome).toBe("diverged");
    expect(above.points.at(-1)!.f).toBeGreaterThan(above.points[0].f);
  });

  it("reproduces the article's fixed step: slow along the gentle axis, sign flips across", () => {
    const run = runDescent(valley, start, { eta: 0.04, method: "gd", beta: 0, maxSteps: 60 });
    const gentle = axisRate("gd", 2, 0.04, 0);
    const steep = axisRate("gd", 40, 0.04, 0);

    expect(gentle.rate).toBeCloseTo(0.92);
    expect(gentle.oscillates).toBe(false);
    expect(steep.factor).toBeCloseTo(-0.6);
    expect(steep.oscillates).toBe(true);
    expect(run.outcome).toBe("unfinished");
    expect(run.points[1].y + 2).toBeCloseTo(-0.6 * (3 + 2));
  });

  it("matches the closed-form error decay along each axis for plain gradient descent", () => {
    const run = runDescent(valley, start, { eta: 0.03, method: "gd", beta: 0, maxSteps: 10 });
    const point = run.points[10];

    expect(point.x - 1).toBeCloseTo((1 - 0.03 * 2) ** 10 * (4 - 1));
    expect(point.y + 2).toBeCloseTo((1 - 0.03 * 40) ** 10 * (3 + 2));
  });

  it("gives momentum a larger stable step than plain descent", () => {
    const plain = runDescent(valley, start, { eta: 0.06, method: "gd", beta: 0, maxSteps: 300 });
    const heavy = runDescent(valley, start, { eta: 0.06, method: "momentum", beta: 0.5, maxSteps: 300 });

    expect(plain.outcome).toBe("diverged");
    expect(heavy.outcome).toBe("converged");
  });

  it("reports spiralling momentum as a rate of sqrt(beta)", () => {
    const rate = axisRate("momentum", 2, 0.4, 0.6);
    expect(rate.oscillates).toBe(true);
    expect(rate.rate).toBeCloseTo(Math.sqrt(0.6));
  });
});

describe("LP vertex walk", () => {
  const vertices = feasibleVertices(ARTICLE_LP);

  it("finds the four vertices of the article LP", () => {
    expect(vertices).toHaveLength(4);
    const expected = [[0, 0], [2.5, 0], [1, 3], [0, 4]];
    for (const [x, y] of expected) {
      expect(vertices.some((v) => Math.hypot(v[0] - x, v[1] - y) < 1e-6)).toBe(true);
    }
  });

  it("agrees with the article: optimum (1, 3) with objective 9", () => {
    const best = optimalVertices(vertices, [3, 2]);
    expect(best).toHaveLength(1);
    expect(vertices[best[0]][0]).toBeCloseTo(1);
    expect(vertices[best[0]][1]).toBeCloseTo(3);
    expect(objectiveValue([3, 2], vertices[best[0]])).toBeCloseTo(9);
  });

  it("walks from the origin to an optimal vertex, improving every move", () => {
    const start = vertices.findIndex((v) => v[0] === 0 && v[1] === 0);
    for (const cost of [[3, 2], [1, 3], [-1, 2], [2, -1]] as const) {
      const path = greedyVertexWalk(vertices, cost, start);
      const values = path.map((index) => objectiveValue(cost, vertices[index]));
      expect(values.every((value, i) => i === 0 || value > values[i - 1])).toBe(true);
      expect(optimalVertices(vertices, cost)).toContain(path.at(-1));
    }
  });

  it("does not move when the cost is zero, and lists an optimal edge for parallel costs", () => {
    const start = vertices.findIndex((v) => v[0] === 0 && v[1] === 0);
    expect(greedyVertexWalk(vertices, [0, 0], start)).toStrictEqual([start]);
    expect(optimalVertices(vertices, [1, 1])).toHaveLength(2);
  });

  it("keeps a dragged probe inside the polygon and never beats the best vertex", () => {
    const centre: [number, number] = [1, 1];
    const pulled = pullIntoPolygon(ARTICLE_LP, centre, [6, 6]);
    expect(isFeasible(ARTICLE_LP, pulled, 1e-6)).toBe(true);
    expect(pullIntoPolygon(ARTICLE_LP, centre, [0.5, 0.5])).toEqual([0.5, 0.5]);
    const best = objectiveValue([3, 2], vertices[optimalVertices(vertices, [3, 2])[0]]);
    for (let x = -1; x <= 6; x += 0.7) {
      for (let y = -1; y <= 6; y += 0.7) {
        const point = pullIntoPolygon(ARTICLE_LP, centre, [x, y]);
        expect(objectiveValue([3, 2], point)).toBeLessThanOrEqual(best + 1e-6);
      }
    }
  });

  it("clips a level line to the plotting box", () => {
    const box = { xMin: -1, xMax: 5, yMin: -1, yMax: 5 };
    const line = levelLine([1, 1], 4, box)!;
    for (const [x, y] of line) expect(x + y).toBeCloseTo(4);
    expect(levelLine([1, 0], 100, box)).toBeUndefined();
    expect(levelLine([0, 0], 1, box)).toBeUndefined();
  });

  it("interpolates along an edge", () => {
    const path = [0, 1];
    const point = pathPoint(vertices, path, 0.5);
    expect(point[0]).toBeCloseTo((vertices[0][0] + vertices[1][0]) / 2);
    const end = pathPoint(vertices, path, 9);
    expect(end[0]).toBeCloseTo(vertices[1][0]);
    expect(end[1]).toBeCloseTo(vertices[1][1]);
  });
});

describe("convexity chord", () => {
  const [quadratic, doubleWell, absolute] = CURVE_FUNCTIONS;

  it("never dips below the graph for the convex presets", () => {
    for (const fn of [quadratic, absolute]) {
      for (let a = -2.4; a <= 2.4; a += 0.4) {
        for (let b = -2.4; b <= 2.4; b += 0.4) {
          expect(violationIntervals(fn.f, a, b)).toEqual([]);
        }
      }
    }
  });

  it("finds a violating stretch for the double well across its hump", () => {
    const intervals = violationIntervals(doubleWell.f, -1.5, 1.5);
    expect(intervals.length).toBeGreaterThan(0);
    const [start, end] = intervals[0];
    const reading = chordReading(doubleWell.f, -1.5, 1.5, (start + end) / 2);
    expect(reading.slack).toBeLessThan(0);
  });

  it("mixes inputs and outputs by the same ratio, as in the definition", () => {
    const reading = chordReading(quadratic.f, -2, 2, 0.25);
    expect(reading.mix).toBeCloseTo(0.25 * -2 + 0.75 * 2);
    expect(reading.chord).toBeCloseTo(quadratic.f(-2));
  });

  it("stops in different valleys depending on the start, and only one is global", () => {
    const global = globalMinimum(doubleWell);
    const fromLeft = descendFrom(doubleWell, -2).at(-1)!;
    const fromRight = descendFrom(doubleWell, 2).at(-1)!;

    expect(Math.abs(fromLeft - global.x)).toBeLessThan(0.05);
    expect(Math.abs(fromRight - global.x)).toBeGreaterThan(1);
    expect(doubleWell.f(fromRight)).toBeGreaterThan(global.value + 0.3);
  });
});
