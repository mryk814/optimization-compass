export const SEARCH_ENTITY_TYPES = [
  "case", "comparison", "content", "feature", "feature_value", "glossary",
  "implementation", "method", "problem", "source", "trace", "view",
] as const;

export const SEARCH_INTENTS = [
  "classify_problem", "understand_method", "find_implementation",
  "compare_visualize", "check_evidence", "find_case",
] as const;

export const SEARCH_FIELDS = [
  "canonical_label", "alias", "title", "summary", "keyword", "related",
] as const;

export type SearchEntityType = typeof SEARCH_ENTITY_TYPES[number];
export type SearchIntent = typeof SEARCH_INTENTS[number];
export type SearchField = typeof SEARCH_FIELDS[number];

export interface SearchFields {
  canonical_label: string[];
  alias: string[];
  title: string[];
  summary: string[];
  keyword: string[];
  related: string[];
}

export interface SearchDocument {
  document_id: string;
  entity_type: SearchEntityType;
  entity_id: string;
  canonical_route: string;
  external_url: string | null;
  title_ja: string;
  title_en: string;
  summary: string;
  intents: SearchIntent[];
  domains: string[];
  source_ids: string[];
  related_document_ids: string[];
  last_reviewed: string | null;
  content_status: string;
  search_visibility: "public";
  fields: SearchFields;
  tokens: SearchFields;
}

export interface SearchIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  normalization: Record<string, string>;
  ranking_policy: Record<SearchField, number>;
  documents: SearchDocument[];
}

export interface SearchHit {
  document: SearchDocument;
  score: number;
  matchedFields: SearchField[];
}

const STOP_TOKENS = new Set([
  "あり", "いる", "から", "こと", "した", "する", "たい", "でき", "です",
  "とは", "ない", "ます", "まで", "もの", "最適", "適化", "手法", "方法", "問題",
]);

const FIELD_WEIGHTS: Record<SearchField, number> = {
  canonical_label: 120,
  alias: 105,
  title: 90,
  summary: 45,
  keyword: 55,
  related: 30,
};

const TYPE_PRIORITY = new Map<SearchEntityType, number>(
  ["method", "problem", "case", "implementation", "content", "glossary", "comparison", "trace", "source", "feature", "feature_value", "view"]
    .map((type, index) => [type as SearchEntityType, index]),
);

export function normalizeSearchText(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase().replace(/[\s\-_‐‑‒–—―/・,、。:：;；()（）[\]{}]+/gu, " ").trim();
}

export function lexicalTokens(value: string): string[] {
  const normalized = normalizeSearchText(value);
  const tokens = new Set(normalized.match(/[a-z0-9]+(?:\.[a-z0-9]+)*/gu) ?? []);
  for (const part of normalized.split(" ")) if (part.length > 1) tokens.add(part);
  for (const run of normalized.match(/[\u3040-\u30ff\u3400-\u9fff]+/gu) ?? []) {
    if (run.length === 1) tokens.add(run);
    else for (let index = 0; index < run.length - 1; index += 1) tokens.add(run.slice(index, index + 2));
  }
  return [...tokens].filter((token) => !STOP_TOKENS.has(token)).sort();
}

export function searchDocuments(
  index: SearchIndex,
  query: string,
  filters: { entityTypes?: ReadonlySet<SearchEntityType>; intent?: SearchIntent } = {},
): SearchHit[] {
  const normalizedQuery = normalizeSearchText(query);
  const queryTokens = new Set(lexicalTokens(query));
  if (!normalizedQuery) return [];
  const hits: SearchHit[] = [];
  for (const document of index.documents) {
    if (filters.entityTypes?.size && !filters.entityTypes.has(document.entity_type)) continue;
    if (filters.intent && !document.intents.includes(filters.intent)) continue;
    let score = 0;
    const matchedFields: SearchField[] = [];
    for (const field of SEARCH_FIELDS) {
      const values = document.fields[field].map(normalizeSearchText);
      const weight = FIELD_WEIGHTS[field];
      let fieldScore = 0;
      if (values.includes(normalizedQuery)) {
        fieldScore = ({ canonical_label: 6000, alias: 5500, title: 5000 } as Partial<Record<SearchField, number>>)[field] ?? 4000;
        fieldScore += weight;
      } else if (normalizedQuery.length >= 3 && values.some((value) => value.startsWith(normalizedQuery))) fieldScore = 2500 + weight;
      else if (normalizedQuery.length >= 3 && values.some((value) => value.includes(normalizedQuery))) fieldScore = 1000 + weight;
      else {
        const overlap = document.tokens[field].filter((token) => queryTokens.has(token)).length;
        if (overlap) fieldScore = weight + Math.min(overlap, 6) * 4;
      }
      if (fieldScore) {
        score += fieldScore;
        matchedFields.push(field);
      }
    }
    if (score) hits.push({ document, score, matchedFields });
  }
  return hits.sort((left, right) => right.score - left.score
    || (TYPE_PRIORITY.get(left.document.entity_type) ?? 99) - (TYPE_PRIORITY.get(right.document.entity_type) ?? 99)
    || left.document.document_id.localeCompare(right.document.document_id));
}

