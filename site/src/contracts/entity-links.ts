export type EntityType =
  | "case"
  | "comparison"
  | "content"
  | "feature"
  | "feature_value"
  | "implementation"
  | "journey"
  | "method"
  | "problem"
  | "scenario"
  | "source"
  | "trace"
  | "view";

export interface EntityRelation {
  relation_type: string;
  target_type: EntityType;
  target_id: string;
}

export interface LinkedEntity {
  entity_type: EntityType;
  entity_id: string;
  label: string;
  summary: string;
  canonical_url: string | null;
  aliases: string[];
  external_url: string | null;
  relations: EntityRelation[];
}

export interface EntityLinkIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  entities: LinkedEntity[];
}

const ENTITY_TYPES = new Set<EntityType>([
  "case", "comparison", "content", "feature", "feature_value", "implementation",
  "journey", "method", "problem", "scenario", "source", "trace", "view",
]);

export function parseEntityLinkIndex(raw: unknown): EntityLinkIndex {
  const data = record(raw, "entity link index");
  exactKeys(data, ["contract_version", "dataset_version", "generated_at", "entities"], "entity link index");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported entity link contract.");
  const entities = array(data.entities, "entities").map((value, index) => parseEntity(value, index));
  const keys = new Set<string>();
  const routes = new Set<string>();
  for (const entity of entities) {
    const key = entityKey(entity.entity_type, entity.entity_id);
    if (keys.has(key)) throw new Error(`Duplicate entity key: ${key}.`);
    keys.add(key);
    for (const route of [...(entity.canonical_url ? [entity.canonical_url] : []), ...entity.aliases]) {
      if (routes.has(route)) throw new Error(`Duplicate canonical or alias URL: ${route}.`);
      routes.add(route);
    }
  }
  for (const entity of entities) {
    for (const relation of entity.relations) {
      const target = entityKey(relation.target_type, relation.target_id);
      if (!keys.has(target)) throw new Error(`Dangling entity relation: ${target}.`);
    }
  }
  return {
    contract_version: "1.0.0",
    dataset_version: nonEmpty(data.dataset_version, "dataset_version"),
    generated_at: nonEmpty(data.generated_at, "generated_at"),
    entities,
  };
}

export function entityKey(entityType: EntityType, entityId: string): string {
  return `${entityType}:${entityId}`;
}

export function findEntity(
  index: EntityLinkIndex,
  entityType: EntityType,
  entityId: string,
): LinkedEntity | undefined {
  return index.entities.find(
    (entity) => entity.entity_type === entityType && entity.entity_id === entityId,
  );
}

export function relatedEntities(
  index: EntityLinkIndex,
  entity: LinkedEntity,
  relationType?: string,
): LinkedEntity[] {
  return entity.relations
    .filter((relation) => relationType === undefined || relation.relation_type === relationType)
    .flatMap((relation) => {
      const target = findEntity(index, relation.target_type, relation.target_id);
      return target ? [target] : [];
    });
}

export function resolveAlias(index: EntityLinkIndex, pathname: string): LinkedEntity | undefined {
  return index.entities.find((entity) => entity.aliases.includes(pathname));
}

function parseEntity(value: unknown, index: number): LinkedEntity {
  const data = record(value, `entities[${index}]`);
  exactKeys(
    data,
    ["entity_type", "entity_id", "label", "summary", "canonical_url", "aliases", "external_url", "relations"],
    `entities[${index}]`,
  );
  const entityType = type(data.entity_type, `entities[${index}].entity_type`);
  const canonicalUrl = nullableRoute(data.canonical_url, `entities[${index}].canonical_url`);
  const aliases = array(data.aliases, `entities[${index}].aliases`).map((item, aliasIndex) =>
    route(item, `entities[${index}].aliases[${aliasIndex}]`),
  );
  const relations = array(data.relations, `entities[${index}].relations`).map((item, relationIndex) => {
    const relation = record(item, `entities[${index}].relations[${relationIndex}]`);
    exactKeys(relation, ["relation_type", "target_type", "target_id"], `entities[${index}].relations[${relationIndex}]`);
    return {
      relation_type: nonEmpty(relation.relation_type, "relation_type"),
      target_type: type(relation.target_type, "target_type"),
      target_id: nonEmpty(relation.target_id, "target_id"),
    };
  });
  return {
    entity_type: entityType,
    entity_id: nonEmpty(data.entity_id, "entity_id"),
    label: nonEmpty(data.label, "label"),
    summary: string(data.summary, "summary"),
    canonical_url: canonicalUrl,
    aliases,
    external_url: nullableString(data.external_url, "external_url"),
    relations,
  };
}

function type(value: unknown, field: string): EntityType {
  const candidate = nonEmpty(value, field) as EntityType;
  if (!ENTITY_TYPES.has(candidate)) throw new Error(`${field} is unsupported.`);
  return candidate;
}
function route(value: unknown, field: string): string {
  const candidate = nonEmpty(value, field);
  if (!candidate.startsWith("/") || candidate.startsWith("//") || /[?#]/u.test(candidate)) {
    throw new Error(`${field} is not a safe site route.`);
  }
  return candidate;
}
function nullableRoute(value: unknown, field: string): string | null {
  return value === null ? null : route(value, field);
}
function nullableString(value: unknown, field: string): string | null {
  return value === null ? null : string(value, field);
}
function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`);
  return value as Record<string, unknown>;
}
function array(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value;
}
function string(value: unknown, field: string): string {
  if (typeof value !== "string") throw new Error(`${field} must be a string.`);
  return value;
}
function nonEmpty(value: unknown, field: string): string {
  const candidate = string(value, field);
  if (!candidate.trim()) throw new Error(`${field} must not be blank.`);
  return candidate;
}
function exactKeys(data: Record<string, unknown>, expected: readonly string[], field: string): void {
  const expectedSet = new Set(expected);
  const unknown = Object.keys(data).filter((key) => !expectedSet.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key));
  if (unknown.length > 0) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`);
  if (missing.length > 0) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`);
}
