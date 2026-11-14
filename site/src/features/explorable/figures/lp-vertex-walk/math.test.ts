import { describe, expect, it } from "vitest";

import {
  ARTICLE_LP,
  ARTICLE_REVENUE,
  feasibleVertices,
  objectiveValue,
  optimalVertices,
  type Vec2,
} from "../../math/lp2d";
import { STOCKS, followPlan, levelChord, shortages, stockUsage, usesUp, violated } from "./math";

// The numbers the lesson steps and the article of concept.linear-program say. They were first
// computed with exact fractions and HiGHS (the article's Python block reproduces the optimum);
// this file holds the figure to the same values.
const VERTICES = feasibleVertices(ARTICLE_LP);
const CORNER: Vec2 = [4, 3];
const BREAD_ONLY: Vec2 = [6, 0];
const CROISSANT_ONLY: Vec2 = [0, 13 / 3];

const best = (cost: Vec2) => optimalVertices(VERTICES, cost).map((index) => VERTICES[index]);
const expectPoints = (actual: readonly Vec2[], expected: readonly Vec2[]) => {
  expect(actual).toHaveLength(expected.length);
  for (const point of expected) {
    expect(actual.some((seen) => Math.hypot(seen[0] - point[0], seen[1] - point[1]) < 1e-9)).toBe(true);
  }
};

describe("the bakery's stock", () => {
  it("is 18 of flour and 13 of butter, used 3 and 1 per bread, 2 and 3 per croissant", () => {
    expect(STOCKS.map((stock) => [stock.name, stock.per, stock.limit])).toEqual([
      ["小麦粉", [3, 2], 18],
      ["バター", [1, 3], 13],
    ]);
  });

  it("gives the revenue and the stock used at each corner", () => {
    expectPoints(VERTICES, [[0, 0], BREAD_ONLY, CORNER, CROISSANT_ONLY]);
    expect(objectiveValue(ARTICLE_REVENUE, BREAD_ONLY)).toBe(18);
    expect(stockUsage(BREAD_ONLY)).toEqual([18, 6]);
    expect(objectiveValue(ARTICLE_REVENUE, CORNER)).toBe(24);
    expect(stockUsage(CORNER)).toEqual([18, 13]);
    // Croissants only: about 17.3, below bread only, with more than 9 of flour left over.
    expect(objectiveValue(ARTICLE_REVENUE, CROISSANT_ONLY)).toBeCloseTo(52 / 3, 12);
    expect(18 - stockUsage(CROISSANT_ONLY)[0]).toBeCloseTo(28 / 3, 12);
    expect(18 - stockUsage(CROISSANT_ONLY)[0]).toBeGreaterThan(9);
    expect(best(ARTICLE_REVENUE)).toEqual([CORNER]);
  });
});

