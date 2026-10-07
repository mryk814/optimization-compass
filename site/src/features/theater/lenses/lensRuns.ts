/**
 * Three search instruments on one fixed teaching landscape and one evaluation budget.
 *
 * The objective is the Case `hyperparameter-search` teaching function on X = [-3, 3]
 * (the same function as OBJECTIVE_EDUCATIONAL_WAVY_1D). Every run spends exactly
 * `LENS_BUDGET` evaluations and includes x = 0. Each snapshot records only what that method
 * holds after t evaluations — the "algorithm's view" — so the page can hide the true curve.
 *
 * This is an in-browser teaching computation, not a canonical Trace. It shows how what a
 * method observes shapes where it goes next; it does not rank the methods.
 */
import { mulberry32 } from "../../explorable/math/cmaes";
import { expectedImprovement, posterior } from "../../explorable/math/bayesOpt";

export const LENS_DOMAIN: readonly [number, number] = [-3, 3];
export const LENS_BUDGET = 10;
export const LENS_START = 0;

export function lensObjective(x: number): number {
  return 0.16 * (x - 1.7) ** 2 + 0.45 * Math.sin(2.2 * x) + 0.12 * Math.sin(5.3 * x);
}

export const LENS_GRID: readonly number[] = Array.from(
  { length: 241 },
  (_, index) => LENS_DOMAIN[0] + ((LENS_DOMAIN[1] - LENS_DOMAIN[0]) * index) / 240,
);

const clampToDomain = (x: number) => Math.min(LENS_DOMAIN[1], Math.max(LENS_DOMAIN[0], x));

export type LensId = "gradient" | "population" | "surrogate";

export interface Evaluation {
  /** 1-based evaluation count at which this point was measured. */
  index: number;
  x: number;
  y: number;
  /** Why the method spent this evaluation: to move, to probe a slope, to sample, to fill a design. */
  purpose: "move" | "probe" | "sample" | "design" | "acquire";
}

/** What the method holds after `evaluations.length` evaluations. */
export type LensView =
  | { kind: "gradient"; at: number; atValue: number; slope: number | null; next: number | null }
  | { kind: "population"; mean: number; sigma: number; generation: number; current: Evaluation[]; next: number | null }
  | { kind: "surrogate"; mean: number[]; sd: number[]; ei: number[]; next: number | null };

export interface LensSnapshot {
  evaluations: Evaluation[];
  view: LensView;
  best: Evaluation | null;
}

export interface FailureEvent {
  /** Evaluation count at which the signal becomes visible. */
  at: number;
  kind: "budget_spent_on_probes" | "stuck_in_basin" | "population_collapsed" | "model_uncertain";
  text: string;
}

export interface LensRun {
  id: LensId;
  snapshots: LensSnapshot[];
  events: FailureEvent[];
}

function bestOf(evaluations: readonly Evaluation[]): Evaluation | null {
  return evaluations.reduce<Evaluation | null>((best, item) => (best === null || item.y < best.y ? item : best), null);
}

/** Forward-difference gradient descent: each slope costs one extra evaluation. */
export const GRADIENT_SETTINGS = { step: 0.35, h: 0.05 } as const;

