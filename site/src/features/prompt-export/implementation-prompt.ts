import type { GalleryCase } from "../../contracts/gallery";
import type { EntityType, LinkedEntity } from "../../contracts/entity-links";
import type { PredicateExpression, SiteData } from "../../contracts/site-data";
import type { AtlasStateV1 } from "../../state/atlas-state";
import {
  recommend,
  type EntityRecommendation,
  type ImplementationSummary,
  type RecommendationResult,
} from "../diagnose/recommend";
import type { PromptSupportData } from "./support-data";

export type RequestedOutputId =
  | "mathematical_model"
  | "clarifying_questions"
  | "implementation_plan"
  | "runnable_prototype"
  | "test_validation_plan"
  | "comparison_experiment"
  | "existing_code_review"
  | "deployment_checklist";

export const REQUESTED_OUTPUT_OPTIONS: ReadonlyArray<{ id: RequestedOutputId; label: string }> = [
  { id: "mathematical_model", label: "数理モデルを整理する" },
  { id: "clarifying_questions", label: "確認質問を作る" },
  { id: "implementation_plan", label: "実装方針を作る" },
  { id: "runnable_prototype", label: "小さな実行可能prototypeを作る" },
  { id: "test_validation_plan", label: "test / validation planを作る" },
  { id: "comparison_experiment", label: "候補手法の比較実験を設計する" },
  { id: "existing_code_review", label: "既存コードの改善点を調べる" },
  { id: "deployment_checklist", label: "実務導入チェックリストを作る" },
];

export const DEFAULT_REQUESTED_OUTPUTS: RequestedOutputId[] = [
  "implementation_plan",
  "runnable_prototype",
  "test_validation_plan",
];

export const QUALITY_REQUIREMENTS = [
  "未記載の条件を勝手に確定しない。",
  "unknownは最初に確認質問として返す。",
  "数理モデル、理論手法、solver implementationを区別する。",
  "汎用最適化より適切な専用解法があれば先に検討する。",
  "候補を文脈なしの単一scoreでrankingしない。",
  "手法の前提条件とproblem条件の適合を確認する。",
  "小さな検証可能instanceから始める。",
  "input validation、status handling、testsを含める。",
  "stopping condition、tolerance、budget、seedを明示する。",
  "不確実なAPIやoptionは公式documentationで確認する。",
  "Atlasのsource IDと、追加調査したsourceを区別する。",
  "機密情報・個人情報・秘密鍵を要求せず、入力にも含めない。",
] as const;

export interface PromptFormState {
  intent: string;
  decision_variables: string;
  objective: string;
  constraints: string;
  input_data_format: string;
  problem_scale: string;
  evaluation_cost: string;
  computation_budget: string;
  programming_language: string;
  preferred_libraries: string;
  prohibited_libraries: string;
  runtime_environment: string;
  additional_unknowns: string;
  requested_outputs: RequestedOutputId[];
}

export interface PromptCandidate {
  entity_id: string;
  name: string;
  summary: string;
  reasons: string[];
  warnings: string[];
  source_ids: string[];
}

export interface PromptFeatureValue {
  feature_id: string;
  feature_name: string;
  values: Array<{ value_id: string; label: string }>;
  source_ids: string[];
}

export interface PromptImplementation extends ImplementationSummary {}

export interface PromptMethodCondition {
  condition_id: string;
  method_id: string;
  condition_type: "predicate" | "policy";
  description: string;
  source_ids: string[];
}

export interface PromptFailureMode {
  failure_mode_id: string;
  name: string;
  severity: string;
  affected_entity_ids: string[];
  symptoms: string[];
  diagnostic_checks: string[];
  mitigations: string[];
  source_ids: string[];
}

export interface PromptRelatedEntity {
  entity_type: EntityType;
  entity_id: string;
  label: string;
  relation_type: string;
  canonical_url: string | null;
}

