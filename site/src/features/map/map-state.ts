import type { ViewNode } from "../../contracts/viewspec";

export function ancestorIds(
  nodeId: string | undefined,
  parentByChild: ReadonlyMap<string, string>,
): string[] {
  if (!nodeId) return [];
  const closestFirst: string[] = [];
  const seen = new Set([nodeId]);
  let current = parentByChild.get(nodeId);
  while (current !== undefined && !seen.has(current)) {
    closestFirst.push(current);
    seen.add(current);
    current = parentByChild.get(current);
  }
  return closestFirst.reverse();
}

export function visiblePreorder(
  roots: readonly ViewNode[],
  childrenByParent: ReadonlyMap<string, readonly ViewNode[]>,
  expanded: ReadonlySet<string>,
): ViewNode[] {
  const result: ViewNode[] = [];
  const visited = new Set<string>();
  const visit = (node: ViewNode) => {
    if (visited.has(node.node_id)) return;
    visited.add(node.node_id);
    result.push(node);
    if (!expanded.has(node.node_id)) return;
    for (const child of childrenByParent.get(node.node_id) ?? []) visit(child);
  };
  roots.forEach(visit);
  return result;
}
