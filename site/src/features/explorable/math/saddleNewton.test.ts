import { describe, expect, it } from "vitest";

import {
  classify, curvatures, gradient, newtonRun, SADDLE, SINGULAR_X1, START_A, START_B, VALLEYS, value,
} from "./saddleNewton";

describe("saddle Newton (PA006 running example)", () => {
  it("has two valley bottoms at f = −33/256 and a saddle at f = 1", () => {
    for (const valley of VALLEYS) {
      expect(value(valley)).toBeCloseTo(-33 / 256, 12);
      expect(Math.hypot(...gradient(valley))).toBeLessThan(1e-12);
      expect(classify(valley)).toBe("valley");
    }
    expect(value(SADDLE)).toBe(1);
    expect(classify(SADDLE)).toBe("saddle");
    const [low, high] = curvatures(SADDLE);
    expect(low).toBeCloseTo(-Math.sqrt(17), 12);
    expect(high).toBeCloseTo(Math.sqrt(17), 12);
  });

  it("agrees with the article: A reaches the left valley in 6 steps, B the saddle in 3", () => {
    const a = newtonRun(START_A);
    expect(a.stop).toBe("converged");
    expect(a.points).toHaveLength(7);
    const endA = a.points.at(-1)!;
    expect(endA[0]).toBeCloseTo(VALLEYS[1][0], 8);
    expect(endA[1]).toBeCloseTo(VALLEYS[1][1], 8);
    const [lowA, highA] = curvatures(endA);
    expect(lowA).toBeCloseTo(3.798, 3);
    expect(highA).toBeCloseTo(8.952, 3);

    const b = newtonRun(START_B);
    expect(b.stop).toBe("converged");
    expect(b.points).toHaveLength(4);
    expect(classify(b.points.at(-1)!)).toBe("saddle");
  });

  it("stops on the singular line instead of dividing by zero", () => {
    expect(newtonRun([SINGULAR_X1, 0.3]).stop).toBe("singular");
  });

  it("reports a non-stationary start as not yet decided by curvature", () => {
    expect(classify(START_A)).toBe("not-stationary");
  });
});