export function parseSearchIndex(input: unknown): SearchIndex {
  const data = record(input, "SearchIndex");
  exactKeys(data, ["contract_version", "dataset_version", "generated_at", "normalization", "ranking_policy", "documents"], "SearchIndex");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported SearchIndex version.");
  const documents = array(data.documents, "documents").map(parseDocument);
  const ids = documents.map((document) => document.document_id);
  if (new Set(ids).size !== ids.length || ids.some((id, index) => index > 0 && id < ids[index - 1]!)) {
    throw new Error("Search documents must have unique sorted IDs.");
  }
  const ranking = record(data.ranking_policy, "ranking_policy");
  exactKeys(ranking, SEARCH_FIELDS, "ranking_policy");
  const ranking_policy = Object.fromEntries(SEARCH_FIELDS.map((field) => [field, number(ranking[field], `ranking_policy.${field}`)])) as Record<SearchField, number>;
  const normalizationData = record(data.normalization, "normalization");
  return {
    contract_version: "1.0.0",
    dataset_version: string(data.dataset_version, "dataset_version"),
    generated_at: string(data.generated_at, "generated_at"),
    normalization: Object.fromEntries(Object.entries(normalizationData).map(([key, value]) => [key, string(value, `normalization.${key}`)])),
    ranking_policy,
    documents,
  };
}

function parseDocument(value: unknown, index: number): SearchDocument {
  const field = `documents[${index}]`;
  const data = record(value, field);
  exactKeys(data, ["document_id", "entity_type", "entity_id", "canonical_route", "external_url", "title_ja", "title_en", "summary", "intents", "domains", "source_ids", "related_document_ids", "last_reviewed", "content_status", "search_visibility", "fields", "tokens"], field);
  const entity_type = enumValue(data.entity_type, SEARCH_ENTITY_TYPES, `${field}.entity_type`);
  const canonical_route = string(data.canonical_route, `${field}.canonical_route`);
  if (!canonical_route.startsWith("/") || canonical_route.startsWith("//") || canonical_route.includes("#")) throw new Error(`${field}.canonical_route is invalid.`);
  if (data.search_visibility !== "public") throw new Error(`${field}.search_visibility is invalid.`);
  return {
    document_id: string(data.document_id, `${field}.document_id`), entity_type,
    entity_id: string(data.entity_id, `${field}.entity_id`), canonical_route,
    external_url: nullableString(data.external_url, `${field}.external_url`),
    title_ja: string(data.title_ja, `${field}.title_ja`), title_en: string(data.title_en, `${field}.title_en`),
    summary: typeof data.summary === "string" ? data.summary : fail(`${field}.summary must be a string.`),
    intents: array(data.intents, `${field}.intents`).map((item) => enumValue(item, SEARCH_INTENTS, `${field}.intents`)),
    domains: strings(data.domains, `${field}.domains`), source_ids: strings(data.source_ids, `${field}.source_ids`),
    related_document_ids: strings(data.related_document_ids, `${field}.related_document_ids`),
    last_reviewed: nullableString(data.last_reviewed, `${field}.last_reviewed`),
    content_status: string(data.content_status, `${field}.content_status`), search_visibility: "public",
    fields: parseFields(data.fields, `${field}.fields`), tokens: parseFields(data.tokens, `${field}.tokens`),
  };
}

function parseFields(value: unknown, field: string): SearchFields {
  const data = record(value, field); exactKeys(data, SEARCH_FIELDS, field);
  return Object.fromEntries(SEARCH_FIELDS.map((name) => [name, strings(data[name], `${field}.${name}`)])) as unknown as SearchFields;
}

function record(value: unknown, field: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function strings(value: unknown, field: string): string[] { return array(value, field).map((item, index) => string(item, `${field}[${index}]`)); }
function string(value: unknown, field: string): string { if (typeof value !== "string" || !value) throw new Error(`${field} must be non-empty.`); return value; }
function nullableString(value: unknown, field: string): string | null { if (value === null) return null; return string(value, field); }
function number(value: unknown, field: string): number { if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${field} must be a number.`); return value; }
function enumValue<const T extends readonly string[]>(value: unknown, allowed: T, field: string): T[number] { if (typeof value !== "string" || !allowed.includes(value)) throw new Error(`${field} is invalid.`); return value as T[number]; }
function exactKeys(data: Record<string, unknown>, expected: readonly string[], field: string): void { const keys = new Set(expected); const unknown = Object.keys(data).filter((key) => !keys.has(key)); const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key)); if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`); if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`); }
function fail(message: string): never { throw new Error(message); }
