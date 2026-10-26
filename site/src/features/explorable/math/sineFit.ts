/**
 * Fitting y = a sin(ωt) to eight readings of a spring, the running example of the
 * nonlinear least-squares article. The amplitude a enters linearly and the angular frequency ω
 * does not, so the sum of squares over (ω, a) has several valleys.
 */
export const SPRING_T: readonly number[] = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5];
export const SPRING_Y: readonly number[] = [0, 1.9, 1.6, 0.4, -1.6, -1.7, -0.7, 1.4];

export interface Params {
  a: number;
  w: number;
}

export function residuals({ a, w }: Params, ys: readonly number[] = SPRING_Y): number[] {
  return SPRING_T.map((t, index) => a * Math.sin(w * t) - ys[index]);
}

export function sse(p: Params, ys: readonly number[] = SPRING_Y): number {
  return residuals(p, ys).reduce((total, r) => total + r * r, 0);
}

/** For a fixed ω the amplitude is a one-column linear least-squares problem. */
export function bestAmplitude(w: number, ys: readonly number[] = SPRING_Y): number {
  let ss = 0;
  let sy = 0;
  SPRING_T.forEach((t, index) => {
    const s = Math.sin(w * t);
    ss += s * s;
    sy += s * ys[index];
  });
  return ss > 1e-12 ? sy / ss : 0;
}

/** Smallest sum of squares reachable at this ω once the amplitude is chosen optimally. */
export function profileSse(w: number): number {
  return sse({ a: bestAmplitude(w), w });
}

export interface Valley {
  w: number;
  sse: number;
}

/** Local minima of the ω-profile over [lo, hi], found on a fine grid. */
export function profileValleys(lo = 0.2, hi = 5.8, samples = 5600): Valley[] {
  const values = Array.from({ length: samples + 1 }, (_, i) => profileSse(lo + ((hi - lo) * i) / samples));
  const valleys: Valley[] = [];
  for (let i = 1; i < samples; i += 1) {
    if (values[i] < values[i - 1] && values[i] <= values[i + 1]) valleys.push({ w: lo + ((hi - lo) * i) / samples, sse: values[i] });
  }
  return valleys;
}

/** Columns of the Jacobian: ∂r/∂a = sin(ωt), ∂r/∂ω = a t cos(ωt). */
export function jacobian({ a, w }: Params): Array<readonly [number, number]> {
  return SPRING_T.map((t) => [Math.sin(w * t), a * t * Math.cos(w * t)] as const);
}

interface Normal {
  /** JᵀJ entries for the (a, ω) ordering. */
  aa: number;
  aw: number;
  ww: number;
  /** Jᵀr. */
  ga: number;
  gw: number;
}

function normal(p: Params): Normal {
  const r = residuals(p);
  return jacobian(p).reduce<Normal>(
    (acc, [ja, jw], index) => ({
      aa: acc.aa + ja * ja,
      aw: acc.aw + ja * jw,
      ww: acc.ww + jw * jw,
      ga: acc.ga + ja * r[index],
      gw: acc.gw + jw * r[index],
    }),
    { aa: 0, aw: 0, ww: 0, ga: 0, gw: 0 },
  );
}

function solve2(n: Normal, dampA: number, dampW: number): Params | undefined {
  const m11 = n.aa + dampA;
  const m22 = n.ww + dampW;
  const det = m11 * m22 - n.aw * n.aw;
  if (Math.abs(det) < 1e-14) return undefined;
  return { a: (-n.ga * m22 + n.gw * n.aw) / det, w: (-n.gw * m11 + n.ga * n.aw) / det };
}

/**
 * The local bowl a Gauss–Newton step minimizes: the sum of squares of the linearized
 * residuals r + J d, as a function of a nearby point (ω, a). Its bottom is the GN step.
 */
export function linearizedSse(at: Params, p: Params): number {
  const r = residuals(at);
  const da = p.a - at.a;
  const dw = p.w - at.w;
  return jacobian(at).reduce((total, [ja, jw], index) => total + (r[index] + ja * da + jw * dw) ** 2, 0);
}

export type Method = "gn" | "lm";

export interface Iterate extends Params {
  sse: number;
  /** Sum of squares the local bowl predicted for this point; undefined for the start. */
  predicted?: number;
  /** Levenberg–Marquardt damping λ of the accepted trial that reached this point. */
  lambda?: number;
}

export type Outcome = "global" | "local" | "diverged" | "stalled" | "budget";

export interface Descent {
  path: Iterate[];
  outcome: Outcome;
}

/**
 * Observations are 0.5 s apart, so ω and ω + 4π give the same eight predictions:
 * 4π · (k / 2) = 2πk for every observation time.
 */
export const ALIAS_SHIFT = 4 * Math.PI;

/** Best fit found by both methods from good starts (see the article's small example). */
export const GLOBAL_MINIMUM: Iterate = { a: 1.98586, w: 2.00189, sse: 0.19012 };
const GLOBAL_TOLERANCE = 1e-3;

/** Where the reader can still see the iterate; a GN step that leaves this box has flown off. */
export const OFF_MAP = { w: 12, a: 6 };