export function runGradientLens(): LensRun {
  const evaluations: Evaluation[] = [];
  const snapshots: LensSnapshot[] = [];
  const push = (view: LensView) => snapshots.push({ evaluations: [...evaluations], view, best: bestOf(evaluations) });
  let x = LENS_START;
  push({ kind: "gradient", at: x, atValue: Number.NaN, slope: null, next: x });
  while (evaluations.length < LENS_BUDGET) {
    const fx = lensObjective(x);
    evaluations.push({ index: evaluations.length + 1, x, y: fx, purpose: "move" });
    push({ kind: "gradient", at: x, atValue: fx, slope: null, next: x + GRADIENT_SETTINGS.h });
    if (evaluations.length >= LENS_BUDGET) break;
    const probe = x + GRADIENT_SETTINGS.h;
    const fp = lensObjective(probe);
    evaluations.push({ index: evaluations.length + 1, x: probe, y: fp, purpose: "probe" });
    const slope = (fp - fx) / GRADIENT_SETTINGS.h;
    const next = clampToDomain(x - GRADIENT_SETTINGS.step * slope);
    push({ kind: "gradient", at: x, atValue: fx, slope, next: evaluations.length < LENS_BUDGET ? next : null });
    x = next;
  }
  const probes = evaluations.filter((item) => item.purpose === "probe").length;
  const events: FailureEvent[] = [{
    at: 2,
    kind: "budget_spent_on_probes",
    text: `傾きを測るたびに評価を1回使う。予算${LENS_BUDGET}回のうち${probes}回が差分用で、移動に使えたのは${LENS_BUDGET - probes}回。`,
  }];
  const final = bestOf(evaluations);
  const globalX = gridArgmin();
  if (final && basinOf(final.x) !== basinOf(globalX)) {
    events.push({
      at: LENS_BUDGET,
      kind: "stuck_in_basin",
      text: "出発点の近くの谷で傾きが小さくなった。勾配だけでは、測っていない別の谷があるかを知る手段がない。",
    });
  }
  return { id: "gradient", snapshots, events };
}

/** A (1, 3) evolution strategy: one mean, three samples per generation, σ grows on success. */
export const POPULATION_SETTINGS = { lambda: 3, sigma0: 1.2, grow: 1.25, shrink: 0.6, seed: 2604 } as const;

export function runPopulationLens(): LensRun {
  const random = mulberry32(POPULATION_SETTINGS.seed);
  const gauss = () => {
    const u1 = Math.max(random(), 1e-12);
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * random());
  };
  const evaluations: Evaluation[] = [];
  const snapshots: LensSnapshot[] = [];
  let mean = LENS_START;
  let sigma: number = POPULATION_SETTINGS.sigma0;
  let generation = 0;
  let current: Evaluation[] = [];
  const push = () => snapshots.push({
    evaluations: [...evaluations],
    view: { kind: "population", mean, sigma, generation, current: [...current], next: evaluations.length < LENS_BUDGET ? mean : null },
    best: bestOf(evaluations),
  });
  push();
  let parentValue = lensObjective(mean);
  evaluations.push({ index: 1, x: mean, y: parentValue, purpose: "move" });
  current = [evaluations[0]];
  push();
  let collapsedAt: number | undefined;
  while (evaluations.length < LENS_BUDGET) {
    generation += 1;
    current = [];
    for (let k = 0; k < POPULATION_SETTINGS.lambda && evaluations.length < LENS_BUDGET; k += 1) {
      const x = clampToDomain(mean + sigma * gauss());
      const item: Evaluation = { index: evaluations.length + 1, x, y: lensObjective(x), purpose: "sample" };
      evaluations.push(item);
      current.push(item);
      push();
    }
    const winner = bestOf(current);
    if (!winner) break;
    sigma *= winner.y < parentValue ? POPULATION_SETTINGS.grow : POPULATION_SETTINGS.shrink;
    mean = winner.x;
    parentValue = winner.y;
    // The selection step changes the method's state without an evaluation: show it on the last frame.
    snapshots[snapshots.length - 1] = {
      ...snapshots[snapshots.length - 1],
      view: { kind: "population", mean, sigma, generation, current: [...current], next: evaluations.length < LENS_BUDGET ? mean : null },
    };
    if (collapsedAt === undefined && sigma < 0.35) collapsedAt = evaluations.length;
  }
  const events: FailureEvent[] = [];
  if (collapsedAt !== undefined) {
    events.push({
      at: collapsedAt,
      kind: "population_collapsed",
      text: "改善しない世代が続き、分布の幅σが縮んだ。集団が1点に集まると、遠くの谷を引く確率も下がる。",
    });
  }
  return { id: "population", snapshots, events };
}

