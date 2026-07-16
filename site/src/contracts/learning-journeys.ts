export type JourneyStatus = "complete" | "partial" | "draft";
export type JourneyScenarioRole = "primary" | "failure_contrast" | "sensitivity" | "alternate";
export type JourneyDimensionState = "complete" | "missing" | "not_applicable" | "broken";
export type JourneyOrphanPolicy = "standalone" | "warning" | "error";

export const journeyDimensionNames = [
  "formulation", "canonical_problem_instance", "primary_scenario", "alternate_scenario",
  "canonical_comparison", "method_roles", "implementation", "source_review",
  "terminology_prerequisite", "static_text_alternative", "cross_surface_links",
  "route_reachability", "validation_status",
] as const;
export type JourneyDimensionName = typeof journeyDimensionNames[number];

export interface LearningJourney {
  journey_id: string;
  case_id: string;
  dataset_version: string;
  canonical_url: string;
  title_ja: string;
  title_en: string;
  domain: string;
  status: JourneyStatus;
  completion_reasons: string[];
  problem_archetype_id: string;
  problem_instance_ids: string[];
  formulation: {
    variable_domain_summary: string;
    decision_variables: string;
    objective: string;
    constraints: string;
  };
  scenarios: {
    scenario_id: string;
    role: JourneyScenarioRole;
    canonical_url: string;
    problem_definition_id: string;
    problem_instance_id: string;
  }[];
  comparisons: { comparison_id: string; canonical_url: string }[];
  candidate_method_ids: string[];
  conditional_method_ids: string[];
  excluded_method_ids: string[];
  implementation_ids: string[];
  content_ids: string[];
  learning_objective: string;
  prerequisite_journey_ids: string[];
  takeaway: string;
  limitations: string[];
  source_ids: string[];
  last_reviewed: string;
}

export interface LearningJourneyIndex {
  contract_version: "1.1.0";
  dataset_version: string;
  generated_at: string;
  summary: {
    target_complete_journeys: 5;
    total_journeys: number;
    status_counts: Record<JourneyStatus, number>;
    milestone_status: "met" | "not_met";
  };
  journeys: LearningJourney[];
  assessments: Array<{
    journey_id: string;
    status: JourneyStatus;
    dimensions: Record<JourneyDimensionName, { state: JourneyDimensionState; target_ids: string[]; reason_codes: string[] }>;
    missing_dimensions: JourneyDimensionName[];
  }>;
  orphan_assets: Array<{
    asset_type: "scenario" | "comparison" | "visualization_artifact" | "content";
    asset_id: string;
    policy: JourneyOrphanPolicy;
    reason_code: string;
  }>;
}