describe("the plans the lesson steps show", () => {
  it("step 1 ends on 5 breads and 1 croissant, inside the stock", () => {
    expect(stockUsage([5, 1])).toEqual([17, 8]);
    expect(violated([5, 1])).toBe(false);
  });

  it("step 2: with 5 breads, flour runs out at 1.5 croissants and butter at about 2.7", () => {
    expect(usesUp([5, 1.5], 0)).toBe(true);
    expect(violated([5, 1.5])).toBe(false);
    expect(shortages([5, 1.6])[0]).toBeGreaterThan(0);
    expect(shortages([5, 1.6])[1]).toBe(0);
    expect(usesUp([5, 8 / 3], 1)).toBe(true);
    expect(shortages([5, 2.7])[1]).toBeGreaterThan(0);
    expect(stockUsage([5, 3.5])).toEqual([22, 15.5]);
    expect(shortages([5, 3.5])).toEqual([4, 2.5]);
  });

  it("step 3: 4 breads alone and 2 breads with 1.5 croissants both sell for 12", () => {
    expect(objectiveValue(ARTICLE_REVENUE, [4, 0])).toBe(12);
    expect(objectiveValue(ARTICLE_REVENUE, [2, 1.5])).toBe(12);
    expectPoints(levelChord(VERTICES, ARTICLE_REVENUE, 12), [[4, 0], [0, 3]]);
    // (2, 1.5) is half of (4, 3): both bars go from half to full together in step 5.
    expect(stockUsage([2, 1.5])).toEqual([9, 6.5]);
  });

  it("step 5: the line's part inside the range ends by shrinking to the one point (4, 3) at 24", () => {
    const length = (value: number) => {
      const chord = levelChord(VERTICES, ARTICLE_REVENUE, value);
      return chord.length === 2 ? Math.hypot(chord[0][0] - chord[1][0], chord[0][1] - chord[1][1]) : 0;
    };
    expect(length(12)).toBeCloseTo(5, 12);
    // It first grows while both ends are still on the axes, so the step does not say "shrinks from 12".
    expect(length(18)).toBeCloseTo(7, 12);
    // Past 18 both ends are on the stock lines and it only shrinks.
    expect(length(20)).toBeLessThan(length(18));
    expect(length(23)).toBeLessThan(length(20));
    expect(length(23)).toBeGreaterThan(0);
    expectPoints(levelChord(VERTICES, ARTICLE_REVENUE, 24), [CORNER]);
    expect(usesUp(CORNER, 0) && usesUp(CORNER, 1)).toBe(true);
  });

  it("step 6: one tenth more sells for 26.4 but is 1.8 of flour and 1.3 of butter short", () => {
    const plan: Vec2 = [4.4, 3.3];
    expect(objectiveValue(ARTICLE_REVENUE, plan)).toBeCloseTo(26.4, 12);
    expect(shortages(plan)[0]).toBeCloseTo(1.8, 12);
    expect(shortages(plan)[1]).toBeCloseTo(1.3, 12);
    expect(levelChord(VERTICES, ARTICLE_REVENUE, 26.4)).toEqual([]);
  });
});

describe("cutting the croissant's price (bread stays at 3)", () => {
  it("keeps (4, 3) best down to 2, where the whole edge to (6, 0) ties at 18", () => {
    for (const [price, revenue] of [[4, 24], [3, 21], [2.5, 19.5]] as const) {
      expect(best([3, price])).toEqual([CORNER]);
      expect(objectiveValue([3, price], CORNER)).toBe(revenue);
      expect(followPlan(VERTICES, [3, price], [1, 1])).toEqual(CORNER);
    }
    expectPoints(best([3, 2]), [BREAD_ONLY, CORNER]);
    expect(objectiveValue([3, 2], CORNER)).toBe(18);
    expectPoints(levelChord(VERTICES, [3, 2], 18), [BREAD_ONLY, CORNER]);
    // On a tie the following plan stays where it is.
    expect(followPlan(VERTICES, [3, 2], CORNER)).toEqual(CORNER);
  });

  it("moves the best plan to bread only below 2, still selling for 18", () => {
    for (const [price, atCorner] of [[1.5, 16.5], [1, 15]] as const) {
      expectPoints(best([3, price]), [BREAD_ONLY]);
      expect(objectiveValue([3, price], BREAD_ONLY)).toBe(18);
      expect(objectiveValue([3, price], CORNER)).toBe(atCorner);
      expectPoints([followPlan(VERTICES, [3, price], CORNER)], [BREAD_ONLY]);
    }
  });

  it("keeps (4, 3) best exactly while the croissant sells for 2 to 9", () => {
    const cornerIsBest = (price: number) => (
      best([3, price]).some((point) => Math.hypot(point[0] - 4, point[1] - 3) < 1e-9)
    );
    expect(cornerIsBest(2)).toBe(true);
    expect(cornerIsBest(9)).toBe(true);
    expect(cornerIsBest(9.01)).toBe(false);
    expect(cornerIsBest(1.99)).toBe(false);
  });
});

describe("levelChord", () => {
  it("has no line to cut with when both prices are zero", () => {
    expect(levelChord(VERTICES, [0, 0], 0)).toEqual([]);
    expect(followPlan(VERTICES, [0, 0], [2, 1])).toEqual([2, 1]);
  });

  it("returns the corner alone when the line only touches the origin", () => {
    expectPoints(levelChord(VERTICES, ARTICLE_REVENUE, 0), [[0, 0]]);
  });
});
