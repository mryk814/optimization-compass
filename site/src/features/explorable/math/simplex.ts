/**
 * Primal simplex on the bakery LP of the primal simplex article, in exact fractions.
 *
 *   max 3 x1 + 4 x2  s.t.  3 x1 + 2 x2 + s1 = 18 (flour),  x1 + 3 x2 + s2 = 13 (butter),  all >= 0
 *
 * The article works in the minimisation form min -3 x1 - 4 x2, so a negative reduced cost means
 * "increasing this variable raises the sales". Every number the figure shows comes from here.
 */

/** An exact fraction n/d with d > 0, kept in lowest terms. */
export interface Fraction {
  readonly n: number;
  readonly d: number;
}

const gcd = (a: number, b: number): number => (b === 0 ? Math.abs(a) : gcd(b, a % b));

export function frac(n: number, d = 1): Fraction {
  if (d === 0) throw new Error("zero denominator");
  const sign = d < 0 ? -1 : 1;
  const g = gcd(n, d) || 1;
  return { n: (sign * n) / g, d: Math.abs(d) / g };
}

export const add = (a: Fraction, b: Fraction) => frac(a.n * b.d + b.n * a.d, a.d * b.d);
export const sub = (a: Fraction, b: Fraction) => frac(a.n * b.d - b.n * a.d, a.d * b.d);
export const mul = (a: Fraction, b: Fraction) => frac(a.n * b.n, a.d * b.d);
export const div = (a: Fraction, b: Fraction) => frac(a.n * b.d, a.d * b.n);
export const neg = (a: Fraction) => frac(-a.n, a.d);
export const sign = (a: Fraction) => Math.sign(a.n);
export const less = (a: Fraction, b: Fraction) => a.n * b.d < b.n * a.d;
export const value = (a: Fraction) => a.n / a.d;

/** "13/3", "−5/3", "4". Uses a true minus sign. */
export function fracText(a: Fraction): string {
  const body = a.d === 1 ? `${Math.abs(a.n)}` : `${Math.abs(a.n)}/${a.d}`;
  return a.n < 0 ? `−${body}` : body;
}

export type VariableIndex = 0 | 1 | 2 | 3;
export const VARIABLES = [0, 1, 2, 3] as const;

export interface VariableInfo {
  symbol: string;
  name: string;
}

export const VARIABLE_INFO: readonly VariableInfo[] = [
  { symbol: "x₁", name: "食パン" },
  { symbol: "x₂", name: "クロワッサン" },
  { symbol: "s₁", name: "小麦粉の余り" },
  { symbol: "s₂", name: "バターの余り" },
];

/** Columns of [A | I] for x1, x2, s1, s2, the right-hand side, and the minimisation costs. */
export const COLUMNS: readonly (readonly [number, number])[] = [[3, 1], [2, 3], [1, 0], [0, 1]];
export const RHS: readonly [number, number] = [18, 13];
export const COSTS: readonly number[] = [-3, -4, 0, 0];
export const RESOURCES = ["小麦粉", "バター"] as const;

/** A basis lists which variable is basic in row 0 and row 1. */
export type Basis = readonly [VariableIndex, VariableIndex];
export const START_BASIS: Basis = [2, 3];

export interface BasisState {
  basis: Basis;
  /** The flour stock b of this state; the article's value is 18. The butter stock stays 13. */
  flour: Fraction;
  /** Value of every variable; the nonbasic ones are 0. Negative means the basis is infeasible. */
  values: Fraction[];
  /** Reduced cost of every variable in the minimisation form; basic ones are 0. */
  reduced: Fraction[];
  /** The bakery's sales 3 x1 + 4 x2. */
  sales: Fraction;
  point: readonly [Fraction, Fraction];
  feasible: boolean;
  /** Shadow prices of flour and butter, c_B^T B^{-1} with the sign of the maximisation form. */
  prices: readonly [Fraction, Fraction];
}

/** Solve the 2x2 system B y = r, where B holds the basic columns. */
function solve(basis: Basis, r: readonly [Fraction, Fraction]): [Fraction, Fraction] {
  const [p, q] = basis.map((index) => COLUMNS[index]);
  const det = p[0] * q[1] - q[0] * p[1];
  if (det === 0) throw new Error(`singular basis ${basis.join(",")}`);
  const D = frac(det);
  const y0 = div(sub(mul(r[0], frac(q[1])), mul(frac(q[0]), r[1])), D);
  const y1 = div(sub(mul(frac(p[0]), r[1]), mul(frac(p[1]), r[0])), D);
  return [y0, y1];
}

