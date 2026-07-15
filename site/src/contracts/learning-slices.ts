export interface FeasibleStep {
  step: number;
  point: [number, number];
  objective: number;
  constraint_value: number;
  violation: number;
  feasible: boolean;
  active_constraint: boolean;
  label_ja: string;
}

export interface FeasibleRegionArtifact {
  contract_version: "1.0.0";
  dataset_version: string;
  artifact_id: "constrained-disk-feasible-region";
  artifact_kind: "executable_trace";
  renderer_family: "feasible_region";
  problem_definition_id: "PROBLEM_CONSTRAINED_CONTINUOUS_2D";
  problem_instance_id: "INSTANCE_CONSTRAINED_DISK_2D";
  objective_direction: "minimize";
  objective_expression: string;
  bounds: { x: [number, number]; y: [number, number] };
  constraint: { constraint_id: string; kind: "disk"; center: [number, number]; radius: number; sense: "lte"; expression: string };
  contour_values: number[];
  known_reference: { point: [number, number]; value: number; active_constraints: string[]; source_ids: string[] };
  initial_point: [number, number];
  best_feasible_point: [number, number];
  active_constraint_id: string;
  paths: {
    path_id: string;
    method_id: string;
    label_ja: string;
    role: "constraint_aware" | "unconstrained_failure";
    execution_kind: "executable_teaching_trace";
    steps: FeasibleStep[];
    termination_reason_ja: string;
  }[];
  method_distinctions_ja: string[];
  text_alternative_ja: string;
  source_ids: string[];
  last_verified: string;
}

export interface ObjectivePoint {
  point_id: string;
  decision: [number, number];
  objectives: [number, number];
  dominated: boolean;
}

export interface ParetoFrontArtifact {
  contract_version: "1.0.0";
  dataset_version: string;
  artifact_id: "biobjective-quadratic-pareto-front";
  artifact_kind: "result_visualization";
  execution_status: "executable_result";
  renderer_family: "pareto_front";
  problem_definition_id: "PROBLEM_BIOBJECTIVE_CONTINUOUS";
  problem_instance_id: "INSTANCE_BIOBJECTIVE_QUADRATIC_2D";
  objective_directions: ["minimize", "minimize"];
  axis_labels: [string, string];
  points: ObjectivePoint[];
  pareto_front: ObjectivePoint[];
  preference_selections: { weight_f1: number; decision: [number, number]; objectives: [number, number] }[];
  reference: { ideal: [number, number]; nadir: [number, number]; ideal_is_feasible: boolean; status: "known_exact" };
  weighted_sum_limitation_ja: string;
  text_alternative_ja: string;
  source_ids: string[];
  last_verified: string;
}

export type LearningSliceArtifact = FeasibleRegionArtifact | ParetoFrontArtifact;

export function parseLearningSliceArtifact(raw: unknown): LearningSliceArtifact {
  const data = record(raw, "learning slice");
  if (data.renderer_family === "feasible_region") return parseFeasible(data);
  if (data.renderer_family === "pareto_front") return parsePareto(data);
  throw new Error(`Unsupported learning-slice renderer: ${String(data.renderer_family)}`);
}

