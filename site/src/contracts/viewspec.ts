export type AnswerType = "single_choice" | "multi_choice";
export type NodeEmphasis = "primary" | "normal" | "muted";

export interface AnswerBinding {
  question_id: string;
  answer_value: string;
}

export interface EntityReference {
  entity_type: string;
  entity_id: string;
}

export interface ViewNode {
  node_id: string;
  node_type: string;
  parent_node_id: string | null;
  label: string;
  label_en: string;
  summary: string;
  display_order: number;
  default_collapsed: boolean;
  emphasis: NodeEmphasis;
  question_id: string | null;
  answer_type: AnswerType | null;
  allowed_answers: string[];
  answer_bindings: AnswerBinding[];
  related_entities: EntityReference[];
  source_ids: string[];
}

export interface ViewEdge {
  edge_id: string;
  edge_type: string;
  source_node_id: string;
  target_node_id: string;
  label: string;
  explanation: string;
}

export interface ViewEntity {
  entity_id: string;
  entity_type: string;
  label: string;
  label_en: string;
  summary: string;
  source_ids: string[];
  url: string;
}

export interface ViewSpec {
  dataset_version: string;
  generated_at: string;
  view_id: string;
  version: string;
  title: string;
  description: string;
  root_node_ids: string[];
  nodes: ViewNode[];
  edges: ViewEdge[];
  entities: ViewEntity[];
}

export type MapDiagnosticKind =
  | "missing-root"
  | "missing-parent"
  | "missing-edge-node"
  | "cycle"
  | "missing-entity"
  | "missing-source";

export interface MapDiagnostic {
  kind: MapDiagnosticKind;
  message: string;
  subjectId: string;
}

