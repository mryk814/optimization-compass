export type ComparisonMode =
  | "method_contrast"
  | "parameter_sensitivity"
  | "initial_condition_sensitivity"
  | "failure_contrast"
  | "strategy_contrast"
  | "result_tradeoff";

export type ComparisonRendererFamily =
  | "continuous_trajectory"
  | "generic_metric_history"
  | "search_tree"
  | "feasible_region"
  | "pareto_front";

export interface ComparisonBudget {
  metric: string;
  value: number;
}

export interface ComparisonMetric {
  metric_id: string;
  label_ja: string;
  direction: "minimize" | "maximize" | "target" | "none";
  unit: string;
}

export interface ComparisonArtifact {
  artifact_id: string;
  artifact_kind: "executable_trace" | "result_visualization";
  renderer_family: ComparisonRendererFamily;
  renderer_contract_version: string;
  payload_path: string;
}

export interface ComparisonMember {
  member_id: string;
  role: string;
  method_id: string;
  scenario_id: string;
  label_ja: string;
  label_en: string;
  parameters: Record<string, string | number | boolean>;
  budget: ComparisonBudget;
  artifact: ComparisonArtifact;
}

export interface ComparisonSet {
  comparison_id: string;
  canonical_url: string;
  identity_status: "canonical" | "derived";
  canonical_comparison_id: string;
  aliases: string[];
  mode: ComparisonMode;
  journey_id: string;
  case_id: string;
  problem_definition_id: string;
  problem_instance_id: string;
  benchmark_context_id: string;
  title_ja: string;
  title_en: string;
  comparison_question: string;
  formulation_summary: string;
  fixed_factors: string[];
  changed_factors: string[];
  seed_policy: string;
  budget: ComparisonBudget;
  stopping_policy: string;
  tuning_policy: string;
  synchronization_axis: string;
  metrics: ComparisonMetric[];
  comparability: "comparable_with_caveat" | "contrast_only" | "not_comparable";
  ranking_eligible: boolean;
  fairness_note: string;
  caveat: string;
  takeaway: string;
  limitations: string[];
  source_ids: string[];
  last_verified: string;
  members: ComparisonMember[];
}

export interface ComparisonIndex {
  contract_version: "2.0.0";
  dataset_version: string;
  comparisons: ComparisonSet[];
}

const modes: ComparisonMode[] = [
  "method_contrast", "parameter_sensitivity", "initial_condition_sensitivity",
  "failure_contrast", "strategy_contrast", "result_tradeoff",
];
const rendererFamilies: ComparisonRendererFamily[] = [
  "continuous_trajectory", "generic_metric_history", "search_tree", "feasible_region", "pareto_front",
];

export function parseComparisonIndex(raw: unknown): ComparisonIndex {
  const data = record(raw, "comparison index");
  exact(data, ["contract_version", "dataset_version", "comparisons"], "comparison index");
  if (data.contract_version !== "2.0.0") throw new Error("Unsupported comparison contract.");
  const comparisons = list(data.comparisons, "comparisons").map(parseComparison);
  unique(comparisons.map((comparison) => comparison.comparison_id), "comparison IDs");
  const ids = new Set(comparisons.map((comparison) => comparison.comparison_id));
  for (const comparison of comparisons) {
    if (!ids.has(comparison.canonical_comparison_id)) {
      throw new Error(`comparison canonical identity does not resolve: ${comparison.canonical_comparison_id}`);
    }
  }
  return {
    contract_version: "2.0.0",
    dataset_version: text(data.dataset_version, "dataset_version"),
    comparisons,
  };
}

