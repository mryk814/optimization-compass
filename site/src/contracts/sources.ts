export interface FreshnessRule { source_type: string; max_age_days: number }
export interface EvidenceTarget {
  evidence_link_id: string; target_table: string; target_id: string; target_type: string;
  label: string; canonical_url: string | null; external_url: string | null;
  supported_field: string; claim_summary: string; evidence_role: string;
  confidence: string; last_verified: string;
}
export interface SourceRecord {
  source_id: string; source_type: string; title: string; publisher: string;
  publication_date: string | null; last_verified: string; official_url: string;
  license: "unknown"; access_note: string; supported_claim: string;
  source_quality: string; currentness_status: string; evidence_targets: EvidenceTarget[];
}
export interface SourceEvidenceIndex {
  contract_version: "1.0.0"; dataset_version: string; generated_at: string;
  freshness_policy: FreshnessRule[]; sources: SourceRecord[];
}

export function parseSourceEvidenceIndex(input: unknown): SourceEvidenceIndex {
  const data = record(input, "source evidence index");
  exact(data, ["contract_version", "dataset_version", "generated_at", "freshness_policy", "sources"], "source evidence index");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported source evidence contract.");
  const freshnessPolicy = array(data.freshness_policy, "freshness_policy").map((value, index) => {
    const rule = record(value, `freshness_policy[${index}]`);
    exact(rule, ["source_type", "max_age_days"], `freshness_policy[${index}]`);
    return { source_type: text(rule.source_type, "source_type"), max_age_days: positiveInteger(rule.max_age_days, "max_age_days") };
  });
  const sources = array(data.sources, "sources").map(parseSource);
  const ids = new Set<string>(); const evidenceIds = new Set<string>();
  for (const source of sources) {
    if (ids.has(source.source_id)) throw new Error(`Duplicate source ID: ${source.source_id}.`);
    ids.add(source.source_id);
    for (const target of source.evidence_targets) {
      if (evidenceIds.has(target.evidence_link_id)) throw new Error(`Duplicate evidence link ID: ${target.evidence_link_id}.`);
      evidenceIds.add(target.evidence_link_id);
    }
  }
  return { contract_version: "1.0.0", dataset_version: text(data.dataset_version, "dataset_version"), generated_at: isoDateTime(data.generated_at, "generated_at"), freshness_policy: freshnessPolicy, sources };
}

function parseSource(value: unknown, index: number): SourceRecord {
  const data = record(value, `sources[${index}]`);
  exact(data, ["source_id", "source_type", "title", "publisher", "publication_date", "last_verified", "official_url", "license", "access_note", "supported_claim", "source_quality", "currentness_status", "evidence_targets"], `sources[${index}]`);
  if (data.license !== "unknown") throw new Error(`sources[${index}].license is unsupported.`);
  return {
    source_id: text(data.source_id, "source_id"), source_type: text(data.source_type, "source_type"),
    title: text(data.title, "title"), publisher: text(data.publisher, "publisher"),
    publication_date: nullableText(data.publication_date, "publication_date"),
    last_verified: isoDate(data.last_verified, "last_verified"), official_url: httpUrl(data.official_url, "official_url"),
    license: "unknown", access_note: text(data.access_note, "access_note"), supported_claim: string(data.supported_claim, "supported_claim"),
    source_quality: string(data.source_quality, "source_quality"), currentness_status: string(data.currentness_status, "currentness_status"),
    evidence_targets: array(data.evidence_targets, "evidence_targets").map(parseTarget),
  };
}
function parseTarget(value: unknown, index: number): EvidenceTarget {
  const data = record(value, `evidence_targets[${index}]`);
  exact(data, ["evidence_link_id", "target_table", "target_id", "target_type", "label", "canonical_url", "external_url", "supported_field", "claim_summary", "evidence_role", "confidence", "last_verified"], `evidence_targets[${index}]`);
  return {
    evidence_link_id: text(data.evidence_link_id, "evidence_link_id"), target_table: text(data.target_table, "target_table"),
    target_id: text(data.target_id, "target_id"), target_type: text(data.target_type, "target_type"), label: text(data.label, "label"),
    canonical_url: nullableRoute(data.canonical_url, "canonical_url"), external_url: nullableHttpUrl(data.external_url, "external_url"),
    supported_field: string(data.supported_field, "supported_field"), claim_summary: string(data.claim_summary, "claim_summary"),
    evidence_role: string(data.evidence_role, "evidence_role"), confidence: text(data.confidence, "confidence"), last_verified: isoDate(data.last_verified, "last_verified"),
  };
}
function record(value: unknown, field: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function exact(data: Record<string, unknown>, keys: string[], field: string): void { const expected = new Set(keys); const unknown = Object.keys(data).filter((key) => !expected.has(key)); const missing = keys.filter((key) => !(key in data)); if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`); if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`); }
function string(value: unknown, field: string): string { if (typeof value !== "string") throw new Error(`${field} must be a string.`); return value; }
function text(value: unknown, field: string): string { const result = string(value, field); if (!result.trim()) throw new Error(`${field} must be non-empty.`); return result; }
function nullableText(value: unknown, field: string): string | null { return value === null ? null : text(value, field); }
function positiveInteger(value: unknown, field: string): number { if (typeof value !== "number" || !Number.isSafeInteger(value) || value <= 0) throw new Error(`${field} must be a positive integer.`); return value; }
function isoDate(value: unknown, field: string): string { const result = text(value, field); if (!/^\d{4}-\d{2}-\d{2}$/u.test(result)) throw new Error(`${field} must be an ISO date.`); return result; }
function isoDateTime(value: unknown, field: string): string { const result = text(value, field); if (Number.isNaN(Date.parse(result))) throw new Error(`${field} must be an ISO datetime.`); return result; }
function httpUrl(value: unknown, field: string): string { const result = text(value, field); const url = new URL(result); if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) throw new Error(`${field} must be a safe HTTP(S) URL.`); return result; }
function nullableHttpUrl(value: unknown, field: string): string | null { return value === null ? null : httpUrl(value, field); }
function nullableRoute(value: unknown, field: string): string | null { if (value === null) return null; const result = text(value, field); if (!result.startsWith('/') || result.startsWith('//')) throw new Error(`${field} must be a site route.`); return result; }
