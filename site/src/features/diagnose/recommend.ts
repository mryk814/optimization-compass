import type {
  SiteAlternative,
  SiteData,
  SiteImplementation,
  SiteMethod,
  SiteMethodImplementation,
  SiteProblem,
} from "../../contracts/site-data";

export interface RecommendationOptions {
  language?: "ja" | "en";
  max_methods?: number;
  max_implementations_per_method?: number;
  expected_dataset_version?: string;
}
export interface ImplementationSummary {
  implementation_id: string; library_name: string; solver_name: string; language: string;
  license: string; maintenance_status: string; last_release: string;
  official_docs_url: string; official_repo_url: string; support_level: string; notes: string;
}
export type PriorityBand = "first_choice" | "conditional" | "excluded" | "alternative";
export interface EntityRecommendation {
  entity_id: string; name: string; name_en: string; summary: string;
  priority_band: PriorityBand; supporting_rule_count: number;
  high_priority_rule_count: number; medium_priority_rule_count: number;
  reasons: string[]; warnings: string[]; source_ids: string[];
  implementations: ImplementationSummary[];
}
export interface RuleTrace {
  rule_id: string; question_id: string; matched_answer: string; action_type: string;
  action_target_type: string; action_target_ids: string[]; priority_effect: string;
  explanation: string; warnings: string; source_ids: string[];
}
export interface Followup { question_id: string; explanation: string; target_type: string; target_ids: string[] }
export interface RecommendationResult {
  alternatives_first: EntityRecommendation[];
  first_choices: EntityRecommendation[];
  conditional_choices: EntityRecommendation[];
  excluded_methods: EntityRecommendation[];
  candidate_problem_archetypes: EntityRecommendation[];
  followups: Followup[]; warnings: string[]; trace: RuleTrace[];
  answered_question_count: number; dataset_version: string; disclaimer: string;
}

interface Candidate {
  entity_id: string; high: number; medium: number; candidate: number;
  reasons: string[]; warnings: string[]; source_ids: string[];
}
type Answers = Record<string, readonly string[]>;

function newCandidate(entityId: string): Candidate {
  return { entity_id: entityId, high: 0, medium: 0, candidate: 0, reasons: [], warnings: [], source_ids: [] };
}
function appendUnique(items: string[], value: string): void { if (value && !items.includes(value)) items.push(value); }
function stableUnion(...collections: readonly string[][]): string[] {
  const result: string[] = [];
  collections.forEach((items) => items.forEach((item) => appendUnique(result, item)));
  return result;
}
function addRule(candidate: Candidate, priority: string, explanation: string, warning: string, sourceIds: string[]): void {
  if (priority === "high") candidate.high += 1;
  else if (priority === "medium") candidate.medium += 1;
  else if (priority === "candidate") candidate.candidate += 1;
  appendUnique(candidate.reasons, explanation);
  appendUnique(candidate.warnings, warning);
  sourceIds.forEach((sourceId) => appendUnique(candidate.source_ids, sourceId));
}
function addCandidates(collection: Map<string, Candidate>, ids: string[], priority: string, explanation: string, warning: string, sources: string[]): void {
  ids.forEach((id) => {
    const candidate = collection.get(id) ?? newCandidate(id);
    collection.set(id, candidate);
    addRule(candidate, priority, explanation, warning, sources);
  });
}
function absorb(target: Candidate, source: Candidate): void {
  target.high += source.high; target.medium += source.medium; target.candidate += source.candidate;
  source.reasons.forEach((item) => appendUnique(target.reasons, item));
  source.warnings.forEach((item) => appendUnique(target.warnings, item));
  source.source_ids.forEach((item) => appendUnique(target.source_ids, item));
}
function demote(candidate: Candidate, warning: string): void {
  candidate.medium += candidate.high; candidate.high = 0; appendUnique(candidate.warnings, warning);
}
function supportCount(candidate: Candidate): number { return candidate.high + candidate.medium + candidate.candidate; }
function compareCandidates(left: Candidate, right: Candidate): number {
  return right.high - left.high || right.medium - left.medium || supportCount(right) - supportCount(left) || left.entity_id.localeCompare(right.entity_id);
}

