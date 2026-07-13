export type AnswerType = "single_choice" | "multi_choice";
export type ActionType =
  | "promote_method"
  | "exclude_method"
  | "recommend_alternative"
  | "include_problem"
  | "ask_followup"
  | "warn";
export type TargetType = "method" | "alternative" | "problem" | "feature";
export type Priority = "high" | "medium" | "candidate" | "none";

export interface SiteChoice { value: string; label_ja: string; label_en: string }
export interface SiteQuestion {
  question_id: string; sequence: number; question_ja: string; question_en: string;
  beginner_wording: string; answer_type: AnswerType; allowed_answers: string[];
  choices: SiteChoice[]; mapped_feature_id: string; why_asked: string;
  required: boolean; confidence: string; source_ids: string[];
}
export interface SiteRule {
  rule_id: string; question_id: string; answer_condition: string; action_type: ActionType;
  action_target_type: TargetType; action_target_ids: string[]; priority_effect: Priority;
  explanation: string; warnings: string; source_ids: string[];
}
export interface SiteMethod {
  method_id: string; name_ja: string; name_en: string; summary: string;
  variable_types: string; solution_scope: string; optimality_certificate: string;
  exactness: string; reference_source_ids: string[];
}
export interface SiteImplementation {
  implementation_id: string; library_name: string; solver_name: string; language: string;
  license: string; maintenance_status: string; last_release: string;
  official_docs_url: string; official_repo_url: string; notes: string;
}
export interface SiteMethodImplementation {
  method_id: string; implementation_id: string; support_level: string;
  implementation_notes: string;
}
export interface SiteAlternative {
  alternative_id: string; name_ja: string; name_en: string;
  why_before_generic_optimization: string; preferred_approach: string;
  false_positive_warning: string; source_ids: string[];
}
export interface SiteProblem {
  problem_id: string; name_ja: string; name_en: string; summary: string; source_ids: string[];
}
export interface SiteFeature {
  feature_id: string; name_ja: string; name_en: string; definition: string; source_ids: string[];
}
export interface SiteFeatureValue {
  feature_id: string; value_code: string; label_ja: string; label_en: string; sort_order: number;
}
export interface SiteSource { source_id: string; title: string; supported_claim: string; url: string }
export interface SiteData {
  contract_version: "1.0.0"; dataset_version: string; generated_at: string;
  questions: SiteQuestion[]; rules: SiteRule[]; methods: SiteMethod[];
  implementations: SiteImplementation[]; method_implementation_map: SiteMethodImplementation[];
  alternatives: SiteAlternative[]; problems: SiteProblem[]; features: SiteFeature[];
  feature_values: SiteFeatureValue[]; sources: SiteSource[];
}

type Row = Record<string, unknown>;
const ACTIONS = new Set<ActionType>([
  "promote_method", "exclude_method", "recommend_alternative", "include_problem",
  "ask_followup", "warn",
]);
const TARGETS = new Set<TargetType>(["method", "alternative", "problem", "feature"]);
const PRIORITIES = new Set<Priority>(["high", "medium", "candidate", "none"]);

function row(value: unknown, owner: string): Row {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`SiteData ${owner} must be an object.`);
  }
  return value as Row;
}
function exactKeys(value: Row, expected: readonly string[], owner: string): void {
  const allowed = new Set(expected);
  const extras = Object.keys(value).filter((key) => !allowed.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(value, key));
  if (extras.length || missing.length) {
    throw new Error(`SiteData ${owner} fields mismatch; missing=${missing.join(",")}, extra=${extras.join(",")}.`);
  }
}
function string(value: unknown, owner: string, nonEmpty = false): string {
  if (typeof value !== "string" || (nonEmpty && value.trim() === "")) {
    throw new Error(`SiteData ${owner} must be ${nonEmpty ? "a non-empty " : "a "}string.`);
  }
  return value;
}
function number(value: unknown, owner: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`SiteData ${owner} must be finite.`);
  return value;
}
function strings(value: unknown, owner: string, nonEmpty = false): string[] {
  if (!Array.isArray(value) || (nonEmpty && value.length === 0)) throw new Error(`SiteData ${owner} must be an array.`);
  const result = value.map((item, index) => string(item, `${owner}[${index}]`, true));
  if (new Set(result).size !== result.length) throw new Error(`SiteData ${owner} contains duplicates.`);
  return result;
}
function rows(value: unknown, owner: string): Row[] {
  if (!Array.isArray(value)) throw new Error(`SiteData ${owner} must be an array.`);
  return value.map((item, index) => row(item, `${owner}[${index}]`));
}
function unique<T>(items: T[], key: (item: T) => string, owner: string): Map<string, T> {
  const result = new Map<string, T>();
  for (const item of items) {
    const id = key(item);
    if (result.has(id)) throw new Error(`SiteData duplicate ${owner} ID: ${id}`);
    result.set(id, item);
  }
  return result;
}

