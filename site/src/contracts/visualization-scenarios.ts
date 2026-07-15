export type VisualizationPurpose = "mechanism" | "comparison" | "failure_contrast" | "sensitivity";
export type VisualizationArtifactKind = "executable_trace" | "schematic_animation" | "static_diagram" | "result_visualization";
export type RendererFamily =
  | "simplex_geometry"
  | "continuous_trajectory"
  | "generic_metric_history"
  | "search_tree"
  | "surrogate_uncertainty";

export interface VisualizationScenario {
  contract_version: "1.0.0";
  dataset_version: string;
  scenario_id: string;
  identity_status: "canonical" | "derived" | "generated_only";
  canonical_scenario_id: string | null;
  title_ja: string;
  title_en: string;
  purpose: VisualizationPurpose;
  problem_definition_id: string;
  problem_instance_id: string;
  lesson: {
    expected_phenomenon_ja: string;
    expected_phenomenon_en: string;
    limitations_ja: string;
    limitations_en: string;
  };
  experiment: {
    oracle_policy: ("objective_value" | "gradient")[];
    initial_condition: { point: number[] };
    parameter_preset_id: string;
    seed: { status: "fixed" | "not_applicable"; value: number | null };
    budget: { metric: "oracle_evaluations"; value: number };
    stopping: Record<string, number | boolean>;
    tuning_policy: "fixed_preset";
  };
  runs: {
    run_id: string;
    method_id: string;
    profile_id: string;
    implementation_mapping_status: "supported" | "unsupported" | "unknown" | "not_applicable";
    implementation_id: string | null;
    artifact_id: string;
  }[];
  artifact: {
    artifact_kind: VisualizationArtifactKind;
    artifact_contract: "AlgorithmTrace" | "SurrogateUncertainty";
    artifact_contract_version: "1.0.0";
    renderer_family: RendererFamily;
    renderer_contract_version: "1.0.0";
    observable_ids: string[];
    payload_path: string;
    payload_bytes: number;
    payload_sha256: string;
  };
  source_ids: string[];
  last_verified: string;
}

export interface VisualizationScenarioIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  scenarios: VisualizationScenario[];
}

const purposes = new Set<VisualizationPurpose>(["mechanism", "comparison", "failure_contrast", "sensitivity"]);
const artifactKinds = new Set<VisualizationArtifactKind>(["executable_trace", "schematic_animation", "static_diagram", "result_visualization"]);
const rendererFamilies = new Set<RendererFamily>([
  "simplex_geometry",
  "continuous_trajectory",
  "generic_metric_history",
  "search_tree",
  "surrogate_uncertainty",
]);

export function parseVisualizationScenarioIndex(raw: unknown): VisualizationScenarioIndex {
  const data = record(raw, "VisualizationScenarioIndex");
  exact(data, ["contract_version", "dataset_version", "scenarios"], "VisualizationScenarioIndex");
  version(data.contract_version, "contract_version");
  const datasetVersion = text(data.dataset_version, "dataset_version");
  const scenarios = list(data.scenarios, "scenarios").map((item, index) =>
    parseScenario(item, `scenarios[${index}]`),
  );
  if (scenarios.length === 0) throw new Error("scenarios must not be empty.");
  if (new Set(scenarios.map((item) => item.scenario_id)).size !== scenarios.length) {
    throw new Error("scenario IDs must be unique.");
  }
  if (scenarios.some((item) => item.dataset_version !== datasetVersion)) {
    throw new Error("scenario dataset version must match the index.");
  }
  return { contract_version: "1.0.0", dataset_version: datasetVersion, scenarios };
}

