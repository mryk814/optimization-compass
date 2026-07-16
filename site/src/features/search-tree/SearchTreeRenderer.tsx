import { useMemo, useRef, useState, type KeyboardEvent } from "react";

import type { SearchTreeFramePayload, SearchTreeNode } from "../../contracts/search-tree";

const stateLabels: Record<SearchTreeNode["state"], string> = {
  open: "未探索",
  active: "探索中",
  branched: "枝分かれ済み",
  feasible: "実行可能",
  infeasible_pruned: "実行不可能で枝刈り",
  bound_pruned: "boundで枝刈り",
  optimal: "最適解",
};

export function SearchTreeRenderer({
  payload,
  visibleLayers,
  focusTarget,
}: {
  payload: SearchTreeFramePayload;
  visibleLayers?: readonly string[];
  focusTarget?: string;
}) {
  const visible = new Set(visibleLayers ?? ["search_nodes", "global_bound", "incumbent", "prune_reason"]);
  const [focusedNodeId, setFocusedNodeId] = useState(payload.active_node_id ?? payload.nodes[0].node_id);
  const itemRefs = useRef(new Map<string, HTMLLIElement>());
  const orderedNodes = useMemo(
    () => [...payload.nodes].sort((left, right) => left.depth - right.depth || left.node_id.localeCompare(right.node_id)),
    [payload.nodes],
  );
  const roots = orderedNodes.filter((node) => node.parent_id === null);
  const children = (parentId: string) => orderedNodes.filter((node) => node.parent_id === parentId);
  const focusNode = (nodeId: string) => {
    setFocusedNodeId(nodeId);
    itemRefs.current.get(nodeId)?.focus();
  };
  const handleKey = (event: KeyboardEvent<HTMLLIElement>, node: SearchTreeNode) => {
    const index = orderedNodes.findIndex((candidate) => candidate.node_id === node.node_id);
    if (event.key === "ArrowDown" && index < orderedNodes.length - 1) focusNode(orderedNodes[index + 1].node_id);
    else if (event.key === "ArrowUp" && index > 0) focusNode(orderedNodes[index - 1].node_id);
    else if (event.key === "ArrowRight" && children(node.node_id)[0]) focusNode(children(node.node_id)[0].node_id);
    else if (event.key === "ArrowLeft" && node.parent_id) focusNode(node.parent_id);
    else if (event.key === "Home") focusNode(orderedNodes[0].node_id);
    else if (event.key === "End") focusNode(orderedNodes.at(-1)!.node_id);
    else return;
    event.preventDefault();
  };
  const renderNode = (node: SearchTreeNode) => {
    const childNodes = children(node.node_id);
    return (
      <li
        aria-current={payload.active_node_id === node.node_id ? "step" : undefined}
        aria-expanded={childNodes.length ? true : undefined}
        className={`search-tree-node search-tree-node-${node.state}`}
        key={node.node_id}
        onFocus={() => setFocusedNodeId(node.node_id)}
        onKeyDown={(event) => handleKey(event, node)}
        ref={(element) => { if (element) itemRefs.current.set(node.node_id, element); else itemRefs.current.delete(node.node_id); }}
        role="treeitem"
        tabIndex={focusedNodeId === node.node_id ? 0 : -1}
      >
        <div className="search-tree-node-card">
          <strong>{node.branch_label_ja}</strong>
          <span>{stateLabels[node.state]}</span>
          <small>value {node.objective_value} · bound {node.bound === null ? "—" : node.bound.toFixed(2)}</small>
          <small>{assignmentLabel(node.partial_assignment)}</small>
          {node.prune_explanation_ja && <p>{node.prune_explanation_ja}</p>}
        </div>
        {childNodes.length > 0 && <ul role="group">{childNodes.map(renderNode)}</ul>}
      </li>
    );
  };
  return (
    <section
      className="search-tree-renderer"
      aria-labelledby="search-tree-heading"
      data-guided-focus={focusTarget}
    >
      <h2 id="search-tree-heading">探索木</h2>
      <dl className="search-tree-metrics" aria-label="探索の現在値">
        {visible.has("incumbent") && <Metric label="Best feasible" value={payload.best_feasible_value ?? "未発見"} />}
        {visible.has("global_bound") && <Metric label="Global bound" value={payload.global_bound.toFixed(2)} />}
        {visible.has("global_bound") && <Metric label="Gap" value={payload.absolute_gap === null ? "—" : `${payload.absolute_gap.toFixed(2)} (${((payload.relative_gap ?? 0) * 100).toFixed(1)}%)`} />}
        {visible.has("search_nodes") && <Metric label="Nodes" value={`${payload.progress.explored_nodes} explored · ${payload.progress.open_nodes} open`} />}
      </dl>
      {visible.has("prune_reason") && <p className="search-tree-decision" aria-live="polite">{payload.decision_explanation_ja}</p>}
      <p className={`search-tree-terminal search-tree-terminal-${payload.terminal_state}`}>
        {terminalLabel(payload.terminal_state)}
      </p>
      {visible.has("search_nodes") && <div className="search-tree-viewport">
        <ul aria-label="0-1 knapsackの探索木。上下矢印でnode移動、左右矢印で親子移動。" className="search-tree" role="tree">
          {roots.map(renderNode)}
        </ul>
      </div>}
      <details className="search-tree-text-summary" open>
        <summary>Textual tree summary</summary>
        <ol>
          {orderedNodes.map((node) => (
            <li key={node.node_id}>
              <strong>{node.node_id}</strong>: {node.branch_label_ja}、{stateLabels[node.state]}、
              value {node.objective_value}、bound {node.bound === null ? "なし" : node.bound.toFixed(2)}。
              {node.prune_explanation_ja ? ` ${node.prune_explanation_ja}` : ""}
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div><dt>{label}</dt><dd><output aria-label={label}>{value}</output></dd></div>;
}

function assignmentLabel(assignment: Record<string, 0 | 1>): string {
  const entries = Object.entries(assignment);
  return entries.length ? entries.map(([item, value]) => `${item}=${value}`).join(", ") : "未割当";
}

function terminalLabel(state: SearchTreeFramePayload["terminal_state"]): string {
  return {
    ongoing: "探索中 — incumbentは候補で、最適性はまだ証明されていません。",
    optimality_proven: "最適性証明済み — best feasibleとglobal boundが一致しました。",
    budget_exhausted: "node予算で停止 — 実行可能な候補解はありますが、最適性は未証明です。",
  }[state];
}