export interface ImplementationPromptPack {
  contract_version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  intent: string;
  user_problem: {
    decision_variables: string;
    objective: string;
    constraints: string;
    input_data_format: string;
    problem_scale: string;
    evaluation_cost: string;
    computation_budget: string;
  };
  atlas_context: {
    origin: { kind: "diagnose"; answered_question_count: number } | { kind: "gallery"; case_id: string; title: string };
    feature_values: PromptFeatureValue[];
    problem_archetypes: PromptCandidate[];
    alternatives_first: PromptCandidate[];
    first_candidates: PromptCandidate[];
    conditional_candidates: PromptCandidate[];
    excluded_methods: PromptCandidate[];
    implementations: PromptImplementation[];
    method_conditions: PromptMethodCondition[];
    failure_modes: PromptFailureMode[];
    related_entities: PromptRelatedEntity[];
  };
  unknowns: string[];
  environment: {
    programming_language: string;
    preferred_libraries: string;
    prohibited_libraries: string;
    runtime_environment: string;
  };
  requested_outputs: RequestedOutputId[];
  quality_requirements: string[];
  source_ids: string[];
}

export interface ImplementationPromptDraft {
  dataset_version: string;
  generated_at: string;
  atlas_context: ImplementationPromptPack["atlas_context"];
  source_ids: string[];
  initial_form: PromptFormState;
}

export interface DiagnosePromptInput {
  state: AtlasStateV1;
  result: RecommendationResult;
  support: PromptSupportData;
  generatedAt: string;
}

export interface GalleryPromptInput {
  item: GalleryCase;
  datasetVersion: string;
  support: PromptSupportData;
  generatedAt: string;
}

const UNKNOWN_FIELDS: Array<readonly [keyof Omit<PromptFormState, "additional_unknowns" | "requested_outputs">, string]> = [
  ["intent", "やりたいこと"],
  ["decision_variables", "decision variables"],
  ["objective", "objective / minimize-maximize"],
  ["constraints", "constraints"],
  ["input_data_format", "input data / format"],
  ["problem_scale", "problem scale"],
  ["evaluation_cost", "evaluation cost"],
  ["computation_budget", "computation budget"],
  ["programming_language", "programming language"],
  ["preferred_libraries", "preferred libraries"],
  ["prohibited_libraries", "prohibited libraries"],
  ["runtime_environment", "runtime / deployment environment"],
];

function blankForm(): PromptFormState {
  return {
    intent: "unknown",
    decision_variables: "unknown",
    objective: "unknown",
    constraints: "unknown",
    input_data_format: "unknown",
    problem_scale: "unknown",
    evaluation_cost: "unknown",
    computation_budget: "unknown",
    programming_language: "unknown",
    preferred_libraries: "unknown",
    prohibited_libraries: "unknown",
    runtime_environment: "unknown",
    additional_unknowns: "",
    requested_outputs: [...DEFAULT_REQUESTED_OUTPUTS],
  };
}

function normalize(value: string): string {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : "unknown";
}

function uniqueSorted(values: Iterable<string>): string[] {
  return [...new Set([...values].filter(Boolean))].sort((left, right) => left.localeCompare(right));
}

function candidate(item: EntityRecommendation): PromptCandidate {
  return {
    entity_id: item.entity_id,
    name: item.name,
    summary: item.summary,
    reasons: [...item.reasons],
    warnings: [...item.warnings],
    source_ids: uniqueSorted(item.source_ids),
  };
}

function methodCandidate(
  data: SiteData,
  methodId: string,
  reasons: string[],
  sourceIds: string[],
): PromptCandidate {
  const method = data.methods.find((item) => item.method_id === methodId);
  if (!method) throw new Error(`Prompt method is missing from SiteData: ${methodId}`);
  return {
    entity_id: methodId,
    name: method.name_ja,
    summary: method.summary,
    reasons,
    warnings: [],
    source_ids: uniqueSorted([...sourceIds, ...method.reference_source_ids]),
  };
}

function problemCandidate(support: PromptSupportData, problemId: string, sourceIds: string[]): PromptCandidate {
  const problem = support.entityLinks.entities.find(
    (item) => item.entity_type === "problem" && item.entity_id === problemId,
  );
  if (!problem) throw new Error(`Prompt problem archetype is missing from EntityLinkIndex: ${problemId}`);
  const evidenceIds = problem.relations
    .filter((relation) => relation.relation_type === "evidence" && relation.target_type === "source")
    .map((relation) => relation.target_id);
  return {
    entity_id: problemId,
    name: problem.label,
    summary: problem.summary,
    reasons: [],
    warnings: [],
    source_ids: uniqueSorted([...sourceIds, ...evidenceIds]),
  };
}

