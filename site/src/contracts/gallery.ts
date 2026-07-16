export interface GalleryCase {
  case_id: string; title_ja: string; title_en: string; domain: string; problem_archetype_id: string;
  feature_values: { feature_id: string; value: string }[]; question_answers: Record<string, string>;
  candidate_methods: { method_id: string; reason: string }[]; conditional_methods: { method_id: string; reason: string }[];
  excluded_methods: { method_id: string; reason: string }[]; implementation_ids: string[];
  visualization_ids: string[]; comparison_ids: string[]; source_ids: string[]; difficulty: "intro" | "intermediate";
  status: "published" | "draft"; last_reviewed: string; question: string; decision_variables: string;
  objective: string; constraints: string; map_node_id: string; python_example: string; practical_notes: string;
  limitations: string[];
}
export interface GalleryIndex { contract_version: "2.0.0"; dataset_version: string; cases: GalleryCase[] }

export function parseGalleryIndex(raw: unknown): GalleryIndex {
  const data = object(raw, "gallery");
  if (data.contract_version !== "2.0.0") throw new Error("Unsupported gallery contract.");
  const cases = array(data.cases, "gallery cases").map((rawCase, index) => {
    const item = object(rawCase, `gallery case ${index}`);
    if ("candidate_method_ids" in item) throw new Error("candidate_method_ids has been replaced by candidate_methods.");
    const difficulty = string(item.difficulty, "difficulty");
    if (difficulty !== "intro" && difficulty !== "intermediate") throw new Error(`Unsupported difficulty: ${difficulty}`);
    return {
      case_id: nonEmpty(item.case_id, "case_id"), title_ja: nonEmpty(item.title_ja, "title_ja"), title_en: nonEmpty(item.title_en, "title_en"),
      domain: nonEmpty(item.domain, "domain"), problem_archetype_id: nonEmpty(item.problem_archetype_id, "problem_archetype_id"),
      feature_values: array(item.feature_values, "feature_values").map((value) => { const row = object(value, "feature value"); return { feature_id: nonEmpty(row.feature_id, "feature_id"), value: nonEmpty(row.value, "value") }; }),
      question_answers: record(item.question_answers, "question_answers"), candidate_methods: nonEmptyMethodReasons(item.candidate_methods, "candidate_methods"),
      conditional_methods: methodReasons(item.conditional_methods, "conditional_methods"),
      excluded_methods: array(item.excluded_methods, "excluded_methods").map((value) => { const row = object(value, "excluded method"); return { method_id: nonEmpty(row.method_id, "method_id"), reason: nonEmpty(row.reason, "reason") }; }),
      implementation_ids: strings(item.implementation_ids, "implementation_ids"), visualization_ids: strings(item.visualization_ids, "visualization_ids"), comparison_ids: strings(item.comparison_ids, "comparison_ids"), source_ids: strings(item.source_ids, "source_ids"),
      difficulty, status: contentStatus(item.status), last_reviewed: nonEmpty(item.last_reviewed, "last_reviewed"), question: nonEmpty(item.question, "question"), decision_variables: nonEmpty(item.decision_variables, "decision_variables"), objective: nonEmpty(item.objective, "objective"), constraints: nonEmpty(item.constraints, "constraints"), map_node_id: nonEmpty(item.map_node_id, "map_node_id"), python_example: nonEmpty(item.python_example, "python_example"), practical_notes: nonEmpty(item.practical_notes, "practical_notes"), limitations: nonEmptyStrings(item.limitations, "limitations"),
    } satisfies GalleryCase;
  });
  if (new Set(cases.map((item) => item.case_id)).size !== cases.length) throw new Error("Duplicate gallery case ID.");
  return { contract_version: "2.0.0", dataset_version: nonEmpty(data.dataset_version, "dataset_version"), cases };
}
function object(value: unknown, owner: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`); return value as Record<string, unknown>; }
function record(value: unknown, owner: string): Record<string, string> { const row = object(value, owner); const result: Record<string, string> = {}; for (const [key, item] of Object.entries(row)) result[nonEmpty(key, owner)] = nonEmpty(item, `${owner}.${key}`); return result; }
function array(value: unknown, owner: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`); return value; }
function string(value: unknown, owner: string): string { if (typeof value !== "string") throw new Error(`${owner} must be a string.`); return value; }
function nonEmpty(value: unknown, owner: string): string { const result = string(value, owner); if (!result.trim()) throw new Error(`${owner} must not be blank.`); return result; }
function strings(value: unknown, owner: string): string[] { return array(value, owner).map((item, index) => nonEmpty(item, `${owner}[${index}]`)); }
function nonEmptyStrings(value: unknown, owner: string): string[] { const result = strings(value, owner); if (result.length === 0) throw new Error(`${owner} must not be empty.`); return result; }
function methodReasons(value: unknown, owner: string): { method_id: string; reason: string }[] { return array(value, owner).map((item) => { const row = object(item, owner); return { method_id: nonEmpty(row.method_id, `${owner}.method_id`), reason: nonEmpty(row.reason, `${owner}.reason`) }; }); }
function nonEmptyMethodReasons(value: unknown, owner: string): { method_id: string; reason: string }[] { const result = methodReasons(value, owner); if (result.length === 0) throw new Error(`${owner} must not be empty.`); return result; }
function contentStatus(value: unknown): "published" | "draft" { if (value === "published" || value === "draft") return value; throw new Error(`Unsupported gallery status: ${String(value)}`); }
