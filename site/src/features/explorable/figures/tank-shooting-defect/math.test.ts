import { describe, expect, it } from "vitest";

import fixture from "./fixture.json";
import {
  KAPPA, LAST_ITERATION, OUTFLOW, SUBSTEP_CHOICES, TOLERANCE,
  cost, cutFlow, defectNorms, defects, fineKnots, planAt, pumpedLitres, segmentEnd, segmentLevels,
} from "./math";

const check = fixture.check;
const relative = (value: number, expected: number) => Math.abs(value - expected) / Math.abs(expected);

// The numbers asserted with literals are the ones the steps of content/concepts/dynamics-defect.md say.
describe("tank cut into shooting segments", () => {
  it("uses the constants of the Python example", () => {
    expect(OUTFLOW).toBeCloseTo(check.C, 6);
    expect(OUTFLOW).toBeCloseTo(1.7718, 4);
    expect(KAPPA).toBe(check.kappa);
    expect(LAST_ITERATION).toBe(4);
  });

  it("carries a knot by one Euler step as the hand checks of the article do", () => {
    expect(segmentEnd(1, 0, 1)).toBeCloseTo(0.4685, 4);
    expect(segmentEnd(0.5, 0, 1)).toBeCloseTo(0.1241, 4);
    expect(0.5 - segmentEnd(0.5, 0, 1)).toBeCloseTo(0.3759, 4);
    expect(OUTFLOW * Math.sqrt(0.5)).toBeCloseTo(1.2528, 4);
    expect(segmentLevels(1, 0.2, 5)).toHaveLength(6);
  });

  it("reproduces the cost and defect norms Python computed for iterations 0 to 2 of every run", () => {
    for (const substeps of SUBSTEP_CHOICES) {
      check.runs[substeps].iterations.forEach((expected, iteration) => {
        const plan = planAt(substeps, iteration);
        const { total, track, pump } = cost(plan);
        expect(total).toBeCloseTo(expected.cost, 6);
        expect(track).toBeCloseTo(expected.track, 6);
        expect(pump).toBeCloseTo(expected.pump, 6);
        const norms = defectNorms(defects(plan, Number(substeps)));
        expect(norms.argmax).toBe(expected.argmax);
        expect(relative(norms.max, expected.max)).toBeLessThan(1e-6);
        expect(relative(norms.l2, expected.l2)).toBeLessThan(1e-6);
        expect(relative(norms.total, expected.total)).toBeLessThan(1e-6);
      });
    }
  });

  it("starts with zero cost and 1911 L of water appearing at the knots", () => {
    const plan = planAt("1", 0);
    expect(cost(plan).total).toBe(0);
    const d = defects(plan, 1);
    expect(d[0] * 1000).toBeCloseTo(31.5, 1);
    for (const value of d.slice(1)) expect(value * 1000).toBeCloseTo(375.9, 1);
    expect(Math.round(defectNorms(d).total * 1000)).toBe(1911);
    expect(defectNorms(d).l2).toBeCloseTo(0.841, 3);
  });

  it("closes the gaps at a cost of 7.56, the pump bringing 1856 L", () => {
    const first = planAt("1", 1);
    expect(cost(first).total).toBeCloseTo(7.5595, 4);
    expect(cost(first).pump).toBeCloseTo(7.2811, 4);
    // Looks closed, but still outside the tolerance.
    expect(defectNorms(defects(first, 1)).max).toBeCloseTo(6.48e-5, 7);
    expect(defectNorms(defects(first, 1)).max).toBeGreaterThan(TOLERANCE);

    const second = defectNorms(defects(planAt("1", 2), 1)).max;
    expect(second).toBeGreaterThan(1e-8);
    expect(second).toBeLessThan(1e-7);
    const third = defectNorms(defects(planAt("1", 3), 1)).max;
    expect(third).toBeGreaterThan(1e-12);
    expect(third).toBeLessThan(1e-11);

    const final = planAt("1", 3);
    expect(cost(final).total).toBeCloseTo(7.5575, 4);
    expect(Math.round(pumpedLitres(final))).toBe(1856);
    expect(final.s.map((level) => Number(level.toFixed(3)))).toEqual([1, 0.519, 0.486, 0.484, 0.484, 0.483, 0.461]);
    expect(final.q[0]).toBeCloseTo(0.168, 3);
  });

  it("opens exactly one 0.300 m gap when one segment pumps 1 L/s less, wherever the segment is", () => {
    const plan = planAt("1", 3);
    for (const segment of [2, 3, 4, 5, 6]) {
      const norms = defectNorms(defects(cutFlow(plan, segment), 1));
      const expected = check.cut[String(segment) as keyof typeof check.cut];
      expect(norms.argmax).toBe(segment);
      expect(norms.argmax).toBe(expected.argmax);
      expect(norms.max).toBeCloseTo(0.3, 9);
      expect(norms.l2).toBeCloseTo(0.3, 9);
      expect(norms.max).toBeCloseTo(expected.max, 9);
    }
    expect(cutFlow(plan, 0)).toBe(plan);
  });

  it("finds the finely solved level above the knots although the defect is at rounding level", () => {
    const plan = planAt("1", 3);
    const fine = fineKnots(plan.q);
    // Python integrated the last iterate; iteration 3 differs from it by less than 1e-7.
    const last = fineKnots(planAt("1", LAST_ITERATION).q);
    check.runs["1"].fine_knots.forEach((expected, k) => expect(last[k]).toBeCloseTo(expected, 7));
    expect(plan.s[1]).toBeCloseTo(0.519, 3);
    expect(fine[1]).toBeCloseTo(0.582, 3);
    expect(fine[6]).toBeCloseTo(0.476, 3);
    const gaps = fine.map((level, k) => Math.abs(level - plan.s[k]));
    expect(Math.max(...gaps)).toBeCloseTo(0.063, 3);
    expect(gaps.indexOf(Math.max(...gaps))).toBe(1);
  });

  it("moves the answer when each segment is solved with five Euler steps", () => {
    const plan = planAt("5", 4);
    expect(defectNorms(defects(plan, 5)).max).toBeLessThan(1e-11);
    expect(plan.q[0]).toBeCloseTo(0.01, 3);
    expect(cost(plan).total).toBeCloseTo(check.runs["5"].final_cost, 6);
    expect(cost(plan).total).toBeCloseTo(7.441, 3);
    expect(Math.round(pumpedLitres(plan))).toBe(1785);
    const fine = fineKnots(plan.q);
    const gap = Math.max(...fine.map((level, k) => Math.abs(level - plan.s[k])));
    expect(gap).toBeCloseTo(check.runs["5"].max_gap_to_fine, 7);
    expect(gap).toBeCloseTo(0.012, 3);
    const two = planAt("2", 4);
    expect(Math.max(...fineKnots(two.q).map((level, k) => Math.abs(level - two.s[k])))).toBeCloseTo(0.031, 3);
  });

  it("blends fractional iterations between their neighbours", () => {
    const half = planAt("1", 0.5);
    expect(half.q[1]).toBeCloseTo(planAt("1", 1).q[1] / 2, 12);
    // After iteration 1 the defect falls steadily on a log axis: halfway is near the geometric mean.
    const from = defectNorms(defects(planAt("1", 1), 1)).max;
    const to = defectNorms(defects(planAt("1", 2), 1)).max;
    const middle = defectNorms(defects(planAt("1", 1.5), 1)).max;
    expect(Math.log10(middle)).toBeCloseTo((Math.log10(from) + Math.log10(to)) / 2, 0);
    expect(planAt("1", 9)).toBe(planAt("1", 4));
    expect(planAt("1", -1)).toBe(planAt("1", 0));
  });
});