function featureValue(data: SiteData, featureId: string, valueIds: string[]): PromptFeatureValue {
  const feature = data.features.find((item) => item.feature_id === featureId);
  if (!feature) throw new Error(`Prompt feature is missing from SiteData: ${featureId}`);
  return {
    feature_id: featureId,
    feature_name: feature.name_ja,
    values: valueIds.map((valueId) => ({
      value_id: valueId,
      label: data.feature_values.find((item) => item.feature_id === featureId && item.value_code === valueId)?.label_ja ?? valueId,
    })),
    source_ids: uniqueSorted(feature.source_ids),
  };
}

function expressionText(expression: PredicateExpression | null): string {
  if (expression === null) return "none";
  if (expression.kind === "predicate") return expression.predicate_id;
  if (expression.kind === "not") return `NOT (${expressionText(expression.item)})`;
  if (expression.kind === "when") {
    const otherwise = expression.otherwise ? ` ELSE ${expressionText(expression.otherwise)}` : "";
    return `WHEN ${expressionText(expression.condition)} THEN ${expressionText(expression.then)}${otherwise}`;
  }
  return `${expression.kind.toUpperCase()} (${expression.items.map(expressionText).join(", ")})`;
}

function methodConditions(data: SiteData, methodIds: string[]): PromptMethodCondition[] {
  const selected = new Set(methodIds);
  const predicates: PromptMethodCondition[] = data.predicates
    .filter((item) => item.subject_type === "method" && selected.has(item.subject_id))
    .map((item) => ({
      condition_id: item.predicate_id,
      method_id: item.subject_id,
      condition_type: "predicate",
      description: `${item.predicate_kind}: ${item.feature_id} ${item.operator} ${JSON.stringify(item.value)} (${item.rationale_key})`,
      source_ids: uniqueSorted(item.source_ids),
    }));
  const policies: PromptMethodCondition[] = data.predicate_policies
    .filter((item) => item.subject_type === "method" && selected.has(item.subject_id))
    .map((item) => ({
      condition_id: item.policy_id,
      method_id: item.subject_id,
      condition_type: "policy",
      description: `${item.effect}: ${expressionText(item.expression)} (${item.rationale_key})`,
      source_ids: uniqueSorted(item.source_ids),
    }));
  return [...predicates, ...policies].sort((left, right) => left.condition_id.localeCompare(right.condition_id));
}

function failureModes(
  support: PromptSupportData,
  methodIds: string[],
  implementationIds: string[],
): PromptFailureMode[] {
  const selected = new Set([...methodIds, ...implementationIds]);
  return support.failureModes.failure_modes
    .filter((item) => item.affected_entities.some((entity) => selected.has(entity.entity_id)))
    .map((item) => ({
      failure_mode_id: item.failure_mode_id,
      name: item.name_ja,
      severity: item.severity,
      affected_entity_ids: uniqueSorted(item.affected_entities.filter((entity) => selected.has(entity.entity_id)).map((entity) => entity.entity_id)),
      symptoms: item.symptoms.map((symptom) => symptom.description),
      diagnostic_checks: item.diagnostics.map((diagnostic) => diagnostic.check_text),
      mitigations: item.mitigations.map((mitigation) => `${mitigation.action} / ${mitigation.applicability} / tradeoff: ${mitigation.tradeoff}`),
      source_ids: uniqueSorted(item.source_ids),
    }))
    .sort((left, right) => left.failure_mode_id.localeCompare(right.failure_mode_id));
}

const RELATED_TYPES = new Set<EntityType>(["case", "comparison", "content", "trace", "view"]);

function entityKey(entity: Pick<LinkedEntity, "entity_type" | "entity_id">): string {
  return `${entity.entity_type}:${entity.entity_id}`;
}