function parseScenario(raw: unknown, field: string): VisualizationScenario {
  const data = record(raw, field);
  exact(data, ["contract_version", "dataset_version", "scenario_id", "identity_status", "canonical_scenario_id", "title_ja", "title_en", "purpose", "problem_definition_id", "problem_instance_id", "lesson", "experiment", "runs", "artifact", "source_ids", "last_verified"], field);
  version(data.contract_version, `${field}.contract_version`);
  const lesson = parseLesson(data.lesson, `${field}.lesson`);
  const experiment = parseExperiment(data.experiment, `${field}.experiment`);
  const runs = list(data.runs, `${field}.runs`).map((item, index) => parseRun(item, `${field}.runs[${index}]`));
  if (runs.length === 0 || new Set(runs.map((run) => run.run_id)).size !== runs.length) {
    throw new Error(`${field}.runs must be non-empty and unique.`);
  }
  const purpose = oneOf(data.purpose, purposes, `${field}.purpose`);
  const identityStatus = scenarioIdentityStatus(data.identity_status, `${field}.identity_status`);
  const scenarioId = text(data.scenario_id, `${field}.scenario_id`);
  const canonicalScenarioId = data.canonical_scenario_id === null
    ? null
    : text(data.canonical_scenario_id, `${field}.canonical_scenario_id`);
  if (identityStatus === "canonical" && canonicalScenarioId !== scenarioId) {
    throw new Error(`${field} canonical scenario must point to itself.`);
  }
  if (identityStatus === "derived" && (!canonicalScenarioId || canonicalScenarioId === scenarioId)) {
    throw new Error(`${field} derived scenario must point to a different canonical scenario.`);
  }
  if (identityStatus === "generated_only" && canonicalScenarioId !== null) {
    throw new Error(`${field} generated-only scenario cannot point to a canonical scenario.`);
  }
  return {
    contract_version: "1.0.0",
    dataset_version: text(data.dataset_version, `${field}.dataset_version`),
    scenario_id: scenarioId,
    identity_status: identityStatus,
    canonical_scenario_id: canonicalScenarioId,
    title_ja: text(data.title_ja, `${field}.title_ja`),
    title_en: text(data.title_en, `${field}.title_en`),
    purpose,
    problem_definition_id: text(data.problem_definition_id, `${field}.problem_definition_id`),
    problem_instance_id: text(data.problem_instance_id, `${field}.problem_instance_id`),
    lesson,
    experiment,
    runs,
    artifact: parseArtifact(data.artifact, `${field}.artifact`),
    source_ids: nonEmptyTextList(data.source_ids, `${field}.source_ids`),
    last_verified: text(data.last_verified, `${field}.last_verified`),
  };
}

function scenarioIdentityStatus(value: unknown, field: string): VisualizationScenario["identity_status"] {
  if (value !== "canonical" && value !== "derived" && value !== "generated_only") {
    throw new Error(`${field} is invalid.`);
  }
  return value;
}

function parseLesson(raw: unknown, field: string): VisualizationScenario["lesson"] {
  const data = record(raw, field);
  exact(data, ["expected_phenomenon_ja", "expected_phenomenon_en", "limitations_ja", "limitations_en"], field);
  return {
    expected_phenomenon_ja: text(data.expected_phenomenon_ja, `${field}.expected_phenomenon_ja`),
    expected_phenomenon_en: text(data.expected_phenomenon_en, `${field}.expected_phenomenon_en`),
    limitations_ja: text(data.limitations_ja, `${field}.limitations_ja`),
    limitations_en: text(data.limitations_en, `${field}.limitations_en`),
  };
}

function parseExperiment(raw: unknown, field: string): VisualizationScenario["experiment"] {
  const data = record(raw, field);
  exact(data, ["oracle_policy", "initial_condition", "parameter_preset_id", "seed", "budget", "stopping", "tuning_policy"], field);
  const initial = record(data.initial_condition, `${field}.initial_condition`);
  exact(initial, ["point"], `${field}.initial_condition`);
  const seed = record(data.seed, `${field}.seed`);
  exact(seed, ["status", "value"], `${field}.seed`);
  const seedStatus = seed.status === "fixed" || seed.status === "not_applicable" ? seed.status : invalid(`${field}.seed.status`);
  if ((seedStatus === "fixed") !== (typeof seed.value === "number" && Number.isSafeInteger(seed.value))) {
    if (!(seedStatus === "not_applicable" && seed.value === null)) throw new Error(`${field}.seed is invalid.`);
  }
  const budget = record(data.budget, `${field}.budget`);
  exact(budget, ["metric", "value"], `${field}.budget`);
  if (budget.metric !== "oracle_evaluations") throw new Error(`${field}.budget.metric is invalid.`);
  const stopping = parameterRecord(data.stopping, `${field}.stopping`);
  return {
    oracle_policy: nonEmptyTextList(data.oracle_policy, `${field}.oracle_policy`).map((value) => {
      if (value !== "objective_value" && value !== "gradient") throw new Error(`${field}.oracle_policy is invalid.`);
      return value;
    }),
    initial_condition: { point: numberList(initial.point, `${field}.initial_condition.point`) },
    parameter_preset_id: text(data.parameter_preset_id, `${field}.parameter_preset_id`),
    seed: { status: seedStatus, value: seed.value as number | null },
    budget: { metric: "oracle_evaluations", value: positiveInteger(budget.value, `${field}.budget.value`) },
    stopping,
    tuning_policy: data.tuning_policy === "fixed_preset" ? "fixed_preset" : invalid(`${field}.tuning_policy`),
  };
}

