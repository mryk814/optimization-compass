import { describe, expect, it } from "vitest";

import { solveMilp } from "./milpLattice";

// Reference values come from an exact-rational script (fractions.Fraction vertex enumeration plus
// a full lattice listing), not from this module.
describe("solveMilp", () => {
  it("article defaults: LP (3, 1.5)=21, rounding (3, 2) breaks both limits, integer optimum (4, 0)=20", () => {
    const s = solveMilp(24, 6);

    expect(s.lpPoint[0]).toBeCloseTo(3, 9);
    expect(s.lpPoint[1]).toBeCloseTo(1.5, 9);
    expect(s.lpValue).toBeCloseTo(21, 9);
    expect(s.lpIsInteger).toBe(false);
    expect(s.rounded).toEqual([3, 2]);
    expect(s.roundedFeasible).toBe(false);
    expect(s.roundedValue).toBe(23);
    expect(s.roundedExcess).toEqual([2, 1]);
    expect(s.integerBest).toEqual([4, 0]);
    expect(s.integerValue).toBe(20);
    expect(s.integerTies).toBe(1);
    expect(s.insideCount).toBe(13);
    expect(s.gap).toBeCloseTo(1, 9);
  });

  it("b2=4: the LP optimum is already the integer point (4, 0), so there is no gap", () => {
    const s = solveMilp(24, 4);

    expect(s.lpPoint[0]).toBeCloseTo(4, 9);
    expect(s.lpPoint[1]).toBeCloseTo(0, 9);
    expect(s.lpIsInteger).toBe(true);
    expect(s.roundedFeasible).toBe(true);
    expect(s.integerBest).toEqual([4, 0]);
    expect(s.integerValue).toBe(20);
    expect(s.insideCount).toBe(9);
    expect(s.gap).toBeCloseTo(0, 9);
  });

  it("b2=7: the bound rises to 21.5 while the integer optimum stays 20, so the gap grows to 1.5", () => {
    const s = solveMilp(24, 7);

    expect(s.lpPoint[0]).toBeCloseTo(2.5, 9);
    expect(s.lpPoint[1]).toBeCloseTo(2.25, 9);
    expect(s.lpValue).toBeCloseTo(21.5, 9);
    expect(s.rounded).toEqual([3, 2]);
    expect(s.roundedFeasible).toBe(false);
    expect(s.integerBest).toEqual([4, 0]);
    expect(s.integerValue).toBe(20);
    expect(s.insideCount).toBe(14);
    expect(s.gap).toBeCloseTo(1.5, 9);
  });

  it("b1=23, b2=5: rounding (3, 1) is feasible and optimal, yet the bound 19.75 is not reached", () => {
    const s = solveMilp(23, 5);

    expect(s.lpPoint[0]).toBeCloseTo(3.25, 9);
    expect(s.lpPoint[1]).toBeCloseTo(0.875, 9);
    expect(s.lpValue).toBeCloseTo(19.75, 9);
    expect(s.rounded).toEqual([3, 1]);
    expect(s.roundedFeasible).toBe(true);
    expect(s.roundedValue).toBe(19);
    expect(s.integerBest).toEqual([3, 1]);
    expect(s.integerValue).toBe(19);
    expect(s.insideCount).toBe(10);
    expect(s.gap).toBeCloseTo(0.75, 9);
  });

  it("b1=30, b2=8: rounding (4, 2) is infeasible and the integer optimum is (5, 0)", () => {
    const s = solveMilp(30, 8);

    expect(s.lpPoint[0]).toBeCloseTo(3.5, 9);
    expect(s.lpPoint[1]).toBeCloseTo(2.25, 9);
    expect(s.lpValue).toBeCloseTo(26.5, 9);
    expect(s.rounded).toEqual([4, 2]);
    expect(s.roundedFeasible).toBe(false);
    expect(s.integerBest).toEqual([5, 0]);
    expect(s.integerValue).toBe(25);
    expect(s.insideCount).toBe(19);
    expect(s.gap).toBeCloseTo(1.5, 9);
  });

  it("the largest limits stay inside the plot window", () => {
    const s = solveMilp(36, 12);

    expect(s.lpPoint[0]).toBeCloseTo(3, 9);
    expect(s.lpPoint[1]).toBeCloseTo(4.5, 9);
    expect(s.lpValue).toBeCloseTo(33, 9);
    expect(s.integerBest).toEqual([4, 3]);
    expect(s.integerValue).toBe(32);
    expect(s.insideCount).toBe(31);
    expect(s.gap).toBeCloseTo(1, 9);
  });
});
