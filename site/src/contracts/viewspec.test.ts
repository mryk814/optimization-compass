import { describe, expect, test } from "vitest";

import generatedViewSpec from "../../public/data/views/problem-structure.json";
import { buildMapModel, parseViewSpec } from "./viewspec";

function rawView() {
  return {
    dataset_version: "0.2.0",
    generated_at: "2026-07-13T00:00:00Z",
    view_id: "problem-structure",
    version: "1.0.0",
    title: "構造マップ",
    description: "説明",
    root_node_ids: ["opaque-root"],
    nodes: [
      {
        node_id: "opaque-root",
        node_type: "future_branch",
        parent_node_id: null,
        label: "Root",
        label_en: "Root",
        summary: "root summary",
        display_order: 0,
        default_collapsed: true,
        emphasis: "primary",
        question_id: null,
        answer_type: null,
        allowed_answers: [],
        answer_bindings: [],
        related_entities: [{ entity_type: "future_entity", entity_id: "E1" }],
        source_ids: ["S1"],
      },
    ],
    edges: [],
    entities: [
      {
        entity_id: "E1",
        entity_type: "future_entity",
        label: "Future",
        label_en: "Future",
        summary: "future summary",
        source_ids: ["S1"],
        url: "javascript:alert(1)",
      },
      {
        entity_id: "S1",
        entity_type: "source",
        label: "Source",
        label_en: "Source",
        summary: "source summary",
        source_ids: [],
        url: "https://example.com/source",
      },
    ],
  };
}

describe("ViewSpec runtime boundary", () => {
  test("accepts the shipped problem-structure artifact without diagnostics", () => {
    const model = buildMapModel(parseViewSpec(generatedViewSpec));

    expect(model.rootNodes).toHaveLength(5);
    expect(model.diagnostics).toEqual([]);
  });

  test("parses the canonical shape while preserving unknown non-empty types", () => {
    const view = parseViewSpec(rawView());

    expect(view.nodes[0].node_type).toBe("future_branch");
    expect(view.entities[0].entity_type).toBe("future_entity");
    expect(buildMapModel(view).rootNodes.map((node) => node.node_id)).toEqual(["opaque-root"]);
  });

  test.each([
    ["top-level", { ...rawView(), title: 4 }],
    ["node", { ...rawView(), nodes: [{ ...rawView().nodes[0], display_order: -1 }] }],
    ["edge", { ...rawView(), edges: [{ edge_id: "e", edge_type: "hierarchy" }] }],
    ["entity", { ...rawView(), entities: [{ ...rawView().entities[0], label: null }] }],
  ])("rejects malformed %s shapes", (_label, value) => {
    expect(() => parseViewSpec(value)).toThrow(/ViewSpec/u);
  });

  test("rejects duplicate node and entity IDs", () => {
    const view = rawView();
    expect(() => parseViewSpec({ ...view, nodes: [...view.nodes, view.nodes[0]] })).toThrow(
      /duplicate node/u,
    );
    expect(() =>
      parseViewSpec({ ...view, entities: [...view.entities, { ...view.entities[0] }] }),
    ).toThrow(/duplicate entity/u);
  });

  test("accepts a valid empty map", () => {
    const view = parseViewSpec({ ...rawView(), nodes: [], edges: [], entities: [], root_node_ids: [] });
    const model = buildMapModel(view);
    expect(model.rootNodes).toEqual([]);
    expect(model.diagnostics).toEqual([]);
  });

  test("orders roots and siblings deterministically and reports broken references and cycles", () => {
    const base = rawView();
    const node = base.nodes[0];
    const view = parseViewSpec({
      ...base,
      root_node_ids: ["b", "a", "missing-root"],
      nodes: [
        { ...node, node_id: "a", node_type: "branch", display_order: 2, related_entities: [] },
        { ...node, node_id: "b", node_type: "branch", display_order: 1, related_entities: [] },
        { ...node, node_id: "child-z", parent_node_id: "a", display_order: 1, related_entities: [] },
        { ...node, node_id: "child-a", parent_node_id: "a", display_order: 1, related_entities: [] },
        { ...node, node_id: "cycle-a", parent_node_id: "cycle-b", related_entities: [] },
        { ...node, node_id: "cycle-b", parent_node_id: "cycle-a", related_entities: [] },
        {
          ...node,
          node_id: "broken",
          parent_node_id: "absent",
          related_entities: [{ entity_type: "method", entity_id: "absent" }],
          source_ids: ["absent-source"],
        },
      ],
      entities: [],
    });
    const model = buildMapModel(view);

    expect(model.rootNodes.map((item) => item.node_id)).toEqual(["b", "a"]);
    expect(model.childrenByParent.get("a")?.map((item) => item.node_id)).toEqual([
      "child-a",
      "child-z",
    ]);
    expect(model.diagnostics.map((item) => item.kind)).toEqual(
      expect.arrayContaining(["missing-root", "missing-parent", "cycle", "missing-entity", "missing-source"]),
    );
  });
});
