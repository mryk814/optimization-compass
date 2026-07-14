import { parseAlgorithmTrace, type AlgorithmTrace } from "./trace";

export const SEARCH_TREE_CONTRACT_VERSION = "1.0.0" as const;

export type SearchTreeNodeState =
  | "open" | "active" | "branched" | "feasible"
  | "infeasible_pruned" | "bound_pruned" | "optimal";

export interface SearchTreeNode {
  node_id: string;
  parent_id: string | null;
  depth: number;
  branch_label_ja: string;
  branch_label_en: string;
  partial_assignment: Record<string, 0 | 1>;
  weight: number;
  objective_value: number;
  bound: number | null;
  feasibility: "undetermined" | "feasible" | "infeasible";
  state: SearchTreeNodeState;
  prune_reason: "capacity_exceeded" | "bound_not_better" | null;
  prune_explanation_ja: string | null;
  prune_explanation_en: string | null;
}

export interface SearchTreeIncumbent {
  node_id: string | null;
  source: "heuristic" | "tree";
  assignment: Record<string, 0 | 1>;
  value: number;
  weight: number;
}

export interface SearchTreeFramePayload {
  contract_version: typeof SEARCH_TREE_CONTRACT_VERSION;
  renderer_family: "search_tree";
  renderer_contract_version: typeof SEARCH_TREE_CONTRACT_VERSION;
  nodes: SearchTreeNode[];
  active_node_id: string | null;
  incumbent: SearchTreeIncumbent | null;
  best_feasible_value: number | null;
  global_bound: number;
  absolute_gap: number | null;
  relative_gap: number | null;
  progress: { explored_nodes: number; open_nodes: number; node_budget: number };
  decision_explanation_ja: string;
  decision_explanation_en: string;
  terminal_state: "ongoing" | "optimality_proven" | "budget_exhausted";
}

export interface SearchTreeArtifact {
  contract_version: typeof SEARCH_TREE_CONTRACT_VERSION;
  dataset_version: string;
  artifact_id: string;
  artifact_kind: "executable_trace";
  renderer_family: "search_tree";
  renderer_contract_version: typeof SEARCH_TREE_CONTRACT_VERSION;
  scenario_id: string;
  trace: AlgorithmTrace;
  static_fallback: {
    path: string;
    media_type: "image/svg+xml";
    alt_ja: string;
    alt_en: string;
  };
}

export interface SearchTreeIndexEntry {
  artifact_id: string;
  path: string;
  trace_id: string;
  scenario_id: string;
  artifact_kind: "executable_trace";
  renderer_family: "search_tree";
  renderer_contract_version: typeof SEARCH_TREE_CONTRACT_VERSION;
  static_fallback_path: string;
}

export interface SearchTreeIndex {
  contract_version: typeof SEARCH_TREE_CONTRACT_VERSION;
  dataset_version: string;
  artifacts: SearchTreeIndexEntry[];
}

