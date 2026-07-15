export type LearningEntityType =
  | "method" | "problem" | "feature" | "case" | "implementation"
  | "scenario" | "comparison" | "view_preset";

export type LearningRelationType =
  | "prerequisite_for" | "next_step" | "contrast_with" | "special_case_of"
  | "generalizes" | "applied_in" | "common_misconception_for"
  | "see_visualization" | "see_comparison" | "see_case" | "implemented_by";

export interface LearningEdge {
  edge_id: string;
  source_type: LearningEntityType;
  source_id: string;
  target_type: LearningEntityType;
  target_id: string;
  relation: LearningRelationType;
  rationale: string;
  difficulty: "beginner" | "intermediate" | "advanced" | "all";
  audience: "learner" | "practitioner" | "researcher" | "all";
  display_order: number;
  source_ids: string[];
  last_verified: string;
  status: "current" | "deprecated" | "draft";
}

export interface TerminologyAlias {
  term_id: string;
  target_type: "method" | "problem" | "feature" | "implementation";
  target_id: string;
  label_ja: string;
  label_en: string;
  abbreviations: string[];
  synonyms: string[];
  domain_terms: string[];
  misspellings: string[];
  deprecated_terms: string[];
  disambiguation_note: string | null;
  locale: string;
  rationale: string;
  source_ids: string[];
  last_verified: string;
}

export interface LearningEntity {
  entity_type: LearningEntityType;
  entity_id: string;
  label_ja: string;
  label_en: string;
  canonical_url: string | null;
  external_url: string | null;
}

export interface LearningGraphIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  edges: LearningEdge[];
  aliases: TerminologyAlias[];
  entities: LearningEntity[];
}

const ENTITY_TYPES = new Set<LearningEntityType>([
  "method", "problem", "feature", "case", "implementation", "scenario", "comparison", "view_preset",
]);
const RELATION_TYPES = new Set<LearningRelationType>([
  "prerequisite_for", "next_step", "contrast_with", "special_case_of", "generalizes",
  "applied_in", "common_misconception_for", "see_visualization", "see_comparison", "see_case", "implemented_by",
]);

export function parseLearningGraphIndex(raw: unknown): LearningGraphIndex {
  const data = record(raw, "learning graph");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported learning graph contract.");
  const entities = array(data.entities, "entities").map(parseEntity);
  const entityKeys = new Set(entities.map((entity) => key(entity.entity_type, entity.entity_id)));
  const edges = array(data.edges, "edges").map((value, index) => parseEdge(value, index));
  const semanticKeys = new Set<string>();
  for (const edge of edges) {
    if (!entityKeys.has(key(edge.source_type, edge.source_id)) || !entityKeys.has(key(edge.target_type, edge.target_id))) {
      throw new Error(`Dangling learning edge: ${edge.edge_id}.`);
    }
    const semantic = `${key(edge.source_type, edge.source_id)}:${edge.relation}:${key(edge.target_type, edge.target_id)}`;
    if (semanticKeys.has(semantic)) throw new Error(`Duplicate learning edge: ${semantic}.`);
    semanticKeys.add(semantic);
  }
  const aliases = array(data.aliases, "aliases").map((value, index) => parseAlias(value, index));
  const owners = new Map<string, TerminologyAlias[]>();
  for (const alias of aliases) {
    if (!entityKeys.has(key(alias.target_type, alias.target_id))) throw new Error(`Dangling terminology target: ${alias.term_id}.`);
    for (const term of aliasTerms(alias)) owners.set(normalizeTerm(term), [...(owners.get(normalizeTerm(term)) ?? []), alias]);
  }
  for (const [term, rows] of owners) {
    if (new Set(rows.map((row) => key(row.target_type, row.target_id))).size > 1 && rows.some((row) => !row.disambiguation_note)) {
      throw new Error(`Ambiguous terminology requires disambiguation: ${term}.`);
    }
  }
  return { contract_version: "1.0.0", dataset_version: nonEmpty(data.dataset_version, "dataset_version"), edges, aliases, entities };
}

export function aliasTerms(alias: TerminologyAlias): string[] {
  return [alias.label_ja, alias.label_en, ...alias.abbreviations, ...alias.synonyms, ...alias.domain_terms, ...alias.misspellings, ...alias.deprecated_terms];
}

export function findLearningEntity(index: LearningGraphIndex, type: LearningEntityType, id: string): LearningEntity | undefined {
  return index.entities.find((entity) => entity.entity_type === type && entity.entity_id === id);
}