export function parseLearningJourneyIndex(raw: unknown): LearningJourneyIndex {
  const data = record(raw, "learning journey index");
  exactKeys(data, ["contract_version", "dataset_version", "generated_at", "summary", "journeys", "assessments", "orphan_assets"], "learning journey index");
  if (data.contract_version !== "1.1.0") throw new Error("Unsupported learning journey contract.");
  const datasetVersion = nonEmpty(data.dataset_version, "dataset_version");
  const summary = parseSummary(data.summary);
  const journeys = array(data.journeys, "journeys").map((value, index) => parseJourney(value, index));
  const ids = new Set<string>();
  for (const journey of journeys) {
    if (ids.has(journey.journey_id)) throw new Error(`Duplicate journey ID: ${journey.journey_id}.`);
    ids.add(journey.journey_id);
    if (journey.dataset_version !== datasetVersion) throw new Error("Journey dataset version does not match the index.");
  }
  for (const journey of journeys) {
    const missing = journey.prerequisite_journey_ids.filter((id) => !ids.has(id));
    if (missing.length > 0) throw new Error(`Journey has missing prerequisites: ${missing.join(", ")}.`);
  }
  validateAcyclic(journeys);
  const assessments = array(data.assessments, "assessments").map(parseAssessment);
  if (new Set(assessments.map((item) => item.journey_id)).size !== assessments.length) throw new Error("Journey assessment IDs must be unique.");
  if (assessments.length !== journeys.length || assessments.some((assessment) => !ids.has(assessment.journey_id))) throw new Error("Every journey needs one assessment.");
  const statusByJourney = new Map(journeys.map((journey) => [journey.journey_id, journey.status]));
  if (assessments.some((assessment) => statusByJourney.get(assessment.journey_id) !== assessment.status)) throw new Error("Journey assessment status must match journey status.");
  const assessmentByJourney = new Map(assessments.map((assessment) => [assessment.journey_id, assessment]));
  for (const journey of journeys) {
    const assessment = assessmentByJourney.get(journey.journey_id);
    if (!assessment) throw new Error("Every journey needs one assessment.");
    const expectedReasons = [...new Set([
      ...Object.values(assessment.dimensions).flatMap((dimension) => dimension.reason_codes),
      ...(journey.status === "draft" ? ["case_is_draft"] : []),
    ])].sort();
    if (journey.completion_reasons.join("|") !== expectedReasons.join("|")) throw new Error("Journey completion reasons must match its assessment.");
  }
  if (summary.total_journeys !== journeys.length) throw new Error("Journey summary total must match journeys.");
  const actualCounts = { complete: 0, partial: 0, draft: 0 } satisfies Record<JourneyStatus, number>;
  journeys.forEach((journey) => { actualCounts[journey.status] += 1; });
  if ((Object.keys(actualCounts) as JourneyStatus[]).some((status) => actualCounts[status] !== summary.status_counts[status])) throw new Error("Journey summary counts must match journeys.");
  const orphanAssets = array(data.orphan_assets, "orphan_assets").map((value, index) => {
    const row = record(value, `orphan_assets[${index}]`);
    exactKeys(row, ["asset_type", "asset_id", "policy", "reason_code"], `orphan_assets[${index}]`);
    return {
      asset_type: enumValue(row.asset_type, ["scenario", "comparison", "visualization_artifact", "content"] as const, "asset_type"),
      asset_id: nonEmpty(row.asset_id, "asset_id"),
      policy: enumValue(row.policy, ["standalone", "warning", "error"] as const, "policy"),
      reason_code: nonEmpty(row.reason_code, "reason_code"),
    };
  });
  if (new Set(orphanAssets.map((item) => `${item.asset_type}:${item.asset_id}`)).size !== orphanAssets.length) throw new Error("Orphan assets must be unique.");
  if (orphanAssets.some((item) => item.policy === "error")) throw new Error("Error-policy orphan assets cannot be published.");
  return {
    contract_version: "1.1.0",
    dataset_version: datasetVersion,
    generated_at: nonEmpty(data.generated_at, "generated_at"),
    summary,
    journeys,
    assessments,
    orphan_assets: orphanAssets,
  };
}

function parseSummary(value: unknown): LearningJourneyIndex["summary"] {
  const data = record(value, "summary");
  exactKeys(data, ["target_complete_journeys", "total_journeys", "status_counts", "milestone_status"], "summary");
  if (data.target_complete_journeys !== 5) throw new Error("Journey target must be five.");
  const counts = record(data.status_counts, "status_counts");
  exactKeys(counts, ["complete", "partial", "draft"], "status_counts");
  const statusCounts = {
    complete: integer(counts.complete, "complete", 0),
    partial: integer(counts.partial, "partial", 0),
    draft: integer(counts.draft, "draft", 0),
  };
  const totalJourneys = integer(data.total_journeys, "total_journeys", 0);
  if (Object.values(statusCounts).reduce((sum, count) => sum + count, 0) !== totalJourneys) throw new Error("Journey counts must equal total.");
  const milestoneStatus = enumValue(data.milestone_status, ["met", "not_met"] as const, "milestone_status");
  if (milestoneStatus !== (statusCounts.complete >= 5 ? "met" : "not_met")) throw new Error("Journey milestone must be derived from count.");
  return { target_complete_journeys: 5, total_journeys: totalJourneys, status_counts: statusCounts, milestone_status: milestoneStatus };
}

