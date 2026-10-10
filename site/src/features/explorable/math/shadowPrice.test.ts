import { describe, expect, it } from "vitest";

import { basisState, frac, fracText, START_BASIS } from "./simplex";
import {
  BASE, BASE_FLOUR, BASE_PRICE, BASE_RANGE, estimateAt, feasibleRange, flourAt, inRange, optimumAt,
  polygonAt, readingAt, SLIDER_MAX, SLIDER_MIN, sortedBasis,
} from "./shadowPrice";

const text = (b: number, d = 1) => {
  const reading = readingAt(frac(b, d));
  return {
    basis: sortedBasis(reading.state).join(","),
    point: reading.state.point.map(fracText),
    value: fracText(reading.state.sales),
    estimate: fracText(reading.estimate),
    gap: fracText(reading.gap),
    prices: reading.state.prices.map(fracText),
    certificate: fracText(reading.certificate),
  };
};

describe("flour shadow price and its range", () => {
  it("keeps the article's solve at b = 18 and its price 5/7", () => {
    expect(optimumAt(BASE_FLOUR).point.map(fracText)).toEqual(["4", "3"]);
    expect(fracText(BASE.sales)).toBe("24");
    expect(BASE.prices.map(fracText)).toEqual(["5/7", "6/7"]);
    expect(fracText(BASE_PRICE)).toBe("5/7");
    // The generalised solver still gives the unchanged origin state for the article's stock.
    expect(basisState(START_BASIS).flour).toEqual(frac(18));
  });

  it("the basis {x1, x2} is feasible exactly for 26/3 <= b <= 39", () => {
    expect(BASE_RANGE.low && fracText(BASE_RANGE.low)).toBe("26/3");
    expect(BASE_RANGE.high && fracText(BASE_RANGE.high)).toBe("39");
    const x = (b: number, d = 1) => basisState([0, 1], frac(b, d)).values.slice(0, 2).map(fracText);
    expect(x(19)).toEqual(["31/7", "20/7"]);
    expect(x(26, 3)).toEqual(["0", "13/3"]);
    expect(x(39)).toEqual(["13", "0"]);
    expect(basisState([0, 1], frac(25, 3)).feasible).toBe(false);
    expect(basisState([0, 1], frac(40)).feasible).toBe(false);
    expect(inRange(BASE_RANGE, frac(26, 3))).toBe(true);
    expect(inRange(BASE_RANGE, frac(39))).toBe(true);
    expect(inRange(BASE_RANGE, frac(25, 3))).toBe(false);
    expect(inRange(BASE_RANGE, frac(40))).toBe(false);
  });

  it("b = 19: the estimate is exact, value 173/7", () => {
    expect(text(19)).toEqual({
      basis: "0,1", point: ["31/7", "20/7"], value: "173/7", estimate: "173/7", gap: "0",
      prices: ["5/7", "6/7"], certificate: "173/7",
    });
    expect(readingAt(frac(19)).state.sales.n / readingAt(frac(19)).state.sales.d).toBeCloseTo(24.714, 3);
  });

  it("b = 40: the optimum is 39 at (13, 0), the 5/7 estimate overshoots by 5/7", () => {
    expect(text(40)).toEqual({
      basis: "0,2", point: ["13", "0"], value: "39", estimate: "278/7", gap: "5/7",
      prices: ["0", "3"], certificate: "39",
    });
    expect(readingAt(frac(40)).sameBasis).toBe(false);
  });

  it("b = 39 is the last stock where the estimate is exact", () => {
    expect(text(39)).toMatchObject({ value: "39", estimate: "39", gap: "0", point: ["13", "0"] });
    expect(readingAt(frac(39)).sameBasis).toBe(true);
  });

  it("b below 26/3 changes the basis to {x2, s2}: value 2b at (0, b/2), flour price 2", () => {
    expect(text(6)).toEqual({
      basis: "1,3", point: ["0", "3"], value: "12", estimate: "108/7", gap: "24/7",
      prices: ["2", "0"], certificate: "12",
    });
    expect(text(8)).toMatchObject({ basis: "1,3", point: ["0", "4"], value: "16" });
    expect(text(26, 3)).toMatchObject({ value: "52/3", point: ["0", "13/3"], estimate: "52/3", gap: "0" });
    expect(text(25, 3)).toMatchObject({ basis: "1,3", value: "50/3", gap: "3/7" });
    expect(readingAt(frac(6)).sameBasis).toBe(false);
  });

  it("the certificate u b + v 13 equals the optimum at every slider position", () => {
    for (let k = SLIDER_MIN; k <= SLIDER_MAX; k += 1) {
      const reading = readingAt(flourAt(k));
      expect(fracText(reading.certificate)).toBe(fracText(reading.state.sales));
      expect(reading.state.feasible).toBe(true);
      expect(reading.state.reduced.every((c) => c.n >= 0)).toBe(true);
    }
  });

  it("inside the range the shown basis has the same value as the pivoting walk", () => {
    for (let k = SLIDER_MIN; k <= SLIDER_MAX; k += 1) {
      const flour = flourAt(k);
      expect(fracText(readingAt(flour).state.sales)).toBe(fracText(optimumAt(flour).sales));
    }
    // At 26/3 the walk stops on {x2, s2}; the vertex (0, 13/3) is degenerate and {x1, x2} describes it too.
    expect(sortedBasis(optimumAt(frac(26, 3))).join()).toBe("1,3");
    expect(sortedBasis(readingAt(frac(26, 3)).state).join()).toBe("0,1");
  });

  it("the estimate is never below the true optimum, and equals it only inside the range", () => {
    for (let k = SLIDER_MIN; k <= SLIDER_MAX; k += 1) {
      const reading = readingAt(flourAt(k));
      expect(reading.gap.n >= 0).toBe(true);
      expect(reading.gap.n === 0).toBe(inRange(BASE_RANGE, reading.flour));
    }
  });

  it("finds the range of any basis from the same solver", () => {
    expect(feasibleRange([1, 3]).high && fracText(feasibleRange([1, 3]).high!)).toBe("26/3");
    expect(feasibleRange([0, 2]).low && fracText(feasibleRange([0, 2]).low!)).toBe("39");
    expect(fracText(estimateAt(frac(40)))).toBe("278/7");
  });

  it("draws the polygon of the current stock", () => {
    expect(polygonAt(frac(18))).toEqual([[0, 0], [6, 0], [4, 3], [0, 13 / 3]]);
    expect(polygonAt(frac(6))).toEqual([[0, 0], [2, 0], [0, 3]]);
    expect(polygonAt(frac(45))).toEqual([[0, 0], [13, 0], [0, 13 / 3]]);
  });
});
