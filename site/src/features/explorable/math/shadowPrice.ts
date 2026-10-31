/**
 * How far the flour shadow price 5/7 can be trusted, on the bakery LP of the primal simplex article.
 *
 *   max 3 x1 + 4 x2  s.t.  3 x1 + 2 x2 <= b (flour),  x1 + 3 x2 <= 13 (butter),  x >= 0
 *
 * Everything is derived from the exact-fraction solver in `simplex.ts` with the flour stock `b`
 * as a parameter: the optimum at each b is found by pivoting from the origin, the dual prices are
 * the ones of that optimal basis, and the range of b is where that basis stays feasible.
 */
import {
  add, basisState, dantzigEntering, edgeMove, frac, less, mul, pivot, RHS, sign, sub, START_BASIS, value,
  type Basis, type BasisState, type Fraction, type VariableIndex,
} from "./simplex";

/** The slider moves in thirds so that the break point 26/3 is reachable exactly. */
export const FLOUR_DENOMINATOR = 3;
export const FLOUR_MIN = frac(6);
export const FLOUR_MAX = frac(45);
/** The article's stock; its optimal basis and prices are the ones the estimate extends. */
export const BASE_FLOUR = frac(18);
export const BUTTER = frac(RHS[1]);

/** The stock `k / 3` for the slider integer k. */
export const flourAt = (k: number): Fraction => frac(k, FLOUR_DENOMINATOR);
/** Slider integer for a stock that is a multiple of 1/3. */
export const sliderIndex = (flour: Fraction): number => (flour.n * FLOUR_DENOMINATOR) / flour.d;
export const SLIDER_MIN = sliderIndex(FLOUR_MIN);
export const SLIDER_MAX = sliderIndex(FLOUR_MAX);

/** The optimum at flour stock `flour` (>= 0): primal simplex from the origin with Dantzig's rule. */
export function optimumAt(flour: Fraction): BasisState {
  if (sign(flour) < 0) throw new Error("the origin must be feasible");
  let state = basisState(START_BASIS, flour);
  for (let guard = 0; guard < 8; guard += 1) {
    const entering = dantzigEntering(state);
    if (entering === undefined) return state;
    const move = edgeMove(state, entering as VariableIndex);
    if (move.leaving === undefined) throw new Error("unbounded");
    state = pivot(state, move);
  }
  throw new Error("simplex did not stop");
}

const same = (a: Fraction, b: Fraction) => a.n === b.n && a.d === b.d;

/** The range of flour stocks where `basis` stays feasible; an undefined end is unbounded. */
export interface FlourRange {
  low?: Fraction;
  high?: Fraction;
}

/** Basic values are linear in b, so two exact solves give each line; the range follows from v >= 0. */
export function feasibleRange(basis: Basis): FlourRange {
  const at0 = basisState(basis, frac(0));
  const at1 = basisState(basis, frac(1));
  const range: FlourRange = {};
  for (const index of basis) {
    const v0 = at0.values[index];
    const slope = sub(at1.values[index], v0);
    if (sign(slope) === 0) continue;
    const root = mul(frac(-1), mul(v0, frac(slope.d, slope.n)));
    if (sign(slope) > 0) {
      if (!range.low || less(range.low, root)) range.low = root;
    } else if (!range.high || less(root, range.high)) {
      range.high = root;
    }
  }
  return range;
}

export const inRange = (range: FlourRange, flour: Fraction) => (
  (!range.low || !less(flour, range.low)) && (!range.high || !less(range.high, flour))
);

/** The optimal basis of the article (flour 18) and its price, extended linearly to every b. */
export const BASE = optimumAt(BASE_FLOUR);
export const BASE_RANGE = feasibleRange(BASE.basis);
export const BASE_PRICE = BASE.prices[0];

/** What the shadow price predicts for the sales at `flour`: 24 + (5/7)(b - 18). */
export const estimateAt = (flour: Fraction): Fraction => add(BASE.sales, mul(BASE_PRICE, sub(flour, BASE_FLOUR)));

export interface FlourReading {
  flour: Fraction;
  /** The true optimum at this stock. */
  state: BasisState;
  /** The 5/7 estimate, and estimate minus true value. */
  estimate: Fraction;
  gap: Fraction;
  /** Whether the optimal basis is still the one of the article, so the estimate is exact. */
  sameBasis: boolean;
  /** u b + v 13 with the prices of this optimal basis. It equals the optimum when the solve is right. */
  certificate: Fraction;
}

export function readingAt(flour: Fraction): FlourReading {
  const walked = optimumAt(flour);
  // At the end b = 26/3 the vertex is degenerate: {x1, x2} and {x2, s2} both describe it. Inside the
  // range the article's basis is feasible with unchanged reduced costs, so it is the one shown.
  const state = inRange(BASE_RANGE, flour) ? basisState(BASE.basis, flour) : walked;
  if (!same(state.sales, walked.sales)) throw new Error("the shown basis is not optimal");
  const estimate = estimateAt(flour);
  return {
    flour,
    state,
    estimate,
    gap: sub(estimate, state.sales),
    sameBasis: inRange(BASE_RANGE, flour),
    certificate: add(mul(state.prices[0], flour), mul(state.prices[1], BUTTER)),
  };
}

/** Basis variables in index order, for display (the pivots leave them in row order). */
export const sortedBasis = (state: BasisState): VariableIndex[] => [...state.basis].sort() as VariableIndex[];

/** The feasible polygon at flour stock `flour`, counter-clockwise, as plain numbers for drawing. */
export function polygonAt(flour: Fraction): [number, number][] {
  const b = value(flour);
  // Vertices of {3x1+2x2<=b, x1+3x2<=13, x>=0}: the origin, the two axis cuts, and the crossing.
  const xAxis = Math.min(b / 3, 13);
  const yAxis = Math.min(b / 2, 13 / 3);
  const crossing: [number, number] = [(3 * b - 26) / 7, (39 - b) / 7];
  const points: [number, number][] = [[0, 0], [xAxis, 0]];
  if (crossing[0] > 1e-9 && crossing[1] > 1e-9) points.push(crossing);
  points.push([0, yAxis]);
  return points.filter(([x, y], i) => i === 0 || x !== points[i - 1][0] || y !== points[i - 1][1]);
}