function parseAssessment(value: unknown, index: number): LearningJourneyIndex["assessments"][number] {
  const field = `assessments[${index}]`;
  const data = record(value, field);
  exactKeys(data, ["journey_id", "status", "dimensions", "missing_dimensions"], field);
  const dimensions = record(data.dimensions, `${field}.dimensions`);
  exactKeys(dimensions, journeyDimensionNames, `${field}.dimensions`);
  const parsedDimensions = Object.fromEntries(journeyDimensionNames.map((name) => {
    const dimension = record(dimensions[name], `${field}.dimensions.${name}`);
    exactKeys(dimension, ["state", "target_ids", "reason_codes"], `${field}.dimensions.${name}`);
    const state = enumValue(dimension.state, ["complete", "missing", "not_applicable", "broken"] as const, `${name}.state`);
    const reasonCodes = uniqueStrings(dimension.reason_codes, `${name}.reason_codes`);
    if (state === "complete" && reasonCodes.length > 0) throw new Error("Complete dimensions cannot have reason codes.");
    if (["missing", "broken"].includes(state) && reasonCodes.length === 0) throw new Error("Missing and broken dimensions require reason codes.");
    return [name, {
      state,
      target_ids: uniqueStrings(dimension.target_ids, `${name}.target_ids`),
      reason_codes: reasonCodes,
    }];
  })) as LearningJourneyIndex["assessments"][number]["dimensions"];
  const missingDimensions = uniqueStrings(data.missing_dimensions, `${field}.missing_dimensions`).map((name) => enumValue(name, journeyDimensionNames, "missing_dimension"));
  const expectedMissing = journeyDimensionNames.filter((name) => ["missing", "broken"].includes(parsedDimensions[name].state)).sort();
  if (missingDimensions.join("|") !== expectedMissing.join("|")) throw new Error("Missing dimensions must be derived from states.");
  const status = enumValue(data.status, ["complete", "partial", "draft"] as const, `${field}.status`);
  if (status === "complete" && missingDimensions.length > 0) throw new Error("Complete journey cannot have missing dimensions.");
  if (status === "partial" && missingDimensions.length === 0) throw new Error("Partial journey must have missing dimensions.");
  return { journey_id: nonEmpty(data.journey_id, `${field}.journey_id`), status, dimensions: parsedDimensions, missing_dimensions: missingDimensions };
}

function parseJourney(value: unknown, index: number): LearningJourney {
  const field = `journeys[${index}]`;
  const data = record(value, field);
  exactKeys(data, [
    "journey_id", "case_id", "dataset_version", "canonical_url", "title_ja", "title_en", "domain",
    "status", "completion_reasons", "problem_archetype_id", "problem_instance_ids", "formulation",
    "scenarios", "comparisons", "candidate_method_ids", "conditional_method_ids", "excluded_method_ids",
    "implementation_ids", "content_ids", "learning_objective", "prerequisite_journey_ids", "takeaway",
    "limitations", "source_ids", "last_reviewed",
  ], field);
  const journeyId = nonEmpty(data.journey_id, `${field}.journey_id`);
  const caseId = nonEmpty(data.case_id, `${field}.case_id`);
  if (journeyId !== caseId) throw new Error("journey_id must equal case_id.");
  const canonicalUrl = route(data.canonical_url, `${field}.canonical_url`);
  if (canonicalUrl !== `/gallery/${caseId}`) throw new Error("Journey route must be generated from case_id.");
  const status = enumValue(data.status, ["complete", "partial", "draft"] as const, `${field}.status`);
  const formulation = record(data.formulation, `${field}.formulation`);
  exactKeys(formulation, ["variable_domain_summary", "decision_variables", "objective", "constraints"], `${field}.formulation`);
  const scenarios = array(data.scenarios, `${field}.scenarios`).map((value, scenarioIndex) => {
    const row = record(value, `${field}.scenarios[${scenarioIndex}]`);
    exactKeys(row, ["scenario_id", "role", "canonical_url", "problem_definition_id", "problem_instance_id"], `${field}.scenarios[${scenarioIndex}]`);
    return {
      scenario_id: nonEmpty(row.scenario_id, "scenario_id"),
      role: enumValue(row.role, ["primary", "failure_contrast", "sensitivity", "alternate"] as const, "role"),
      canonical_url: route(row.canonical_url, "canonical_url"),
      problem_definition_id: nonEmpty(row.problem_definition_id, "problem_definition_id"),
      problem_instance_id: nonEmpty(row.problem_instance_id, "problem_instance_id"),
    };
  });
  const comparisons = array(data.comparisons, `${field}.comparisons`).map((value, comparisonIndex) => {
    const row = record(value, `${field}.comparisons[${comparisonIndex}]`);
    exactKeys(row, ["comparison_id", "canonical_url"], `${field}.comparisons[${comparisonIndex}]`);
    return { comparison_id: nonEmpty(row.comparison_id, "comparison_id"), canonical_url: route(row.canonical_url, "canonical_url") };
  });
  if (new Set(scenarios.map((item) => item.scenario_id)).size !== scenarios.length) throw new Error("Journey scenario IDs must be unique.");
  if (new Set(comparisons.map((item) => item.comparison_id)).size !== comparisons.length) throw new Error("Journey comparison IDs must be unique.");
  if (status === "complete" && (scenarios.filter((item) => item.role === "primary").length !== 1 || comparisons.length === 0)) throw new Error("Complete journey is incomplete.");
  return {
    journey_id: journeyId,
    case_id: caseId,
    dataset_version: nonEmpty(data.dataset_version, `${field}.dataset_version`),
    canonical_url: canonicalUrl,
    title_ja: nonEmpty(data.title_ja, `${field}.title_ja`),
    title_en: nonEmpty(data.title_en, `${field}.title_en`),
    domain: nonEmpty(data.domain, `${field}.domain`),
    status,
    completion_reasons: uniqueStrings(data.completion_reasons, "completion_reasons"),
    problem_archetype_id: nonEmpty(data.problem_archetype_id, "problem_archetype_id"),
    problem_instance_ids: uniqueStrings(data.problem_instance_ids, "problem_instance_ids"),
    formulation: {
      variable_domain_summary: nonEmpty(formulation.variable_domain_summary, "variable_domain_summary"),
      decision_variables: nonEmpty(formulation.decision_variables, "decision_variables"),
      objective: nonEmpty(formulation.objective, "objective"),
      constraints: nonEmpty(formulation.constraints, "constraints"),
    },
    scenarios,
    comparisons,
    candidate_method_ids: uniqueStrings(data.candidate_method_ids, "candidate_method_ids"),
    conditional_method_ids: uniqueStrings(data.conditional_method_ids, "conditional_method_ids"),
    excluded_method_ids: uniqueStrings(data.excluded_method_ids, "excluded_method_ids"),
    implementation_ids: uniqueStrings(data.implementation_ids, "implementation_ids"),
    content_ids: uniqueStrings(data.content_ids, "content_ids"),
    learning_objective: nonEmpty(data.learning_objective, "learning_objective"),
    prerequisite_journey_ids: uniqueStrings(data.prerequisite_journey_ids, "prerequisite_journey_ids"),
    takeaway: nonEmpty(data.takeaway, "takeaway"),
    limitations: uniqueStrings(data.limitations, "limitations"),
    source_ids: uniqueStrings(data.source_ids, "source_ids"),
    last_reviewed: date(data.last_reviewed, "last_reviewed"),
  };
}

