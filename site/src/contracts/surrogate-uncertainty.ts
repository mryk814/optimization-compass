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
  contract_version: "1.0.0" | "1.1.0";
  strategy: "exploit" | "explore";
  noise_preset: "noiseless" | "small_noise";
  noise_std: number;
  exploration_xi: number;
  domain: [number, number];
  objective_expression: string;
  truth_disclosure_ja: string;
  frames: SurrogateFrame[];
  random_history: Observation[];
  evaluation_ledger?: EvaluationLedger;
}

export type EvaluationFidelity = "low" | "high";
export type EvaluationStatus = "ok" | "failed" | "censored" | "timeout";

export interface EvaluationLedgerEntry {
  call_id: number;
  x: number;
  fidelity: EvaluationFidelity;
  cost: number;
  status: EvaluationStatus;
  observed_value: number | null;
  accumulated_cost: number;
  accumulated_high_fidelity_equivalent_cost: number;
  best_so_far: number | null;
}

export interface EvaluationLedger {
  contract_version: "1.0.0";
  fidelity_costs: { low: number; high: number };
  budget_cost: number;
  high_fidelity_equivalent_budget: number;
  calls: EvaluationLedgerEntry[];
}

export function parseSurrogateUncertaintyPayload(value: unknown): SurrogateUncertaintyPayload {
  const data = object(value, "SurrogateUncertaintyPayload");
  if (data.contract_version !== "1.0.0" && data.contract_version !== "1.1.0") throw new Error("Unsupported SurrogateUncertainty contract.");
  const contractVersion = data.contract_version;
  const fields = ["contract_version", "strategy", "noise_preset", "noise_std", "exploration_xi", "domain", "objective_expression", "truth_disclosure_ja", "frames", "random_history"] as const;
  exact(data, contractVersion === "1.1.0" ? [...fields, "evaluation_ledger"] : fields, "SurrogateUncertaintyPayload");
  const frames = array(data.frames, "frames", parseFrame);
  const randomHistory = array(data.random_history, "random_history", parseObservation);
  if (frames.length === 0) throw new Error("frames must not be empty.");
  frames.forEach((frame, index) => {
    if (frame.frame_index !== index || frame.oracle_evaluations !== index + 3) throw new Error("frames are not consecutive.");
  });
  if (randomHistory.length !== frames.at(-1)?.oracle_evaluations) throw new Error("random comparison budget differs from the renderer frames.");
  const domain = numberArray(data.domain, "domain");
  if (domain.length !== 2 || domain[0] >= domain[1]) throw new Error("domain must be an increasing pair.");
  const evaluationLedger = contractVersion === "1.1.0"
    ? parseEvaluationLedger(data.evaluation_ledger, "evaluation_ledger")
    : undefined;
  return {
    contract_version: contractVersion,
    strategy: literal(data.strategy, ["exploit", "explore"] as const, "strategy"),
    noise_preset: literal(data.noise_preset, ["noiseless", "small_noise"] as const, "noise_preset"),
    noise_std: nonNegative(data.noise_std, "noise_std"),
    exploration_xi: nonNegative(data.exploration_xi, "exploration_xi"),
    domain: domain as [number, number],
    objective_expression: string(data.objective_expression, "objective_expression"),
    truth_disclosure_ja: string(data.truth_disclosure_ja, "truth_disclosure_ja"),
    frames,
    random_history: randomHistory,
    ...(evaluationLedger ? { evaluation_ledger: evaluationLedger } : {}),
  };
}

