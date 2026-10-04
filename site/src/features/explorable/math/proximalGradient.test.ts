import { describe, expect, it } from "vitest";

import { proximalMinimum, proximalObjective, proximalRun, proximalStep, softThreshold } from "./proximalGradient";

describe("proximal gradient's two operations", () => {
  it("matches the article's computed intermediate points and objective values", () => {
    const run = proximalRun(0, 0.25, 0.8);
    const expected = [
      [0.75, 0.55, 3.44125],
      [1.1625, 0.9625, 2.845703125],
      [1.471875, 1.271875, 2.5107080078125],
    ];
    expected.forEach(([z, x, objective], k) => {
      expect(run[k].z).toBeCloseTo(z, 12);
      expect(run[k].threshold).toBe(0.2);
      expect(run[k].next).toBeCloseTo(x, 12);
      expect(proximalObjective(x, 0.8)).toBeCloseTo(objective, 12);
    });
  });

  it("solves the proximal subproblem, including both sides and its zero interval", () => {
    for (const eta of [0.1, 0.25, 1]) {
      for (const lambda of [0, 0.8, 3, 4]) {
        const threshold = eta * lambda;
        for (const z of [-5, -threshold, -threshold / 2, 0, threshold / 2, threshold, 5]) {
          const x = softThreshold(z, threshold);
          // Independent optimality condition: 0 in lambda*partial|x| + (x-z)/eta.
          if (x === 0) expect(Math.abs(z / eta)).toBeLessThanOrEqual(lambda + 1e-12);
          else expect((x - z) / eta + lambda * Math.sign(x)).toBeCloseTo(0, 12);
        }
      }
    }
  });

  it("matches the closed-form geometric error and descends for every allowed step size", () => {
    for (const eta of [0.1, 0.25, 0.5, 1]) {
      for (const lambda of [0, 0.8, 2.9, 3, 4]) {
        const minimum = proximalMinimum(lambda);
        const positiveRun = proximalRun(0, eta, lambda);
        positiveRun.forEach((step, k) => {
          expect(step.next).toBeCloseTo(minimum * (1 - (1 - eta) ** (k + 1)), 12);
        });
        for (const start of [-3, 0, 5]) {
          proximalRun(start, eta, lambda).forEach(step => {
            expect(proximalObjective(step.next, lambda)).toBeLessThanOrEqual(proximalObjective(step.x, lambda) + 1e-12);
          });
        }
        const fixed = proximalStep(minimum, eta, lambda);
        expect(fixed.mapping).toBeCloseTo(0, 12);
        if (minimum === 0) expect(3).toBeLessThanOrEqual(lambda);
        else expect(minimum - 3 + lambda).toBeCloseTo(0, 12);
      }
    }
  });

  it("keeps a zero solution despite a nonzero smooth gradient", () => {
    const step = proximalStep(0, 0.25, 3);
    expect(step.gradient).toBe(-3);
    expect(step.z).toBe(0.75);
    expect(step.next).toBe(0);
    expect(step.mapping).toBe(0);
  });
});
