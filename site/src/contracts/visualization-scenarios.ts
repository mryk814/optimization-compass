export type VisualizationPurpose = "mechanism" | "comparison" | "failure_contrast" | "sensitivity";
export type VisualizationComparisonRole = "primary_example" | "sensitivity_variant" | "failure_contrast" | "baseline";
export type NarrationMilestoneId = "start" | "first_change" | "pattern_visible" | "termination";
export type VisualizationArtifactKind = "executable_trace" | "schematic_animation" | "static_diagram" | "result_visualization";
export type RendererFamily =
  | "simplex_geometry"
  | "continuous_trajectory"
  | "generic_metric_history"
  | "search_tree"
  | "surrogate_uncertainty";

export interface VisualizationScenario {
  contract_version: "1.1.0";
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
    learning_objective: LocalizedText;
    misconception: LocalizedText | null;
    expected_phenomenon_ja: string;
    expected_phenomenon_en: string;
    success_signals: VisualizationSignal[];
    failure_signals: VisualizationSignal[];
    primary_observables: VisualizationObservable[];
    secondary_observables: VisualizationObservable[];
    narration_steps: VisualizationNarrationStep[];
    comparison_role: VisualizationComparisonRole;
    prerequisite_concept_ids: string[];
    recommended_next_scenario_ids: string[];
    known_reference_display: {
      policy: "show" | "show_if_available" | "not_shown";
      note_ja: string;
      note_en: string;
    };
    static_summary: LocalizedText;
    text_alternative: LocalizedText;
    derived_media_caption: LocalizedText;
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
  contract_version: "1.1.0";
  dataset_version: string;
  scenarios: VisualizationScenario[];
}

export interface LocalizedText { ja: string; en: string }
export interface VisualizationObservable { observable_id: string; label_ja: string; label_en: string }
export interface VisualizationSignal {
  signal_id: string;
  label_ja: string;
  label_en: string;
  observable_ids: string[];
}
export interface VisualizationNarrationStep {
  milestone_id: NarrationMilestoneId;
  title_ja: string;
  title_en: string;
  observable_ids: string[];
}

const purposes = new Set<VisualizationPurpose>(["mechanism", "comparison", "failure_contrast", "sensitivity"]);
const comparisonRoles = new Set<VisualizationComparisonRole>(["primary_example", "sensitivity_variant", "failure_contrast", "baseline"]);
const narrationMilestones = new Set<NarrationMilestoneId>(["start", "first_change", "pattern_visible", "termination"]);
const knownReferencePolicies = new Set<VisualizationScenario["lesson"]["known_reference_display"]["policy"]>(["show", "show_if_available", "not_shown"]);
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
  scenarioVersion(data.contract_version, "contract_version");
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
  const scenarioIds = new Set(scenarios.map((item) => item.scenario_id));
  if (scenarios.some((item) => item.lesson.recommended_next_scenario_ids.some((id) => !scenarioIds.has(id)))) {
    throw new Error("recommended scenarios must exist in the index.");
  }
  return { contract_version: "1.1.0", dataset_version: datasetVersion, scenarios };
}

