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

/** The sweep is a timeline of whole steps; one step moves the mixing ratio by 1 / SWEEP_HALF. */
export const SWEEP_HALF = 10;
export const SWEEP_STEPS = SWEEP_HALF * 2;

/** Mixing ratio at a sweep position in [0, SWEEP_STEPS]: 0 to 1 over the first half, back to 0 over the second. */
export function sweepTheta(position: number): number {
  const clamped = Math.min(SWEEP_STEPS, Math.max(0, position));
  return clamped <= SWEEP_HALF ? clamped / SWEEP_HALF : (SWEEP_STEPS - clamped) / SWEEP_HALF;
}

/** Largest mixing ratio the sweep has reached by this position (how much of the trace is drawn). */
export function sweepReach(position: number): number {
  return Math.min(1, Math.max(0, position) / SWEEP_HALF);
}

export interface SlackSample {
  theta: number;
  /** Chord height minus graph height at this mixing ratio. Negative breaks the definition. */
  slack: number;
}

/** The gap between chord and graph over theta in [0, 1]: the curve the sweep draws. */
export function slackTrace(
  fn: (x: number) => number,
  a: number,
  b: number,
  samples = 100,
): SlackSample[] {
  const trace: SlackSample[] = [];
  for (let index = 0; index <= samples; index += 1) {
    const theta = index / samples;
    trace.push({ theta, slack: chordReading(fn, a, b, theta).slack });
  }
  return trace;
}

/**
 * Closed form of the gap for the quadratic preset c x^2 + d:
 * c * theta * (1 - theta) * (a - b)^2. The offset d cancels.
 */
export function quadraticHump(curvature: number, a: number, b: number, theta: number): number {
  return curvature * theta * (1 - theta) * (a - b) ** 2;
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
