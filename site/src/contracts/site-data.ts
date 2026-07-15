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
export type PredicateSubjectType = "method" | "method_family" | "implementation";
export type PredicateExpression =
  | { kind: "predicate"; predicate_id: string }
  | { kind: "all" | "any"; items: PredicateExpression[] }
  | { kind: "not"; item: PredicateExpression }
  | { kind: "when"; condition: PredicateExpression; then: PredicateExpression; otherwise: PredicateExpression | null };
export interface SitePredicate {
  predicate_id: string; schema_version: "1.0.0"; subject_type: PredicateSubjectType;
  subject_id: string; predicate_kind: "assumption" | "capability" | "incompatibility" | "recommendation_guard";
  feature_id: string; operator: "eq" | "neq" | "in" | "not_in" | "lt" | "lte" | "gt" | "gte" | "contains";
  value: unknown; value_type: "controlled_code" | "number" | "string" | "boolean" | "list";
  rationale_key: string; source_ids: string[]; confidence: "high" | "medium" | "low"; last_verified: string;
}
export interface SitePredicatePolicy {
  policy_id: string; schema_version: "1.0.0"; subject_type: PredicateSubjectType;
  subject_id: string; effect: "require" | "exclude"; expression: PredicateExpression | null;
  inheritance_mode: "inheritable" | "local_only"; override_action: "add" | "replace" | "suppress";
  overrides_policy_id: string | null; rationale_key: string; source_ids: string[];
  confidence: "high" | "medium" | "low"; last_verified: string;
}
export interface SitePredicateCoverage {
  subject_type: "method" | "implementation"; subject_id: string;
  status: "complete" | "partial" | "not_started" | "not_applicable";
  rationale: string; source_ids: string[]; last_verified: string;
}
export interface SiteRuleTargetRetirement {
  retirement_id: string; rule_id: string; method_id: string; policy_id: string;
  reason: string; source_ids: string[]; last_verified: string;
}
export interface SiteData {
  contract_version: "2.0.0"; dataset_version: string; generated_at: string;
  questions: SiteQuestion[]; rules: SiteRule[]; methods: SiteMethod[];
  implementations: SiteImplementation[]; method_implementation_map: SiteMethodImplementation[];
  alternatives: SiteAlternative[]; problems: SiteProblem[]; features: SiteFeature[];
  feature_values: SiteFeatureValue[]; sources: SiteSource[];
  predicates: SitePredicate[]; predicate_policies: SitePredicatePolicy[];
  predicate_coverage: SitePredicateCoverage[]; rule_target_retirements: SiteRuleTargetRetirement[];
}

