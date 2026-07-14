export interface Observation {
  x: number;
  value: number;
  observed_value: number;
}

export interface PredictivePoint {
  x: number;
  true_value: number;
  mean: number;
  lower: number;
  upper: number;
  acquisition: number;
}

export interface SurrogateFrame {
  frame_index: number;
  oracle_evaluations: number;
  observations: Observation[];
  predictive_summary: PredictivePoint[];
  selected_point: number | null;
  selected_mean: number | null;
  selected_uncertainty: number | null;
  selected_acquisition: number | null;
  incumbent_x: number;
  incumbent_value: number;
  random_incumbent_value: number;
  explanation_ja: string;
}

export interface SurrogateUncertaintyPayload {
  contract_version: "1.0.0";
  strategy: "exploit" | "explore";
  noise_preset: "noiseless" | "small_noise";
  noise_std: number;
  exploration_xi: number;
  domain: [number, number];
  objective_expression: string;
  truth_disclosure_ja: string;
  frames: SurrogateFrame[];
  random_history: Observation[];
}

export function parseSurrogateUncertaintyPayload(value: unknown): SurrogateUncertaintyPayload {
  const data = object(value, "SurrogateUncertaintyPayload");
  exact(data, ["contract_version", "strategy", "noise_preset", "noise_std", "exploration_xi", "domain", "objective_expression", "truth_disclosure_ja", "frames", "random_history"], "SurrogateUncertaintyPayload");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported SurrogateUncertainty contract.");
  const frames = array(data.frames, "frames", parseFrame);
  const randomHistory = array(data.random_history, "random_history", parseObservation);
  if (frames.length === 0) throw new Error("frames must not be empty.");
  frames.forEach((frame, index) => {
    if (frame.frame_index !== index || frame.oracle_evaluations !== index + 3) throw new Error("frames are not consecutive.");
  });
  if (randomHistory.length !== frames.at(-1)?.oracle_evaluations) throw new Error("random comparison budget differs from the renderer frames.");
  const domain = numberArray(data.domain, "domain");
  if (domain.length !== 2 || domain[0] >= domain[1]) throw new Error("domain must be an increasing pair.");
  return {
    contract_version: "1.0.0",
    strategy: literal(data.strategy, ["exploit", "explore"] as const, "strategy"),
    noise_preset: literal(data.noise_preset, ["noiseless", "small_noise"] as const, "noise_preset"),
    noise_std: nonNegative(data.noise_std, "noise_std"),
    exploration_xi: nonNegative(data.exploration_xi, "exploration_xi"),
    domain: domain as [number, number],
    objective_expression: string(data.objective_expression, "objective_expression"),
    truth_disclosure_ja: string(data.truth_disclosure_ja, "truth_disclosure_ja"),
    frames,
    random_history: randomHistory,
  };
}

function parseFrame(value: unknown, field: string): SurrogateFrame {
  const data = object(value, field);
  exact(data, ["frame_index", "oracle_evaluations", "observations", "predictive_summary", "selected_point", "selected_mean", "selected_uncertainty", "selected_acquisition", "incumbent_x", "incumbent_value", "random_incumbent_value", "explanation_ja"], field);
  return {
    frame_index: integer(data.frame_index, `${field}.frame_index`, 0),
    oracle_evaluations: integer(data.oracle_evaluations, `${field}.oracle_evaluations`, 1),
    observations: array(data.observations, `${field}.observations`, parseObservation),
    predictive_summary: array(data.predictive_summary, `${field}.predictive_summary`, parsePredictivePoint),
    selected_point: nullableNumber(data.selected_point, `${field}.selected_point`),
    selected_mean: nullableNumber(data.selected_mean, `${field}.selected_mean`),
    selected_uncertainty: nullableNumber(data.selected_uncertainty, `${field}.selected_uncertainty`),
    selected_acquisition: nullableNumber(data.selected_acquisition, `${field}.selected_acquisition`),
    incumbent_x: number(data.incumbent_x, `${field}.incumbent_x`),
    incumbent_value: number(data.incumbent_value, `${field}.incumbent_value`),
    random_incumbent_value: number(data.random_incumbent_value, `${field}.random_incumbent_value`),
    explanation_ja: string(data.explanation_ja, `${field}.explanation_ja`),
  };
}

function parseObservation(value: unknown, field: string): Observation {
  const data = object(value, field);
  exact(data, ["x", "value", "observed_value"], field);
  return { x: number(data.x, `${field}.x`), value: number(data.value, `${field}.value`), observed_value: number(data.observed_value, `${field}.observed_value`) };
}

function parsePredictivePoint(value: unknown, field: string): PredictivePoint {
  const data = object(value, field);
  exact(data, ["x", "true_value", "mean", "lower", "upper", "acquisition"], field);
  return { x: number(data.x, `${field}.x`), true_value: number(data.true_value, `${field}.true_value`), mean: number(data.mean, `${field}.mean`), lower: number(data.lower, `${field}.lower`), upper: number(data.upper, `${field}.upper`), acquisition: nonNegative(data.acquisition, `${field}.acquisition`) };
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`);
  return value as Record<string, unknown>;
}
function exact(data: Record<string, unknown>, expected: readonly string[], field: string): void {
  const keys = new Set(expected);
  const unknown = Object.keys(data).filter((key) => !keys.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key));
  if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`);
  if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`);
}
function array<T>(value: unknown, field: string, parser: (item: unknown, field: string) => T): T[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value.map((item, index) => parser(item, `${field}[${index}]`));
}
function numberArray(value: unknown, field: string): number[] { return array(value, field, number); }
function number(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${field} must be finite.`);
  return value;
}
function nonNegative(value: unknown, field: string): number {
  const candidate = number(value, field);
  if (candidate < 0) throw new Error(`${field} must be non-negative.`);
  return candidate;
}
function integer(value: unknown, field: string, minimum: number): number {
  const candidate = number(value, field);
  if (!Number.isSafeInteger(candidate) || candidate < minimum) throw new Error(`${field} must be an integer >= ${minimum}.`);
  return candidate;
}
function nullableNumber(value: unknown, field: string): number | null { return value === null ? null : number(value, field); }
function string(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`);
  return value;
}
function literal<const T extends readonly string[]>(value: unknown, values: T, field: string): T[number] {
  if (typeof value !== "string" || !values.includes(value)) throw new Error(`${field} is invalid.`);
  return value as T[number];
}
