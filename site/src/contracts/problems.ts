export type ObjectiveDirection = "minimize" | "maximize" | "multiobjective";
export type KnownReferenceStatus = "known_exact" | "known_reference" | "best_known" | "unknown" | "not_meaningful";

export interface ProblemDefinition {
  problem_definition_id: string;
  name_ja: string;
  name_en: string;
  mathematical_family: string;
  variable_domain: string;
  objective_form: string;
  objective_direction: ObjectiveDirection;
  available_oracles: string[];
  constraint_class: string;
  dimensionality_policy: Record<string, unknown>;
  known_reference_semantics: string;
  related_problem_ids: string[];
  feature_ids: string[];
  source_ids: string[];
  last_verified: string;
}

export interface ProblemInstance {
  problem_instance_id: string;
  problem_definition_id: string;
  name_ja: string;
  name_en: string;
  registry_key: string;
  dimension: number;
  parameters: Record<string, unknown>;
  bounds: Record<string, unknown>;
  constraints: Record<string, unknown>[];
  initialization_candidates: Record<string, unknown>[];
  seed_status: "fixed" | "not_applicable" | "unknown";
  seed_value: number | null;
  known_reference_status: KnownReferenceStatus;
  known_reference: Record<string, unknown> | null;
  display: Record<string, unknown>;
  intended_phenomena: string[];
  limitations_ja: string;
  limitations_en: string;
  source_ids: string[];
  last_verified: string;
}

export interface ProblemCatalog {
  contract_version: "1.0.0";
  dataset_version: string;
  definitions: ProblemDefinition[];
  instances: ProblemInstance[];
}

export function parseProblemCatalog(input: unknown): ProblemCatalog {
  const data = record(input, "ProblemCatalog");
  exact(data, ["contract_version", "dataset_version", "definitions", "instances"], "ProblemCatalog");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported ProblemCatalog version.");
  const definitions = array(data.definitions, "definitions").map(parseDefinition);
  const instances = array(data.instances, "instances").map(parseInstance);
  if (definitions.length === 0 || instances.length === 0) throw new Error("ProblemCatalog collections must not be empty.");
  const definitionIds = unique(definitions.map((item) => item.problem_definition_id), "definition");
  unique(instances.map((item) => item.problem_instance_id), "instance");
  unique(instances.map((item) => item.registry_key), "registry key");
  for (const instance of instances) {
    if (!definitionIds.has(instance.problem_definition_id)) throw new Error(`Unknown problem definition: ${instance.problem_definition_id}.`);
  }
  return { contract_version: "1.0.0", dataset_version: text(data.dataset_version, "dataset_version"), definitions, instances };
}

function parseDefinition(value: unknown, index: number): ProblemDefinition {
  const field = `definitions[${index}]`; const data = record(value, field);
  exact(data, ["problem_definition_id", "name_ja", "name_en", "mathematical_family", "variable_domain", "objective_form", "objective_direction", "available_oracles", "constraint_class", "dimensionality_policy", "known_reference_semantics", "related_problem_ids", "feature_ids", "source_ids", "last_verified"], field);
  if (!isDirection(data.objective_direction)) throw new Error(`${field}.objective_direction is invalid.`);
  return {
    problem_definition_id: text(data.problem_definition_id, `${field}.problem_definition_id`), name_ja: text(data.name_ja, `${field}.name_ja`), name_en: text(data.name_en, `${field}.name_en`), mathematical_family: text(data.mathematical_family, `${field}.mathematical_family`), variable_domain: text(data.variable_domain, `${field}.variable_domain`), objective_form: text(data.objective_form, `${field}.objective_form`), objective_direction: data.objective_direction, available_oracles: texts(data.available_oracles, `${field}.available_oracles`), constraint_class: text(data.constraint_class, `${field}.constraint_class`), dimensionality_policy: record(data.dimensionality_policy, `${field}.dimensionality_policy`), known_reference_semantics: text(data.known_reference_semantics, `${field}.known_reference_semantics`), related_problem_ids: texts(data.related_problem_ids, `${field}.related_problem_ids`), feature_ids: texts(data.feature_ids, `${field}.feature_ids`), source_ids: texts(data.source_ids, `${field}.source_ids`), last_verified: text(data.last_verified, `${field}.last_verified`),
  };
}