function outcomeOf(last: Iterate, stop: "settled" | "stalled" | "budget"): Outcome {
  if (!Number.isFinite(last.sse) || Math.abs(last.w) > OFF_MAP.w || Math.abs(last.a) > OFF_MAP.a) return "diverged";
  if (stop !== "settled") return stop;
  return Math.abs(last.sse - GLOBAL_MINIMUM.sse) < GLOBAL_TOLERANCE ? "global" : "local";
}

/** Stop once the sum of squares no longer changes at the three decimals the figure shows. */
function settled(path: readonly Iterate[]): boolean {
  const [before, after] = path.slice(-2);
  return Math.abs(before.sse - after.sse) < 5e-4;
}

/** Plain Gauss–Newton: take every full step, however far the linear model reaches. */
export function gaussNewton(start: Params, maxSteps = 8): Descent {
  const path: Iterate[] = [{ ...start, sse: sse(start) }];
  let p = start;
  let stop: "settled" | "stalled" | "budget" = "budget";
  for (let k = 0; k < maxSteps; k += 1) {
    const step = solve2(normal(p), 0, 0);
    if (!step) { stop = "stalled"; break; }
    const next = { a: p.a + step.a, w: p.w + step.w };
    path.push({ ...next, sse: sse(next), predicted: linearizedSse(p, next) });
    p = next;
    if (Math.abs(p.w) > OFF_MAP.w || Math.abs(p.a) > OFF_MAP.a) break;
    if (settled(path)) { stop = "settled"; break; }
  }
  return { path, outcome: outcomeOf(path[path.length - 1], stop) };
}

/**
 * Levenberg–Marquardt with Marquardt's diagonal scaling: shrink the step (raise λ) until the
 * sum of squares decreases, then trust the model a little more (lower λ).
 */
export function levenbergMarquardt(start: Params, maxSteps = 30, initialLambda = 1): Descent {
  const path: Iterate[] = [{ ...start, sse: sse(start) }];
  let p = start;
  let lambda = initialLambda;
  let stop: "settled" | "stalled" | "budget" = "budget";
  for (let k = 0; k < maxSteps; k += 1) {
    const n = normal(p);
    const current = sse(p);
    let accepted: Params | undefined;
    let step: Params | undefined;
    let used = lambda;
    while (lambda <= 1e8) {
      step = solve2(n, lambda * (n.aa + 1e-12), lambda * (n.ww + 1e-12));
      if (!step) break;
      const trial = { a: p.a + step.a, w: p.w + step.w };
      if (sse(trial) < current) {
        accepted = trial;
        used = lambda;
        lambda = Math.max(lambda / 3, 1e-7);
        break;
      }
      lambda *= 2;
    }
    if (!accepted || !step) { stop = "stalled"; break; }
    path.push({ ...accepted, sse: sse(accepted), predicted: linearizedSse(p, accepted), lambda: used });
    p = accepted;
    if (settled(path)) { stop = "settled"; break; }
  }
  return { path, outcome: outcomeOf(path[path.length - 1], stop) };
}

export function descend(method: Method, start: Params): Descent {
  return method === "gn" ? gaussNewton(start) : levenbergMarquardt(start);
}

/**
 * One step of a descent, read at a point along it: the bowl built at the step's start
 * predicts one sum of squares, and the real landscape gives another.
 */
export interface StepReading {
  /** Index of the step: it goes from path[index] to path[index + 1]. */
  index: number;
  /** How far along the step, 0 to 1. */
  fraction: number;
  from: Iterate;
  to: Iterate;
  head: Params;
  /** Sum of squares at the step's start: the level both predictions are measured against. */
  startSse: number;
  /** The bowl's value at the head. It falls to `to.predicted` when the step is complete. */
  predicted: number;
  /** The real sum of squares at the head. It reaches `to.sse` when the step is complete. */
  actual: number;
  /** Fall the bowl promised for the whole step (startSse - to.predicted). */
  predictedDecrease: number;
  /** Fall the step actually gave (startSse - to.sse). Negative when the sum of squares rose. */
  actualDecrease: number;
  /** True when the whole step ended higher than it started. */
  overshoot: boolean;
}

/** The step in progress (or the last finished one) at a fractional position along the path. */
export function stepReading(path: readonly Iterate[], position: number): StepReading | undefined {
  if (path.length < 2) return undefined;
  // A whole number means "that many steps are done", so it reads the step just finished.
  const index = Math.min(Math.max(Math.ceil(position - 1e-9) - 1, 0), path.length - 2);
  const fraction = Math.min(Math.max(position - index, 0), 1);
  const from = path[index];
  const to = path[index + 1];
  const head = { a: from.a + (to.a - from.a) * fraction, w: from.w + (to.w - from.w) * fraction };
  const predictedEnd = to.predicted ?? linearizedSse(from, to);
  return {
    index,
    fraction,
    from,
    to,
    head,
    startSse: from.sse,
    predicted: linearizedSse(from, head),
    actual: sse(head),
    predictedDecrease: from.sse - predictedEnd,
    actualDecrease: from.sse - to.sse,
    overshoot: to.sse > from.sse,
  };
}

/** Bottom of the linearized bowl at p: the full Gauss–Newton point. */
export function bowlBottom(p: Params): Params | undefined {
  const step = solve2(normal(p), 0, 0);
  return step ? { a: p.a + step.a, w: p.w + step.w } : undefined;
}
