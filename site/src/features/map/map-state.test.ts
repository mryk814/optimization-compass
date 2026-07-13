import { describe, expect, test } from "vitest";

import type { ViewNode } from "../../contracts/viewspec";
import { ancestorIds, visiblePreorder } from "./map-state";

function node(node_id: string, parent_node_id: string | null): ViewNode {
  return {
    node_id,
    node_type: "branch",
    parent_node_id,
    label: node_id,
    label_en: node_id,
    summary: "",
    display_order: 0,
    default_collapsed: true,
    emphasis: "normal",
    question_id: null,
    answer_type: null,
    allowed_answers: [],
    answer_bindings: [],
    related_entities: [],
    source_ids: [],
  };
}

describe("map tree state", () => {
  test("returns visible preorder without recursing through cycles", () => {
    const root = node("opaque-r", null);
    const child = node("opaque-c", "opaque-r");
    const result = visiblePreorder(
      [root],
      new Map([
        ["opaque-r", [child]],
        ["opaque-c", [root]],
      ]),
      new Set(["opaque-r", "opaque-c"]),
    );
    expect(result.map((item) => item.node_id)).toEqual(["opaque-r", "opaque-c"]);
  });

  test("resolves ancestors from explicit parent relationships and stops on cycles", () => {
    expect(
      ancestorIds("leaf", new Map([["leaf", "middle"], ["middle", "root"], ["root", "middle"]])),
    ).toEqual(["root", "middle"]);
  });
});
