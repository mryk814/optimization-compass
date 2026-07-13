import type { CSSProperties, KeyboardEvent, MutableRefObject } from "react";

import type { MapModel, ViewNode } from "../../contracts/viewspec";
import { ancestorIds, visiblePreorder } from "./map-state";

interface MapTreeProps {
  model: MapModel;
  expanded: ReadonlySet<string>;
  selectedId?: string;
  focusedId?: string;
  zoom: number;
  nodeRefs: MutableRefObject<Map<string, HTMLElement>>;
  onToggle(nodeId: string): void;
  onSelect(nodeId: string): void;
  onFocusChange(nodeId: string): void;
}

export function MapTree({
  model,
  expanded,
  selectedId,
  focusedId,
  zoom,
  nodeRefs,
  onToggle,
  onSelect,
  onFocusChange,
}: MapTreeProps) {
  const visible = visiblePreorder(model.rootNodes, model.childrenByParent, expanded);
  const effectiveFocusedId =
    focusedId !== undefined && visible.some((node) => node.node_id === focusedId)
      ? focusedId
      : visible[0]?.node_id;
  const selectedAncestors = new Set(ancestorIds(selectedId, model.parentByChild));

  const focusNode = (nodeId: string) => {
    onFocusChange(nodeId);
    nodeRefs.current.get(nodeId)?.focus();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLElement>, node: ViewNode) => {
    const index = visible.findIndex((item) => item.node_id === node.node_id);
    const children = model.childrenByParent.get(node.node_id) ?? [];
    const parentId = model.parentByChild.get(node.node_id);
    let target: string | undefined;
    switch (event.key) {
      case "ArrowDown":
        target = visible[Math.min(index + 1, visible.length - 1)]?.node_id;
        break;
      case "ArrowUp":
        target = visible[Math.max(index - 1, 0)]?.node_id;
        break;
      case "Home":
        target = visible[0]?.node_id;
        break;
      case "End":
        target = visible.at(-1)?.node_id;
        break;
      case "ArrowRight":
        if (children.length > 0 && !expanded.has(node.node_id)) onToggle(node.node_id);
        else if (children.length > 0) target = children[0].node_id;
        break;
      case "ArrowLeft":
        if (children.length > 0 && expanded.has(node.node_id)) onToggle(node.node_id);
        else target = parentId;
        break;
      case "Enter":
      case " ":
        onSelect(node.node_id);
        break;
      default:
        return;
    }
    event.preventDefault();
    event.stopPropagation();
    if (target) focusNode(target);
  };

  const renderNode = (node: ViewNode, level: number, path: ReadonlySet<string>) => {
    if (path.has(node.node_id)) return null;
    const nextPath = new Set(path).add(node.node_id);
    const children = model.childrenByParent.get(node.node_id) ?? [];
    const hasChildren = children.length > 0;
    const isExpanded = expanded.has(node.node_id);
    const isSelected = node.node_id === selectedId;
    const isAncestor = selectedAncestors.has(node.node_id);
    const nodeAncestors = ancestorIds(node.node_id, model.parentByChild);
    const isRelated = isSelected || isAncestor || (selectedId !== undefined && nodeAncestors.includes(selectedId));
    const className = [
      "map-tree-item",
      isSelected ? "map-tree-item-selected" : "",
      isAncestor ? "map-tree-item-ancestor" : "",
      selectedId && !isRelated ? "map-tree-item-unrelated" : "",
      `map-tree-item-${node.emphasis}`,
    ].filter(Boolean).join(" ");

    return (
      <div key={node.node_id}>
        <div
          aria-expanded={hasChildren ? isExpanded : undefined}
          aria-level={level}
          aria-selected={isSelected}
          className={className}
          onClick={() => onSelect(node.node_id)}
          onFocus={() => onFocusChange(node.node_id)}
          onKeyDown={(event) => onKeyDown(event, node)}
          ref={(element) => {
            if (element) nodeRefs.current.set(node.node_id, element);
            else nodeRefs.current.delete(node.node_id);
          }}
          role="treeitem"
          tabIndex={effectiveFocusedId === node.node_id ? 0 : -1}
        >
          {hasChildren ? (
            <button
              aria-label={`${node.label} を${isExpanded ? "折りたたむ" : "展開"}`}
              className="map-tree-toggle"
              onClick={(event) => {
                event.stopPropagation();
                onToggle(node.node_id);
              }}
              tabIndex={-1}
              type="button"
            >
              {isExpanded ? "−" : "+"}
            </button>
          ) : (
            <span aria-hidden="true" className="map-tree-leaf-mark">·</span>
          )}
          <span className="map-tree-label">{node.label || node.node_id}</span>
          {node.node_type !== "branch" && <span className="map-tree-type">{node.node_type}</span>}
        </div>
        {hasChildren && isExpanded && (
          <div role="group">
            {children.map((child) => renderNode(child, level + 1, nextPath))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      aria-label="最適化問題の構造"
      className="map-tree"
      role="tree"
      style={{ "--map-zoom": `${zoom / 100}` } as CSSProperties}
    >
      {model.rootNodes.map((root) => renderNode(root, 1, new Set()))}
    </div>
  );
}
