export type CoverageStatus = "available" | "partial" | "missing" | "not_applicable";
export type SubjectType = "method" | "problem" | "feature_family";

export interface CoverageReport {
  contract_version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  summary: {
    subject_counts: Record<SubjectType, number>;
    status_counts: Record<CoverageStatus, number>;
    baseline: "not_provided";
  };
  subjects: Array<{
    subject_type: SubjectType;
    subject_id: string;
    label: string;
    dimensions: Record<string, { state: "connected" | "absent" | "broken"; count: number; target_ids: string[]; reason_codes: string[] }>;
  }>;
  expectations: Array<{
    expectation_id: string; subject_type: SubjectType; subject_id: string; purpose: string;
    artifact_kind: string; renderer_family: string; applicability: "expected" | "not_applicable";
    status: CoverageStatus; rationale: string; reason_codes: string[]; scenario_ids: string[];
    artifact_ids: string[]; route_ids: string[]; source_ids: string[]; slice_id: string | null;
  }>;
  priorities: Array<{
    slice_id: string; title_ja: string; title_en: string; rank: number; total: number;
    factors: Record<string, { score: number; reason: string }>;
    proposed_scope: string; source_ids: string[];
  }>;
  integrity_issues: Array<{ code: string; severity: "warning" | "error"; entity_type: string; entity_id: string; detail: string }>;
}

const statuses = ["available", "partial", "missing", "not_applicable"] as const;
const subjectTypes = ["method", "problem", "feature_family"] as const;
const dimensions = ["map", "recommendation", "content", "visualization", "comparison", "gallery", "implementation", "source"] as const;

