import { describe, expect, it } from "vitest";
import { act, ADVANCED, CAPACITY, certificate, ITEMS, nodeId, relaxation, SCENARIOS, startSearch, totals, type Choice } from "./branchBound";

const choices: Choice[] = Array.from({ length: 2 ** ITEMS.length }, (_, mask) => ITEMS.map((_, i) => (mask >> i & 1) as 0 | 1));
const feasible = choices.filter((choice) => totals(choice).weight <= CAPACITY);
const optimum = Math.max(...feasible.map((choice) => totals(choice).value));
describe("fractional knapsack proof", () => {
  it("bounds every completion of every partial assignment, including infeasible ones", () => {
    for (let length = 0; length <= ITEMS.length; length += 1) {
      for (const choice of choices) {
        const prefix = choice.slice(0, length);
        const completions = feasible.filter((full) => prefix.every((take, i) => take === full[i]));
        const bound = relaxation(prefix);
        expect(bound.feasible).toBe(completions.length > 0);
        for (const full of completions) expect(totals(full).value).toBeLessThanOrEqual(bound.bound + 1e-12);
      }
    }
    expect(relaxation([]).bound).toBeCloseTo(46 / 3);
    expect(relaxation([0]).bound).toBeCloseTo(12.6);
    expect(optimum).toBe(13);
  });
  it("finishes at the enumerated optimum from every feasible seed under varied node orders", () => {
    for (const seed of feasible) for (const order of ["first", "last", "bound"]) {
      let state = startSearch(seed);
      let steps = 0;
      while (state.frontier.length) {
        const node = order === "last" ? state.frontier.at(-1)!
          : order === "bound" ? [...state.frontier].sort((a, b) => relaxation(b).bound - relaxation(a).bound)[0] : state.frontier[0];
        const before = certificate(state);
        const r = relaxation(node);
        const prune = !r.feasible || r.bound <= before.lower;
        if (prune) for (const full of feasible.filter((full) => node.every((take, i) => take === full[i]))) {
          expect(totals(full).value).toBeLessThanOrEqual(before.lower);
        }
        state = act(state, nodeId(node), prune ? "prune" : "open");
        const after = certificate(state);
        expect(after.lower).toBeLessThanOrEqual(optimum);
        expect(after.upper + 1e-12).toBeGreaterThanOrEqual(optimum);
        expect(after.upper).toBeLessThanOrEqual(before.upper + 1e-12);
        expect(after.lower).toBeGreaterThanOrEqual(before.lower);
        expect(++steps).toBeLessThan(32);
      }
      expect(certificate(state)).toEqual({ lower: optimum, upper: optimum, gap: 0, proven: true });
    }
  });
  it("keeps a good seed unchanged while the certificate tightens and rejects premature pruning", () => {
    let state = startSearch([1, 0, 1, 0]);
    const rejected = act(state, "root", "prune");
    expect(rejected.frontier).toBe(state.frontier);
    expect(certificate(state).proven).toBe(false);
    state = act(state, "root", "open");
    state = act(state, "0", "prune");
    state = act(state, "1", "open");
    state = act(state, "11", "open");
    expect(certificate(state).lower).toBe(13);
    expect(certificate(state).upper).toBeCloseTo(14.4);
    expect(certificate(state).proven).toBe(false);
    expect(() => startSearch([1, 1, 1, 1])).toThrow();
  });
});

describe.each(SCENARIOS)("$title exhaustive certificate", (scenario) => {
  const all: Choice[] = Array.from({ length: 2 ** scenario.items.length }, (_, mask) => scenario.items.map((_, i) => (mask >> i & 1) as 0 | 1));
  const possible = all.filter((choice) => totals(choice, scenario).weight <= scenario.capacity);
  const exact = Math.max(...possible.map((choice) => totals(choice, scenario).value));
  it("bounds every feasible completion and detects every infeasible prefix", () => {
    for (let length = 0; length <= scenario.items.length; length++) {
      for (let mask = 0; mask < 2 ** length; mask++) {
        const prefix: Choice = Array.from({ length }, (_, i) => (mask >> i & 1) as 0 | 1);
        const completions = possible.filter((full) => prefix.every((take, i) => take === full[i]));
        const r = relaxation(prefix, scenario);
        expect(r.feasible).toBe(completions.length > 0);
        for (const full of completions) expect(totals(full, scenario).value).toBeLessThanOrEqual(r.bound + 1e-12);
      }
    }
    expect(() => startSearch(scenario.items.map(() => 1), scenario)).toThrow();
  });
  it("retains an optimum and prunes safely from all feasible seeds in three orders", () => {
    for (const seed of possible) for (const order of ["first", "last", "bound"]) {
      let state = startSearch(seed, scenario);
      let steps = 0;
      while (state.frontier.length) {
        const node = order === "last" ? state.frontier.at(-1)!
          : order === "bound" ? [...state.frontier].sort((a, b) => relaxation(b, scenario).bound - relaxation(a, scenario).bound)[0] : state.frontier[0];
        const before = certificate(state);
        const r = relaxation(node, scenario);
        const prune = !r.feasible || r.bound <= before.lower;
        if (prune) for (const full of possible.filter((full) => node.every((take, i) => take === full[i]))) expect(totals(full, scenario).value).toBeLessThanOrEqual(before.lower);
        state = act(state, nodeId(node), prune ? "prune" : "open");
        const after = certificate(state);
        expect(after.lower).toBeLessThanOrEqual(exact);
        expect(after.upper + 1e-12).toBeGreaterThanOrEqual(exact);
        expect(after.upper).toBeLessThanOrEqual(before.upper + 1e-12);
        expect(after.lower).toBeGreaterThanOrEqual(before.lower);
        expect(++steps).toBeLessThan(2 ** (scenario.items.length + 1));
      }
      expect(certificate(state)).toEqual({ lower: exact, upper: exact, gap: 0, proven: true });
    }
  });
});
it("has a genuine eight-item greedy trap and a density-order-independent relaxation", () => {
  let room = ADVANCED.capacity;
  const greedy = ADVANCED.items.map((item) => { const take = item.weight <= room ? 1 : 0; room -= take * item.weight; return take; });
  expect(totals(greedy, ADVANCED).value).toBe(17);
  expect(totals([1, 1, 0, 1, 0, 0, 0, 0], ADVANCED)).toEqual({ weight: 10, value: 18 });
  expect(relaxation([], { ...ADVANCED, items: [...ADVANCED.items].reverse() }).bound).toBeCloseTo(relaxation([], ADVANCED).bound);
});