function parseFeasible(data: Record<string, unknown>): FeasibleRegionArtifact {
  literal(data.contract_version, "1.0.0", "contract_version");
  literal(data.artifact_id, "constrained-disk-feasible-region", "artifact_id");
  literal(data.artifact_kind, "executable_trace", "artifact_kind");
  literal(data.renderer_family, "feasible_region", "renderer_family");
  literal(data.problem_definition_id, "PROBLEM_CONSTRAINED_CONTINUOUS_2D", "problem_definition_id");
  literal(data.problem_instance_id, "INSTANCE_CONSTRAINED_DISK_2D", "problem_instance_id");
  literal(data.objective_direction, "minimize", "objective_direction");
  const bounds = record(data.bounds, "bounds");
  const constraint = record(data.constraint, "constraint");
  literal(constraint.kind, "disk", "constraint.kind");
  literal(constraint.sense, "lte", "constraint.sense");
  const known = record(data.known_reference, "known_reference");
  const paths = list(data.paths, "paths").map((rawPath, pathIndex) => {
    const path = record(rawPath, `paths[${pathIndex}]`);
    const role: FeasibleRegionArtifact["paths"][number]["role"] = path.role === "constraint_aware" || path.role === "unconstrained_failure"
      ? path.role
      : invalid("path.role");
    literal(path.execution_kind, "executable_teaching_trace", "path.execution_kind");
    const steps = list(path.steps, "path.steps").map((rawStep, index) => {
      const step = record(rawStep, `steps[${index}]`);
      return {
        step: integer(step.step, "step"), point: pair(step.point, "point"), objective: number(step.objective, "objective"),
        constraint_value: number(step.constraint_value, "constraint_value"), violation: nonNegative(step.violation, "violation"),
        feasible: boolean(step.feasible, "feasible"), active_constraint: boolean(step.active_constraint, "active_constraint"),
        label_ja: text(step.label_ja, "label_ja"),
      };
    });
    if (steps.length < 2) throw new Error("path.steps must contain at least two steps.");
    return { path_id: text(path.path_id, "path_id"), method_id: text(path.method_id, "method_id"), label_ja: text(path.label_ja, "label_ja"), role, execution_kind: "executable_teaching_trace" as const, steps, termination_reason_ja: text(path.termination_reason_ja, "termination_reason_ja") };
  });
  if (new Set(paths.map((path) => path.role)).size !== 2) throw new Error("both feasible-region path roles are required.");
  return {
    contract_version: "1.0.0", dataset_version: text(data.dataset_version, "dataset_version"), artifact_id: "constrained-disk-feasible-region",
    artifact_kind: "executable_trace", renderer_family: "feasible_region", problem_definition_id: "PROBLEM_CONSTRAINED_CONTINUOUS_2D",
    problem_instance_id: "INSTANCE_CONSTRAINED_DISK_2D", objective_direction: "minimize", objective_expression: text(data.objective_expression, "objective_expression"),
    bounds: { x: pair(bounds.x, "bounds.x"), y: pair(bounds.y, "bounds.y") },
    constraint: { constraint_id: text(constraint.constraint_id, "constraint_id"), kind: "disk", center: pair(constraint.center, "constraint.center"), radius: positive(constraint.radius, "constraint.radius"), sense: "lte", expression: text(constraint.expression, "constraint.expression") },
    contour_values: numbers(data.contour_values, "contour_values"),
    known_reference: { point: pair(known.point, "known_reference.point"), value: number(known.value, "known_reference.value"), active_constraints: texts(known.active_constraints, "known_reference.active_constraints"), source_ids: texts(known.source_ids, "known_reference.source_ids") },
    initial_point: pair(data.initial_point, "initial_point"), best_feasible_point: pair(data.best_feasible_point, "best_feasible_point"), active_constraint_id: text(data.active_constraint_id, "active_constraint_id"),
    paths, method_distinctions_ja: texts(data.method_distinctions_ja, "method_distinctions_ja"), text_alternative_ja: text(data.text_alternative_ja, "text_alternative_ja"), source_ids: texts(data.source_ids, "source_ids"), last_verified: text(data.last_verified, "last_verified"),
  };
}