function parseComparison(raw: unknown, index: number): ComparisonSet {
  const field = `comparisons[${index}]`;
  const data = record(raw, field);
  exact(data, [
    "comparison_id", "canonical_url", "identity_status", "canonical_comparison_id", "aliases", "mode",
    "journey_id", "case_id", "problem_definition_id", "problem_instance_id", "benchmark_context_id",
    "title_ja", "title_en", "comparison_question", "formulation_summary", "fixed_factors", "changed_factors",
    "seed_policy", "budget", "stopping_policy", "tuning_policy", "synchronization_axis", "metrics",
    "comparability", "ranking_eligible", "fairness_note", "caveat", "takeaway", "limitations", "source_ids",
    "last_verified", "members",
  ], field);
  const comparisonId = text(data.comparison_id, `${field}.comparison_id`);
  const canonicalUrl = route(data.canonical_url, `${field}.canonical_url`);
  if (canonicalUrl !== `/compare/${comparisonId}`) throw new Error("comparison canonical_url must be generated from comparison_id.");
  const identityStatus = oneOf(data.identity_status, ["canonical", "derived"] as const, "identity_status");
  const canonicalComparisonId = text(data.canonical_comparison_id, "canonical_comparison_id");
  if ((identityStatus === "canonical") !== (canonicalComparisonId === comparisonId)) {
    throw new Error("comparison canonical identity is invalid.");
  }
  const journeyId = text(data.journey_id, "journey_id");
  const caseId = text(data.case_id, "case_id");
  if (journeyId !== caseId) throw new Error("comparison journey_id must equal case_id.");
  const budget = parseBudget(data.budget, `${field}.budget`);
  const members = list(data.members, `${field}.members`).map((member, memberIndex) => (
    parseMember(member, `${field}.members[${memberIndex}]`)
  ));
  if (members.length < 2) throw new Error("comparison requires at least two members.");
  unique(members.map((member) => member.member_id), "comparison member IDs");
  if (members.some((member) => member.budget.metric !== budget.metric || member.budget.value !== budget.value)) {
    throw new Error("comparison members must use the declared aligned budget.");
  }
  const synchronizationAxis = text(data.synchronization_axis, "synchronization_axis");
  if (synchronizationAxis !== budget.metric) throw new Error("synchronization_axis must match the aligned budget metric.");
  const families = new Set(members.map((member) => member.artifact.renderer_family));
  if (families.size > 1 && !(families.size === 2 && families.has("continuous_trajectory") && families.has("generic_metric_history"))) {
    throw new Error("comparison members use incompatible renderer families.");
  }
  const metrics = list(data.metrics, "metrics").map(parseMetric);
  if (metrics.length === 0) throw new Error("comparison metrics must be non-empty.");
  unique(metrics.map((metric) => metric.metric_id), "comparison metric IDs");
  const comparability = oneOf(
    data.comparability,
    ["comparable_with_caveat", "contrast_only", "not_comparable"] as const,
    "comparability",
  );
  const rankingEligible = bool(data.ranking_eligible, "ranking_eligible");
  if (rankingEligible && comparability !== "comparable_with_caveat") {
    throw new Error("ranking eligibility requires comparable_with_caveat.");
  }
  return {
    comparison_id: comparisonId,
    canonical_url: canonicalUrl,
    identity_status: identityStatus,
    canonical_comparison_id: canonicalComparisonId,
    aliases: texts(data.aliases, "aliases"),
    mode: oneOf(data.mode, modes, "mode"),
    journey_id: journeyId,
    case_id: caseId,
    problem_definition_id: text(data.problem_definition_id, "problem_definition_id"),
    problem_instance_id: text(data.problem_instance_id, "problem_instance_id"),
    benchmark_context_id: text(data.benchmark_context_id, "benchmark_context_id"),
    title_ja: text(data.title_ja, "title_ja"),
    title_en: text(data.title_en, "title_en"),
    comparison_question: text(data.comparison_question, "comparison_question"),
    formulation_summary: text(data.formulation_summary, "formulation_summary"),
    fixed_factors: nonEmptyTexts(data.fixed_factors, "fixed_factors"),
    changed_factors: nonEmptyTexts(data.changed_factors, "changed_factors"),
    seed_policy: text(data.seed_policy, "seed_policy"),
    budget,
    stopping_policy: text(data.stopping_policy, "stopping_policy"),
    tuning_policy: text(data.tuning_policy, "tuning_policy"),
    synchronization_axis: synchronizationAxis,
    metrics,
    comparability,
    ranking_eligible: rankingEligible,
    fairness_note: text(data.fairness_note, "fairness_note"),
    caveat: text(data.caveat, "caveat"),
    takeaway: text(data.takeaway, "takeaway"),
    limitations: nonEmptyTexts(data.limitations, "limitations"),
    source_ids: nonEmptyTexts(data.source_ids, "source_ids"),
    last_verified: text(data.last_verified, "last_verified"),
    members,
  };
}