function validateAnswers(data: SiteData, answers: Answers): Record<string, string[]> {
  const questions = new Map(data.questions.map((question) => [question.question_id, question]));
  const normalized: Record<string, string[]> = {};
  for (const [questionId, rawValues] of Object.entries(answers)) {
    const question = questions.get(questionId);
    if (!question) throw new Error(`unknown question IDs: ['${questionId}']`);
    if (!Array.isArray(rawValues) || rawValues.length === 0) throw new Error(`answers for ${questionId} must be non-empty`);
    if (new Set(rawValues).size !== rawValues.length) throw new Error(`answers for ${questionId} contain duplicate values`);
    const invalid = rawValues.filter((value) => !question.allowed_answers.includes(value));
    if (invalid.length) throw new Error(`invalid answers for ${questionId}: ${JSON.stringify(invalid)}`);
    if (question.answer_type === "single_choice" && rawValues.length !== 1) throw new Error(`single_choice answer for ${questionId} must contain exactly one value`);
    if (rawValues.includes("unknown") && rawValues.length !== 1) throw new Error(`unknown must be the sole value for ${questionId}`);
    normalized[questionId] = [...rawValues];
  }
  return normalized;
}

function variableCompatibility(domain: string, variableTypes: string): "native" | "encoded" | "incompatible" | "unknown" {
  const tokens = variableTypes.split(";").map((token) => token.trim().toLowerCase()).filter(Boolean);
  if (!tokens.length) return "unknown";
  const terms: Record<string, Set<string>> = {
    continuous: new Set(["continuous", "real"]), integer: new Set(["integer", "finite_domain", "discrete"]),
    binary: new Set(["binary", "boolean", "finite_domain", "discrete"]), categorical: new Set(["categorical", "discrete"]),
    mixed: new Set(["mixed"]),
  };
  const nativeTerms = terms[domain] ?? new Set([domain]);
  const markers = ["by_encoding", "by_model", "by_wrapper", "by_relaxation"];
  for (const token of tokens) {
    if (token === "mixed" && domain !== "mixed") return "native";
    if (nativeTerms.has(token)) return "native";
    if ([...nativeTerms].some((term) => token.includes(term)) && !markers.some((marker) => token.includes(marker))) return "native";
  }
  if (tokens.some((token) => markers.some((marker) => token.includes(marker)))) return "encoded";
  return "incompatible";
}
function supportsCertificate(method: SiteMethod): boolean {
  const scope = method.solution_scope.toLowerCase();
  const certificate = method.optimality_certificate.toLowerCase();
  const exactness = method.exactness.toLowerCase();
  if (scope.includes("global_certificate")) return true;
  if (["gap", "bound", "dual", "primal", "unsat", "certificate", "proof"].some((term) => certificate.includes(term))) return true;
  return exactness.includes("exact") && scope.includes("global");
}
function maintenanceOrder(status: string): number {
  if (status === "active" || status === "maintained") return 0;
  if (status === "legacy") return 3;
  return 1;
}