export function parseCoverageReport(input: unknown): CoverageReport {
  const data = object(input, "coverage");
  exact(data, ["contract_version", "dataset_version", "generated_at", "summary", "subjects", "expectations", "priorities", "integrity_issues"], "coverage");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported coverage contract.");
  const summary = object(data.summary, "summary");
  exact(summary, ["subject_counts", "status_counts", "baseline"], "summary");
  if (summary.baseline !== "not_provided") throw new Error("summary.baseline must be explicit.");
  const subjectCounts = enumCounts(summary.subject_counts, subjectTypes, "subject_counts");
  const statusCounts = enumCounts(summary.status_counts, statuses, "status_counts");
  const subjects = list(data.subjects, "subjects").map((value, index) => {
    const row = object(value, `subjects[${index}]`);
    exact(row, ["subject_type", "subject_id", "label", "dimensions"], `subjects[${index}]`);
    const subjectType = oneOf(row.subject_type, subjectTypes, `subjects[${index}].subject_type`);
    const rawDimensions = object(row.dimensions, `subjects[${index}].dimensions`);
    exact(rawDimensions, dimensions, `subjects[${index}].dimensions`);
    const parsedDimensions: CoverageReport["subjects"][number]["dimensions"] = {};
    dimensions.forEach((name) => {
      const dimension = object(rawDimensions[name], `dimensions.${name}`);
      exact(dimension, ["state", "count", "target_ids", "reason_codes"], `dimensions.${name}`);
      parsedDimensions[name] = {
        state: oneOf(dimension.state, ["connected", "absent", "broken"] as const, `dimensions.${name}.state`),
        count: integer(dimension.count, `dimensions.${name}.count`, 0),
        target_ids: strings(dimension.target_ids, `dimensions.${name}.target_ids`),
        reason_codes: strings(dimension.reason_codes, `dimensions.${name}.reason_codes`),
      };
    });
    return { subject_type: subjectType, subject_id: text(row.subject_id, "subject_id"), label: text(row.label, "label"), dimensions: parsedDimensions };
  });
  const expectations = list(data.expectations, "expectations").map((value, index) => {
    const row = object(value, `expectations[${index}]`);
    exact(row, ["expectation_id", "subject_type", "subject_id", "purpose", "artifact_kind", "renderer_family", "applicability", "status", "rationale", "reason_codes", "scenario_ids", "artifact_ids", "route_ids", "source_ids", "slice_id"], `expectations[${index}]`);
    return {
      expectation_id: text(row.expectation_id, "expectation_id"), subject_type: oneOf(row.subject_type, subjectTypes, "subject_type"),
      subject_id: text(row.subject_id, "subject_id"), purpose: text(row.purpose, "purpose"), artifact_kind: text(row.artifact_kind, "artifact_kind"),
      renderer_family: text(row.renderer_family, "renderer_family"), applicability: oneOf(row.applicability, ["expected", "not_applicable"] as const, "applicability"),
      status: oneOf(row.status, statuses, "status"), rationale: text(row.rationale, "rationale"), reason_codes: strings(row.reason_codes, "reason_codes"),
      scenario_ids: strings(row.scenario_ids, "scenario_ids"), artifact_ids: strings(row.artifact_ids, "artifact_ids"), route_ids: strings(row.route_ids, "route_ids"),
      source_ids: strings(row.source_ids, "source_ids"), slice_id: row.slice_id === null ? null : text(row.slice_id, "slice_id"),
    };
  });
  const priorities = list(data.priorities, "priorities").map((value, index) => {
    const row = object(value, `priorities[${index}]`);
    exact(row, ["slice_id", "title_ja", "title_en", "rank", "total", "factors", "proposed_scope", "source_ids"], `priorities[${index}]`);
    const rawFactors = object(row.factors, "factors");
    exact(rawFactors, ["classification", "misconception", "visualization", "demand"], "factors");
    const factors: Record<string, { score: number; reason: string }> = {};
    Object.entries(rawFactors).forEach(([name, value]) => { const factor = object(value, `factors.${name}`); exact(factor, ["score", "reason"], `factors.${name}`); factors[name] = { score: integer(factor.score, "score", 0, 3), reason: text(factor.reason, "reason") }; });
    return { slice_id: text(row.slice_id, "slice_id"), title_ja: text(row.title_ja, "title_ja"), title_en: text(row.title_en, "title_en"), rank: integer(row.rank, "rank", 1), total: integer(row.total, "total", 0, 12), factors, proposed_scope: text(row.proposed_scope, "proposed_scope"), source_ids: strings(row.source_ids, "source_ids") };
  });
  const integrityIssues = list(data.integrity_issues, "integrity_issues").map((value, index) => { const row = object(value, `integrity_issues[${index}]`); exact(row, ["code", "severity", "entity_type", "entity_id", "detail"], `integrity_issues[${index}]`); return { code: text(row.code, "code"), severity: oneOf(row.severity, ["warning", "error"] as const, "severity"), entity_type: text(row.entity_type, "entity_type"), entity_id: text(row.entity_id, "entity_id"), detail: text(row.detail, "detail") }; });
  return { contract_version: "1.0.0", dataset_version: text(data.dataset_version, "dataset_version"), generated_at: text(data.generated_at, "generated_at"), summary: { subject_counts: subjectCounts, status_counts: statusCounts, baseline: "not_provided" }, subjects, expectations, priorities, integrity_issues: integrityIssues };
}

function object(value: unknown, field: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`); return value as Record<string, unknown>; }
function list(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function exact(value: Record<string, unknown>, keys: readonly string[], field: string): void { const wanted = new Set(keys); const unknown = Object.keys(value).filter((key) => !wanted.has(key)); const missing = keys.filter((key) => !(key in value)); if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`); if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`); }
function text(value: unknown, field: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`); return value; }
function strings(value: unknown, field: string): string[] { return list(value, field).map((item, index) => text(item, `${field}[${index}]`)); }
function integer(value: unknown, field: string, min: number, max = Number.MAX_SAFE_INTEGER): number { if (typeof value !== "number" || !Number.isSafeInteger(value) || value < min || value > max) throw new Error(`${field} must be an integer from ${min} to ${max}.`); return value; }
function oneOf<const T extends readonly string[]>(value: unknown, allowed: T, field: string): T[number] { if (typeof value !== "string" || !allowed.includes(value)) throw new Error(`${field} is invalid.`); return value as T[number]; }
function enumCounts<const T extends readonly string[]>(value: unknown, keys: T, field: string): Record<T[number], number> { const row = object(value, field); exact(row, keys, field); return Object.fromEntries(keys.map((key) => [key, integer(row[key], `${field}.${key}`, 0)])) as Record<T[number], number>; }
