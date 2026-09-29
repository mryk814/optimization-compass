export interface CurveFunction {
  id: "quadratic" | "double-well" | "absolute";
  label: string;
  convex: boolean;
  f(x: number): number;
  /** A (sub)gradient used only for the downhill animation. */
  df(x: number): number;
  defaultA: number;
  defaultB: number;
}

export const CURVE_DOMAIN: readonly [number, number] = [-2.6, 2.6];

export const CURVE_FUNCTIONS: readonly CurveFunction[] = [
  {
    id: "quadratic",
    label: "二次関数（凸）",
    convex: true,
    f: (x) => 0.35 * x * x + 0.2,
    df: (x) => 0.7 * x,
    defaultA: -1.8,
    defaultB: 1.6,
  },
  {
    id: "double-well",
    label: "二つの谷（凸ではない）",
    convex: false,
    f: (x) => 0.18 * x ** 4 - 0.9 * x * x + 0.25 * x + 1.4,
    df: (x) => 0.72 * x ** 3 - 1.8 * x + 0.25,
    defaultA: -1.5,
    defaultB: 1.5,
  },
  {
    id: "absolute",
    label: "絶対値（凸だが滑らかでない）",
    convex: true,
    f: (x) => 0.9 * Math.abs(x - 0.3) + 0.1,
    df: (x) => (x > 0.3 ? 0.9 : x < 0.3 ? -0.9 : 0),
    defaultA: -1.8,
    defaultB: 2,
  },
];

export interface ChordReading {
  /** theta * a + (1 - theta) * b, the input mixed by the definition. */
  mix: number;
  /** f at the mixed input. */
  atMix: number;
  /** theta * f(a) + (1 - theta) * f(b), the outputs mixed by the same ratio. */
  chord: number;
  /** chord - atMix. The definition of convexity asks for this to be non-negative. */
  slack: number;
}

export function chordReading(fn: (x: number) => number, a: number, b: number, theta: number): ChordReading {
  const mix = theta * a + (1 - theta) * b;
  const atMix = fn(mix);
  const chord = theta * fn(a) + (1 - theta) * fn(b);
  return { mix, atMix, chord, slack: chord - atMix };
}

const VIOLATION_TOLERANCE = 1e-9;

/** Sub-intervals of theta in [0, 1] where the chord dips below the graph. */
export function violationIntervals(
  fn: (x: number) => number,
  a: number,
  b: number,
  samples = 240,
): Array<readonly [number, number]> {
  const intervals: Array<[number, number]> = [];
  let open: number | undefined;
  for (let index = 0; index <= samples; index += 1) {
    const theta = index / samples;
    const violates = chordReading(fn, a, b, theta).slack < -VIOLATION_TOLERANCE;
    if (violates && open === undefined) open = theta;
    if (!violates && open !== undefined) {
      intervals.push([open, (index - 1) / samples]);
      open = undefined;
    }
  }
  if (open !== undefined) intervals.push([open, 1]);
  return intervals;
}

/** Plain gradient descent on one variable, clamped to the plotted domain. */
export function descendFrom(fn: CurveFunction, start: number, eta = 0.12, steps = 60): number[] {
  const path = [start];
  let x = start;
  for (let step = 0; step < steps; step += 1) {
    const slope = fn.df(x);
    if (Math.abs(slope) < 1e-4) break;
    x = Math.min(CURVE_DOMAIN[1], Math.max(CURVE_DOMAIN[0], x - eta * slope));
    path.push(x);
  }
  return path;
}

export function globalMinimum(fn: CurveFunction, samples = 2600): { x: number; value: number } {
  let best = { x: CURVE_DOMAIN[0], value: Infinity };
  for (let index = 0; index <= samples; index += 1) {
    const x = CURVE_DOMAIN[0] + ((CURVE_DOMAIN[1] - CURVE_DOMAIN[0]) * index) / samples;
    const value = fn.f(x);
    if (value < best.value) best = { x, value };
  }
  return best;
}