function parseInstance(value: unknown, index: number): ProblemInstance {
  const field = `instances[${index}]`; const data = record(value, field);
  exact(data, ["problem_instance_id", "problem_definition_id", "name_ja", "name_en", "registry_key", "dimension", "parameters", "bounds", "constraints", "initialization_candidates", "seed_status", "seed_value", "known_reference_status", "known_reference", "display", "intended_phenomena", "limitations_ja", "limitations_en", "source_ids", "last_verified"], field);
  if (!isSeedStatus(data.seed_status)) throw new Error(`${field}.seed_status is invalid.`);
  if (!isReferenceStatus(data.known_reference_status)) throw new Error(`${field}.known_reference_status is invalid.`);
  const dimension = integer(data.dimension, `${field}.dimension`); const seedValue = nullableInteger(data.seed_value, `${field}.seed_value`);
  if ((data.seed_status === "fixed") !== (seedValue !== null)) throw new Error(`${field} fixed seed is inconsistent.`);
  const knownReference = data.known_reference === null ? null : record(data.known_reference, `${field}.known_reference`);
  const needsReference = ["known_exact", "known_reference", "best_known"].includes(data.known_reference_status);
  if (needsReference !== (knownReference !== null)) throw new Error(`${field} known reference is inconsistent.`);
  return {
    problem_instance_id: text(data.problem_instance_id, `${field}.problem_instance_id`), problem_definition_id: text(data.problem_definition_id, `${field}.problem_definition_id`), name_ja: text(data.name_ja, `${field}.name_ja`), name_en: text(data.name_en, `${field}.name_en`), registry_key: text(data.registry_key, `${field}.registry_key`), dimension, parameters: record(data.parameters, `${field}.parameters`), bounds: record(data.bounds, `${field}.bounds`), constraints: records(data.constraints, `${field}.constraints`), initialization_candidates: records(data.initialization_candidates, `${field}.initialization_candidates`), seed_status: data.seed_status, seed_value: seedValue, known_reference_status: data.known_reference_status, known_reference: knownReference, display: record(data.display, `${field}.display`), intended_phenomena: texts(data.intended_phenomena, `${field}.intended_phenomena`), limitations_ja: text(data.limitations_ja, `${field}.limitations_ja`), limitations_en: text(data.limitations_en, `${field}.limitations_en`), source_ids: texts(data.source_ids, `${field}.source_ids`), last_verified: text(data.last_verified, `${field}.last_verified`),
  };
}

function isDirection(value: unknown): value is ObjectiveDirection { return value === "minimize" || value === "maximize" || value === "multiobjective"; }
function isSeedStatus(value: unknown): value is ProblemInstance["seed_status"] { return value === "fixed" || value === "not_applicable" || value === "unknown"; }
function isReferenceStatus(value: unknown): value is KnownReferenceStatus { return value === "known_exact" || value === "known_reference" || value === "best_known" || value === "unknown" || value === "not_meaningful"; }
function record(value: unknown, field: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function records(value: unknown, field: string): Record<string, unknown>[] { return array(value, field).map((item, index) => record(item, `${field}[${index}]`)); }
function text(value: unknown, field: string): string { if (typeof value !== "string" || value.trim() === "") throw new Error(`${field} must be non-empty.`); return value; }
function texts(value: unknown, field: string): string[] { const result = array(value, field).map((item, index) => text(item, `${field}[${index}]`)); if (result.length === 0) throw new Error(`${field} must not be empty.`); unique(result, field); return result; }
function integer(value: unknown, field: string): number { if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 1) throw new Error(`${field} must be a positive integer.`); return value; }
function nullableInteger(value: unknown, field: string): number | null { if (value === null) return null; if (typeof value !== "number" || !Number.isSafeInteger(value)) throw new Error(`${field} must be an integer or null.`); return value; }
function unique(values: string[], field: string): Set<string> { const result = new Set(values); if (result.size !== values.length) throw new Error(`Duplicate ${field}.`); return result; }
function exact(data: Record<string, unknown>, expected: readonly string[], field: string): void { const allowed = new Set(expected); const unknown = Object.keys(data).filter((key) => !allowed.has(key)); const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key)); if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`); if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`); }