export interface MapModel {
  nodeById: ReadonlyMap<string, ViewNode>;
  entityByKey: ReadonlyMap<string, ViewEntity>;
  childrenByParent: ReadonlyMap<string, readonly ViewNode[]>;
  parentByChild: ReadonlyMap<string, string>;
  rootNodes: readonly ViewNode[];
  diagnostics: readonly MapDiagnostic[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function fail(path: string, detail: string): never {
  throw new Error(`ViewSpec ${path} ${detail}.`);
}

function record(value: unknown, path: string): Record<string, unknown> {
  if (!isRecord(value)) fail(path, "must be an object");
  return value;
}

function string(value: unknown, path: string, allowEmpty = true): string {
  if (typeof value !== "string") fail(path, "must be a string");
  if (!allowEmpty && value.trim().length === 0) fail(path, "must not be empty");
  return value;
}

function nullableString(value: unknown, path: string): string | null {
  if (value === null) return null;
  return string(value, path, false);
}

function stringArray(value: unknown, path: string): string[] {
  if (!Array.isArray(value)) fail(path, "must be an array");
  return value.map((item, index) => string(item, `${path}[${index}]`, false));
}

function parseNode(value: unknown, index: number): ViewNode {
  const path = `nodes[${index}]`;
  const raw = record(value, path);
  const displayOrder = raw.display_order;
  if (!Number.isInteger(displayOrder) || (displayOrder as number) < 0) {
    fail(`${path}.display_order`, "must be a non-negative integer");
  }
  if (typeof raw.default_collapsed !== "boolean") {
    fail(`${path}.default_collapsed`, "must be a boolean");
  }
  if (raw.emphasis !== "primary" && raw.emphasis !== "normal" && raw.emphasis !== "muted") {
    fail(`${path}.emphasis`, "must be primary, normal, or muted");
  }
  const answerType = raw.answer_type;
  if (answerType !== null && answerType !== "single_choice" && answerType !== "multi_choice") {
    fail(`${path}.answer_type`, "must be null, single_choice, or multi_choice");
  }
  if (!Array.isArray(raw.answer_bindings)) fail(`${path}.answer_bindings`, "must be an array");
  if (!Array.isArray(raw.related_entities)) fail(`${path}.related_entities`, "must be an array");

  return {
    node_id: string(raw.node_id, `${path}.node_id`, false),
    node_type: string(raw.node_type, `${path}.node_type`, false),
    parent_node_id: nullableString(raw.parent_node_id, `${path}.parent_node_id`),
    label: string(raw.label, `${path}.label`),
    label_en: string(raw.label_en, `${path}.label_en`),
    summary: string(raw.summary, `${path}.summary`),
    display_order: displayOrder as number,
    default_collapsed: raw.default_collapsed,
    emphasis: raw.emphasis,
    question_id: nullableString(raw.question_id, `${path}.question_id`),
    answer_type: answerType,
    allowed_answers: stringArray(raw.allowed_answers, `${path}.allowed_answers`),
    answer_bindings: raw.answer_bindings.map((item, bindingIndex) => {
      const binding = record(item, `${path}.answer_bindings[${bindingIndex}]`);
      return {
        question_id: string(binding.question_id, `${path}.answer_bindings[${bindingIndex}].question_id`, false),
        answer_value: string(binding.answer_value, `${path}.answer_bindings[${bindingIndex}].answer_value`, false),
      };
    }),
    related_entities: raw.related_entities.map((item, referenceIndex) => {
      const reference = record(item, `${path}.related_entities[${referenceIndex}]`);
      return {
        entity_type: string(reference.entity_type, `${path}.related_entities[${referenceIndex}].entity_type`, false),
        entity_id: string(reference.entity_id, `${path}.related_entities[${referenceIndex}].entity_id`, false),
      };
    }),
    source_ids: stringArray(raw.source_ids, `${path}.source_ids`),
  };
}

function parseEdge(value: unknown, index: number): ViewEdge {
  const path = `edges[${index}]`;
  const raw = record(value, path);
  return {
    edge_id: string(raw.edge_id, `${path}.edge_id`, false),
    edge_type: string(raw.edge_type, `${path}.edge_type`, false),
    source_node_id: string(raw.source_node_id, `${path}.source_node_id`, false),
    target_node_id: string(raw.target_node_id, `${path}.target_node_id`, false),
    label: string(raw.label, `${path}.label`),
    explanation: string(raw.explanation, `${path}.explanation`),
  };
}

function parseEntity(value: unknown, index: number): ViewEntity {
  const path = `entities[${index}]`;
  const raw = record(value, path);
  return {
    entity_id: string(raw.entity_id, `${path}.entity_id`, false),
    entity_type: string(raw.entity_type, `${path}.entity_type`, false),
    label: string(raw.label, `${path}.label`),
    label_en: string(raw.label_en, `${path}.label_en`),
    summary: string(raw.summary, `${path}.summary`),
    source_ids: stringArray(raw.source_ids, `${path}.source_ids`),
    url: string(raw.url, `${path}.url`),
  };
}

function assertUnique(values: readonly string[], kind: "node" | "entity" | "edge"): void {
  const seen = new Set<string>();
  for (const value of values) {
    if (seen.has(value)) fail(`duplicate ${kind} ID`, `"${value}"`);
    seen.add(value);
  }
}

export function parseViewSpec(value: unknown): ViewSpec {
  const raw = record(value, "payload");
  if (!Array.isArray(raw.nodes)) fail("nodes", "must be an array");
  if (!Array.isArray(raw.edges)) fail("edges", "must be an array");
  if (!Array.isArray(raw.entities)) fail("entities", "must be an array");
  const view: ViewSpec = {
    dataset_version: string(raw.dataset_version, "dataset_version", false),
    generated_at: string(raw.generated_at, "generated_at", false),
    view_id: string(raw.view_id, "view_id", false),
    version: string(raw.version, "version", false),
    title: string(raw.title, "title", false),
    description: string(raw.description, "description"),
    root_node_ids: stringArray(raw.root_node_ids, "root_node_ids"),
    nodes: raw.nodes.map(parseNode),
    edges: raw.edges.map(parseEdge),
    entities: raw.entities.map(parseEntity),
  };
  assertUnique(view.nodes.map((node) => node.node_id), "node");
  assertUnique(view.entities.map((entity) => entity.entity_id), "entity");
  assertUnique(view.edges.map((edge) => edge.edge_id), "edge");
  return view;
}

export function entityKey(type: string, id: string): string {
  return `${type}\u0000${id}`;
}

function byDisplayOrder(left: ViewNode, right: ViewNode): number {
  if (left.display_order !== right.display_order) return left.display_order - right.display_order;
  if (left.node_id === right.node_id) return 0;
  return left.node_id < right.node_id ? -1 : 1;
}

export function buildMapModel(view: ViewSpec): MapModel {
  const diagnostics: MapDiagnostic[] = [];
  const nodeById = new Map(view.nodes.map((node) => [node.node_id, node]));
  const entityByKey = new Map(view.entities.map((entity) => [entityKey(entity.entity_type, entity.entity_id), entity]));
  const children = new Map<string, ViewNode[]>();
  const parentByChild = new Map<string, string>();

  for (const node of view.nodes) {
    if (node.parent_node_id !== null) {
      if (!nodeById.has(node.parent_node_id)) {
        diagnostics.push({ kind: "missing-parent", subjectId: node.node_id, message: `「${node.label || node.node_id}」の親 ${node.parent_node_id} が見つかりません。` });
      } else {
        parentByChild.set(node.node_id, node.parent_node_id);
        const siblings = children.get(node.parent_node_id) ?? [];
        siblings.push(node);
        children.set(node.parent_node_id, siblings);
      }
    }
    for (const reference of node.related_entities) {
      if (!entityByKey.has(entityKey(reference.entity_type, reference.entity_id))) {
        diagnostics.push({ kind: "missing-entity", subjectId: node.node_id, message: `関連先 ${reference.entity_type}:${reference.entity_id} が見つかりません。` });
      }
    }
    for (const sourceId of node.source_ids) {
      if (!entityByKey.has(entityKey("source", sourceId))) {
        diagnostics.push({ kind: "missing-source", subjectId: node.node_id, message: `根拠 ${sourceId} が見つかりません。` });
      }
    }
  }
  for (const entity of view.entities) {
    for (const sourceId of entity.source_ids) {
      if (!entityByKey.has(entityKey("source", sourceId))) {
        diagnostics.push({ kind: "missing-source", subjectId: entity.entity_id, message: `${entity.entity_id} の根拠 ${sourceId} が見つかりません。` });
      }
    }
  }
  for (const edge of view.edges) {
    if (!nodeById.has(edge.source_node_id) || !nodeById.has(edge.target_node_id)) {
      diagnostics.push({ kind: "missing-edge-node", subjectId: edge.edge_id, message: `接続 ${edge.edge_id} の端点が見つかりません。` });
    }
  }

  const cycleMembers = new Set<string>();
  for (const node of view.nodes) {
    const path = new Set<string>();
    let current: string | undefined = node.node_id;
    while (current !== undefined) {
      if (path.has(current)) {
        cycleMembers.add(current);
        break;
      }
      path.add(current);
      current = parentByChild.get(current);
    }
  }
  for (const nodeId of [...cycleMembers].sort()) {
    diagnostics.push({ kind: "cycle", subjectId: nodeId, message: `親子関係に循環があります: ${nodeId}` });
  }

  const roots = view.root_node_ids.flatMap((rootId) => {
    const node = nodeById.get(rootId);
    if (!node) {
      diagnostics.push({ kind: "missing-root", subjectId: rootId, message: `ルート ${rootId} が見つかりません。` });
      return [];
    }
    return [node];
  }).sort(byDisplayOrder);
  const childrenByParent = new Map(
    [...children.entries()].map(([parent, childNodes]) => [parent, childNodes.sort(byDisplayOrder)]),
  );

  return { nodeById, entityByKey, childrenByParent, parentByChild, rootNodes: roots, diagnostics };
}

export function safeHttpUrl(value: string): string | undefined {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : undefined;
  } catch {
    return undefined;
  }
}