function parsePareto(data: Record<string, unknown>): ParetoFrontArtifact {
  literal(data.contract_version, "1.0.0", "contract_version");
  literal(data.artifact_id, "biobjective-quadratic-pareto-front", "artifact_id");
  literal(data.artifact_kind, "result_visualization", "artifact_kind");
  literal(data.execution_status, "executable_result", "execution_status");
  literal(data.renderer_family, "pareto_front", "renderer_family");
  literal(data.problem_definition_id, "PROBLEM_BIOBJECTIVE_CONTINUOUS", "problem_definition_id");
  literal(data.problem_instance_id, "INSTANCE_BIOBJECTIVE_QUADRATIC_2D", "problem_instance_id");
  const directions = texts(data.objective_directions, "objective_directions");
  if (directions.length !== 2 || directions.some((value) => value !== "minimize")) throw new Error("objective directions are invalid.");
  const axisLabels = texts(data.axis_labels, "axis_labels");
  if (axisLabels.length !== 2) throw new Error("axis_labels must contain two labels.");
  const point = (raw: unknown, owner: string): ObjectivePoint => {
    const value = record(raw, owner);
    return { point_id: text(value.point_id, `${owner}.point_id`), decision: pair(value.decision, `${owner}.decision`), objectives: pair(value.objectives, `${owner}.objectives`), dominated: boolean(value.dominated, `${owner}.dominated`) };
  };
  const points = list(data.points, "points").map((item, index) => point(item, `points[${index}]`));
  const paretoFront = list(data.pareto_front, "pareto_front").map((item, index) => point(item, `pareto_front[${index}]`));
  if (paretoFront.some((item) => item.dominated)) throw new Error("pareto_front contains a dominated point.");
  const preferences = list(data.preference_selections, "preference_selections").map((raw, index) => {
    const value = record(raw, `preference_selections[${index}]`);
    const weight = number(value.weight_f1, "weight_f1");
    if (weight < 0 || weight > 1) throw new Error("weight_f1 must be between zero and one.");
    return { weight_f1: weight, decision: pair(value.decision, "decision"), objectives: pair(value.objectives, "objectives") };
  });
  const reference = record(data.reference, "reference");
  literal(reference.status, "known_exact", "reference.status");
  return {
    contract_version: "1.0.0", dataset_version: text(data.dataset_version, "dataset_version"), artifact_id: "biobjective-quadratic-pareto-front",
    artifact_kind: "result_visualization", execution_status: "executable_result", renderer_family: "pareto_front", problem_definition_id: "PROBLEM_BIOBJECTIVE_CONTINUOUS", problem_instance_id: "INSTANCE_BIOBJECTIVE_QUADRATIC_2D",
    objective_directions: ["minimize", "minimize"], axis_labels: [axisLabels[0], axisLabels[1]], points, pareto_front: paretoFront, preference_selections: preferences,
    reference: { ideal: pair(reference.ideal, "reference.ideal"), nadir: pair(reference.nadir, "reference.nadir"), ideal_is_feasible: boolean(reference.ideal_is_feasible, "reference.ideal_is_feasible"), status: "known_exact" },
    weighted_sum_limitation_ja: text(data.weighted_sum_limitation_ja, "weighted_sum_limitation_ja"), text_alternative_ja: text(data.text_alternative_ja, "text_alternative_ja"), source_ids: texts(data.source_ids, "source_ids"), last_verified: text(data.last_verified, "last_verified"),
  };
}

function record(value: unknown, owner: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`); return value as Record<string, unknown>; }
function list(value: unknown, owner: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`); return value; }
function text(value: unknown, owner: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${owner} must be non-empty.`); return value; }
function texts(value: unknown, owner: string): string[] { return list(value, owner).map((item, index) => text(item, `${owner}[${index}]`)); }
function number(value: unknown, owner: string): number { if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${owner} must be finite.`); return value; }
function numbers(value: unknown, owner: string): number[] { return list(value, owner).map((item) => number(item, owner)); }
function positive(value: unknown, owner: string): number { const result = number(value, owner); if (result <= 0) throw new Error(`${owner} must be positive.`); return result; }
function nonNegative(value: unknown, owner: string): number { const result = number(value, owner); if (result < 0) throw new Error(`${owner} must be non-negative.`); return result; }
function integer(value: unknown, owner: string): number { const result = number(value, owner); if (!Number.isSafeInteger(result) || result < 0) throw new Error(`${owner} must be a non-negative integer.`); return result; }
function boolean(value: unknown, owner: string): boolean { if (typeof value !== "boolean") throw new Error(`${owner} must be boolean.`); return value; }
function pair(value: unknown, owner: string): [number, number] { const result = numbers(value, owner); if (result.length !== 2) throw new Error(`${owner} must contain two values.`); return [result[0], result[1]]; }
function literal(value: unknown, expected: string, owner: string): void { if (value !== expected) throw new Error(`${owner} must be ${expected}.`); }
function invalid(owner: string): never { throw new Error(`${owner} is invalid.`); }
