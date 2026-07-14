export const TRACE_CONTRACT_VERSION = "1.0.0" as const;
export const MAX_TRACE_FRAMES = 1_000;
export const MAX_TRACE_BYTES = 2 * 1024 * 1024;

export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };
export type SupportStatus = "supported" | "unsupported" | "unknown" | "not_applicable";
export type DecisionState = "accepted" | "rejected" | "not_applicable";
export type PlaybackDirection = "forward" | "reverse";
export type PlaybackSpeed = 0.25 | 0.5 | 1 | 2 | 4;

export interface TracePoint {
  point_id: string;
  role: string;
  coordinates: number[];
  value: number | null;
  label_ja: string;
  label_en: string;
}

export interface TraceVector {
  vector_id: string;
  role: string;
  origin: number[];
  components: number[];
  label_ja: string;
  label_en: string;
}

export interface TraceMetric {
  metric_id: string;
  label_ja: string;
  label_en: string;
  value: number;
  unit: string | null;
}

export interface TraceFrame {
  frame_index: number;
  iteration: number;
  oracle_evaluations: number;
  elapsed_steps: number;
  elapsed_time_ms: number;
  event_type: string;
  decision: DecisionState;
  explanation_key: string;
  event_label_ja: string | null;
  event_label_en: string | null;
  keyframe: boolean;
  points: TracePoint[];
  vectors: TraceVector[];
  metrics: TraceMetric[];
  payload: JsonValue;
}

export type TerminalStatus =
  | "completed"
  | "converged"
  | "budget_exhausted"
  | "diverged"
  | "stopped"
  | "failed";

export interface AlgorithmTrace {
  contract_version: typeof TRACE_CONTRACT_VERSION;
  dataset_version: string;
  data_version: string;
  trace_id: string;
  method_id: string;
  profile_id: string;
  objective_id: string;
  scenario_id: string;
  generator_id: string;
  generator_version: string;
  implementation_mapping_status: SupportStatus;
  implementation_id: string | null;
  objective: Record<string, JsonValue>;
  preset: Record<string, JsonValue>;
  parameters: Record<string, JsonValue>;
  initial_state: Record<string, JsonValue>;
  seed: Record<string, JsonValue>;
  evaluation_budget: number;
  stopping: Record<string, JsonValue>;
  environment: Record<string, JsonValue>;
  fairness_statement: string;
  frames: TraceFrame[];
  terminal_status: TerminalStatus;
  terminal_summary_ja: string;
  terminal_summary_en: string;
  source_ids: string[];
}

export interface TraceBundle {
  contract_version: typeof TRACE_CONTRACT_VERSION;
  bundle_id: string;
  comparison_id: string;
  dataset_version: string;
  data_version: string;
  objective_id: string;
  objective: Record<string, JsonValue>;
  initial_state: Record<string, JsonValue>;
  seed: Record<string, JsonValue>;
  evaluation_budget: number;
  stopping: Record<string, JsonValue>;
  environment: Record<string, JsonValue>;
  fairness_statement: string;
  member_traces: AlgorithmTrace[];
  synchronization: "oracle_evaluations";
}

export interface TraceIndexEntry {
  trace_id: string;
  path: string;
  method_id: string;
  profile_id: string;
  objective_id: string;
  scenario_id: string;
  title_ja: string;
  title_en: string;
}

export interface TraceIndex {
  contract_version: typeof TRACE_CONTRACT_VERSION;
  dataset_version: string;
  data_version: string;
  traces: TraceIndexEntry[];
}

