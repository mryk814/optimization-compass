export interface ComparisonSet { comparison_id: string; title_ja: string; title_en: string; objective_id: string; objective_expression: string; initial_point: number[]; budget: number; stopping: string; fairness_note: string; members: { method_id: string; trace_id: string; label: string; parameters: Record<string, number> }[]; }
export interface ComparisonIndex { contract_version: "1.0.0"; dataset_version: string; comparisons: ComparisonSet[] }
export function parseComparisonIndex(raw: unknown): ComparisonIndex {
  const data = object(raw, "comparisons");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported comparison contract.");
  const comparisons = array(data.comparisons, "comparisons").map((value, index) => {
    const item = object(value, `comparison ${index}`);
    const budget = number(item.budget, "budget"); const initialPoint = array(item.initial_point, "initial_point").map((point) => number(point, "initial_point")); if (!Number.isInteger(budget) || budget <= 0) throw new Error("comparison budget must be a positive integer."); if (initialPoint.length !== 2) throw new Error("comparison initial_point must be two-dimensional.");
    const members = array(item.members, "members").map((member) => { const row = object(member, "comparison member"); return { method_id: nonEmpty(row.method_id, "method_id"), trace_id: nonEmpty(row.trace_id, "trace_id"), label: nonEmpty(row.label, "label"), parameters: numericRecord(row.parameters, "parameters") }; });
    if (members.length === 0 || new Set(members.map((member) => member.trace_id)).size !== members.length || new Set(members.map((member) => member.method_id)).size !== members.length) throw new Error("comparison members must be non-empty and unique.");
    return { comparison_id: nonEmpty(item.comparison_id, "comparison_id"), title_ja: nonEmpty(item.title_ja, "title_ja"), title_en: nonEmpty(item.title_en, "title_en"), objective_id: nonEmpty(item.objective_id, "objective_id"), objective_expression: nonEmpty(item.objective_expression, "objective_expression"), initial_point: initialPoint, budget, stopping: nonEmpty(item.stopping, "stopping"), fairness_note: nonEmpty(item.fairness_note, "fairness_note"), members } satisfies ComparisonSet;
  });
  if (new Set(comparisons.map((item) => item.comparison_id)).size !== comparisons.length) throw new Error("Duplicate comparison ID.");
  return { contract_version: "1.0.0", dataset_version: nonEmpty(data.dataset_version, "dataset_version"), comparisons };
}
function object(value: unknown, owner: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, owner: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`); return value; }
function nonEmpty(value: unknown, owner: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${owner} must be non-empty.`); return value; }
function number(value: unknown, owner: string): number { if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${owner} must be finite.`); return value; }
function numericRecord(value: unknown, owner: string): Record<string, number> { const row = object(value, owner); return Object.fromEntries(Object.entries(row).map(([key, item]) => [key, number(item, `${owner}.${key}`)])); }
