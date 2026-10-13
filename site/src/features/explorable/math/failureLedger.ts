/**
 * Evaluation ledger of the EC027 failed-simulation lesson (`src/optimization_compass/failed_simulation.py`).
 *
 * A simulation call ends as `ok` (a number comes back) or as `crash`, `timeout`, `nonphysical`
 * (no number). The ledger keeps that status next to the point. Two ways to read it:
 *  - `status`: failures stay statuses; only successes carry values.
 *  - `penalty`: every failure is replaced by one fixed number P and read as a value.
 *
 * Values of successful rows are computed from the lesson's objective
 * (u1−0.65)² + (u2−0.35)² + 0.08·mode, not copied from the trace file.
 */

export type EvalStatus = "ok" | "crash" | "timeout" | "nonphysical";
export type Policy = "status" | "penalty";

export interface LedgerRow {
  call: number;
  u1: number;
  u2: number;
  mode: 0 | 1;
  status: EvalStatus;
  /** Objective value for `ok`; `null` for every failure. */
  value: number | null;
}

/** The budget is counted in simulation calls. A failed call uses one, exactly like a successful one. */
export const BUDGET = 20;
export const BUDGET_UNIT = "評価回数";
export const DOMAIN: readonly [number, number] = [0, 1];
export const PROBE_RANGE: readonly [number, number] = [-0.1, 1.15];
export const PROBE_DEFAULT: readonly [number, number] = [0.2, 0.04];
/** Penalty choices a team might type in; P = 0 and P = 0.05 are smaller than some real values. */
export const PENALTY_CHOICES: readonly number[] = [0, 0.05, 0.1, 1, 10, 100, 1000, 1_000_000];
export const PENALTY_DEFAULT_INDEX = 4;
export const SPLIT_U1 = 0.5;

export const STATUS_LABEL: Readonly<Record<EvalStatus, string>> = {
  ok: "成功",
  crash: "クラッシュ",
  timeout: "時間切れ",
  nonphysical: "物理的にありえない出力",
};

export function objectiveValue(u1: number, u2: number, mode: number): number {
  return (u1 - 0.65) ** 2 + (u2 - 0.35) ** 2 + 0.08 * mode;
}

type RawRow = readonly [number, number, 0 | 1, EvalStatus];

/** Calls 1–6 are the lesson's feasible ledger; call 7 is the nonphysical candidate of its failure ledger. */
const RAW: readonly RawRow[] = [
  [0.65, 0.35, 0, "ok"],
  [0.15, 0.05, 1, "crash"],
  [0.45, 0.10, 0, "ok"],
  [0.82, 0.62, 1, "timeout"],
  [0.60, 0.30, 0, "ok"],
  [0.70, 0.42, 1, "ok"],
  [0.10, 0.08, 0, "nonphysical"],
];

export const LEDGER: readonly LedgerRow[] = RAW.map(([u1, u2, mode, status], index) => ({
  call: index + 1,
  u1,
  u2,
  mode,
  status,
  value: status === "ok" ? objectiveValue(u1, u2, mode) : null,
}));

export const LEDGER_LENGTH = LEDGER.length;

export interface Tally {
  spent: number;
  ok: number;
  crash: number;
  timeout: number;
  nonphysical: number;
  failed: number;
  remaining: number;
}

/** What the first `n` calls cost. Failures are counted: the budget does not know which calls succeeded. */
export function tally(n: number): Tally {
  const rows = LEDGER.slice(0, n);
  const count = (status: EvalStatus) => rows.filter((row) => row.status === status).length;
  const ok = count("ok");
  return {
    spent: rows.length,
    ok,
    crash: count("crash"),
    timeout: count("timeout"),
    nonphysical: count("nonphysical"),
    failed: rows.length - ok,
    remaining: BUDGET - rows.length,
  };
}

export interface HalfSummary {
  side: "left" | "right";
  /** Evaluations whose point lies in this half. */
  evaluations: number;
  /** How many of them contribute a number to the mean. */
  used: number;
  mean: number | null;
}