function relatedEntities(
  support: PromptSupportData,
  seeds: Array<{ entity_type: EntityType; entity_id: string }>,
): PromptRelatedEntity[] {
  const entities = new Map(support.entityLinks.entities.map((item) => [entityKey(item), item]));
  const related = new Map<string, PromptRelatedEntity>();
  seeds.forEach((seed) => {
    const source = entities.get(entityKey(seed));
    source?.relations.forEach((relation) => {
      if (!RELATED_TYPES.has(relation.target_type)) return;
      const target = entities.get(`${relation.target_type}:${relation.target_id}`);
      if (!target) return;
      const key = `${relation.relation_type}:${entityKey(target)}`;
      related.set(key, {
        entity_type: target.entity_type,
        entity_id: target.entity_id,
        label: target.label,
        relation_type: relation.relation_type,
        canonical_url: target.canonical_url,
      });
    });
  });
  return [...related.values()].sort((left, right) =>
    left.entity_type.localeCompare(right.entity_type)
      || left.entity_id.localeCompare(right.entity_id)
      || left.relation_type.localeCompare(right.relation_type));
}

function diagnoseFeatures(state: AtlasStateV1, data: SiteData): PromptFeatureValue[] {
  return Object.entries(state.answers)
    .filter(([, answer]) => answer.status !== "not_applicable")
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([questionId, answer]) => {
      const question = data.questions.find((item) => item.question_id === questionId);
      if (!question) throw new Error(`Prompt question is missing from SiteData: ${questionId}`);
      return featureValue(data, question.mapped_feature_id, answer.status === "unknown" ? ["unknown"] : answer.values);
    });
}

function diagnoseImplementations(result: RecommendationResult): PromptImplementation[] {
  const implementations = new Map<string, PromptImplementation>();
  [...result.first_choices, ...result.conditional_choices].forEach((item) => {
    item.implementations.forEach((implementation) => implementations.set(implementation.implementation_id, { ...implementation }));
  });
  return [...implementations.values()].sort((left, right) => left.implementation_id.localeCompare(right.implementation_id));
}

function galleryImplementations(item: GalleryCase, data: SiteData): PromptImplementation[] {
  const relevantMethods = new Set([
    ...item.candidate_method_ids,
    ...item.conditional_methods.map((entry) => entry.method_id),
  ]);
  return [...item.implementation_ids].sort().map((implementationId) => {
    const implementation = data.implementations.find((entry) => entry.implementation_id === implementationId);
    if (!implementation) throw new Error(`Prompt implementation is missing from SiteData: ${implementationId}`);
    const mapping = data.method_implementation_map.find(
      (entry) => entry.implementation_id === implementationId && relevantMethods.has(entry.method_id),
    );
    return {
      implementation_id: implementation.implementation_id,
      library_name: implementation.library_name,
      solver_name: implementation.solver_name,
      language: implementation.language,
      license: implementation.license || "unknown",
      maintenance_status: implementation.maintenance_status || "unknown",
      last_release: implementation.last_release || "unknown",
      official_docs_url: implementation.official_docs_url,
      official_repo_url: implementation.official_repo_url,
      support_level: mapping?.support_level ?? "unknown",
      notes: mapping?.implementation_notes || implementation.notes,
    };
  });
}

function contextSourceIds(context: ImplementationPromptPack["atlas_context"]): string[] {
  return uniqueSorted([
    ...context.feature_values.flatMap((item) => item.source_ids),
    ...context.problem_archetypes.flatMap((item) => item.source_ids),
    ...context.alternatives_first.flatMap((item) => item.source_ids),
    ...context.first_candidates.flatMap((item) => item.source_ids),
    ...context.conditional_candidates.flatMap((item) => item.source_ids),
    ...context.excluded_methods.flatMap((item) => item.source_ids),
    ...context.method_conditions.flatMap((item) => item.source_ids),
    ...context.failure_modes.flatMap((item) => item.source_ids),
  ]);
}