export function parseSearchTreeArtifact(input: unknown): SearchTreeArtifact {
  const data = record(input, "SearchTreeArtifact");
  exactKeys(data, [
    "contract_version", "dataset_version", "artifact_id", "artifact_kind", "renderer_family",
    "renderer_contract_version", "scenario_id", "trace", "static_fallback",
  ], "SearchTreeArtifact");
  contractVersion(data.contract_version, "contract_version");
  literal(data.artifact_kind, "executable_trace", "artifact_kind");
  literal(data.renderer_family, "search_tree", "renderer_family");
  contractVersion(data.renderer_contract_version, "renderer_contract_version");

  const trace = parseAlgorithmTrace(data.trace);
  const payloads = trace.frames.map((frame, index) => parseSearchTreeFramePayload(frame.payload, `frames[${index}].payload`));
  const datasetVersion = nonEmpty(data.dataset_version, "dataset_version");
  if (trace.dataset_version !== datasetVersion) throw new Error("Artifact and trace dataset versions differ.");
  const scenarioId = nonEmpty(data.scenario_id, "scenario_id");
  if (trace.scenario_id !== scenarioId) throw new Error("Artifact and trace scenario IDs differ.");
  const finalState = payloads.at(-1)!.terminal_state;
  if (trace.terminal_status === "completed" ? finalState !== "optimality_proven" :
      trace.terminal_status === "budget_exhausted" ? finalState !== "budget_exhausted" : true) {
    throw new Error("Trace and search-tree terminal states differ.");
  }
  const fallback = record(data.static_fallback, "static_fallback");
  exactKeys(fallback, ["path", "media_type", "alt_ja", "alt_en"], "static_fallback");
  literal(fallback.media_type, "image/svg+xml", "static_fallback.media_type");
  return {
    contract_version: SEARCH_TREE_CONTRACT_VERSION,
    dataset_version: datasetVersion,
    artifact_id: nonEmpty(data.artifact_id, "artifact_id"),
    artifact_kind: "executable_trace",
    renderer_family: "search_tree",
    renderer_contract_version: SEARCH_TREE_CONTRACT_VERSION,
    scenario_id: scenarioId,
    trace,
    static_fallback: {
      path: safeRelativePath(fallback.path, "static_fallback.path", "svg"),
      media_type: "image/svg+xml",
      alt_ja: nonEmpty(fallback.alt_ja, "static_fallback.alt_ja"),
      alt_en: nonEmpty(fallback.alt_en, "static_fallback.alt_en"),
    },
  };
}

export function parseSearchTreeIndex(input: unknown): SearchTreeIndex {
  const data = record(input, "SearchTreeIndex");
  exactKeys(data, ["contract_version", "dataset_version", "artifacts"], "SearchTreeIndex");
  contractVersion(data.contract_version, "contract_version");
  const artifacts = array(data.artifacts, "artifacts").map((raw, index): SearchTreeIndexEntry => {
    const item = record(raw, `artifacts[${index}]`);
    exactKeys(item, [
      "artifact_id", "path", "trace_id", "scenario_id", "artifact_kind",
      "renderer_family", "renderer_contract_version", "static_fallback_path",
    ], `artifacts[${index}]`);
    literal(item.artifact_kind, "executable_trace", "artifact_kind");
    literal(item.renderer_family, "search_tree", "renderer_family");
    contractVersion(item.renderer_contract_version, "renderer_contract_version");
    return {
      artifact_id: nonEmpty(item.artifact_id, "artifact_id"),
      path: safeRelativePath(item.path, "path", "json"),
      trace_id: nonEmpty(item.trace_id, "trace_id"),
      scenario_id: nonEmpty(item.scenario_id, "scenario_id"),
      artifact_kind: "executable_trace",
      renderer_family: "search_tree",
      renderer_contract_version: SEARCH_TREE_CONTRACT_VERSION,
      static_fallback_path: safeRelativePath(item.static_fallback_path, "static_fallback_path", "svg"),
    };
  });
  if (artifacts.length === 0) throw new Error("SearchTreeIndex requires artifacts.");
  unique(artifacts.map((item) => item.artifact_id), "artifact_id");
  return {
    contract_version: SEARCH_TREE_CONTRACT_VERSION,
    dataset_version: nonEmpty(data.dataset_version, "dataset_version"),
    artifacts,
  };
}

