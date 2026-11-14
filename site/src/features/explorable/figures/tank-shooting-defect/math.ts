/**
 * The tank of content/concepts/dynamics-defect.md, cut into six shooting segments.
 *
 * Levels are in m, flows in L/s: dh/dt = (q − C√h) / 1000 with C = 1000·a·√(2g), area 1 m².
 * The solver's iterates come from the Python fixture (scripts/lesson_figures/dynamics_defect.py);
 * everything shown about a plan (where the model carries each knot, the defects, the cost, the
 * finely solved level) is computed here from that plan, so a dragged plan is measured the same way.
 */
import fixture from "./fixture.json";

const { g, a, area, dt, n, h0, h_target: hTarget, w, tol } = fixture.constants;

export const SEGMENTS = n;
export const H0 = h0;
export const H_TARGET = hTarget;
export const TOLERANCE = tol;
export const SEGMENT_SECONDS = dt;
/** Outflow in L/s at a level of 1 m. */
export const OUTFLOW = 1000 * a * Math.sqrt(2 * g);
/** Metres of level that 1 L/s held for one segment adds. */
export const KAPPA = dt / 1000 / area;
/** Litres per metre of level. */
export const LITRES_PER_METRE = 1000 * area;

export const SUBSTEP_CHOICES = ["1", "2", "5"] as const;
export type Substeps = (typeof SUBSTEP_CHOICES)[number];
export const LAST_ITERATION = fixture.runs["1"].length - 1;

/** Knot levels s_0..s_6 (s_0 is the fixed start) and the flow of each segment q_0..q_5. */
export interface Plan {
  s: readonly number[];
  q: readonly number[];
}

/** The levels the discretised model passes through in one segment: start, each Euler substep. */
export function segmentLevels(s: number, q: number, substeps: number): number[] {
  const k = KAPPA / substeps;
  const levels = [s];
  let h = s;
  for (let i = 0; i < substeps; i += 1) {
    h += k * (q - OUTFLOW * Math.sqrt(Math.max(h, 0)));
    levels.push(h);
  }
  return levels;
}

/** f_d: where the discretised model carries a knot by the end of its segment. */
export function segmentEnd(s: number, q: number, substeps: number): number {
  return segmentLevels(s, q, substeps)[substeps];
}

/** d_k for the knots 1..6: the knot minus where the model carries the knot before it. */
export function defects(plan: Plan, substeps: number): number[] {
  return plan.q.map((flow, k) => plan.s[k + 1] - segmentEnd(plan.s[k], flow, substeps));
}

export interface Cost {
  total: number;
  /** Squared distance from the target, 10 cm counted as 1. */
  track: number;
  /** Squared flow, 1 L/s counted as 1. */
  pump: number;
}

export function cost(plan: Plan): Cost {
  const track = plan.s.slice(1).reduce((sum, level) => sum + ((level - hTarget) / w) ** 2, 0);
  const pump = plan.q.reduce((sum, flow) => sum + flow * flow, 0);
  return { total: track + pump, track, pump };
}

export interface DefectNorms {
  max: number;
  /** Knot (1-based) with the largest defect. */
  argmax: number;
  l2: number;
  /** Signed sum, in m: with an area of 1 m² the water that appeared at the knots, in m³. */
  total: number;
}

export function defectNorms(d: readonly number[]): DefectNorms {
  const sizes = d.map(Math.abs);
  const max = Math.max(...sizes);
  return {
    max,
    argmax: sizes.indexOf(max) + 1,
    l2: Math.sqrt(d.reduce((sum, value) => sum + value * value, 0)),
    total: d.reduce((sum, value) => sum + value, 0),
  };
}

export function pumpedLitres(plan: Plan): number {
  return plan.q.reduce((sum, flow) => sum + flow, 0) * dt;
}

/**
 * The solver's plan at an iteration of the run solved with `substeps` Euler steps per segment.
 * A fractional iteration blends its two neighbours. From iteration 0 to 1 the blend is linear.
 * After that the defect falls by orders of magnitude per iteration, so the blend is chosen to
 * make the defect fall at a steady rate on a log axis instead of all at the last instant.
 */
export function planAt(substeps: Substeps, iteration: number): Plan {
  const run = fixture.runs[substeps];
  const position = Math.min(Math.max(iteration, 0), run.length - 1);
  const lower = Math.min(Math.floor(position), run.length - 2);
  const t = position - lower;
  const from = run[lower];
  const to = run[lower + 1];
  if (t === 0) return from;
  if (t === 1) return to;
  let weight = t;
  if (lower >= 1) {
    const ratio = defectNorms(defects(to, Number(substeps))).max / defectNorms(defects(from, Number(substeps))).max;
    if (ratio > 0 && ratio < 1) weight = (1 - ratio ** t) / (1 - ratio);
  }
  return blendPlans(from, to, weight);
}

export function blendPlans(from: Plan, to: Plan, weight: number): Plan {
  const mix = (x: number, y: number) => x + (y - x) * weight;
  return { s: from.s.map((value, k) => mix(value, to.s[k])), q: from.q.map((value, k) => mix(value, to.q[k])) };
}

/** The plan with one segment (1-based) pumping 1 L/s less. The knots stay where they are. */
export function cutFlow(plan: Plan, segment: number): Plan {
  if (segment < 1 || segment > plan.q.length) return plan;
  return { s: plan.s, q: plan.q.map((flow, k) => (k === segment - 1 ? flow - 1 : flow)) };
}

const FINE_STEP_S = 1;

/**
 * The continuous model under the plan's flows, by RK4 with 1 s steps: the level at every second
 * from 0 to 30 min (1801 values). It starts from s_0 and never looks at the other knots.
 */
export function fineLevels(q: readonly number[]): number[] {
  const rate = (h: number, flow: number) => (flow - OUTFLOW * Math.sqrt(Math.max(h, 0))) / 1000 / area;
  const levels = [h0];
  let h = h0;
  for (const flow of q) {
    for (let i = 0; i < dt / FINE_STEP_S; i += 1) {
      const k1 = rate(h, flow);
      const k2 = rate(h + (FINE_STEP_S / 2) * k1, flow);
      const k3 = rate(h + (FINE_STEP_S / 2) * k2, flow);
      const k4 = rate(h + FINE_STEP_S * k3, flow);
      h += (FINE_STEP_S / 6) * (k1 + 2 * k2 + 2 * k3 + k4);
      levels.push(h);
    }
  }
  return levels;
}

/** The finely solved level at the knots (0, 5, …, 30 min). */
export function fineKnots(q: readonly number[]): number[] {
  const levels = fineLevels(q);
  const perSegment = dt / FINE_STEP_S;
  return Array.from({ length: q.length + 1 }, (_, k) => levels[k * perSegment]);
}