function parseEvaluationLedger(value: unknown, field: string): EvaluationLedger {
  const data = object(value, field);
  exact(data, ["contract_version", "fidelity_costs", "budget_cost", "high_fidelity_equivalent_budget", "calls"], field);
  const costs = object(data.fidelity_costs, `${field}.fidelity_costs`);
  exact(costs, ["low", "high"], `${field}.fidelity_costs`);
  const fidelityCosts = { low: positive(costs.low, `${field}.fidelity_costs.low`), high: positive(costs.high, `${field}.fidelity_costs.high`) };
  const calls = array(data.calls, `${field}.calls`, parseEvaluationLedgerEntry);
  if (calls.length === 0) throw new Error(`${field}.calls must not be empty.`);
  let accumulatedCost = 0;
  let accumulatedHighEquivalent = 0;
  let bestHigh: number | null = null;
  calls.forEach((call, index) => {
    if (call.call_id !== index + 1) throw new Error(`${field}.calls must use consecutive call IDs.`);
    if (call.cost !== fidelityCosts[call.fidelity]) throw new Error(`${field}.calls[${index}].cost does not match fidelity.`);
    accumulatedCost += call.cost;
    accumulatedHighEquivalent += call.cost / fidelityCosts.high;
    if (Math.abs(call.accumulated_cost - accumulatedCost) > 1e-9) throw new Error(`${field}.calls[${index}] accumulated cost is inconsistent.`);
    if (Math.abs(call.accumulated_high_fidelity_equivalent_cost - accumulatedHighEquivalent) > 1e-7) throw new Error(`${field}.calls[${index}] equivalent cost is inconsistent.`);
    if (call.status === "ok" && call.observed_value === null) throw new Error(`${field}.calls[${index}] successful calls require a value.`);
    if (call.status !== "ok" && call.observed_value !== null) throw new Error(`${field}.calls[${index}] unsuccessful calls require null value.`);
    if (call.fidelity === "high" && call.status === "ok") bestHigh = bestHigh === null ? call.observed_value : Math.min(bestHigh, call.observed_value!);
    if (call.best_so_far !== bestHigh) throw new Error(`${field}.calls[${index}] best-so-far is inconsistent.`);
  });
  const budgetCost = positive(data.budget_cost, `${field}.budget_cost`);
  if (accumulatedCost > budgetCost + 1e-9) throw new Error(`${field} calls exceed budget_cost.`);
  const equivalentBudget = positive(data.high_fidelity_equivalent_budget, `${field}.high_fidelity_equivalent_budget`);
  if (Math.abs(equivalentBudget - budgetCost / fidelityCosts.high) > 1e-7) throw new Error(`${field} equivalent budget is inconsistent.`);
  if (data.contract_version !== "1.0.0") throw new Error(`${field}.contract_version is unsupported.`);
  return { contract_version: "1.0.0", fidelity_costs: fidelityCosts, budget_cost: budgetCost, high_fidelity_equivalent_budget: equivalentBudget, calls };
}

function parseEvaluationLedgerEntry(value: unknown, field: string): EvaluationLedgerEntry {
  const data = object(value, field);
  exact(data, ["call_id", "x", "fidelity", "cost", "status", "observed_value", "accumulated_cost", "accumulated_high_fidelity_equivalent_cost", "best_so_far"], field);
  return {
    call_id: integer(data.call_id, `${field}.call_id`, 1),
    x: number(data.x, `${field}.x`),
    fidelity: literal(data.fidelity, ["low", "high"] as const, `${field}.fidelity`),
    cost: positive(data.cost, `${field}.cost`),
    status: literal(data.status, ["ok", "failed", "censored", "timeout"] as const, `${field}.status`),
    observed_value: nullableNumber(data.observed_value, `${field}.observed_value`),
    accumulated_cost: positive(data.accumulated_cost, `${field}.accumulated_cost`),
    accumulated_high_fidelity_equivalent_cost: nonNegative(data.accumulated_high_fidelity_equivalent_cost, `${field}.accumulated_high_fidelity_equivalent_cost`),
    best_so_far: nullableNumber(data.best_so_far, `${field}.best_so_far`),
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
function positive(value: unknown, field: string): number {
  const candidate = number(value, field);
  if (candidate <= 0) throw new Error(`${field} must be positive.`);
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