export function parseSearchTreeFramePayload(input: unknown, owner = "SearchTreeFramePayload"): SearchTreeFramePayload {
  const data = record(input, owner);
  exactKeys(data, [
    "contract_version", "renderer_family", "renderer_contract_version", "nodes", "active_node_id",
    "incumbent", "best_feasible_value", "global_bound", "absolute_gap", "relative_gap", "progress",
    "decision_explanation_ja", "decision_explanation_en", "terminal_state",
  ], owner);
  contractVersion(data.contract_version, `${owner}.contract_version`);
  literal(data.renderer_family, "search_tree", `${owner}.renderer_family`);
  contractVersion(data.renderer_contract_version, `${owner}.renderer_contract_version`);
  const nodes = array(data.nodes, `${owner}.nodes`).map(parseNode);
  if (nodes.length === 0) throw new Error(`${owner}.nodes must not be empty.`);
  unique(nodes.map((node) => node.node_id), "node_id");
  const nodeIds = new Set(nodes.map((node) => node.node_id));
  for (const node of nodes) if (node.parent_id !== null && !nodeIds.has(node.parent_id)) throw new Error(`Missing parent for ${node.node_id}.`);
  const activeNodeId = nullableString(data.active_node_id, "active_node_id");
  if (activeNodeId !== null && !nodeIds.has(activeNodeId)) throw new Error("Active node is missing.");
  const incumbent = data.incumbent === null ? null : parseIncumbent(data.incumbent);
  const best = nullableNonNegativeInteger(data.best_feasible_value, "best_feasible_value");
  if ((incumbent === null) !== (best === null) || (incumbent && incumbent.value !== best)) {
    throw new Error("Incumbent and best_feasible_value differ.");
  }
  const globalBound = nonNegativeNumber(data.global_bound, "global_bound");
  const absoluteGap = nullableNonNegativeNumber(data.absolute_gap, "absolute_gap");
  const relativeGap = nullableNonNegativeNumber(data.relative_gap, "relative_gap");
  if (incumbent === null) {
    if (absoluteGap !== null || relativeGap !== null) throw new Error("Gap requires an incumbent.");
  } else {
    const expected = Math.max(0, globalBound - incumbent.value);
    if (absoluteGap !== expected || relativeGap !== expected / Math.max(1, Math.abs(incumbent.value))) {
      throw new Error("Gap is inconsistent with incumbent and bound.");
    }
  }
  const progress = record(data.progress, "progress");
  exactKeys(progress, ["explored_nodes", "open_nodes", "node_budget"], "progress");
  const terminalState = enumValue(data.terminal_state, ["ongoing", "optimality_proven", "budget_exhausted"] as const, "terminal_state");
  if (terminalState === "optimality_proven" && absoluteGap !== 0) throw new Error("Optimality proof requires zero gap.");
  return {
    contract_version: SEARCH_TREE_CONTRACT_VERSION,
    renderer_family: "search_tree",
    renderer_contract_version: SEARCH_TREE_CONTRACT_VERSION,
    nodes,
    active_node_id: activeNodeId,
    incumbent,
    best_feasible_value: best,
    global_bound: globalBound,
    absolute_gap: absoluteGap,
    relative_gap: relativeGap,
    progress: {
      explored_nodes: nonNegativeInteger(progress.explored_nodes, "explored_nodes"),
      open_nodes: nonNegativeInteger(progress.open_nodes, "open_nodes"),
      node_budget: positiveInteger(progress.node_budget, "node_budget"),
    },
    decision_explanation_ja: nonEmpty(data.decision_explanation_ja, "decision_explanation_ja"),
    decision_explanation_en: nonEmpty(data.decision_explanation_en, "decision_explanation_en"),
    terminal_state: terminalState,
  };
}

function parseNode(value: unknown, index: number): SearchTreeNode {
  const data = record(value, `nodes[${index}]`);
  exactKeys(data, [
    "node_id", "parent_id", "depth", "branch_label_ja", "branch_label_en", "partial_assignment",
    "weight", "objective_value", "bound", "feasibility", "state", "prune_reason",
    "prune_explanation_ja", "prune_explanation_en",
  ], `nodes[${index}]`);
  const state = enumValue(data.state, ["open", "active", "branched", "feasible", "infeasible_pruned", "bound_pruned", "optimal"] as const, "state");
  const pruneReason = data.prune_reason === null ? null : enumValue(data.prune_reason, ["capacity_exceeded", "bound_not_better"] as const, "prune_reason");
  const ja = nullableString(data.prune_explanation_ja, "prune_explanation_ja");
  const en = nullableString(data.prune_explanation_en, "prune_explanation_en");
  const pruned = state === "infeasible_pruned" || state === "bound_pruned";
  if (pruned !== (pruneReason !== null && ja !== null && en !== null)) throw new Error("Pruned node explanation is incomplete.");
  return {
    node_id: nonEmpty(data.node_id, "node_id"), parent_id: nullableString(data.parent_id, "parent_id"),
    depth: nonNegativeInteger(data.depth, "depth"), branch_label_ja: nonEmpty(data.branch_label_ja, "branch_label_ja"),
    branch_label_en: nonEmpty(data.branch_label_en, "branch_label_en"), partial_assignment: assignment(data.partial_assignment),
    weight: nonNegativeInteger(data.weight, "weight"), objective_value: nonNegativeInteger(data.objective_value, "objective_value"),
    bound: nullableNonNegativeNumber(data.bound, "bound"), feasibility: enumValue(data.feasibility, ["undetermined", "feasible", "infeasible"] as const, "feasibility"),
    state, prune_reason: pruneReason, prune_explanation_ja: ja, prune_explanation_en: en,
  };
}

