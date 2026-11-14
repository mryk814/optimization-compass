import { describe, expect, it } from "vitest";

import fixture from "./fixture.json";
import {
  BUDGET, DATA_X, DEGREES, LOG_LAMS, RANDOM_BESTS, SEEDS, SPLITS,
  bestIndex, bestSoFar, curveValue, distinctLambdas, fitCoefficients, gridRun, lamIndexOf, mapScore,
  randomRun, scoreOf, shadeLevel, truth,
} from "./math";

const r3 = (value: number) => Number(value.toFixed(3));
const setting = (point: { d: number; log_lam: number }) => [point.d, Number(point.log_lam.toFixed(2))];

// Numbers asserted here are the ones the lesson steps of
// content/concepts/hyperparameter-optimization.md say. Python pins the same ones from the
// unrounded scores (tests/lesson_figures/test_hyperparameter_optimization.py).
describe("hpo budget race (30-point example)", () => {
  it("imports the example from the Python fixture", () => {
    expect(DATA_X).toHaveLength(30);
    expect(DEGREES).toEqual([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]);
    expect(LOG_LAMS).toHaveLength(15);
    expect([LOG_LAMS[0], LOG_LAMS[14]]).toEqual([-6, 1]);
    expect([SPLITS, SEEDS]).toEqual([12, 8]);
    for (const run of [gridRun("edge"), gridRun("center"), ...fixture.runs.random]) {
      expect(run).toHaveLength(BUDGET);
      for (const point of run) expect(point.cv).toHaveLength(SPLITS);
    }
  });

  it("step 1: one setting is one curve and one score", () => {
    const row = DEGREES.indexOf(15);
    const score = (logLam: number) => r3(mapScore(row, lamIndexOf(logLam), "cv", 0));
    expect([score(-6), score(-1.5), score(1)]).toEqual([4.486, 0.23, 1.079]);
    const scores = LOG_LAMS.map((_, index) => mapScore(row, index, "cv", 0));
    expect(LOG_LAMS[scores.indexOf(Math.min(...scores))]).toBe(-1.5);
    // The weakly penalised curve leaves the panel (drawn for y in [-2.5, 2.5]); the strongly
    // penalised one is almost flat.
    const xs = Array.from({ length: 61 }, (_, i) => -1 + i / 30);
    const wild = xs.map((x) => curveValue(fitCoefficients(15, -6), x));
    const flat = xs.map((x) => curveValue(fitCoefficients(15, 1), x));
    expect(Math.min(...wild)).toBeLessThan(-40);
    expect(Math.max(...flat.map(Math.abs))).toBeLessThan(0.1);
  });

  it("fits the same curves as Python", () => {
    for (const fit of fixture.fits) {
      const coefficients = fitCoefficients(fit.d, fit.log_lam);
      expect(coefficients).toHaveLength(fit.coef.length);
      fit.coef.forEach((value, index) => expect(coefficients[index]).toBeCloseTo(value, 6));
    }
  });

  it("step 2: the same 16 evaluations on a grid and at random", () => {
    const grid = gridRun("edge");
    const random = randomRun(0);
    expect(bestSoFar(grid, 0).map(r3)).toEqual([...Array(4).fill(0.267), ...Array(12).fill(0.192)]);
    expect(bestSoFar(random, 0).map(r3)).toEqual([0.747, ...Array(6).fill(0.172), ...Array(9).fill(0.144)]);
    expect(setting(grid[bestIndex(grid, 16, 0)])).toEqual([6, -3.67]);
    expect(setting(random[bestIndex(random, 16, 0)])).toEqual([3, -1.67]);
    expect([distinctLambdas(grid, 16), distinctLambdas(random, 16)]).toEqual([4, 16]);
    expect([distinctLambdas(grid, 5), distinctLambdas(random, 5), bestIndex(grid, 0, 0)]).toEqual([4, 5, -1]);
  });

  it("step 3: placing the grid at the centre of each interval swaps the order", () => {
    const center = gridRun("center");
    expect(r3(bestSoFar(center, 0)[0])).toBe(0.137);
    expect(setting(center[bestIndex(center, 16, 0)])).toEqual([3, -3.38]);
    expect(bestSoFar(center, 0)[15]).toBeLessThan(bestSoFar(randomRun(0), 0)[15]);
    expect(RANDOM_BESTS).toHaveLength(200);
    expect([r3(Math.min(...RANDOM_BESTS)), r3(Math.max(...RANDOM_BESTS))]).toEqual([0.137, 0.192]);
    const sorted = [...RANDOM_BESTS].sort((a, b) => a - b);
    expect(r3((sorted[99] + sorted[100]) / 2)).toBe(0.138);
    expect(RANDOM_BESTS.filter((best) => r3(best) <= 0.137)).toHaveLength(95);
  });

  it("step 4: other splits move the scores and the chosen setting", () => {
    const grid = gridRun("edge");
    const random = randomRun(0);
    const chosen = random[bestIndex(random, 16, 0)];
    expect([r3(Math.min(...chosen.cv)), r3(Math.max(...chosen.cv))]).toEqual([0.144, 0.177]);
    const randomWinners = Array.from({ length: SPLITS }, (_, split) => bestIndex(random, 16, split));
    const gridWinners = Array.from({ length: SPLITS }, (_, split) => bestIndex(grid, 16, split));
    // The random run keeps (3, -1.67) in 9 of the 12 splits; the grid's choice is one of three settings.
    expect(randomWinners.filter((index) => index !== randomWinners[0])).toHaveLength(3);
    expect(new Set(gridWinners).size).toBe(3);
    for (let split = 0; split < SPLITS; split += 1) {
      expect(bestSoFar(random, split)[15]).toBeLessThan(bestSoFar(grid, split)[15]);
    }
    // Against the grid at the centres (what the step shows) the order itself moves with the split:
    // the random run is lower in 5 of the 12, the grid in 7.
    const center = gridRun("center");
    const randomLower = Array.from({ length: SPLITS }, (_, split) => split)
      .filter((split) => bestSoFar(random, split)[15] < bestSoFar(center, split)[15]);
    expect(randomLower).toEqual([2, 3, 4, 8, 11]);
    expect([r3(bestSoFar(center, 11)[15]), r3(bestSoFar(random, 11)[15])]).toEqual([0.153, 0.153]);
  });

  it("step 6: on the fresh points the gap between the two winners closes", () => {
    const grid = gridRun("edge");
    const random = randomRun(0);
    const g = grid[bestIndex(grid, 16, 0)];
    const r = random[bestIndex(random, 16, 0)];
    expect([r3(scoreOf(g, "cv", 0)), r3(scoreOf(r, "cv", 0))]).toEqual([0.192, 0.144]);
    expect([r3(scoreOf(g, "fresh", 0)), r3(scoreOf(r, "fresh", 0))]).toEqual([0.175, 0.173]);
    expect(r3(g.cv[0] - r.cv[0])).toBe(0.048);
    expect(r3(g.fresh - r.fresh)).toBe(0.002);
    // Both sit near the lowest fresh-point score anywhere on the map.
    const cells = DEGREES.flatMap((_, row) => LOG_LAMS.map((__, column) => mapScore(row, column, "fresh", 0)));
    expect(r3(Math.min(...cells))).toBe(0.17);
    // Where there are data points (x up to 0.89) the two chosen curves are nearly the same line:
    // under 0.2 apart on a panel that spans 5. Past the last point they part (0.44 at x = 1).
    const gap = (x: number) => Math.abs(
      curveValue(fitCoefficients(g.d, g.log_lam), x) - curveValue(fitCoefficients(r.d, r.log_lam), x),
    );
    expect(Math.max(...DATA_X)).toBeLessThan(0.9);
    expect(Math.max(...Array.from({ length: 57 }, (_, i) => gap(-1 + i / 30)))).toBeLessThan(0.2);
    expect(gap(1)).toBeGreaterThan(0.4);
  });

  it("shades scores between 0.13 and 1 and knows the generating curve", () => {
    expect([shadeLevel(0.1), shadeLevel(0.13), shadeLevel(1), shadeLevel(4)]).toEqual([0, 0, 1, 1]);
    expect(shadeLevel(0.36)).toBeCloseTo(0.5, 1);
    expect(truth(0)).toBe(0);
  });
});
