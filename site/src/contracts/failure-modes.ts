export interface FailureModeRecord {
  failure_mode_id: string;
  name_ja: string;
  name_en: string;
  failure_scope: "method_theory" | "implementation_specific" | "mixed";
  severity: "critical" | "high" | "warning" | "info";
  recoverability: "recoverable" | "conditional" | "fatal";
  confidence: "high" | "medium" | "low" | "unverified";
  source_ids: string[];
  symptoms: Array<{ description: string; observable_id: string | null; non_visual_state: string | null }>;
  diagnostics: Array<{ diagnostic_id: string; check_text: string }>;
  mitigations: Array<{ action: string; applicability: string; tradeoff: string }>;
  affected_entities: Array<{ entity_type: "method" | "implementation" | "feature"; entity_id: string; specificity: string }>;
  scenario_ids: string[];
}

export interface FailureModeIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  failure_modes: FailureModeRecord[];
}

export function parseFailureModeIndex(value: unknown): FailureModeIndex {
  const data = object(value, "failure mode index");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported failure mode contract.");
  return {
    contract_version: "1.0.0",
    dataset_version: text(data.dataset_version, "dataset_version"),
    failure_modes: list(data.failure_modes, "failure_modes").map((item, index) => {
      const row = object(item, `failure_modes[${index}]`);
      return {
        failure_mode_id: text(row.failure_mode_id, "failure_mode_id"),
        name_ja: text(row.name_ja, "name_ja"),
        name_en: text(row.name_en, "name_en"),
        failure_scope: oneOf(row.failure_scope, ["method_theory", "implementation_specific", "mixed"] as const, "failure_scope"),
        severity: oneOf(row.severity, ["critical", "high", "warning", "info"] as const, "severity"),
        recoverability: oneOf(row.recoverability, ["recoverable", "conditional", "fatal"] as const, "recoverability"),
        confidence: oneOf(row.confidence, ["high", "medium", "low", "unverified"] as const, "confidence"),
        source_ids: texts(row.source_ids, "source_ids"),
        symptoms: list(row.symptoms, "symptoms").map((item) => {
          const symptom = object(item, "symptom");
          return { description: text(symptom.description, "description"), observable_id: nullableText(symptom.observable_id), non_visual_state: nullableText(symptom.non_visual_state) };
        }),
        diagnostics: list(row.diagnostics, "diagnostics").map((item) => {
          const diagnostic = object(item, "diagnostic");
          return { diagnostic_id: text(diagnostic.diagnostic_id, "diagnostic_id"), check_text: text(diagnostic.check_text, "check_text") };
        }),
        mitigations: list(row.mitigations, "mitigations").map((item) => {
          const mitigation = object(item, "mitigation");
          return { action: text(mitigation.action, "action"), applicability: text(mitigation.applicability, "applicability"), tradeoff: text(mitigation.tradeoff, "tradeoff") };
        }),
        affected_entities: list(row.affected_entities, "affected_entities").map((item) => {
          const affected = object(item, "affected entity");
          return { entity_type: oneOf(affected.entity_type, ["method", "implementation", "feature"] as const, "entity_type"), entity_id: text(affected.entity_id, "entity_id"), specificity: text(affected.specificity, "specificity") };
        }),
        scenario_ids: texts(row.scenario_ids, "scenario_ids"),
      };
    }),
  };
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`);
  return value as Record<string, unknown>;
}
function list(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function text(value: unknown, field: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`); return value; }
function nullableText(value: unknown): string | null { return value === null ? null : text(value, "nullable text"); }
function texts(value: unknown, field: string): string[] { return list(value, field).map((item) => text(item, field)); }
function oneOf<const T extends readonly string[]>(value: unknown, values: T, field: string): T[number] { if (!values.includes(value as T[number])) throw new Error(`${field} is invalid.`); return value as T[number]; }