function parseRun(raw: unknown, field: string): VisualizationScenario["runs"][number] {
  const data = record(raw, field);
  exact(data, ["run_id", "method_id", "profile_id", "implementation_mapping_status", "implementation_id", "artifact_id"], field);
  const status = data.implementation_mapping_status;
  if (status !== "supported" && status !== "unsupported" && status !== "unknown" && status !== "not_applicable") {
    throw new Error(`${field}.implementation_mapping_status is invalid.`);
  }
  if (data.implementation_id !== null && typeof data.implementation_id !== "string") throw new Error(`${field}.implementation_id is invalid.`);
  return {
    run_id: text(data.run_id, `${field}.run_id`),
    method_id: text(data.method_id, `${field}.method_id`),
    profile_id: text(data.profile_id, `${field}.profile_id`),
    implementation_mapping_status: status,
    implementation_id: data.implementation_id,
    artifact_id: text(data.artifact_id, `${field}.artifact_id`),
  };
}

function parseArtifact(raw: unknown, field: string): VisualizationScenario["artifact"] {
  const data = record(raw, field);
  exact(data, ["artifact_kind", "artifact_contract", "artifact_contract_version", "renderer_family", "renderer_contract_version", "observable_ids", "payload_path", "payload_bytes", "payload_sha256"], field);
  if (data.artifact_contract !== "AlgorithmTrace" && data.artifact_contract !== "SurrogateUncertainty") throw new Error(`${field}.artifact_contract is invalid.`);
  version(data.artifact_contract_version, `${field}.artifact_contract_version`);
  version(data.renderer_contract_version, `${field}.renderer_contract_version`);
  return {
    artifact_kind: oneOf(data.artifact_kind, artifactKinds, `${field}.artifact_kind`),
    artifact_contract: data.artifact_contract,
    artifact_contract_version: "1.0.0",
    renderer_family: oneOf(data.renderer_family, rendererFamilies, `${field}.renderer_family`),
    renderer_contract_version: "1.0.0",
    observable_ids: nonEmptyTextList(data.observable_ids, `${field}.observable_ids`),
    payload_path: payloadPath(data.payload_path, `${field}.payload_path`),
    payload_bytes: positiveInteger(data.payload_bytes, `${field}.payload_bytes`),
    payload_sha256: sha256(data.payload_sha256, `${field}.payload_sha256`),
  };
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`);
  return value as Record<string, unknown>;
}
function list(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value;
}
function text(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`);
  return value;
}
function nonEmptyTextList(value: unknown, field: string): string[] {
  const values = list(value, field).map((item, index) => text(item, `${field}[${index}]`));
  if (values.length === 0) throw new Error(`${field} must not be empty.`);
  return values;
}
function numberList(value: unknown, field: string): number[] {
  const values = list(value, field).map((item) => finiteNumber(item, field));
  if (values.length === 0) throw new Error(`${field} must not be empty.`);
  return values;
}
function parameterRecord(value: unknown, field: string): Record<string, number | boolean> {
  const data = record(value, field);
  return Object.fromEntries(Object.entries(data).map(([key, item]) => {
    if (typeof item !== "number" && typeof item !== "boolean") throw new Error(`${field}.${key} is invalid.`);
    if (typeof item === "number" && !Number.isFinite(item)) throw new Error(`${field}.${key} must be finite.`);
    return [key, item];
  }));
}
function finiteNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${field} must be finite.`);
  return value;
}
function positiveInteger(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value <= 0) throw new Error(`${field} must be a positive integer.`);
  return value;
}
function payloadPath(value: unknown, field: string): string {
  const candidate = text(value, field);
  if (!/^(traces|visualizations)\/[a-z0-9._/-]+\.json$/u.test(candidate)) throw new Error(`${field} is invalid.`);
  return candidate;
}
function sha256(value: unknown, field: string): string {
  const candidate = text(value, field);
  if (!/^[0-9a-f]{64}$/u.test(candidate)) throw new Error(`${field} is invalid.`);
  return candidate;
}
function exact(data: Record<string, unknown>, expected: readonly string[], field: string): void {
  const keys = new Set(expected);
  const unknown = Object.keys(data).filter((key) => !keys.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key));
  if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`);
  if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`);
}
function version(value: unknown, field: string): asserts value is "1.0.0" {
  if (value !== "1.0.0") throw new Error(`${field} is unsupported.`);
}
function oneOf<T extends string>(value: unknown, values: ReadonlySet<T>, field: string): T {
  if (typeof value !== "string" || !values.has(value as T)) throw new Error(`${field} is invalid.`);
  return value as T;
}
function invalid(field: string): never {
  throw new Error(`${field} is invalid.`);
}