export function createDiagnosePromptDraft(input: DiagnosePromptInput): ImplementationPromptDraft {
  const { state, result, support, generatedAt } = input;
  if (state.datasetVersion !== support.data.dataset_version || result.dataset_version !== support.data.dataset_version) {
    throw new Error("Diagnose prompt state, result, and support data must use the same dataset version.");
  }
  const firstCandidates = result.first_choices.map(candidate);
  const conditionalCandidates = result.conditional_choices.map(candidate);
  const excludedMethods = result.excluded_methods.map(candidate);
  const problemArchetypes = result.candidate_problem_archetypes.map(candidate);
  const implementations = diagnoseImplementations(result);
  const applicableMethodIds = [...firstCandidates, ...conditionalCandidates].map((item) => item.entity_id);
  const allMethodIds = [...firstCandidates, ...conditionalCandidates, ...excludedMethods].map((item) => item.entity_id);
  const atlasContext: ImplementationPromptPack["atlas_context"] = {
    origin: { kind: "diagnose", answered_question_count: result.answered_question_count },
    feature_values: diagnoseFeatures(state, support.data),
    problem_archetypes: problemArchetypes,
    alternatives_first: result.alternatives_first.map(candidate),
    first_candidates: firstCandidates,
    conditional_candidates: conditionalCandidates,
    excluded_methods: excludedMethods,
    implementations,
    method_conditions: methodConditions(support.data, applicableMethodIds),
    failure_modes: failureModes(support, applicableMethodIds, implementations.map((item) => item.implementation_id)),
    related_entities: relatedEntities(support, [
      ...allMethodIds.map((entity_id) => ({ entity_type: "method" as const, entity_id })),
      ...problemArchetypes.map((item) => ({ entity_type: "problem" as const, entity_id: item.entity_id })),
    ]),
  };
  return {
    dataset_version: support.data.dataset_version,
    generated_at: generatedAt,
    atlas_context: atlasContext,
    source_ids: contextSourceIds(atlasContext),
    initial_form: blankForm(),
  };
}

export function createGalleryPromptDraft(input: GalleryPromptInput): ImplementationPromptDraft {
  const { item, datasetVersion, support, generatedAt } = input;
  if (datasetVersion !== support.data.dataset_version) {
    throw new Error("Gallery prompt case and support data must use the same dataset version.");
  }
  if (!support.entityLinks.entities.some((entity) => entity.entity_type === "case" && entity.entity_id === item.case_id)) {
    throw new Error(`Prompt Gallery case is missing from EntityLinkIndex: ${item.case_id}`);
  }
  const galleryResult = recommend(
    support.data,
    Object.fromEntries(Object.entries(item.question_answers).map(([questionId, value]) => [questionId, [value]])),
    { expected_dataset_version: datasetVersion },
  );
  const firstCandidates = item.candidate_method_ids.map((methodId) =>
    methodCandidate(support.data, methodId, ["Gallery caseで第一候補として登録"], item.source_ids));
  const conditionalCandidates = item.conditional_methods.map((entry) =>
    methodCandidate(support.data, entry.method_id, [entry.reason], item.source_ids));
  const excludedMethods = item.excluded_methods.map((entry) =>
    methodCandidate(support.data, entry.method_id, [entry.reason], item.source_ids));
  const implementations = galleryImplementations(item, support.data);
  const applicableMethodIds = [...firstCandidates, ...conditionalCandidates].map((entry) => entry.entity_id);
  const atlasContext: ImplementationPromptPack["atlas_context"] = {
    origin: { kind: "gallery", case_id: item.case_id, title: item.title_ja },
    feature_values: [...item.feature_values]
      .sort((left, right) => left.feature_id.localeCompare(right.feature_id))
      .map((entry) => featureValue(support.data, entry.feature_id, [entry.value])),
    problem_archetypes: [problemCandidate(support, item.problem_archetype_id, item.source_ids)],
    alternatives_first: galleryResult.alternatives_first.map(candidate),
    first_candidates: firstCandidates,
    conditional_candidates: conditionalCandidates,
    excluded_methods: excludedMethods,
    implementations,
    method_conditions: methodConditions(support.data, applicableMethodIds),
    failure_modes: failureModes(support, applicableMethodIds, implementations.map((entry) => entry.implementation_id)),
    related_entities: relatedEntities(support, [
      { entity_type: "case", entity_id: item.case_id },
      ...applicableMethodIds.map((entity_id) => ({ entity_type: "method" as const, entity_id })),
      { entity_type: "problem", entity_id: item.problem_archetype_id },
    ]),
  };
  const form = blankForm();
  form.intent = item.question;
  form.decision_variables = item.decision_variables;
  form.objective = item.objective;
  form.constraints = item.constraints;
  return {
    dataset_version: datasetVersion,
    generated_at: generatedAt,
    atlas_context: atlasContext,
    source_ids: uniqueSorted([...item.source_ids, ...contextSourceIds(atlasContext)]),
    initial_form: form,
  };
}