export function recommend(data: SiteData, input: Answers, options: RecommendationOptions = {}): RecommendationResult {
  const language = options.language ?? "ja";
  const maxMethods = options.max_methods ?? 8;
  const maxImplementations = options.max_implementations_per_method ?? 3;
  if (!Number.isInteger(maxMethods) || maxMethods < 1 || maxMethods > 30) throw new Error("max_methods must be an integer between 1 and 30");
  if (!Number.isInteger(maxImplementations) || maxImplementations < 0 || maxImplementations > 10) throw new Error("max_implementations_per_method must be an integer between 0 and 10");
  if (options.expected_dataset_version !== undefined && options.expected_dataset_version !== data.dataset_version) {
    throw new Error(`SiteData dataset mismatch: expected ${options.expected_dataset_version}, got ${data.dataset_version}.`);
  }
  const answers = validateAnswers(data, input);
  const methods = new Map(data.methods.map((method) => [method.method_id, method]));
  const methodCandidates = new Map<string, Candidate>();
  const excludedMethods = new Map<string, Candidate>();
  const alternativeCandidates = new Map<string, Candidate>();
  const problemCandidates = new Map<string, Candidate>();
  const followups: Followup[] = [];
  const warnings: string[] = [];
  const trace: RuleTrace[] = [];

  [...data.rules].sort((a, b) => a.rule_id.localeCompare(b.rule_id)).forEach((rule) => {
    if (!answers[rule.question_id]?.includes(rule.answer_condition)) return;
    trace.push({
      rule_id: rule.rule_id, question_id: rule.question_id, matched_answer: rule.answer_condition,
      action_type: rule.action_type, action_target_type: rule.action_target_type,
      action_target_ids: [...rule.action_target_ids], priority_effect: rule.priority_effect,
      explanation: rule.explanation, warnings: rule.warnings, source_ids: [...rule.source_ids],
    });
    const args = [rule.action_target_ids, rule.priority_effect, rule.explanation, rule.warnings, rule.source_ids] as const;
    if (rule.action_type === "promote_method") addCandidates(methodCandidates, ...args);
    else if (rule.action_type === "exclude_method") addCandidates(excludedMethods, ...args);
    else if (rule.action_type === "recommend_alternative") addCandidates(alternativeCandidates, ...args);
    else if (rule.action_type === "include_problem") addCandidates(problemCandidates, ...args);
    else if (rule.action_type === "ask_followup") followups.push({ question_id: rule.question_id, explanation: rule.explanation, target_type: rule.action_target_type, target_ids: [...rule.action_target_ids] });
    else if (rule.action_type === "warn") appendUnique(warnings, rule.warnings || rule.explanation);
  });

  const domain = answers.Q01?.[0];
  if (domain !== undefined && domain !== "structured_or_unknown") {
    let encoded = 0; let excluded = 0;
    [...methodCandidates.entries()].forEach(([methodId, candidate]) => {
      const method = methods.get(methodId); if (!method) return;
      const compatibility = variableCompatibility(domain, method.variable_types);
      if (compatibility === "encoded") {
        demote(candidate, language === "ja" ? "変数domainを直接扱わず、encoding・relaxation・wrapperが必要です。" : "This variable domain requires encoding, relaxation, or a wrapper."); encoded += 1;
      } else if (compatibility === "incompatible") {
        methodCandidates.delete(methodId); const target = excludedMethods.get(methodId) ?? newCandidate(methodId); excludedMethods.set(methodId, target); absorb(target, candidate);
        addRule(target, "high", language === "ja" ? `回答された変数domain (${domain}) と手法の対応 (${method.variable_types}) が一致しません。` : `The selected variable domain (${domain}) is incompatible with the method support (${method.variable_types}).`, language === "ja" ? "変数変換を行う場合は、可行性・距離・保証が変わらないか確認してください。" : "If variables are transformed, re-check feasibility, geometry, and guarantees.", method.reference_source_ids); excluded += 1;
      }
    });
    if (encoded) warnings.push(language === "ja" ? `${encoded}件の候補は変数encoding等が必要なため、条件付き候補へ下げました。` : `${encoded} candidates were demoted because variable encoding is required.`);
    if (excluded) warnings.push(language === "ja" ? `${excluded}件の候補を変数domain不一致として除外しました。` : `${excluded} candidates were excluded for variable-domain mismatch.`);
  }

  const goal = answers.Q10?.[0];
  if (goal === "gap_desired" || goal === "global_proof_required") {
    let demoted = 0; let excluded = 0;
    [...methodCandidates.entries()].forEach(([methodId, candidate]) => {
      const method = methods.get(methodId); if (!method || supportsCertificate(method)) return;
      if (goal === "gap_desired") {
        demote(candidate, language === "ja" ? "この手法単独では一般に最適性gapや上下界を返しません。" : "This method generally does not provide an optimality gap or bounds."); demoted += 1;
      } else {
        methodCandidates.delete(methodId); const target = excludedMethods.get(methodId) ?? newCandidate(methodId); excludedMethods.set(methodId, target); absorb(target, candidate);
        addRule(target, "high", language === "ja" ? "大域最適性の証明要件を満たす一般的なcertificateがありません。" : "The method lacks a general certificate for global optimality.", language === "ja" ? "heuristicをincumbent生成に使う場合も、証明可能なsolverを別に必要とします。" : "A heuristic may generate incumbents, but a certifying solver is still required.", method.reference_source_ids); excluded += 1;
      }
    });
    if (demoted) warnings.push(language === "ja" ? `${demoted}件の候補はgap・上下界を一般に返さないため、条件付きへ下げました。` : `${demoted} candidates were demoted because they generally do not provide gaps or bounds.`);
    if (excluded) warnings.push(language === "ja" ? `${excluded}件の候補を大域証明要件との不一致で除外しました。` : `${excluded} candidates were excluded because they do not satisfy the global-proof requirement.`);
  }
  const conflicts = [...methodCandidates.keys()].filter((id) => excludedMethods.has(id));
  if (conflicts.length) warnings.push("一部の手法に支持規則と除外規則が同時に一致しました。除外を優先しています。");
  excludedMethods.forEach((_candidate, id) => methodCandidates.delete(id));

  const implementationById = new Map(data.implementations.map((item) => [item.implementation_id, item]));
  const mappingsByMethod = new Map<string, Array<{ mapping: SiteMethodImplementation; implementation: SiteImplementation }>>();
  data.method_implementation_map.forEach((mapping) => {
    const implementation = implementationById.get(mapping.implementation_id); if (!implementation) return;
    const items = mappingsByMethod.get(mapping.method_id) ?? []; items.push({ mapping, implementation }); mappingsByMethod.set(mapping.method_id, items);
  });
  mappingsByMethod.forEach((items) => items.sort((left, right) => (left.mapping.support_level === "native" ? 0 : 1) - (right.mapping.support_level === "native" ? 0 : 1) || maintenanceOrder(left.implementation.maintenance_status) - maintenanceOrder(right.implementation.maintenance_status) || left.implementation.implementation_id.localeCompare(right.implementation.implementation_id)));

  const methodEntities = (candidates: Candidate[], band: "first_choice" | "conditional" | "excluded"): EntityRecommendation[] => candidates.flatMap((candidate) => {
    const method = methods.get(candidate.entity_id); if (!method) return [];
    const implementations: ImplementationSummary[] = band === "excluded" ? [] : (mappingsByMethod.get(candidate.entity_id) ?? []).slice(0, maxImplementations).map(({ mapping, implementation }) => ({
      implementation_id: implementation.implementation_id, library_name: implementation.library_name, solver_name: implementation.solver_name,
      language: implementation.language, license: implementation.license || "unknown", maintenance_status: implementation.maintenance_status || "unknown",
      last_release: implementation.last_release || "unknown", official_docs_url: implementation.official_docs_url,
      official_repo_url: implementation.official_repo_url, support_level: mapping.support_level,
      notes: mapping.implementation_notes || implementation.notes,
    }));
    return [{ entity_id: candidate.entity_id, name: language === "ja" ? method.name_ja : method.name_en, name_en: method.name_en, summary: method.summary, priority_band: band, supporting_rule_count: supportCount(candidate), high_priority_rule_count: candidate.high, medium_priority_rule_count: candidate.medium, reasons: [...candidate.reasons], warnings: [...candidate.warnings], source_ids: [...candidate.source_ids], implementations }];
  });
  const sorted = [...methodCandidates.values()].sort(compareCandidates);
  let first = sorted.filter((item) => item.high >= 2); let conditional = sorted.filter((item) => item.high < 2);
  if (!first.length && conditional.length) { first = conditional.slice(0, Math.min(3, maxMethods)); conditional = conditional.slice(first.length); }
  const alternativeById = new Map(data.alternatives.map((item) => [item.alternative_id, item]));
  const problemById = new Map(data.problems.map((item) => [item.problem_id, item]));
  const alternatives = [...alternativeCandidates.values()].sort(compareCandidates).flatMap((candidate): EntityRecommendation[] => {
    const item: SiteAlternative | undefined = alternativeById.get(candidate.entity_id); if (!item) return [];
    return [{ entity_id: candidate.entity_id, name: language === "ja" ? item.name_ja : item.name_en, name_en: item.name_en, summary: item.why_before_generic_optimization, priority_band: "alternative", supporting_rule_count: supportCount(candidate), high_priority_rule_count: candidate.high, medium_priority_rule_count: candidate.medium, reasons: [...candidate.reasons, item.preferred_approach], warnings: [...candidate.warnings, ...(item.false_positive_warning ? [item.false_positive_warning] : [])], source_ids: stableUnion(candidate.source_ids, item.source_ids), implementations: [] }];
  });
  const problems = [...problemCandidates.values()].sort(compareCandidates).flatMap((candidate): EntityRecommendation[] => {
    const item: SiteProblem | undefined = problemById.get(candidate.entity_id); if (!item) return [];
    return [{ entity_id: candidate.entity_id, name: language === "ja" ? item.name_ja : item.name_en, name_en: item.name_en, summary: item.summary, priority_band: "conditional", supporting_rule_count: supportCount(candidate), high_priority_rule_count: candidate.high, medium_priority_rule_count: candidate.medium, reasons: [...candidate.reasons], warnings: [...candidate.warnings], source_ids: stableUnion(candidate.source_ids, item.source_ids), implementations: [] }];
  });
  const seenFollowups = new Set<string>();
  const dedupedFollowups = followups.filter((item) => { const key = `${item.question_id}\0${item.target_type}\0${item.target_ids.join("\0")}`; if (seenFollowups.has(key)) return false; seenFollowups.add(key); return true; });
  return {
    alternatives_first: alternatives,
    first_choices: methodEntities(first.slice(0, maxMethods), "first_choice"),
    conditional_choices: methodEntities(conditional.slice(0, maxMethods), "conditional"),
    excluded_methods: methodEntities([...excludedMethods.values()].sort(compareCandidates), "excluded"),
    candidate_problem_archetypes: problems, followups: dedupedFollowups, warnings, trace,
    answered_question_count: Object.keys(answers).length, dataset_version: data.dataset_version,
    disclaimer: language === "ja" ? "候補選定支援であり、実問題での数値検証・安全性・最適性・商用条件を保証しません。" : "This is decision support, not a guarantee of numerical performance, safety, optimality, or commercial terms.",
  };
}
