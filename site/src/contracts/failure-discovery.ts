export const FAILURE_DISCOVERY_KINDS = ["structured_failure", "case_exclusion"] as const;
export const FAILURE_DISCOVERY_DISPOSITIONS = [
  "excluded", "warning", "conditional", "observed_failure", "unsupported",
] as const;

export type FailureDiscoveryKind = typeof FAILURE_DISCOVERY_KINDS[number];
export type FailureDiscoveryDisposition = typeof FAILURE_DISCOVERY_DISPOSITIONS[number];

export interface FailureDiscoveryMitigation {
  action: string;
  applicability: string;
  tradeoff: string;
}

export interface FailureCaseContext {
  question: string;
  decision_variables: string;
  objective: string;
  constraints: string;
}

export interface FailureDiscoveryEntry {
  entry_id: string;
  entry_kind: FailureDiscoveryKind;
  disposition: FailureDiscoveryDisposition;
  title_ja: string;
  title_en: string;
  summary: string;
  scope: "method_theory" | "implementation_specific" | "mixed" | "case_specific";
  severity: "critical" | "high" | "warning" | "info" | "not_applicable";
  recoverability: "recoverable" | "conditional" | "fatal" | "not_applicable";
  confidence: "high" | "medium" | "low" | "unverified" | "not_applicable";
  failure_mode_id: string | null;
  case_id: string | null;
  method_ids: string[];
  implementation_ids: string[];
  feature_ids: string[];
  scenario_ids: string[];
  source_ids: string[];
  symptoms: string[];
  diagnostics: string[];
  mitigations: FailureDiscoveryMitigation[];
  related_failure_mode_ids: string[];
  case_context: FailureCaseContext | null;
  canonical_route: string;
  last_verified: string;
}

export interface FailureDiscoveryIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  summary: {
    total_entries: number;
    structured_failure_count: number;
    case_exclusion_count: number;
    entries_with_scenarios: number;
  };
  entries: FailureDiscoveryEntry[];
}

export function parseFailureDiscoveryIndex(value: unknown): FailureDiscoveryIndex {
  const data = record(value, "failure discovery index");
  exactKeys(
    data,
    ["contract_version", "dataset_version", "generated_at", "summary", "entries"],
    "failure discovery index",
  );
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported failure discovery contract.");
  const entries = array(data.entries, "entries").map(parseEntry);
  const ids = entries.map((entry) => entry.entry_id);
  if (new Set(ids).size !== ids.length || ids.some((id, index) => index > 0 && id < ids[index - 1]!)) {
    throw new Error("Failure discovery entries must have unique sorted IDs.");
  }
  const summaryData = record(data.summary, "summary");
  exactKeys(
    summaryData,
    ["total_entries", "structured_failure_count", "case_exclusion_count", "entries_with_scenarios"],
    "summary",
  );
  const summary = {
    total_entries: integer(summaryData.total_entries, "total_entries"),
    structured_failure_count: integer(summaryData.structured_failure_count, "structured_failure_count"),
    case_exclusion_count: integer(summaryData.case_exclusion_count, "case_exclusion_count"),
    entries_with_scenarios: integer(summaryData.entries_with_scenarios, "entries_with_scenarios"),
  };
  const expected = {
    total_entries: entries.length,
    structured_failure_count: entries.filter((entry) => entry.entry_kind === "structured_failure").length,
    case_exclusion_count: entries.filter((entry) => entry.entry_kind === "case_exclusion").length,
    entries_with_scenarios: entries.filter((entry) => entry.scenario_ids.length > 0).length,
  };
  if (JSON.stringify(summary) !== JSON.stringify(expected)) {
    throw new Error("Failure discovery summary must be derived from entries.");
  }
  const failureIds = new Set(entries.flatMap((entry) => entry.failure_mode_id ? [entry.failure_mode_id] : []));
  for (const entry of entries) {
    const missing = entry.related_failure_mode_ids.filter((id) => !failureIds.has(id));
    if (missing.length) throw new Error(`Failure discovery entry has dangling failure links: ${missing.join(", ")}.`);
  }
  return {
    contract_version: "1.0.0",
    dataset_version: text(data.dataset_version, "dataset_version"),
    generated_at: text(data.generated_at, "generated_at"),
    summary,
    entries,
  };
}