export function unknownsForForm(form: PromptFormState): string[] {
  const fieldUnknowns = UNKNOWN_FIELDS
    .filter(([field]) => normalize(form[field]) === "unknown")
    .map(([, label]) => label);
  const additional = form.additional_unknowns
    .split(/\r?\n/u)
    .map((item) => item.replace(/^[-*]\s*/u, "").trim())
    .filter(Boolean);
  return uniqueSorted([...fieldUnknowns, ...additional]);
}

export function createImplementationPromptPack(
  draft: ImplementationPromptDraft,
  form: PromptFormState,
): ImplementationPromptPack {
  return {
    contract_version: "1.0.0",
    dataset_version: draft.dataset_version,
    generated_at: draft.generated_at,
    intent: normalize(form.intent),
    user_problem: {
      decision_variables: normalize(form.decision_variables),
      objective: normalize(form.objective),
      constraints: normalize(form.constraints),
      input_data_format: normalize(form.input_data_format),
      problem_scale: normalize(form.problem_scale),
      evaluation_cost: normalize(form.evaluation_cost),
      computation_budget: normalize(form.computation_budget),
    },
    atlas_context: draft.atlas_context,
    unknowns: unknownsForForm(form),
    environment: {
      programming_language: normalize(form.programming_language),
      preferred_libraries: normalize(form.preferred_libraries),
      prohibited_libraries: normalize(form.prohibited_libraries),
      runtime_environment: normalize(form.runtime_environment),
    },
    requested_outputs: REQUESTED_OUTPUT_OPTIONS
      .map((option) => option.id)
      .filter((id) => form.requested_outputs.includes(id)),
    quality_requirements: [...QUALITY_REQUIREMENTS],
    source_ids: [...draft.source_ids],
  };
}

function valueSection(title: string, value: string): string[] {
  return [`### ${title}`, "", value, ""];
}

function candidateSection(title: string, items: PromptCandidate[]): string[] {
  const lines = [`### ${title}`, ""];
  if (items.length === 0) return [...lines, "- なし", ""];
  items.forEach((item) => {
    lines.push(`- **${item.name}** (\`${item.entity_id}\`)`);
    if (item.summary) lines.push(`  - 概要: ${item.summary}`);
    item.reasons.forEach((reason) => lines.push(`  - 理由: ${reason}`));
    item.warnings.forEach((warning) => lines.push(`  - 注意: ${warning}`));
    if (item.source_ids.length > 0) lines.push(`  - Atlas sources: ${item.source_ids.join(", ")}`);
  });
  return [...lines, ""];
}