export function searchTerminology(index: LearningGraphIndex, query: string): TerminologyAlias[] {
  const normalized = normalizeTerm(query);
  if (!normalized) return [];
  return index.aliases
    .filter((alias) => aliasTerms(alias).some((term) => normalized.length <= 2
      ? normalizeTerm(term) === normalized
      : normalizeTerm(term).includes(normalized)))
    .sort((left, right) => score(left, normalized) - score(right, normalized) || left.label_ja.localeCompare(right.label_ja, "ja"));
}

export function normalizeTerm(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase().replace(/[\s\-_–—・/&]+/gu, "");
}

function score(alias: TerminologyAlias, query: string): number {
  const terms = aliasTerms(alias).map(normalizeTerm);
  if (terms.includes(query)) return 0;
  if (terms.some((term) => term.startsWith(query))) return 1;
  return 2;
}

function parseEdge(value: unknown, index: number): LearningEdge {
  const data = record(value, `edge ${index}`);
  const relation = nonEmpty(data.relation, "relation") as LearningRelationType;
  if (!RELATION_TYPES.has(relation)) throw new Error(`Unsupported learning relation: ${relation}.`);
  const difficulty = enumValue(data.difficulty, ["beginner", "intermediate", "advanced", "all"] as const, "difficulty");
  const audience = enumValue(data.audience, ["learner", "practitioner", "researcher", "all"] as const, "audience");
  const status = enumValue(data.status, ["current", "deprecated", "draft"] as const, "status");
  return {
    edge_id: nonEmpty(data.edge_id, "edge_id"), source_type: entityType(data.source_type), source_id: nonEmpty(data.source_id, "source_id"),
    target_type: entityType(data.target_type), target_id: nonEmpty(data.target_id, "target_id"), relation,
    rationale: nonEmpty(data.rationale, "rationale"), difficulty, audience,
    display_order: positiveInteger(data.display_order, "display_order"), source_ids: strings(data.source_ids, "source_ids"),
    last_verified: nonEmpty(data.last_verified, "last_verified"), status,
  };
}

function parseAlias(value: unknown, index: number): TerminologyAlias {
  const data = record(value, `alias ${index}`);
  const targetType = entityType(data.target_type);
  if (targetType === "case" || targetType === "scenario" || targetType === "comparison" || targetType === "view_preset") throw new Error("Unsupported alias target type.");
  return {
    term_id: nonEmpty(data.term_id, "term_id"), target_type: targetType, target_id: nonEmpty(data.target_id, "target_id"),
    label_ja: nonEmpty(data.label_ja, "label_ja"), label_en: nonEmpty(data.label_en, "label_en"),
    abbreviations: strings(data.abbreviations, "abbreviations"), synonyms: strings(data.synonyms, "synonyms"),
    domain_terms: strings(data.domain_terms, "domain_terms"), misspellings: strings(data.misspellings, "misspellings"),
    deprecated_terms: strings(data.deprecated_terms, "deprecated_terms"), disambiguation_note: nullableString(data.disambiguation_note, "disambiguation_note"),
    locale: nonEmpty(data.locale, "locale"), rationale: nonEmpty(data.rationale, "rationale"), source_ids: strings(data.source_ids, "source_ids"),
    last_verified: nonEmpty(data.last_verified, "last_verified"),
  };
}

function parseEntity(value: unknown): LearningEntity {
  const data = record(value, "entity");
  return {
    entity_type: entityType(data.entity_type), entity_id: nonEmpty(data.entity_id, "entity_id"),
    label_ja: nonEmpty(data.label_ja, "label_ja"), label_en: nonEmpty(data.label_en, "label_en"),
    canonical_url: nullableString(data.canonical_url, "canonical_url"), external_url: nullableString(data.external_url, "external_url"),
  };
}

function key(type: LearningEntityType, id: string): string { return `${type}:${id}`; }
function entityType(value: unknown): LearningEntityType { const result = nonEmpty(value, "entity_type") as LearningEntityType; if (!ENTITY_TYPES.has(result)) throw new Error(`Unsupported learning entity type: ${result}.`); return result; }
function enumValue<const T extends readonly string[]>(value: unknown, allowed: T, owner: string): T[number] { const result = nonEmpty(value, owner); if (!allowed.includes(result)) throw new Error(`Unsupported ${owner}: ${result}.`); return result as T[number]; }
function record(value: unknown, owner: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, owner: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`); return value; }
function nonEmpty(value: unknown, owner: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${owner} must not be blank.`); return value; }
function nullableString(value: unknown, owner: string): string | null { if (value === null) return null; return nonEmpty(value, owner); }
function strings(value: unknown, owner: string): string[] { return array(value, owner).map((item, index) => nonEmpty(item, `${owner}[${index}]`)); }
function positiveInteger(value: unknown, owner: string): number { if (!Number.isInteger(value) || Number(value) < 1) throw new Error(`${owner} must be positive.`); return Number(value); }
