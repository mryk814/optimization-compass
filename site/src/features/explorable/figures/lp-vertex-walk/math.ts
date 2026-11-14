import { ARTICLE_LP, objectiveValue, optimalVertices, type Vec2 } from "../../math/lp2d";

/** A stocked ingredient of the bakery LP: what one bread and one croissant use, and how much there is. */
export interface Stock {
  name: string;
  per: Vec2;
  limit: number;
}

/** Flour (100 g) and butter (10 g), read from the shared bakery LP so the two cannot drift. */
export const STOCKS: readonly Stock[] = [
  { name: "小麦粉", per: ARTICLE_LP[0].a, limit: ARTICLE_LP[0].b },
  { name: "バター", per: ARTICLE_LP[1].a, limit: ARTICLE_LP[1].b },
];

const EPSILON = 1e-9;

/** How much of each stock a plan (bread, croissants) uses, in the order of `STOCKS`. */
export function stockUsage(plan: Vec2): number[] {
  return STOCKS.map((stock) => stock.per[0] * plan[0] + stock.per[1] * plan[1]);
}

/** How much of each stock a plan is short of; 0 where the stock is enough. */
export function shortages(plan: Vec2): number[] {
  return stockUsage(plan).map((used, index) => {
    const over = used - STOCKS[index].limit;
    return over > EPSILON ? over : 0;
  });
}

/** True when the plan needs more of some stock than there is. */
export function violated(plan: Vec2): boolean {
  return shortages(plan).some((short) => short > 0);
}

/** True when the plan uses exactly all of stock `index`. */
export function usesUp(plan: Vec2, index: number): boolean {
  return Math.abs(stockUsage(plan)[index] - STOCKS[index].limit) <= 1e-7;
}

/**
 * The part of the line `cost . p = value` inside the convex polygon `vertices`: no point when the
 * line misses it, one when it touches a corner, two (the ends of a segment) otherwise. A line
 * lying on an edge gives that edge's two corners.
 */
export function levelChord(vertices: readonly Vec2[], cost: Vec2, value: number): Vec2[] {
  if (Math.hypot(cost[0], cost[1]) < EPSILON) return [];
  const tolerance = 1e-7 * Math.max(1, Math.abs(value));
  const found: Vec2[] = [];
  const add = (point: Vec2) => {
    if (!found.some((seen) => Math.hypot(seen[0] - point[0], seen[1] - point[1]) < 1e-6)) found.push(point);
  };
  vertices.forEach((from, index) => {
    const to = vertices[(index + 1) % vertices.length];
    const atFrom = objectiveValue(cost, from) - value;
    const atTo = objectiveValue(cost, to) - value;
    if (Math.abs(atFrom) <= tolerance) add(from);
    else if (Math.abs(atTo) > tolerance && atFrom * atTo < 0) {
      const t = atFrom / (atFrom - atTo);
      add([from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t]);
    }
  });
  return found;
}

/**
 * Where a plan that follows the best corner sits: on the single best vertex, or where it already
 * is when two corners tie (the whole edge between them is then best) or every price is zero.
 */
export function followPlan(vertices: readonly Vec2[], cost: Vec2, plan: Vec2): Vec2 {
  if (Math.hypot(cost[0], cost[1]) < EPSILON) return plan;
  const best = optimalVertices(vertices, cost);
  return best.length === 1 ? vertices[best[0]] : plan;
}