export function parseSiteData(raw: unknown, expectedDatasetVersion?: string): SiteData {
  const data = row(raw, "payload");
  if (data.contract_version !== "1.0.0") throw new Error(`Unsupported SiteData contract: ${String(data.contract_version)}`);
  exactKeys(data, ["contract_version", "dataset_version", "generated_at", "questions", "rules", "methods", "implementations", "method_implementation_map", "alternatives", "problems", "features", "feature_values", "sources"], "payload");
  const datasetVersion = string(data.dataset_version, "dataset_version", true);
  if (expectedDatasetVersion !== undefined && datasetVersion !== expectedDatasetVersion) {
    throw new Error(`SiteData dataset mismatch: expected ${expectedDatasetVersion}, got ${datasetVersion}.`);
  }
  const generatedAt = string(data.generated_at, "generated_at", true);
  if (!Number.isFinite(Date.parse(generatedAt))) throw new Error("SiteData generated_at is invalid.");

  const questions = rows(data.questions, "questions").map((item): SiteQuestion => {
    exactKeys(item, ["question_id", "sequence", "question_ja", "question_en", "beginner_wording", "answer_type", "allowed_answers", "choices", "mapped_feature_id", "why_asked", "required", "confidence", "source_ids"], "question");
    const answerType = string(item.answer_type, "question.answer_type", true);
    if (answerType !== "single_choice" && answerType !== "multi_choice") throw new Error(`Unsupported answer type: ${answerType}`);
    const allowed = strings(item.allowed_answers, "question.allowed_answers", true);
    const choices = rows(item.choices, "question.choices").map((choice): SiteChoice => {
      exactKeys(choice, ["value", "label_ja", "label_en"], "choice");
      return {
        value: string(choice.value, "choice.value", true),
        label_ja: string(choice.label_ja, "choice.label_ja", true),
        label_en: string(choice.label_en, "choice.label_en", true),
      };
    });
    if (choices.map((choice) => choice.value).join("\0") !== allowed.join("\0")) throw new Error("SiteData choices do not match allowed answers.");
    if (typeof item.required !== "boolean") throw new Error("SiteData question.required must be boolean.");
    return {
      question_id: string(item.question_id, "question_id", true), sequence: number(item.sequence, "sequence"),
      question_ja: string(item.question_ja, "question_ja", true), question_en: string(item.question_en, "question_en", true),
      beginner_wording: string(item.beginner_wording, "beginner_wording", true), answer_type: answerType,
      allowed_answers: allowed, choices, mapped_feature_id: string(item.mapped_feature_id, "mapped_feature_id", true),
      why_asked: string(item.why_asked, "why_asked", true), required: item.required,
      confidence: string(item.confidence, "confidence", true), source_ids: strings(item.source_ids, "question.source_ids"),
    };
  });
  const rules = rows(data.rules, "rules").map((item): SiteRule => {
    exactKeys(item, ["rule_id", "question_id", "answer_condition", "action_type", "action_target_type", "action_target_ids", "priority_effect", "explanation", "warnings", "source_ids"], "rule");
    const action = string(item.action_type, "rule.action_type", true) as ActionType;
    const target = string(item.action_target_type, "rule.action_target_type", true) as TargetType;
    const priority = string(item.priority_effect, "rule.priority_effect", true) as Priority;
    if (!ACTIONS.has(action)) throw new Error(`Unsupported recommendation action: ${action}`);
    if (!TARGETS.has(target)) throw new Error(`Unsupported recommendation target: ${target}`);
    if (!PRIORITIES.has(priority)) throw new Error(`Unsupported recommendation priority: ${priority}`);
    return {
      rule_id: string(item.rule_id, "rule_id", true), question_id: string(item.question_id, "rule.question_id", true),
      answer_condition: string(item.answer_condition, "rule.answer_condition", true), action_type: action,
      action_target_type: target, action_target_ids: strings(item.action_target_ids, "rule.action_target_ids", true),
      priority_effect: priority, explanation: string(item.explanation, "rule.explanation"),
      warnings: string(item.warnings, "rule.warnings"), source_ids: strings(item.source_ids, "rule.source_ids"),
    };
  });
  const methods = rows(data.methods, "methods").map((item): SiteMethod => (exactKeys(item, ["method_id", "name_ja", "name_en", "summary", "variable_types", "solution_scope", "optimality_certificate", "exactness", "reference_source_ids"], "method"), {
    method_id: string(item.method_id, "method_id", true), name_ja: string(item.name_ja, "method.name_ja", true),
    name_en: string(item.name_en, "method.name_en", true), summary: string(item.summary, "method.summary"),
    variable_types: string(item.variable_types, "method.variable_types"), solution_scope: string(item.solution_scope, "method.solution_scope"),
    optimality_certificate: string(item.optimality_certificate, "method.optimality_certificate"), exactness: string(item.exactness, "method.exactness"),
    reference_source_ids: strings(item.reference_source_ids, "method.reference_source_ids"),
  }));
  const implementations = rows(data.implementations, "implementations").map((item): SiteImplementation => (exactKeys(item, ["implementation_id", "library_name", "solver_name", "language", "license", "maintenance_status", "last_release", "official_docs_url", "official_repo_url", "notes"], "implementation"), {
    implementation_id: string(item.implementation_id, "implementation_id", true), library_name: string(item.library_name, "implementation.library_name"),
    solver_name: string(item.solver_name, "implementation.solver_name"), language: string(item.language, "implementation.language"),
    license: string(item.license, "implementation.license"), maintenance_status: string(item.maintenance_status, "implementation.maintenance_status"),
    last_release: string(item.last_release, "implementation.last_release"), official_docs_url: string(item.official_docs_url, "implementation.official_docs_url"),
    official_repo_url: string(item.official_repo_url, "implementation.official_repo_url"), notes: string(item.notes, "implementation.notes"),
  }));
  const mappings = rows(data.method_implementation_map, "method_implementation_map").map((item): SiteMethodImplementation => (exactKeys(item, ["method_id", "implementation_id", "support_level", "implementation_notes"], "method implementation mapping"), {
    method_id: string(item.method_id, "mapping.method_id", true), implementation_id: string(item.implementation_id, "mapping.implementation_id", true),
    support_level: string(item.support_level, "mapping.support_level"), implementation_notes: string(item.implementation_notes, "mapping.implementation_notes"),
  }));
  const alternatives = rows(data.alternatives, "alternatives").map((item): SiteAlternative => (exactKeys(item, ["alternative_id", "name_ja", "name_en", "why_before_generic_optimization", "preferred_approach", "false_positive_warning", "source_ids"], "alternative"), {
    alternative_id: string(item.alternative_id, "alternative_id", true), name_ja: string(item.name_ja, "alternative.name_ja", true),
    name_en: string(item.name_en, "alternative.name_en", true), why_before_generic_optimization: string(item.why_before_generic_optimization, "alternative.why"),
    preferred_approach: string(item.preferred_approach, "alternative.preferred"), false_positive_warning: string(item.false_positive_warning, "alternative.warning"),
    source_ids: strings(item.source_ids, "alternative.source_ids"),
  }));
  const problems = rows(data.problems, "problems").map((item): SiteProblem => (exactKeys(item, ["problem_id", "name_ja", "name_en", "summary", "source_ids"], "problem"), {
    problem_id: string(item.problem_id, "problem_id", true), name_ja: string(item.name_ja, "problem.name_ja", true),
    name_en: string(item.name_en, "problem.name_en", true), summary: string(item.summary, "problem.summary"), source_ids: strings(item.source_ids, "problem.source_ids"),
  }));
  const features = rows(data.features, "features").map((item): SiteFeature => (exactKeys(item, ["feature_id", "name_ja", "name_en", "definition", "source_ids"], "feature"), {
    feature_id: string(item.feature_id, "feature_id", true), name_ja: string(item.name_ja, "feature.name_ja", true),
    name_en: string(item.name_en, "feature.name_en", true), definition: string(item.definition, "feature.definition"), source_ids: strings(item.source_ids, "feature.source_ids"),
  }));
  const featureValues = rows(data.feature_values, "feature_values").map((item): SiteFeatureValue => (exactKeys(item, ["feature_id", "value_code", "label_ja", "label_en", "sort_order"], "feature value"), {
    feature_id: string(item.feature_id, "feature_value.feature_id", true), value_code: string(item.value_code, "feature_value.value_code", true),
    label_ja: string(item.label_ja, "feature_value.label_ja", true), label_en: string(item.label_en, "feature_value.label_en", true),
    sort_order: number(item.sort_order, "feature_value.sort_order"),
  }));
  const sources = rows(data.sources, "sources").map((item): SiteSource => (exactKeys(item, ["source_id", "title", "supported_claim", "url"], "source"), {
    source_id: string(item.source_id, "source_id", true), title: string(item.title, "source.title", true),
    supported_claim: string(item.supported_claim, "source.supported_claim"), url: string(item.url, "source.url"),
  }));
  const questionById = unique(questions, (item) => item.question_id, "question");
  const methodById = unique(methods, (item) => item.method_id, "method");
  const alternativeById = unique(alternatives, (item) => item.alternative_id, "alternative");
  const problemById = unique(problems, (item) => item.problem_id, "problem");
  const featureById = unique(features, (item) => item.feature_id, "feature");
  const implementationById = unique(implementations, (item) => item.implementation_id, "implementation");
  const sourceById = unique(sources, (item) => item.source_id, "source");
  unique(rules, (item) => item.rule_id, "rule");
  const targets = { method: methodById, alternative: alternativeById, problem: problemById, feature: featureById };
  const requireSources = (ids: string[], owner: string) => ids.forEach((id) => { if (!sourceById.has(id)) throw new Error(`Missing source ${id} for ${owner}.`); });
  questions.forEach((question) => {
    if (!featureById.has(question.mapped_feature_id)) throw new Error(`Missing mapped feature: ${question.mapped_feature_id}`);
    requireSources(question.source_ids, question.question_id);
  });
  rules.forEach((rule) => {
    const question = questionById.get(rule.question_id);
    if (!question?.allowed_answers.includes(rule.answer_condition)) throw new Error(`Non-canonical rule condition: ${rule.rule_id}`);
    rule.action_target_ids.forEach((id) => { if (!targets[rule.action_target_type].has(id)) throw new Error(`Missing target ${id} for ${rule.rule_id}.`); });
    requireSources(rule.source_ids, rule.rule_id);
  });
  methods.forEach((item) => requireSources(item.reference_source_ids, item.method_id));
  alternatives.forEach((item) => requireSources(item.source_ids, item.alternative_id));
  problems.forEach((item) => requireSources(item.source_ids, item.problem_id));
  features.forEach((item) => requireSources(item.source_ids, item.feature_id));
  const mappingKeys = new Set<string>();
  mappings.forEach((mapping) => {
    const key = `${mapping.method_id}\0${mapping.implementation_id}`;
    if (mappingKeys.has(key)) throw new Error(`Duplicate method implementation mapping: ${key}`);
    mappingKeys.add(key);
    if (!methodById.has(mapping.method_id) || !implementationById.has(mapping.implementation_id)) throw new Error(`Broken method implementation mapping: ${key}`);
  });
  featureValues.forEach((item) => { if (!featureById.has(item.feature_id)) throw new Error(`Missing feature for value: ${item.feature_id}`); });
  return {
    contract_version: "1.0.0", dataset_version: datasetVersion, generated_at: generatedAt,
    questions, rules, methods, implementations, method_implementation_map: mappings,
    alternatives, problems, features, feature_values: featureValues, sources,
  };
}
