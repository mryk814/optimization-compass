import { describe, expect, it } from "vitest";

import {
  balanceAt, BEST_Q, freeBalance, misfitTerm, penaltyTerm, state, stateResidual, SWEEP_HOLD_STEPS, SWEEP_LENGTH, sweepQ,
} from "./pdeHeat";

// Expected numbers come from scratchpad/motion_numbers.py (numpy solve with K = 9·[[2,−1],[−1,2]]).
describe("two-point heated rod", () => {
  it("reproduces the article's table for q = 0, 4.5, 9", () => {
    const rows: Array<[number, number, number, number, number]> = [
      [0, 0, 1, 0, 1],
      [4.5, 0.5, 0.25, 0.25, 0.5],
      [9, 1, 0, 1, 1],
    ];
    for (const [q, u, misfit, penalty, total] of rows) {
      const b = balanceAt(q);
      expect(b.u[0]).toBeCloseTo(u, 12);
      expect(b.u[1]).toBeCloseTo(u, 12);
      expect(b.misfit).toBeCloseTo(misfit, 12);
      expect(b.penalty).toBeCloseTo(penalty, 12);
      expect(b.total).toBeCloseTo(total, 12);
    }
  });

  it("matches the sampled values the slider passes through", () => {
    const at2 = balanceAt(2);
    expect(at2.u[0]).toBeCloseTo(0.2222222222, 10);
    expect(at2.misfit).toBeCloseTo(0.6049382716, 10);
    expect(at2.penalty).toBeCloseTo(0.0493827160, 10);
    expect(at2.total).toBeCloseTo(0.6543209877, 10);
    const at12 = balanceAt(12);
    expect(at12.u[0]).toBeCloseTo(1.3333333333, 10);
    expect(at12.misfit).toBeCloseTo(0.1111111111, 10);
    expect(at12.penalty).toBeCloseTo(1.7777777778, 10);
    expect(at12.total).toBeCloseTo(1.8888888889, 10);
  });

  it("solves K u = q for unequal heaters too", () => {
    const [u1, u2] = state(9, 0);
    expect(9 * (2 * u1 - u2)).toBeCloseTo(9, 12);
    expect(9 * (-u1 + 2 * u2)).toBeCloseTo(0, 12);
  });

  it("balances the two terms exactly at the minimum, q = 4.5", () => {
    expect(balanceAt(BEST_Q).misfit).toBeCloseTo(balanceAt(BEST_Q).penalty, 12);
    let lowest = Infinity;
    let at = 0;
    for (let q = 0; q <= 12; q += 0.25) {
      const total = balanceAt(q).total;
      if (total < lowest) {
        lowest = total;
        at = q;
      }
    }
    expect(at).toBe(BEST_Q);
    // No unequal pair of heaters on a coarse grid beats the equal pair.
    for (let q1 = 0; q1 <= 10; q1 += 0.5) {
      for (let q2 = 0; q2 <= 10; q2 += 0.5) {
        const total = misfitTerm(state(q1, q2)) + penaltyTerm(q1, q2);
        expect(total).toBeGreaterThanOrEqual(0.5 - 1e-12);
      }
    }
  });
});

describe("free-u contrast and the state residual", () => {
  it("u = (1, 1) with q = 0 looks perfect (J = 0) but breaks the state equation by 9√2", () => {
    const f = freeBalance(1, 0);
    expect(f.total).toBeCloseTo(0, 12);
    expect(f.residual).toBeCloseTo(9 * Math.SQRT2, 10);
    expect(f.required).toBeCloseTo(9, 12);
  });

  it("only q = 9 makes u = 1 consistent, and then J is 1.0, twice the optimum", () => {
    const f = freeBalance(1, 9);
    expect(f.residual).toBeCloseTo(0, 12);
    expect(f.total).toBeCloseTo(1, 12);
  });

  it("the state residual of the real model is zero for every q", () => {
    for (const q of [0, 2, 4.5, 9, 12]) {
      expect(stateResidual(balanceAt(q).u, q, q)).toBeCloseTo(0, 10);
    }
  });

  it("rests at the chosen q and ends at 12", () => {
    expect(sweepQ(18, 4.5)).toBeCloseTo(4.5, 12);
    expect(sweepQ(18 + SWEEP_HOLD_STEPS, 4.5)).toBeCloseTo(4.5, 12);
    expect(sweepQ(SWEEP_LENGTH, 4.5)).toBeCloseTo(12, 12);
    expect(sweepQ(36 + SWEEP_HOLD_STEPS, 9)).toBeCloseTo(9, 12);
    expect(sweepQ(SWEEP_LENGTH, 9)).toBeCloseTo(12, 12);
  });
});