function parseIncumbent(value: unknown): SearchTreeIncumbent {
  const data = record(value, "incumbent");
  exactKeys(data, ["node_id", "source", "assignment", "value", "weight"], "incumbent");
  return {
    node_id: nullableString(data.node_id, "node_id"), source: enumValue(data.source, ["heuristic", "tree"] as const, "source"),
    assignment: assignment(data.assignment), value: nonNegativeInteger(data.value, "value"), weight: nonNegativeInteger(data.weight, "weight"),
  };
}

function assignment(value: unknown): Record<string, 0 | 1> {
  const data = record(value, "assignment");
  return Object.fromEntries(Object.entries(data).map(([key, raw]) => {
    if (raw !== 0 && raw !== 1) throw new Error(`assignment.${key} must be 0 or 1.`);
    return [key, raw];
  }));
}

function record(value: unknown, owner: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, owner: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`); return value; }
function exactKeys(data: Record<string, unknown>, expected: readonly string[], owner: string): void { const allowed = new Set(expected); const unknown = Object.keys(data).filter((key) => !allowed.has(key)); const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key)); if (unknown.length) throw new Error(`${owner} has unknown fields: ${unknown.join(", ")}.`); if (missing.length) throw new Error(`${owner} is missing fields: ${missing.join(", ")}.`); }
function nonEmpty(value: unknown, owner: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${owner} must be non-empty.`); return value; }
function nullableString(value: unknown, owner: string): string | null { return value === null ? null : nonEmpty(value, owner); }
function number(value: unknown, owner: string): number { if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`${owner} must be finite.`); return value; }
function nonNegativeNumber(value: unknown, owner: string): number { const result = number(value, owner); if (result < 0) throw new Error(`${owner} must be non-negative.`); return result; }
function nullableNonNegativeNumber(value: unknown, owner: string): number | null { return value === null ? null : nonNegativeNumber(value, owner); }
function nonNegativeInteger(value: unknown, owner: string): number { const result = nonNegativeNumber(value, owner); if (!Number.isSafeInteger(result)) throw new Error(`${owner} must be a safe integer.`); return result; }
function nullableNonNegativeInteger(value: unknown, owner: string): number | null { return value === null ? null : nonNegativeInteger(value, owner); }
function positiveInteger(value: unknown, owner: string): number { const result = nonNegativeInteger(value, owner); if (result === 0) throw new Error(`${owner} must be positive.`); return result; }
function contractVersion(value: unknown, owner: string): void { literal(value, SEARCH_TREE_CONTRACT_VERSION, owner); }
function literal<T extends string>(value: unknown, expected: T, owner: string): asserts value is T { if (value !== expected) throw new Error(`${owner} must be ${expected}.`); }
function enumValue<const T extends readonly string[]>(value: unknown, allowed: T, owner: string): T[number] { if (typeof value !== "string" || !allowed.includes(value)) throw new Error(`${owner} is invalid.`); return value as T[number]; }
function unique(values: string[], owner: string): void { if (new Set(values).size !== values.length) throw new Error(`${owner} values must be unique.`); }
function safeRelativePath(value: unknown, owner: string, extension: "json" | "svg"): string { const path = nonEmpty(value, owner); const pattern = extension === "json" ? /^[a-z0-9][a-z0-9._/-]*\.json$/u : /^[a-z0-9][a-z0-9._/-]*\.svg$/u; if (!pattern.test(path) || path.includes("//") || path.split("/").includes("..")) throw new Error(`${owner} is not a safe relative path.`); return path; }