const slugPattern = /^[a-z0-9]+(?:[._-][a-z0-9]+)*$/u;
const traceKeys = [
  "contract_version", "dataset_version", "data_version", "trace_id", "method_id",
  "profile_id", "objective_id", "scenario_id", "generator_id", "generator_version",
  "implementation_mapping_status", "implementation_id", "objective", "preset", "parameters",
  "initial_state", "seed", "evaluation_budget", "stopping", "environment",
  "fairness_statement", "frames", "terminal_status", "terminal_summary_ja",
  "terminal_summary_en", "source_ids",
] as const;
const frameKeys = [
  "frame_index", "iteration", "oracle_evaluations", "elapsed_steps", "elapsed_time_ms",
  "event_type", "decision", "explanation_key", "event_label_ja", "event_label_en", "keyframe",
  "points", "vectors", "metrics", "payload",
] as const;
const pointKeys = ["point_id", "role", "coordinates", "value", "label_ja", "label_en"] as const;
const vectorKeys = ["vector_id", "role", "origin", "components", "label_ja", "label_en"] as const;
const metricKeys = ["metric_id", "label_ja", "label_en", "value", "unit"] as const;
const bundleKeys = [
  "contract_version", "bundle_id", "comparison_id", "dataset_version", "data_version",
  "objective_id", "objective", "initial_state", "seed", "evaluation_budget", "stopping",
  "environment", "fairness_statement", "member_traces", "synchronization",
] as const;

export function parseAlgorithmTrace(input: unknown): AlgorithmTrace {
  const data = record(input, "AlgorithmTrace");
  exactKeys(data, traceKeys, "AlgorithmTrace");
  if (data.contract_version !== TRACE_CONTRACT_VERSION) {
    throw new Error(`Unsupported AlgorithmTrace version: ${String(data.contract_version)}.`);
  }
  const mappingStatus = enumValue(
    data.implementation_mapping_status,
    ["supported", "unsupported", "unknown", "not_applicable"] as const,
    "implementation_mapping_status",
  );
  const implementationId = nullableString(data.implementation_id, "implementation_id");
  if (mappingStatus === "supported" ? implementationId === null : implementationId !== null) {
    throw new Error("Supported implementation mapping requires an ID; every other state forbids it.");
  }
  const frames = array(data.frames, "frames").map(parseFrame);
  if (frames.length === 0 || frames.length > MAX_TRACE_FRAMES) {
    throw new Error(`AlgorithmTrace must contain 1–${MAX_TRACE_FRAMES.toLocaleString("en-US")} frames.`);
  }
  validateProgress(frames);
  const parsed: AlgorithmTrace = {
    contract_version: TRACE_CONTRACT_VERSION,
    dataset_version: string(data.dataset_version, "dataset_version"),
    data_version: string(data.data_version, "data_version"),
    trace_id: string(data.trace_id, "trace_id"),
    method_id: string(data.method_id, "method_id"),
    profile_id: string(data.profile_id, "profile_id"),
    objective_id: string(data.objective_id, "objective_id"),
    scenario_id: string(data.scenario_id, "scenario_id"),
    generator_id: string(data.generator_id, "generator_id"),
    generator_version: string(data.generator_version, "generator_version"),
    implementation_mapping_status: mappingStatus,
    implementation_id: implementationId,
    objective: jsonRecord(data.objective, "objective"),
    preset: jsonRecord(data.preset, "preset"),
    parameters: jsonRecord(data.parameters, "parameters"),
    initial_state: jsonRecord(data.initial_state, "initial_state"),
    seed: jsonRecord(data.seed, "seed"),
    evaluation_budget: positiveInteger(data.evaluation_budget, "evaluation_budget"),
    stopping: jsonRecord(data.stopping, "stopping"),
    environment: jsonRecord(data.environment, "environment"),
    fairness_statement: string(data.fairness_statement, "fairness_statement"),
    frames,
    terminal_status: enumValue(
      data.terminal_status,
      ["completed", "converged", "budget_exhausted", "diverged", "stopped", "failed"] as const,
      "terminal_status",
    ),
    terminal_summary_ja: string(data.terminal_summary_ja, "terminal_summary_ja"),
    terminal_summary_en: string(data.terminal_summary_en, "terminal_summary_en"),
    source_ids: uniqueStrings(data.source_ids, "source_ids"),
  };
  const byteLength = new TextEncoder().encode(canonicalJson(parsed)).byteLength;
  if (byteLength > MAX_TRACE_BYTES) {
    throw new Error(`AlgorithmTrace raw canonical JSON exceeds 2 MiB (${byteLength} bytes).`);
  }
  return parsed;
}