function parseMember(raw: unknown, field: string): ComparisonMember {
  const data = record(raw, field);
  exact(data, ["member_id", "role", "method_id", "scenario_id", "label_ja", "label_en", "parameters", "budget", "artifact"], field);
  return {
    member_id: text(data.member_id, `${field}.member_id`),
    role: text(data.role, `${field}.role`),
    method_id: text(data.method_id, `${field}.method_id`),
    scenario_id: text(data.scenario_id, `${field}.scenario_id`),
    label_ja: text(data.label_ja, `${field}.label_ja`),
    label_en: text(data.label_en, `${field}.label_en`),
    parameters: scalarRecord(data.parameters, `${field}.parameters`),
    budget: parseBudget(data.budget, `${field}.budget`),
    artifact: parseArtifact(data.artifact, `${field}.artifact`),
  };
}

function parseArtifact(raw: unknown, field: string): ComparisonArtifact {
  const data = record(raw, field);
  exact(data, ["artifact_id", "artifact_kind", "renderer_family", "renderer_contract_version", "payload_path"], field);
  const family = oneOf(data.renderer_family, rendererFamilies, `${field}.renderer_family`);
  const kind = oneOf(data.artifact_kind, ["executable_trace", "result_visualization"] as const, `${field}.artifact_kind`);
  if (family === "pareto_front" ? kind !== "result_visualization" : kind !== "executable_trace") {
    throw new Error(`${family} uses an incompatible artifact kind.`);
  }
  return {
    artifact_id: text(data.artifact_id, `${field}.artifact_id`),
    artifact_kind: kind,
    renderer_family: family,
    renderer_contract_version: text(data.renderer_contract_version, `${field}.renderer_contract_version`),
    payload_path: routePath(data.payload_path, `${field}.payload_path`),
  };
}

function parseBudget(raw: unknown, field: string): ComparisonBudget {
  const data = record(raw, field);
  exact(data, ["metric", "value"], field);
  const value = integer(data.value, `${field}.value`);
  if (value <= 0) throw new Error(`${field}.value must be positive.`);
  return { metric: text(data.metric, `${field}.metric`), value };
}

function parseMetric(raw: unknown, index: number): ComparisonMetric {
  const field = `metrics[${index}]`;
  const data = record(raw, field);
  exact(data, ["metric_id", "label_ja", "direction", "unit"], field);
  return {
    metric_id: text(data.metric_id, `${field}.metric_id`),
    label_ja: text(data.label_ja, `${field}.label_ja`),
    direction: oneOf(data.direction, ["minimize", "maximize", "target", "none"] as const, `${field}.direction`),
    unit: text(data.unit, `${field}.unit`),
  };
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`);
  return value as Record<string, unknown>;
}
function list(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function text(value: unknown, field: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`); return value; }
function texts(value: unknown, field: string): string[] { const values = list(value, field).map((item, index) => text(item, `${field}[${index}]`)); unique(values, field); return values; }
function nonEmptyTexts(value: unknown, field: string): string[] { const values = texts(value, field); if (values.length === 0) throw new Error(`${field} must be non-empty.`); return values; }
function bool(value: unknown, field: string): boolean { if (typeof value !== "boolean") throw new Error(`${field} must be boolean.`); return value; }
function integer(value: unknown, field: string): number { if (typeof value !== "number" || !Number.isSafeInteger(value)) throw new Error(`${field} must be an integer.`); return value; }
function route(value: unknown, field: string): string { const result = text(value, field); if (!/^\/[A-Za-z0-9._/-]+$/u.test(result) || result.includes("//")) throw new Error(`${field} must be a safe route.`); return result; }
function routePath(value: unknown, field: string): string { const result = text(value, field); if (!/^[A-Za-z0-9._/-]+$/u.test(result) || result.includes("//") || result.startsWith("/")) throw new Error(`${field} must be a safe relative path.`); return result; }
function scalarRecord(value: unknown, field: string): Record<string, string | number | boolean> { const data = record(value, field); for (const [key, item] of Object.entries(data)) { if (typeof item !== "string" && typeof item !== "number" && typeof item !== "boolean") throw new Error(`${field}.${key} must be scalar.`); } return data as Record<string, string | number | boolean>; }
function oneOf<const T extends readonly string[]>(value: unknown, values: T, field: string): T[number] { const result = text(value, field); if (!values.includes(result)) throw new Error(`${field} is unsupported.`); return result as T[number]; }
function unique(values: string[], field: string): void { if (new Set(values).size !== values.length) throw new Error(`${field} must be unique.`); }
function exact(data: Record<string, unknown>, expected: readonly string[], field: string): void { const keys = new Set(expected); const unknown = Object.keys(data).filter((key) => !keys.has(key)); const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key)); if (unknown.length > 0) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`); if (missing.length > 0) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`); }