export function renderImplementationPromptMarkdown(pack: ImplementationPromptPack): string {
  const outputLabel = new Map(REQUESTED_OUTPUT_OPTIONS.map((option) => [option.id, option.label]));
  const origin = pack.atlas_context.origin.kind === "diagnose"
    ? `Diagnose (${pack.atlas_context.origin.answered_question_count} answered)`
    : `Gallery ${pack.atlas_context.origin.case_id}: ${pack.atlas_context.origin.title}`;
  const lines: string[] = [
    "# 実装用プロンプトパック",
    "",
    "## Metadata",
    "",
    `- Contract version: ${pack.contract_version}`,
    `- Dataset version: ${pack.dataset_version}`,
    `- Generated at: ${pack.generated_at}`,
    `- Atlas origin: ${origin}`,
    "",
    "## ユーザー入力",
    "",
    ...valueSection("やりたいこと", pack.intent),
    ...valueSection("Decision variables", pack.user_problem.decision_variables),
    ...valueSection("Objective / minimize-maximize", pack.user_problem.objective),
    ...valueSection("Constraints", pack.user_problem.constraints),
    ...valueSection("Input data / format", pack.user_problem.input_data_format),
    ...valueSection("Problem scale", pack.user_problem.problem_scale),
    ...valueSection("Evaluation cost", pack.user_problem.evaluation_cost),
    ...valueSection("Computation budget", pack.user_problem.computation_budget),
    "## Unknowns — 最初に確認すること",
    "",
    ...(pack.unknowns.length > 0 ? pack.unknowns.map((item) => `- ${item}`) : ["- なし"]),
    "",
    "## Runtime / implementation environment",
    "",
    `- Programming language: ${pack.environment.programming_language}`,
    `- Preferred libraries: ${pack.environment.preferred_libraries}`,
    `- Prohibited libraries: ${pack.environment.prohibited_libraries}`,
    `- Runtime / deployment: ${pack.environment.runtime_environment}`,
    "",
    "## Atlas由来context（ユーザー入力ではない）",
    "",
    "### Problem features",
    "",
    ...(pack.atlas_context.feature_values.length > 0
      ? pack.atlas_context.feature_values.map((feature) =>
          `- ${feature.feature_name} (\`${feature.feature_id}\`): ${feature.values.map((value) => `${value.label} (\`${value.value_id}\`)`).join(", ")} [${feature.source_ids.join(", ") || "no source ID"}]`)
      : ["- なし"]),
    "",
    ...candidateSection("Problem archetypes", pack.atlas_context.problem_archetypes),
    ...candidateSection("Alternative-first checks", pack.atlas_context.alternatives_first),
    ...candidateSection("First candidates", pack.atlas_context.first_candidates),
    ...candidateSection("Conditional candidates", pack.atlas_context.conditional_candidates),
    ...candidateSection("Excluded methods", pack.atlas_context.excluded_methods),
    "### Representative implementations",
    "",
    ...(pack.atlas_context.implementations.length > 0
      ? pack.atlas_context.implementations.map((item) =>
          `- ${item.library_name || item.solver_name} (\`${item.implementation_id}\`): language=${item.language}, support=${item.support_level}, maintenance=${item.maintenance_status}, docs=${item.official_docs_url || "unknown"}`)
      : ["- なし"]),
    "",
    "### Method assumptions / policies",
    "",
    ...(pack.atlas_context.method_conditions.length > 0
      ? pack.atlas_context.method_conditions.map((item) =>
          `- \`${item.method_id}\` / \`${item.condition_id}\`: ${item.description} [${item.source_ids.join(", ") || "no source ID"}]`)
      : ["- なし"]),
    "",
    "### Failure modes / cautions",
    "",
    ...(pack.atlas_context.failure_modes.length > 0
      ? pack.atlas_context.failure_modes.flatMap((item) => [
          `- **${item.name}** (\`${item.failure_mode_id}\`, severity=${item.severity})`,
          `  - Affected: ${item.affected_entity_ids.join(", ")}`,
          `  - Symptoms: ${item.symptoms.join(" / ") || "unknown"}`,
          `  - Checks: ${item.diagnostic_checks.join(" / ") || "unknown"}`,
          `  - Mitigations: ${item.mitigations.join(" / ") || "unknown"}`,
        ])
      : ["- なし"]),
    "",
    "### Related Atlas entries",
    "",
    ...(pack.atlas_context.related_entities.length > 0
      ? pack.atlas_context.related_entities.map((item) =>
          `- ${item.entity_type} / ${item.relation_type}: ${item.label} (\`${item.entity_id}\`)${item.canonical_url ? ` — ${item.canonical_url}` : ""}`)
      : ["- なし"]),
    "",
    "## Requested outputs",
    "",
    ...(pack.requested_outputs.length > 0
      ? pack.requested_outputs.map((id) => `- ${outputLabel.get(id)}`)
      : ["- 指定なし。unknownの確認質問だけを先に返してください。"]),
    "",
    "## Quality requirements",
    "",
    ...pack.quality_requirements.map((item) => `- ${item}`),
    "",
    "## Source IDs",
    "",
    ...(pack.source_ids.length > 0 ? pack.source_ids.map((item) => `- ${item}`) : ["- なし"]),
    "",
    "まずUnknownsを確認質問として返し、回答後にrequested outputsへ進んでください。",
  ];
  return `${lines.join("\n").trim()}\n`;
}