export function parseTraceIndex(input: unknown): TraceIndex {
  const data = record(input, "TraceIndex");
  exactKeys(data, ["contract_version", "dataset_version", "data_version", "traces"], "TraceIndex");
  if (data.contract_version !== TRACE_CONTRACT_VERSION) {
    throw new Error(`Unsupported TraceIndex version: ${String(data.contract_version)}.`);
  }
  const traces = array(data.traces, "traces").map((value, index): TraceIndexEntry => {
    const entry = record(value, `traces[${index}]`);
    exactKeys(
      entry,
      ["trace_id", "path", "method_id", "profile_id", "objective_id", "scenario_id", "title_ja", "title_en"],
      `traces[${index}]`,
    );
    return {
      trace_id: string(entry.trace_id, "trace_id"), path: safeRelativePath(entry.path),
      method_id: string(entry.method_id, "method_id"), profile_id: string(entry.profile_id, "profile_id"),
      objective_id: string(entry.objective_id, "objective_id"), scenario_id: string(entry.scenario_id, "scenario_id"),
      title_ja: string(entry.title_ja, "title_ja"), title_en: string(entry.title_en, "title_en"),
    };
  });
  unique(traces.map((entry) => entry.trace_id), "trace_id");
  return {
    contract_version: TRACE_CONTRACT_VERSION,
    dataset_version: string(data.dataset_version, "dataset_version"),
    data_version: string(data.data_version, "data_version"),
    traces,
  };
}

export function parseTraceBundle(input: unknown): TraceBundle {
  const data = record(input, "TraceBundle");
  exactKeys(data, bundleKeys, "TraceBundle");
  if (data.contract_version !== TRACE_CONTRACT_VERSION) {
    throw new Error(`Unsupported TraceBundle version: ${String(data.contract_version)}.`);
  }
  if (data.synchronization !== "oracle_evaluations") {
    throw new Error("TraceBundle synchronization must be oracle_evaluations.");
  }
  const bundle: TraceBundle = {
    contract_version: TRACE_CONTRACT_VERSION,
    bundle_id: string(data.bundle_id, "bundle_id"),
    comparison_id: string(data.comparison_id, "comparison_id"),
    dataset_version: string(data.dataset_version, "dataset_version"),
    data_version: string(data.data_version, "data_version"),
    objective_id: string(data.objective_id, "objective_id"),
    objective: jsonRecord(data.objective, "objective"),
    initial_state: jsonRecord(data.initial_state, "initial_state"),
    seed: jsonRecord(data.seed, "seed"),
    evaluation_budget: positiveInteger(data.evaluation_budget, "evaluation_budget"),
    stopping: jsonRecord(data.stopping, "stopping"),
    environment: jsonRecord(data.environment, "environment"),
    fairness_statement: string(data.fairness_statement, "fairness_statement"),
    member_traces: array(data.member_traces, "member_traces").map(parseAlgorithmTrace),
    synchronization: "oracle_evaluations",
  };
  if (bundle.member_traces.length === 0) throw new Error("TraceBundle requires member_traces.");
  unique(bundle.member_traces.map((trace) => trace.trace_id), "member trace_id");
  for (const member of bundle.member_traces) validateBundleMember(bundle, member);
  return bundle;
}

export function synchronizeTraceBundle(
  bundle: TraceBundle,
  oracleEvaluations: number,
): Record<string, TraceFrame> {
  const requested = nonNegativeInteger(oracleEvaluations, "oracleEvaluations");
  return Object.fromEntries(bundle.member_traces.map((trace) => {
    let match = trace.frames[0];
    for (const frame of trace.frames) {
      if (frame.oracle_evaluations > requested) break;
      match = frame;
    }
    return [trace.trace_id, match];
  }));
}

export function traceEventLabel(frame: TraceFrame, locale: "ja" | "en" = "ja"): string {
  const explicit = locale === "ja" ? frame.event_label_ja : frame.event_label_en;
  if (explicit) return explicit;
  return locale === "ja"
    ? `未定義イベント（${frame.event_type}）`
    : `Unknown event (${frame.event_type})`;
}