export function basisState(basis: Basis, flour: Fraction = frac(RHS[0])): BasisState {
  const xb = solve(basis, [flour, frac(RHS[1])]);
  const values = VARIABLES.map(() => frac(0));
  basis.forEach((index, row) => { values[index] = xb[row]; });
  // Dual y solves B^T y = c_B, so reduced cost = c_j - y . A_j.
  const [p, q] = basis.map((index) => COLUMNS[index]);
  const cb = basis.map((index) => frac(COSTS[index]));
  const det = frac(p[0] * q[1] - q[0] * p[1]);
  const y0 = div(sub(mul(cb[0], frac(q[1])), mul(frac(p[1]), cb[1])), det);
  const y1 = div(sub(mul(frac(p[0]), cb[1]), mul(frac(q[0]), cb[0])), det);
  const reduced = VARIABLES.map((j) => sub(
    frac(COSTS[j]),
    add(mul(y0, frac(COLUMNS[j][0])), mul(y1, frac(COLUMNS[j][1]))),
  ));
  const sales = add(mul(frac(3), values[0]), mul(frac(4), values[1]));
  return {
    basis,
    flour,
    values,
    reduced,
    sales,
    point: [values[0], values[1]],
    feasible: values.every((entry) => sign(entry) >= 0),
    prices: [neg(y0), neg(y1)],
  };
}

export const isBasic = (state: BasisState, index: VariableIndex) => state.basis.includes(index);

export interface RatioRow {
  /** The basic variable that shrinks while the entering one grows. */
  variable: VariableIndex;
  /** How much it shrinks per unit of the entering variable (d_i). */
  rate: Fraction;
  /** Its current value divided by the rate, or undefined when it does not shrink. */
  ratio?: Fraction;
}

export interface EdgeMove {
  entering: VariableIndex;
  /** Change of every variable per unit of the entering one. */
  direction: Fraction[];
  rows: RatioRow[];
  /** The minimum ratio θ, or undefined when nothing ever reaches 0 (unbounded). */
  theta?: Fraction;
  leaving?: VariableIndex;
  /** Change of the sales per unit of the entering variable (−reduced cost). */
  salesRate: Fraction;
}

/** What happens when `entering` grows from the vertex of `state`: the ratio test. */
export function edgeMove(state: BasisState, entering: VariableIndex): EdgeMove {
  if (isBasic(state, entering)) throw new Error("entering variable must be nonbasic");
  const d = solve(state.basis, [frac(COLUMNS[entering][0]), frac(COLUMNS[entering][1])]);
  const direction = VARIABLES.map(() => frac(0));
  direction[entering] = frac(1);
  const rows: RatioRow[] = state.basis.map((variable, row) => {
    direction[variable] = neg(d[row]);
    return {
      variable,
      rate: d[row],
      ratio: sign(d[row]) > 0 ? div(state.values[variable], d[row]) : undefined,
    };
  });
  let best: RatioRow | undefined;
  for (const row of rows) {
    if (row.ratio && (!best || less(row.ratio, best.ratio!))) best = row;
  }
  return {
    entering,
    direction,
    rows,
    theta: best?.ratio,
    leaving: best?.variable,
    salesRate: neg(state.reduced[entering]),
  };
}

/** Every variable after increasing the entering one by `amount` (a number, for the slider). */
export function valuesAlong(state: BasisState, move: EdgeMove, amount: number): number[] {
  return VARIABLES.map((j) => value(state.values[j]) + value(move.direction[j]) * amount);
}

/** Pivot: the entering variable takes the row of the leaving one. */
export function pivot(state: BasisState, move: EdgeMove): BasisState {
  if (move.leaving === undefined) throw new Error("unbounded edge has no pivot");
  const basis = state.basis.map((index) => (index === move.leaving ? move.entering : index)) as unknown as Basis;
  return basisState(basis, state.flour);
}

/** The nonbasic variables that raise the sales, i.e. negative reduced cost. */
export function improving(state: BasisState): VariableIndex[] {
  return VARIABLES.filter((j) => !isBasic(state, j) && sign(state.reduced[j]) < 0);
}

/** Dantzig's rule: the most negative reduced cost, the smaller index on a tie. */
export function dantzigEntering(state: BasisState): VariableIndex | undefined {
  let best: VariableIndex | undefined;
  for (const j of improving(state)) {
    if (best === undefined || less(state.reduced[j], state.reduced[best])) best = j;
  }
  return best;
}

/** The bounded feasible polygon in (x1, x2), counter-clockwise from the origin. */
export const POLYGON: readonly (readonly [number, number])[] = [[0, 0], [6, 0], [4, 3], [0, 13 / 3]];