/** Noiseless: a grid point within `minSpacing` of an observation is not proposed again. */
export const SURROGATE_SETTINGS = { design: [-2.6, 0, 2.6], lengthScale: 0.8, minSpacing: 0.05 } as const;

export function runSurrogateLens(): LensRun {
  const evaluations: Evaluation[] = [];
  const snapshots: LensSnapshot[] = [];
  const emptyView = (next: number | null): LensView => ({ kind: "surrogate", mean: [], sd: [], ei: [], next });
  snapshots.push({ evaluations: [], view: emptyView(SURROGATE_SETTINGS.design[0]), best: null });
  for (const x of SURROGATE_SETTINGS.design) {
    evaluations.push({ index: evaluations.length + 1, x, y: lensObjective(x), purpose: "design" });
    const next = SURROGATE_SETTINGS.design[evaluations.length];
    if (next !== undefined) snapshots.push({ evaluations: [...evaluations], view: emptyView(next), best: bestOf(evaluations) });
  }
  let maxSdAtEnd = 0;
  while (true) {
    const xs = evaluations.map((item) => item.x);
    const ys = evaluations.map((item) => item.y);
    const post = posterior(xs, ys, SURROGATE_SETTINGS.lengthScale, LENS_GRID);
    const best = Math.min(...ys);
    const ei = post.mean.map((mean, index) => expectedImprovement(mean, post.sd[index], best));
    const allowed = (x: number) => xs.every((seen) => Math.abs(seen - x) > SURROGATE_SETTINGS.minSpacing);
    let nextIndex = -1;
    for (let i = 0; i < ei.length; i += 1) if (allowed(LENS_GRID[i]) && (nextIndex < 0 || ei[i] > ei[nextIndex])) nextIndex = i;
    const done = evaluations.length >= LENS_BUDGET;
    snapshots.push({
      evaluations: [...evaluations],
      view: { kind: "surrogate", mean: post.mean, sd: post.sd, ei, next: done ? null : LENS_GRID[nextIndex] },
      best: bestOf(evaluations),
    });
    if (done) {
      maxSdAtEnd = Math.max(...post.sd);
      break;
    }
    const x = LENS_GRID[nextIndex];
    evaluations.push({ index: evaluations.length + 1, x, y: lensObjective(x), purpose: "acquire" });
  }
  const events: FailureEvent[] = [{
    at: LENS_BUDGET,
    kind: "model_uncertain",
    text: `予算終了時も、代理モデルの不確実性（標準偏差）は最大${maxSdAtEnd.toFixed(2)}残る。これはカーネルの仮定の下での幅で、真の誤差の保証ではない。`,
  }];
  return { id: "surrogate", snapshots, events };
}

export function gridArgmin(): number {
  let best = LENS_GRID[0];
  for (const x of LENS_GRID) if (lensObjective(x) < lensObjective(best)) best = x;
  return best;
}

/** Index of the local-minimum basin containing x, found by walking downhill on the grid. */
export function basinOf(x: number): number {
  let index = LENS_GRID.reduce((nearest, value, i) => (Math.abs(value - x) < Math.abs(LENS_GRID[nearest] - x) ? i : nearest), 0);
  for (;;) {
    const here = lensObjective(LENS_GRID[index]);
    const left = index > 0 ? lensObjective(LENS_GRID[index - 1]) : Infinity;
    const right = index < LENS_GRID.length - 1 ? lensObjective(LENS_GRID[index + 1]) : Infinity;
    if (left < here && left <= right) index -= 1;
    else if (right < here) index += 1;
    else return index;
  }
}

export function runAllLenses(): Record<LensId, LensRun> {
  return { gradient: runGradientLens(), population: runPopulationLens(), surrogate: runSurrogateLens() };
}

/** Snapshot after `t` evaluations (the last snapshot with that many evaluations). */
export function snapshotAt(run: LensRun, t: number): LensSnapshot {
  let found = run.snapshots[0];
  for (const snapshot of run.snapshots) if (snapshot.evaluations.length <= t) found = snapshot;
  return found;
}
