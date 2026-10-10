import { describe, expect, it } from "vitest";

import {
  basisState, dantzigEntering, edgeMove, fracText, improving, pivot, START_BASIS, valuesAlong,
  type BasisState, type VariableIndex,
} from "./simplex";

const texts = (values: { n: number; d: number }[]) => values.map(fracText);

function walk(choose: (state: BasisState) => VariableIndex | undefined) {
  const states = [basisState(START_BASIS)];
  for (let guard = 0; guard < 6; guard += 1) {
    const state = states.at(-1)!;
    const entering = choose(state);
    if (entering === undefined) break;
    states.push(pivot(state, edgeMove(state, entering)));
  }
  return states;
}

describe("bakery LP primal simplex", () => {
  it("reproduces the article table under Dantzig's rule", () => {
    const states = walk(dantzigEntering);
    expect(states.map((s) => texts([...s.point]))).toEqual([["0", "0"], ["0", "13/3"], ["4", "3"]]);
    expect(states.map((s) => fracText(s.sales))).toEqual(["0", "52/3", "24"]);
    expect(states.map((s) => texts(s.reduced))).toEqual([
      ["−3", "−4", "0", "0"],
      ["−5/3", "0", "0", "4/3"],
      ["0", "0", "5/7", "6/7"],
    ]);
    expect(states.every((s) => s.feasible)).toBe(true);
  });

  it("uses the minimum ratio, so the butter leftover leaves first", () => {
    const origin = basisState(START_BASIS);
    const move = edgeMove(origin, 1);
    expect(move.rows.map((row) => row.ratio && fracText(row.ratio))).toEqual(["9", "13/3"]);
    expect(fracText(move.theta!)).toBe("13/3");
    expect(move.leaving).toBe(3);
    expect(fracText(move.salesRate)).toBe("4");
    // Past the minimum ratio the butter leftover turns negative.
    const beyond = valuesAlong(origin, move, 5);
    expect(beyond[3]).toBeCloseTo(-2);
    expect(beyond[2]).toBeCloseTo(8);
  });

  it("second pivot: x2 shrinks while x1 grows along the butter edge", () => {
    const second = pivot(basisState(START_BASIS), edgeMove(basisState(START_BASIS), 1));
    const move = edgeMove(second, 0);
    expect(move.rows.map((row) => [row.variable, fracText(row.rate), row.ratio && fracText(row.ratio)]))
      .toEqual([[2, "7/3", "4"], [1, "1/3", "13"]]);
    expect(move.leaving).toBe(2);
    expect(fracText(move.salesRate)).toBe("5/3");
  });

  it("reaches the same optimum when x1 enters first", () => {
    const states = walk((state) => (improving(state).includes(0) ? 0 : dantzigEntering(state)));
    expect(states.map((s) => texts([...s.point]))).toEqual([["0", "0"], ["6", "0"], ["4", "3"]]);
    expect(fracText(states[1].sales)).toBe("18");
    expect(texts(states[1].reduced)).toEqual(["0", "−2", "1", "0"]);
  });

  it("stops at the optimum with the shadow prices of flour and butter", () => {
    const optimum = walk(dantzigEntering).at(-1)!;
    expect(improving(optimum)).toEqual([]);
    expect(dantzigEntering(optimum)).toBeUndefined();
    expect(texts([...optimum.prices])).toEqual(["5/7", "6/7"]);
    expect(texts(optimum.values)).toEqual(["4", "3", "0", "0"]);
  });

  it("an infeasible basis shows up as a negative variable", () => {
    const wrong = basisState([2, 1]);
    expect(wrong.feasible).toBe(true);
    const skipRatio = basisState([1, 3]);
    expect(texts(skipRatio.values)).toEqual(["0", "9", "0", "−14"]);
    expect(skipRatio.feasible).toBe(false);
  });
});