function parseFrame(value: unknown, index: number): TraceFrame {
  const data = record(value, `frames[${index}]`);
  exactKeys(data, frameKeys, `frames[${index}]`);
  const eventLabelJa = nullableString(data.event_label_ja, "event_label_ja");
  const eventLabelEn = nullableString(data.event_label_en, "event_label_en");
  if ((eventLabelJa === null) !== (eventLabelEn === null)) {
    throw new Error("Event labels must provide both Japanese and English or neither.");
  }
  const points = array(data.points, "points").map(parsePoint);
  const vectors = array(data.vectors, "vectors").map(parseVector);
  const metrics = array(data.metrics, "metrics").map(parseMetric);
  unique(points.map((point) => point.point_id), "point_id");
  unique(vectors.map((vector) => vector.vector_id), "vector_id");
  unique(metrics.map((metric) => metric.metric_id), "metric_id");
  return {
    frame_index: nonNegativeInteger(data.frame_index, "frame_index"),
    iteration: nonNegativeInteger(data.iteration, "iteration"),
    oracle_evaluations: nonNegativeInteger(data.oracle_evaluations, "oracle_evaluations"),
    elapsed_steps: nonNegativeInteger(data.elapsed_steps, "elapsed_steps"),
    elapsed_time_ms: nonNegativeNumber(data.elapsed_time_ms, "elapsed_time_ms"),
    event_type: slug(data.event_type, "event_type"),
    decision: enumValue(data.decision, ["accepted", "rejected", "not_applicable"] as const, "decision"),
    explanation_key: slug(data.explanation_key, "explanation_key"),
    event_label_ja: eventLabelJa, event_label_en: eventLabelEn,
    keyframe: boolean(data.keyframe, "keyframe"), points, vectors, metrics,
    payload: jsonValue(data.payload, "payload"),
  };
}

function parsePoint(value: unknown, index: number): TracePoint {
  const data = record(value, `points[${index}]`);
  exactKeys(data, pointKeys, `points[${index}]`);
  return {
    point_id: string(data.point_id, "point_id"), role: slug(data.role, "role"),
    coordinates: finiteNumbers(data.coordinates, "coordinates", true),
    value: data.value === null ? null : finiteNumber(data.value, "value"),
    label_ja: string(data.label_ja, "label_ja"), label_en: string(data.label_en, "label_en"),
  };
}

function parseVector(value: unknown, index: number): TraceVector {
  const data = record(value, `vectors[${index}]`);
  exactKeys(data, vectorKeys, `vectors[${index}]`);
  const origin = finiteNumbers(data.origin, "origin", true);
  const components = finiteNumbers(data.components, "components", true);
  if (origin.length !== components.length) throw new Error("Vector origin/components dimensions differ.");
  return {
    vector_id: string(data.vector_id, "vector_id"), role: slug(data.role, "role"), origin, components,
    label_ja: string(data.label_ja, "label_ja"), label_en: string(data.label_en, "label_en"),
  };
}

function parseMetric(value: unknown, index: number): TraceMetric {
  const data = record(value, `metrics[${index}]`);
  exactKeys(data, metricKeys, `metrics[${index}]`);
  return {
    metric_id: string(data.metric_id, "metric_id"), label_ja: string(data.label_ja, "label_ja"),
    label_en: string(data.label_en, "label_en"), value: finiteNumber(data.value, "value"),
    unit: nullableString(data.unit, "unit"),
  };
}

function validateProgress(frames: TraceFrame[]): void {
  frames.forEach((frame, index) => {
    if (frame.frame_index !== index) throw new Error("frame_index must be contiguous from zero.");
    if (index === 0) return;
    const previous = frames[index - 1];
    for (const key of ["iteration", "oracle_evaluations", "elapsed_steps", "elapsed_time_ms"] as const) {
      if (frame[key] < previous[key]) throw new Error(`${key} must be monotonic.`);
    }
  });
}