/** Mean of the recorded numbers in the halves u1 < 0.5 and u1 ≥ 0.5 — the simplest surrogate summary. */
export function halfSummaries(n: number, policy: Policy, penalty: number): readonly [HalfSummary, HalfSummary] {
  const rows = LEDGER.slice(0, n);
  const summarize = (side: "left" | "right"): HalfSummary => {
    const inHalf = rows.filter((row) => (side === "left" ? row.u1 < SPLIT_U1 : row.u1 >= SPLIT_U1));
    const values = inHalf
      .map((row) => (row.value ?? (policy === "penalty" ? penalty : null)))
      .filter((value): value is number => value !== null);
    const mean = values.length === 0 ? null : values.reduce((sum, value) => sum + value, 0) / values.length;
    return { side, evaluations: inHalf.length, used: values.length, mean };
  };
  return [summarize("left"), summarize("right")];
}

export interface RankedCall {
  call: number;
  status: EvalStatus;
  value: number;
}

export interface Ranking {
  bestValue: number;
  /** Calls that share the best value. More than one means a failure ties a real result. */
  bestCalls: readonly number[];
  topThree: readonly RankedCall[];
  recordedMin: number;
  recordedMax: number;
  /** max − min of the successful values only; null with fewer than two successes. */
  successSpread: number | null;
  /** successSpread divided by the recorded range; null when it is undefined. */
  spreadShare: number | null;
}

export function ranking(n: number, policy: Policy, penalty: number): Ranking {
  const recorded: RankedCall[] = LEDGER.slice(0, n).flatMap((row) => {
    if (row.value !== null) return [{ call: row.call, status: row.status, value: row.value }];
    return policy === "penalty" ? [{ call: row.call, status: row.status, value: penalty }] : [];
  });
  const sorted = [...recorded].sort((a, b) => a.value - b.value || a.call - b.call);
  const values = recorded.map((item) => item.value);
  const recordedMin = Math.min(...values);
  const recordedMax = Math.max(...values);
  const successes = LEDGER.slice(0, n).flatMap((row) => (row.value === null ? [] : [row.value]));
  const successSpread = successes.length >= 2 ? Math.max(...successes) - Math.min(...successes) : null;
  const range = recordedMax - recordedMin;
  return {
    bestValue: sorted[0].value,
    bestCalls: sorted.filter((item) => Math.abs(item.value - sorted[0].value) < 1e-12).map((item) => item.call),
    topThree: sorted.slice(0, 3),
    recordedMin,
    recordedMax,
    successSpread,
    spreadShare: successSpread !== null && range > 0 ? successSpread / range : null,
  };
}

export type ProbeVerdict =
  | { kind: "known_violation"; reasons: readonly string[] }
  | {
      kind: "unknown";
      nearest: { call: number; status: EvalStatus; distance: number; value: number | null };
      nearestSuccess: { call: number; distance: number; value: number };
      /** What a nearest-neighbour guess says about the probe under the chosen policy. */
      guess: { kind: "value"; value: number; replaced: boolean } | { kind: "none" };
    };

/**
 * A probe outside the declared bounds is a known violation: it can be decided before running anything.
 * Any other probe is unknown — the ledger says nothing about whether a run there would succeed.
 */
export function probeVerdict(u1: number, u2: number, n: number, policy: Policy, penalty: number): ProbeVerdict {
  const reasons: string[] = [];
  if (u1 < DOMAIN[0] || u1 > DOMAIN[1]) reasons.push("u₁が範囲 [0, 1] の外");
  if (u2 < DOMAIN[0] || u2 > DOMAIN[1]) reasons.push("u₂が範囲 [0, 1] の外");
  if (reasons.length > 0) return { kind: "known_violation", reasons };

  const rows = LEDGER.slice(0, n);
  const distance = (row: LedgerRow) => Math.hypot(row.u1 - u1, row.u2 - u2);
  let nearestRow = rows[0];
  for (const row of rows) if (distance(row) < distance(nearestRow) - 1e-12) nearestRow = row;
  let successRow = rows.find((row) => row.value !== null) ?? rows[0];
  for (const row of rows) if (row.value !== null && distance(row) < distance(successRow) - 1e-12) successRow = row;

  return {
    kind: "unknown",
    nearest: {
      call: nearestRow.call,
      status: nearestRow.status,
      distance: distance(nearestRow),
      value: nearestRow.value,
    },
    nearestSuccess: { call: successRow.call, distance: distance(successRow), value: successRow.value ?? 0 },
    guess:
      nearestRow.value !== null
        ? { kind: "value", value: nearestRow.value, replaced: false }
        : policy === "penalty"
          ? { kind: "value", value: penalty, replaced: true }
          : { kind: "none" },
  };
}