type Row = Record<string, unknown>;
const ACTIONS = new Set<ActionType>([
  "promote_method", "exclude_method", "recommend_alternative", "include_problem",
  "ask_followup", "warn",
]);
const TARGETS = new Set<TargetType>(["method", "alternative", "problem", "feature"]);
const PRIORITIES = new Set<Priority>(["high", "medium", "candidate", "none"]);
const SUBJECT_TYPES = new Set<PredicateSubjectType>(["method", "method_family", "implementation"]);

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
function integer(value: unknown, owner: string, minimum?: number): number {
  const result = number(value, owner);
  if (!Number.isInteger(result)) throw new Error(`SiteData ${owner} must be an integer.`);
  if (minimum !== undefined && result < minimum) {
    throw new Error(`SiteData ${owner} must be at least ${minimum}.`);
  }
  return result;
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

function nullableString(value: unknown, owner: string): string | null {
  return value === null ? null : string(value, owner, true);
}

function predicateExpression(value: unknown, owner: string): PredicateExpression {
  const item = row(value, owner);
  const kind = string(item.kind, `${owner}.kind`, true);
  if (kind === "predicate") {
    exactKeys(item, ["kind", "predicate_id"], owner);
    return { kind, predicate_id: string(item.predicate_id, `${owner}.predicate_id`, true) };
  }
  if (kind === "all" || kind === "any") {
    exactKeys(item, ["kind", "items"], owner);
    const children = rows(item.items, `${owner}.items`).map((child, index) => predicateExpression(child, `${owner}.items[${index}]`));
    if (children.length === 0) throw new Error(`SiteData ${owner}.items must not be empty.`);
    return { kind, items: children };
  }
  if (kind === "not") {
    exactKeys(item, ["kind", "item"], owner);
    return { kind, item: predicateExpression(item.item, `${owner}.item`) };
  }
  if (kind === "when") {
    exactKeys(item, ["kind", "condition", "then", "otherwise"], owner);
    return {
      kind,
      condition: predicateExpression(item.condition, `${owner}.condition`),
      then: predicateExpression(item.then, `${owner}.then`),
      otherwise: item.otherwise === null ? null : predicateExpression(item.otherwise, `${owner}.otherwise`),
    };
  }
  throw new Error(`Unsupported predicate expression: ${kind}`);
}

export function parseSiteData(raw: unknown, expectedDatasetVersion?: string): SiteData {
  const data = row(raw, "payload");
  if (data.contract_version !== "2.0.0") throw new Error(`Unsupported SiteData contract: ${String(data.contract_version)}`);
  exactKeys(data, ["contract_version", "dataset_version", "generated_at", "questions", "rules", "methods", "implementations", "method_implementation_map", "alternatives", "problems", "features", "feature_values", "sources", "predicates", "predicate_policies", "predicate_coverage", "rule_target_retirements"], "payload");
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
      question_id: string(item.question_id, "question_id", true), sequence: integer(item.sequence, "sequence", 1),
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
  const predicates = rows(data.predicates, "predicates").map((item): SitePredicate => {
    exactKeys(item, ["predicate_id", "schema_version", "subject_type", "subject_id", "predicate_kind", "feature_id", "operator", "value", "value_type", "rationale_key", "source_ids", "confidence", "last_verified"], "predicate");
    const subjectType = string(item.subject_type, "predicate.subject_type", true) as PredicateSubjectType;
    const predicateKind = string(item.predicate_kind, "predicate.predicate_kind", true) as SitePredicate["predicate_kind"];
    const operator = string(item.operator, "predicate.operator", true) as SitePredicate["operator"];
    const valueType = string(item.value_type, "predicate.value_type", true) as SitePredicate["value_type"];
    const confidence = string(item.confidence, "predicate.confidence", true) as SitePredicate["confidence"];
    if (item.schema_version !== "1.0.0") throw new Error(`Unsupported predicate schema: ${String(item.schema_version)}`);
    if (!SUBJECT_TYPES.has(subjectType)) throw new Error(`Unsupported predicate subject: ${subjectType}`);
    if (!["assumption", "capability", "incompatibility", "recommendation_guard"].includes(predicateKind)) throw new Error(`Unsupported predicate kind: ${predicateKind}`);
    if (!["eq", "neq", "in", "not_in", "lt", "lte", "gt", "gte", "contains"].includes(operator)) throw new Error(`Unsupported predicate operator: ${operator}`);
    if (!["controlled_code", "number", "string", "boolean", "list"].includes(valueType)) throw new Error(`Unsupported predicate value type: ${valueType}`);
    if (!["high", "medium", "low"].includes(confidence)) throw new Error(`Unsupported predicate confidence: ${confidence}`);
    return {
      predicate_id: string(item.predicate_id, "predicate.predicate_id", true), schema_version: "1.0.0",
      subject_type: subjectType, subject_id: string(item.subject_id, "predicate.subject_id", true), predicate_kind: predicateKind,
      feature_id: string(item.feature_id, "predicate.feature_id", true), operator, value: item.value, value_type: valueType,
      rationale_key: string(item.rationale_key, "predicate.rationale_key", true), source_ids: strings(item.source_ids, "predicate.source_ids", true),
      confidence, last_verified: string(item.last_verified, "predicate.last_verified", true),
    };
  });
  const predicatePolicies = rows(data.predicate_policies, "predicate_policies").map((item): SitePredicatePolicy => {
    exactKeys(item, ["policy_id", "schema_version", "subject_type", "subject_id", "effect", "expression", "inheritance_mode", "override_action", "overrides_policy_id", "rationale_key", "source_ids", "confidence", "last_verified"], "predicate policy");
    const subjectType = string(item.subject_type, "policy.subject_type", true) as PredicateSubjectType;
    const effect = string(item.effect, "policy.effect", true) as SitePredicatePolicy["effect"];
    const inheritanceMode = string(item.inheritance_mode, "policy.inheritance_mode", true) as SitePredicatePolicy["inheritance_mode"];
    const overrideAction = string(item.override_action, "policy.override_action", true) as SitePredicatePolicy["override_action"];
    const confidence = string(item.confidence, "policy.confidence", true) as SitePredicatePolicy["confidence"];
    if (item.schema_version !== "1.0.0") throw new Error(`Unsupported predicate policy schema: ${String(item.schema_version)}`);
    if (!SUBJECT_TYPES.has(subjectType) || !["require", "exclude"].includes(effect) || !["inheritable", "local_only"].includes(inheritanceMode) || !["add", "replace", "suppress"].includes(overrideAction) || !["high", "medium", "low"].includes(confidence)) throw new Error("Unsupported predicate policy vocabulary.");
    return {
      policy_id: string(item.policy_id, "policy.policy_id", true), schema_version: "1.0.0", subject_type: subjectType,
      subject_id: string(item.subject_id, "policy.subject_id", true), effect,
      expression: item.expression === null ? null : predicateExpression(item.expression, "policy.expression"),
      inheritance_mode: inheritanceMode, override_action: overrideAction,
      overrides_policy_id: nullableString(item.overrides_policy_id, "policy.overrides_policy_id"),
      rationale_key: string(item.rationale_key, "policy.rationale_key", true), source_ids: strings(item.source_ids, "policy.source_ids", true),
      confidence, last_verified: string(item.last_verified, "policy.last_verified", true),
    };
  });
  const predicateCoverage = rows(data.predicate_coverage, "predicate_coverage").map((item): SitePredicateCoverage => {
    exactKeys(item, ["subject_type", "subject_id", "status", "rationale", "source_ids", "last_verified"], "predicate coverage");
    const subjectType = string(item.subject_type, "coverage.subject_type", true) as SitePredicateCoverage["subject_type"];
    const status = string(item.status, "coverage.status", true) as SitePredicateCoverage["status"];
    if (!["method", "implementation"].includes(subjectType) || !["complete", "partial", "not_started", "not_applicable"].includes(status)) throw new Error("Unsupported predicate coverage vocabulary.");
    return { subject_type: subjectType, subject_id: string(item.subject_id, "coverage.subject_id", true), status, rationale: string(item.rationale, "coverage.rationale", true), source_ids: strings(item.source_ids, "coverage.source_ids", true), last_verified: string(item.last_verified, "coverage.last_verified", true) };
  });
  const ruleTargetRetirements = rows(data.rule_target_retirements, "rule_target_retirements").map((item): SiteRuleTargetRetirement => {
    exactKeys(item, ["retirement_id", "rule_id", "method_id", "policy_id", "reason", "source_ids", "last_verified"], "rule target retirement");
    return { retirement_id: string(item.retirement_id, "retirement.retirement_id", true), rule_id: string(item.rule_id, "retirement.rule_id", true), method_id: string(item.method_id, "retirement.method_id", true), policy_id: string(item.policy_id, "retirement.policy_id", true), reason: string(item.reason, "retirement.reason", true), source_ids: strings(item.source_ids, "retirement.source_ids", true), last_verified: string(item.last_verified, "retirement.last_verified", true) };
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
    sort_order: integer(item.sort_order, "sort_order"),
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
  const predicateById = unique(predicates, (item) => item.predicate_id, "predicate");
  const policyById = unique(predicatePolicies, (item) => item.policy_id, "predicate policy");
  unique(ruleTargetRetirements, (item) => item.retirement_id, "rule target retirement");
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
  predicates.forEach((item) => {
    if (!featureById.has(item.feature_id)) throw new Error(`Missing predicate feature: ${item.feature_id}`);
    if (item.subject_type === "method" && !methodById.has(item.subject_id)) throw new Error(`Missing predicate method: ${item.subject_id}`);
    requireSources(item.source_ids, item.predicate_id);
  });
  predicatePolicies.forEach((item) => requireSources(item.source_ids, item.policy_id));
  const coverageKeys = new Set<string>();
  predicateCoverage.forEach((item) => {
    const key = `${item.subject_type}\0${item.subject_id}`;
    if (coverageKeys.has(key)) throw new Error(`Duplicate predicate coverage: ${key}`);
    coverageKeys.add(key);
    if (item.subject_type === "method" && !methodById.has(item.subject_id)) throw new Error(`Missing predicate coverage method: ${item.subject_id}`);
    requireSources(item.source_ids, item.subject_id);
  });
  ruleTargetRetirements.forEach((item) => {
    if (!methodById.has(item.method_id) || !policyById.has(item.policy_id)) throw new Error(`Broken rule target retirement: ${item.retirement_id}`);
    requireSources(item.source_ids, item.retirement_id);
  });
  if (predicateById.size === 0 || policyById.size === 0) throw new Error("SiteData predicate catalog must not be empty.");
  const mappingKeys = new Set<string>();
  mappings.forEach((mapping) => {
    const key = `${mapping.method_id}\0${mapping.implementation_id}`;
    if (mappingKeys.has(key)) throw new Error(`Duplicate method implementation mapping: ${key}`);
    mappingKeys.add(key);
    if (!methodById.has(mapping.method_id) || !implementationById.has(mapping.implementation_id)) throw new Error(`Broken method implementation mapping: ${key}`);
  });
  const featureValueKeys = new Set<string>();
  featureValues.forEach((item) => {
    const key = `${item.feature_id}\0${item.value_code}`;
    if (featureValueKeys.has(key)) throw new Error(`Duplicate feature value: ${item.feature_id}/${item.value_code}`);
    featureValueKeys.add(key);
    if (!featureById.has(item.feature_id)) throw new Error(`Missing feature for value: ${item.feature_id}`);
  });
  return {
    contract_version: "2.0.0", dataset_version: datasetVersion, generated_at: generatedAt,
    questions, rules, methods, implementations, method_implementation_map: mappings,
    alternatives, problems, features, feature_values: featureValues, sources,
    predicates, predicate_policies: predicatePolicies, predicate_coverage: predicateCoverage,
    rule_target_retirements: ruleTargetRetirements,
  };
}