function validateBundleMember(bundle: TraceBundle, member: AlgorithmTrace): void {
  const scalarFields = [
    "dataset_version", "data_version", "objective_id", "evaluation_budget", "fairness_statement",
  ] as const;
  for (const field of scalarFields) {
    if (member[field] !== bundle[field]) {
      throw new Error(`Member trace ${member.trace_id} ${field} does not match TraceBundle.`);
    }
  }
  const recordFields = ["objective", "initial_state", "seed", "stopping", "environment"] as const;
  for (const field of recordFields) {
    if (canonicalJson(member[field]) !== canonicalJson(bundle[field])) {
      throw new Error(`Member trace ${member.trace_id} ${field} does not match TraceBundle.`);
    }
  }
  if (member.frames.at(-1)!.oracle_evaluations > bundle.evaluation_budget) {
    throw new Error(`Member trace ${member.trace_id} exceeds TraceBundle evaluation_budget.`);
  }
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${field} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function exactKeys(data: Record<string, unknown>, expected: readonly string[], field: string): void {
  const expectedSet = new Set(expected);
  const unknown = Object.keys(data).filter((key) => !expectedSet.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key));
  if (unknown.length) throw new Error(`${field} has unknown core fields: ${unknown.join(", ")}.`);
  if (missing.length) throw new Error(`${field} is missing core fields: ${missing.join(", ")}.`);
}

function string(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) throw new Error(`${field} must be non-empty.`);
  return value;
}

function nullableString(value: unknown, field: string): string | null {
  return value === null ? null : string(value, field);
}

function slug(value: unknown, field: string): string {
  const result = string(value, field);
  if (!slugPattern.test(result)) throw new Error(`${field} must be a lowercase slug.`);
  return result;
}

function array(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value;
}

function boolean(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") throw new Error(`${field} must be a boolean.`);
  return value;
}

function finiteNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${field} must be finite.`);
  return value;
}

function nonNegativeNumber(value: unknown, field: string): number {
  const result = finiteNumber(value, field);
  if (result < 0) throw new Error(`${field} must be non-negative.`);
  return result;
}

function nonNegativeInteger(value: unknown, field: string): number {
  const result = nonNegativeNumber(value, field);
  if (!Number.isInteger(result)) throw new Error(`${field} must be an integer.`);
  return result;
}

function positiveInteger(value: unknown, field: string): number {
  const result = nonNegativeInteger(value, field);
  if (result === 0) throw new Error(`${field} must be positive.`);
  return result;
}

function finiteNumbers(value: unknown, field: string, nonEmpty = false): number[] {
  const result = array(value, field).map((item, index) => finiteNumber(item, `${field}[${index}]`));
  if (nonEmpty && result.length === 0) throw new Error(`${field} must not be empty.`);
  return result;
}

function uniqueStrings(value: unknown, field: string): string[] {
  const result = array(value, field).map((item, index) => string(item, `${field}[${index}]`));
  if (result.length === 0) throw new Error(`${field} must not be empty.`);
  unique(result, field);
  return result;
}

function unique(values: string[], field: string): void {
  if (new Set(values).size !== values.length) throw new Error(`${field} values must be unique.`);
}

function enumValue<const T extends readonly string[]>(value: unknown, allowed: T, field: string): T[number] {
  if (typeof value !== "string" || !allowed.includes(value)) throw new Error(`${field} is invalid.`);
  return value as T[number];
}

function jsonRecord(value: unknown, field: string): Record<string, JsonValue> {
  return record(jsonValue(value, field), field) as Record<string, JsonValue>;
}

function jsonValue(value: unknown, field: string): JsonValue {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number") return finiteNumber(value, field);
  if (Array.isArray(value)) return value.map((item, index) => jsonValue(item, `${field}[${index}]`));
  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [key, jsonValue(item, `${field}.${key}`)]),
    );
  }
  throw new Error(`${field} contains a non-JSON value.`);
}

function canonicalJson(value: JsonValue | AlgorithmTrace): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  return `{${Object.entries(value)
    .sort(([left], [right]) => left.localeCompare(right, "en"))
    .map(([key, item]) => `${JSON.stringify(key)}:${canonicalJson(item as JsonValue)}`)
    .join(",")}}`;
}

function safeRelativePath(value: unknown): string {
  const path = string(value, "path");
  if (
    !/^[a-z0-9][a-z0-9._/-]*\.json$/u.test(path)
    || path.includes("//")
    || path.split("/").includes("..")
  ) {
    throw new Error("Trace path must be a safe relative URL path.");
  }
  return path;
}