function parseScenario(raw: unknown, field: string): VisualizationScenario {
  const data = record(raw, field);
  exact(data, ["contract_version", "dataset_version", "scenario_id", "identity_status", "canonical_scenario_id", "title_ja", "title_en", "purpose", "problem_definition_id", "problem_instance_id", "lesson", "experiment", "runs", "artifact", "source_ids", "last_verified"], field);
  scenarioVersion(data.contract_version, `${field}.contract_version`);
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
  const artifact = parseArtifact(data.artifact, `${field}.artifact`);
  const lessonObservableIds = new Set([
    ...lesson.primary_observables,
    ...lesson.secondary_observables,
  ].map((item) => item.observable_id));
  if ([...lessonObservableIds].some((id) => !artifact.observable_ids.includes(id))) {
    throw new Error(`${field}.lesson observables must be provided by the artifact.`);
  }
  const signalObservables = [...lesson.success_signals, ...lesson.failure_signals]
    .flatMap((signal) => signal.observable_ids);
  if (signalObservables.some((id) => !lessonObservableIds.has(id))) {
    throw new Error(`${field}.lesson signal observables must be declared by the lesson.`);
  }
  if (lesson.narration_steps.some((step) => step.observable_ids.some((id) => !lessonObservableIds.has(id)))) {
    throw new Error(`${field}.lesson narration observables must be declared by the lesson.`);
  }
  if ((purpose === "failure_contrast" || purpose === "sensitivity")
      && (!lesson.misconception || lesson.failure_signals.length === 0)) {
    throw new Error(`${field}.lesson requires misconception and failure signals.`);
  }
  return {
    contract_version: "1.1.0",
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
    artifact,
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
  exact(data, [
    "learning_objective", "misconception", "expected_phenomenon_ja", "expected_phenomenon_en",
    "success_signals", "failure_signals", "primary_observables", "secondary_observables",
    "narration_steps", "comparison_role", "prerequisite_concept_ids",
    "recommended_next_scenario_ids", "known_reference_display", "static_summary",
    "text_alternative", "derived_media_caption", "limitations_ja", "limitations_en",
  ], field);
  const primaryObservables = list(data.primary_observables, `${field}.primary_observables`)
    .map((item, index) => parseObservable(item, `${field}.primary_observables[${index}]`));
  if (primaryObservables.length === 0) throw new Error(`${field}.primary_observables must not be empty.`);
  const secondaryObservables = list(data.secondary_observables, `${field}.secondary_observables`)
    .map((item, index) => parseObservable(item, `${field}.secondary_observables[${index}]`));
  const observableIds = [...primaryObservables, ...secondaryObservables].map((item) => item.observable_id);
  if (new Set(observableIds).size !== observableIds.length) throw new Error(`${field}.observable IDs must be unique.`);
  const successSignals = list(data.success_signals, `${field}.success_signals`)
    .map((item, index) => parseSignal(item, `${field}.success_signals[${index}]`));
  if (successSignals.length === 0) throw new Error(`${field}.success_signals must not be empty.`);
  const failureSignals = list(data.failure_signals, `${field}.failure_signals`)
    .map((item, index) => parseSignal(item, `${field}.failure_signals[${index}]`));
  const signalIds = [...successSignals, ...failureSignals].map((item) => item.signal_id);
  if (new Set(signalIds).size !== signalIds.length) throw new Error(`${field}.signal IDs must be unique.`);
  const narrationSteps = list(data.narration_steps, `${field}.narration_steps`)
    .map((item, index) => parseNarrationStep(item, `${field}.narration_steps[${index}]`));
  if (narrationSteps.length < 3
      || narrationSteps[0].milestone_id !== "start"
      || narrationSteps.at(-1)?.milestone_id !== "termination"
      || new Set(narrationSteps.map((item) => item.milestone_id)).size !== narrationSteps.length) {
    throw new Error(`${field}.narration_steps must use unique canonical milestones from start to termination.`);
  }
  const knownReference = record(data.known_reference_display, `${field}.known_reference_display`);
  exact(knownReference, ["policy", "note_ja", "note_en"], `${field}.known_reference_display`);
  const prerequisiteConceptIds = textList(data.prerequisite_concept_ids, `${field}.prerequisite_concept_ids`);
  const recommendedNextScenarioIds = textList(data.recommended_next_scenario_ids, `${field}.recommended_next_scenario_ids`);
  if (new Set(prerequisiteConceptIds).size !== prerequisiteConceptIds.length
      || new Set(recommendedNextScenarioIds).size !== recommendedNextScenarioIds.length) {
    throw new Error(`${field}.relation IDs must be unique.`);
  }
  return {
    learning_objective: parseLocalizedText(data.learning_objective, `${field}.learning_objective`),
    misconception: data.misconception === null
      ? null
      : parseLocalizedText(data.misconception, `${field}.misconception`),
    expected_phenomenon_ja: text(data.expected_phenomenon_ja, `${field}.expected_phenomenon_ja`),
    expected_phenomenon_en: text(data.expected_phenomenon_en, `${field}.expected_phenomenon_en`),
    success_signals: successSignals,
    failure_signals: failureSignals,
    primary_observables: primaryObservables,
    secondary_observables: secondaryObservables,
    narration_steps: narrationSteps,
    comparison_role: oneOf(data.comparison_role, comparisonRoles, `${field}.comparison_role`),
    prerequisite_concept_ids: prerequisiteConceptIds,
    recommended_next_scenario_ids: recommendedNextScenarioIds,
    known_reference_display: {
      policy: oneOf(knownReference.policy, knownReferencePolicies, `${field}.known_reference_display.policy`),
      note_ja: text(knownReference.note_ja, `${field}.known_reference_display.note_ja`),
      note_en: text(knownReference.note_en, `${field}.known_reference_display.note_en`),
    },
    static_summary: parseLocalizedText(data.static_summary, `${field}.static_summary`),
    text_alternative: parseLocalizedText(data.text_alternative, `${field}.text_alternative`),
    derived_media_caption: parseLocalizedText(data.derived_media_caption, `${field}.derived_media_caption`),
    limitations_ja: text(data.limitations_ja, `${field}.limitations_ja`),
    limitations_en: text(data.limitations_en, `${field}.limitations_en`),
  };
}

function parseLocalizedText(raw: unknown, field: string): LocalizedText {
  const data = record(raw, field);
  exact(data, ["ja", "en"], field);
  return { ja: text(data.ja, `${field}.ja`), en: text(data.en, `${field}.en`) };
}

function parseObservable(raw: unknown, field: string): VisualizationObservable {
  const data = record(raw, field);
  exact(data, ["observable_id", "label_ja", "label_en"], field);
  return {
    observable_id: text(data.observable_id, `${field}.observable_id`),
    label_ja: text(data.label_ja, `${field}.label_ja`),
    label_en: text(data.label_en, `${field}.label_en`),
  };
}

function parseSignal(raw: unknown, field: string): VisualizationSignal {
  const data = record(raw, field);
  exact(data, ["signal_id", "label_ja", "label_en", "observable_ids"], field);
  const observableIds = nonEmptyTextList(data.observable_ids, `${field}.observable_ids`);
  if (new Set(observableIds).size !== observableIds.length) throw new Error(`${field}.observable IDs must be unique.`);
  return {
    signal_id: text(data.signal_id, `${field}.signal_id`),
    label_ja: text(data.label_ja, `${field}.label_ja`),
    label_en: text(data.label_en, `${field}.label_en`),
    observable_ids: observableIds,
  };
}

function parseNarrationStep(raw: unknown, field: string): VisualizationNarrationStep {
  const data = record(raw, field);
  exact(data, ["milestone_id", "title_ja", "title_en", "observable_ids"], field);
  const observableIds = nonEmptyTextList(data.observable_ids, `${field}.observable_ids`);
  if (new Set(observableIds).size !== observableIds.length) throw new Error(`${field}.observable IDs must be unique.`);
  return {
    milestone_id: oneOf(data.milestone_id, narrationMilestones, `${field}.milestone_id`),
    title_ja: text(data.title_ja, `${field}.title_ja`),
    title_en: text(data.title_en, `${field}.title_en`),
    observable_ids: observableIds,
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
  const values = textList(value, field);
  if (values.length === 0) throw new Error(`${field} must not be empty.`);
  return values;
}
function textList(value: unknown, field: string): string[] {
  return list(value, field).map((item, index) => text(item, `${field}[${index}]`));
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
function scenarioVersion(value: unknown, field: string): asserts value is "1.1.0" {
  if (value !== "1.1.0") throw new Error(`${field} is unsupported.`);
}
function oneOf<T extends string>(value: unknown, values: ReadonlySet<T>, field: string): T {
  if (typeof value !== "string" || !values.has(value as T)) throw new Error(`${field} is invalid.`);
  return value as T;
}
function invalid(field: string): never {
  throw new Error(`${field} is invalid.`);
}
