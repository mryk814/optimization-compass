import { describe, expect, test } from "vitest";

import type { ViewNode } from "../../contracts/viewspec";
import type { AtlasCompatibilityCatalog, AtlasStateV1 } from "../../state/atlas-state";
import {
  ancestorIds,
  applyAnswerBindings,
  matchingBindingNodeIds,
  resolveRelatedNodeId,
  visiblePreorder,
} from "./map-state";

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

  test("applies exact bindings with single replace, stable multi merge, and canonical unknown", () => {
    const catalog: AtlasCompatibilityCatalog = {
      datasetVersion: "0.2.0",
      viewId: "problem-structure",
      viewVersion: "1.0.0",
      nodeIds: new Set(),
      questions: {
        Q01: { answerType: "single_choice", allowedAnswers: ["binary", "continuous"] },
        Q05: { answerType: "multi_choice", allowedAnswers: ["autodiff", "unknown", "hvp"] },
        Q11: { answerType: "single_choice", allowedAnswers: ["none_known", "structured_or_unknown"] },
      },
    };
    const state: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: catalog.datasetVersion,
      viewId: catalog.viewId,
      viewVersion: catalog.viewVersion,
      answers: {
        Q01: { status: "answered", values: ["continuous"] },
        Q05: { status: "answered", values: ["hvp"] },
      },
    };

    const next = applyAnswerBindings(
      state,
      [
        { question_id: "Q01", answer_value: "binary" },
        { question_id: "Q05", answer_value: "autodiff" },
        { question_id: "Q05", answer_value: "unknown" },
        { question_id: "Q11", answer_value: "structured_or_unknown" },
      ],
      catalog,
    );

    expect(next.answers).toEqual({
      Q01: { status: "answered", values: ["binary"] },
      Q05: { status: "unknown", values: ["unknown"] },
      Q11: { status: "answered", values: ["structured_or_unknown"] },
    });
    expect(state.answers.Q01).toEqual({ status: "answered", values: ["continuous"] });
  });

  test("matches bindings and resolves related methods without parsing opaque node IDs", () => {
    const first = { ...node("zzz-opaque", null), display_order: 2 };
    first.answer_bindings = [{ question_id: "Q01", answer_value: "binary" }];
    first.related_entities = [{ entity_type: "method", entity_id: "M_TARGET" }];
    const second = { ...node("totally-unrelated-id", null), display_order: 1 };
    second.answer_bindings = [
      { question_id: "Q01", answer_value: "binary" },
      { question_id: "Q05", answer_value: "autodiff" },
    ];
    second.related_entities = [{ entity_type: "method", entity_id: "M_TARGET" }];
    const state: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: "0.2.0",
      viewId: "problem-structure",
      viewVersion: "1.0.0",
      answers: {
        Q01: { status: "answered", values: ["binary"] },
        Q05: { status: "answered", values: ["autodiff", "hvp"] },
      },
    };

    expect(matchingBindingNodeIds([first, second], state)).toEqual([
      "totally-unrelated-id",
      "zzz-opaque",
    ]);
    expect(resolveRelatedNodeId([first, second], "method", "M_TARGET")).toBe(
      "totally-unrelated-id",
    );
  });
});