function parseEntry(value: unknown, index: number): FailureDiscoveryEntry {
  const field = `entries[${index}]`;
  const data = record(value, field);
  exactKeys(data, [
    "entry_id", "entry_kind", "disposition", "title_ja", "title_en", "summary", "scope",
    "severity", "recoverability", "confidence", "failure_mode_id", "case_id", "method_ids",
    "implementation_ids", "feature_ids", "scenario_ids", "source_ids", "symptoms", "diagnostics",
    "mitigations", "related_failure_mode_ids", "case_context", "canonical_route", "last_verified",
  ], field);
  const entry_kind = enumValue(data.entry_kind, FAILURE_DISCOVERY_KINDS, `${field}.entry_kind`);
  const disposition = enumValue(data.disposition, FAILURE_DISCOVERY_DISPOSITIONS, `${field}.disposition`);
  const scope = enumValue(
    data.scope,
    ["method_theory", "implementation_specific", "mixed", "case_specific"] as const,
    `${field}.scope`,
  );
  const severity = enumValue(
    data.severity,
    ["critical", "high", "warning", "info", "not_applicable"] as const,
    `${field}.severity`,
  );
  const recoverability = enumValue(
    data.recoverability,
    ["recoverable", "conditional", "fatal", "not_applicable"] as const,
    `${field}.recoverability`,
  );
  const confidence = enumValue(
    data.confidence,
    ["high", "medium", "low", "unverified", "not_applicable"] as const,
    `${field}.confidence`,
  );
  const failure_mode_id = nullableText(data.failure_mode_id, `${field}.failure_mode_id`);
  const case_id = nullableText(data.case_id, `${field}.case_id`);
  const case_context = data.case_context === null ? null : parseContext(data.case_context, `${field}.case_context`);
  const canonical_route = text(data.canonical_route, `${field}.canonical_route`);
  if (!canonical_route.startsWith("/failures?entry=")) throw new Error(`${field}.canonical_route is invalid.`);
  const entry: FailureDiscoveryEntry = {
    entry_id: text(data.entry_id, `${field}.entry_id`), entry_kind, disposition,
    title_ja: text(data.title_ja, `${field}.title_ja`), title_en: text(data.title_en, `${field}.title_en`),
    summary: text(data.summary, `${field}.summary`), scope, severity, recoverability, confidence,
    failure_mode_id, case_id,
    method_ids: uniqueStrings(data.method_ids, `${field}.method_ids`),
    implementation_ids: uniqueStrings(data.implementation_ids, `${field}.implementation_ids`),
    feature_ids: uniqueStrings(data.feature_ids, `${field}.feature_ids`),
    scenario_ids: uniqueStrings(data.scenario_ids, `${field}.scenario_ids`),
    source_ids: uniqueStrings(data.source_ids, `${field}.source_ids`),
    symptoms: uniqueStrings(data.symptoms, `${field}.symptoms`),
    diagnostics: uniqueStrings(data.diagnostics, `${field}.diagnostics`),
    mitigations: array(data.mitigations, `${field}.mitigations`).map((item, mitigationIndex) => {
      const mitigation = record(item, `${field}.mitigations[${mitigationIndex}]`);
      exactKeys(mitigation, ["action", "applicability", "tradeoff"], `${field}.mitigations[${mitigationIndex}]`);
      return {
        action: text(mitigation.action, "action"),
        applicability: text(mitigation.applicability, "applicability"),
        tradeoff: text(mitigation.tradeoff, "tradeoff"),
      };
    }),
    related_failure_mode_ids: uniqueStrings(data.related_failure_mode_ids, `${field}.related_failure_mode_ids`),
    case_context, canonical_route, last_verified: text(data.last_verified, `${field}.last_verified`),
  };
  if (entry_kind === "structured_failure") {
    if (!failure_mode_id || case_id || case_context || scope === "case_specific" || severity === "not_applicable") {
      throw new Error(`${field} has inconsistent structured-failure semantics.`);
    }
    if (!entry.symptoms.length || !entry.diagnostics.length || !entry.mitigations.length) {
      throw new Error(`${field} requires symptoms, diagnostics, and mitigations.`);
    }
  } else if (!case_id || failure_mode_id || !case_context || entry.method_ids.length !== 1
    || disposition !== "excluded" || scope !== "case_specific"
    || severity !== "not_applicable" || recoverability !== "not_applicable"
    || confidence !== "not_applicable") {
    throw new Error(`${field} has inconsistent Case-exclusion semantics.`);
  }
  return entry;
}

function parseContext(value: unknown, field: string): FailureCaseContext {
  const data = record(value, field);
  exactKeys(data, ["question", "decision_variables", "objective", "constraints"], field);
  return {
    question: text(data.question, `${field}.question`),
    decision_variables: text(data.decision_variables, `${field}.decision_variables`),
    objective: text(data.objective, `${field}.objective`),
    constraints: text(data.constraints, `${field}.constraints`),
  };
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`);
  return value as Record<string, unknown>;
}
function array(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value;
}
function text(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`);
  return value;
}
function nullableText(value: unknown, field: string): string | null { return value === null ? null : text(value, field); }
function integer(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) throw new Error(`${field} must be a non-negative integer.`);
  return value;
}
function uniqueStrings(value: unknown, field: string): string[] {
  const result = array(value, field).map((item, index) => text(item, `${field}[${index}]`));
  if (new Set(result).size !== result.length || result.some((item, index) => index > 0 && item < result[index - 1]!)) {
    throw new Error(`${field} must be unique and sorted.`);
  }
  return result;
}
function enumValue<const T extends readonly string[]>(value: unknown, allowed: T, field: string): T[number] {
  if (typeof value !== "string" || !allowed.includes(value)) throw new Error(`${field} is invalid.`);
  return value as T[number];
}
function exactKeys(data: Record<string, unknown>, expected: readonly string[], field: string): void {
  const allowed = new Set(expected);
  const unknown = Object.keys(data).filter((key) => !allowed.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key));
  if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`);
  if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`);
}