function validateAcyclic(journeys: LearningJourney[]): void {
  const graph = new Map(journeys.map((journey) => [journey.journey_id, journey.prerequisite_journey_ids]));
  const visiting = new Set<string>(); const visited = new Set<string>();
  const visit = (id: string): void => {
    if (visiting.has(id)) throw new Error(`Circular journey prerequisite: ${id}.`);
    if (visited.has(id)) return;
    visiting.add(id); for (const dependency of graph.get(id) ?? []) visit(dependency); visiting.delete(id); visited.add(id);
  };
  for (const id of graph.keys()) visit(id);
}

function record(value: unknown, field: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function nonEmpty(value: unknown, field: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`); return value; }
function uniqueStrings(value: unknown, field: string): string[] { const values = array(value, field).map((item, index) => nonEmpty(item, `${field}[${index}]`)); if (new Set(values).size !== values.length) throw new Error(`${field} must be unique.`); return values; }
function integer(value: unknown, field: string, min: number): number { if (typeof value !== "number" || !Number.isSafeInteger(value) || value < min) throw new Error(`${field} must be an integer >= ${min}.`); return value; }
function route(value: unknown, field: string): string { const result = nonEmpty(value, field); if (!/^\/[A-Za-z0-9._/-]+$/u.test(result) || result.includes("//")) throw new Error(`${field} must be a safe route.`); return result; }
function date(value: unknown, field: string): string { const result = nonEmpty(value, field); if (!/^\d{4}-\d{2}-\d{2}$/u.test(result)) throw new Error(`${field} must be a date.`); return result; }
function enumValue<const T extends readonly string[]>(value: unknown, values: T, field: string): T[number] { const result = nonEmpty(value, field); if (!values.includes(result)) throw new Error(`${field} is unsupported.`); return result as T[number]; }
function exactKeys(data: Record<string, unknown>, expected: readonly string[], field: string): void { const keys = new Set(expected); const unknown = Object.keys(data).filter((key) => !keys.has(key)); const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key)); if (unknown.length > 0) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`); if (missing.length > 0) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`); }
