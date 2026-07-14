import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

import { decodeAtlasState, encodeAtlasState } from "../../state/atlas-state";
import { MethodPage } from "./MethodPage";

const view = {
  dataset_version: "0.2.0", generated_at: "2026-07-13T00:00:00Z",
  view_id: "problem-structure", version: "1.0.0", title: "Map", description: "",
  root_node_ids: ["opaque-later", "opaque-first"], edges: [], entities: [{
    entity_id: "M_TARGET", entity_type: "method", label: "Target", label_en: "Target",
    summary: "", source_ids: [], url: "",
  }],
  nodes: [
    node("opaque-later", 2),
    node("opaque-first", 1),
  ],
};

function node(node_id: string, display_order: number) {
  return {
    node_id, node_type: "answer", parent_node_id: null, label: node_id, label_en: node_id,
    summary: "", display_order, default_collapsed: true, emphasis: "normal",
    question_id: "Q01", answer_type: "single_choice", allowed_answers: ["binary"],
    answer_bindings: [{ question_id: "Q01", answer_value: "binary" }],
    related_entities: [{ entity_type: "method", entity_id: "M_TARGET" }], source_ids: [],
  };
}

function Probe() { return <output data-testid="location">{useLocation().search}</output>; }

describe("MethodPage Map deep link", () => {
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

  test("uses related_entities display order with opaque node IDs and preserves answers", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => view }));
    const token = encodeAtlasState({
      stateVersion: 1, datasetVersion: "0.2.0", viewId: "problem-structure", viewVersion: "1.0.0",
      answers: { Q01: { status: "answered", values: ["binary"] } },
    });
    render(
      <MemoryRouter initialEntries={[`/methods/M_TARGET?keep=1&tag=a&tag=b&state=${token}`]}>
        <Probe />
        <Routes>
          <Route path="/methods/:methodId" element={<MethodPage />} />
          <Route path="/map" element={<p>MAP ROUTE</p>} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "地図上で見る" }));
    expect(await screen.findByText("MAP ROUTE")).toBeVisible();
    const next = new URLSearchParams(screen.getByTestId("location").textContent ?? "").get("state")!;
    const decoded = decodeAtlasState(next, {
      datasetVersion: "0.2.0", viewId: "problem-structure", viewVersion: "1.0.0",
      nodeIds: new Set(view.nodes.map((item) => item.node_id)),
      questions: { Q01: { answerType: "single_choice", allowedAnswers: ["binary"] } },
    }).state;
    expect(decoded.selectedNodeId).toBe("opaque-first");
    expect(decoded.answers.Q01).toEqual({ status: "answered", values: ["binary"] });
    const params = new URLSearchParams(screen.getByTestId("location").textContent ?? "");
    expect(params.get("keep")).toBe("1");
    expect(params.getAll("tag")).toEqual(["a", "b"]);
  });

  test("keeps MethodPage in place and shows an alert when the target state is too long", async () => {
    const hugeId = "opaque".repeat(400);
    const hugeView = {
      ...view,
      root_node_ids: [hugeId],
      nodes: [node(hugeId, 0)],
    };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => hugeView }));
    render(
      <MemoryRouter initialEntries={["/methods/M_TARGET?keep=1"]}>
        <Probe />
        <Routes>
          <Route path="/methods/:methodId" element={<MethodPage />} />
          <Route path="/map" element={<p>MAP ROUTE</p>} />
        </Routes>
      </MemoryRouter>,
    );

    const before = screen.getByTestId("location").textContent;
    fireEvent.click(await screen.findByRole("button", { name: "地図上で見る" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/maximum is 1800/u);
    expect(screen.getByTestId("location")).toHaveTextContent(before ?? "");
    expect(screen.queryByText("MAP ROUTE")).not.toBeInTheDocument();
  });

  test("uses generated Gallery relations for candidate methods outside the Map view", async () => {
    const gallery = {
      contract_version: "1.0.0", dataset_version: "0.2.0", cases: [{
        case_id: "case.materials", title_ja: "材料ケース", title_en: "Materials case",
        domain: "materials", problem_archetype_id: "PA001", feature_values: [],
        question_answers: {}, candidate_method_ids: ["M_GALLERY"], excluded_methods: [],
        implementation_ids: [], visualization_ids: [], comparison_ids: [], source_ids: ["S001"],
        difficulty: "intro", status: "published", last_reviewed: "2026-07-14",
        question: "どの候補を試すか", decision_variables: "x", objective: "min f(x)",
        constraints: "none", map_node_id: "opaque-first", python_example: "print('ok')",
        practical_notes: "small smoke",
      }],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce({ ok: true, json: async () => ({ ...view, entities: [] }) })
        .mockResolvedValueOnce({ ok: true, json: async () => gallery }),
    );

    render(
      <MemoryRouter initialEntries={["/methods/M_GALLERY"]}>
        <Routes>
          <Route path="/methods/:methodId" element={<MethodPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { level: 1, name: "M_GALLERY" })).toBeVisible();
    expect(screen.getByRole("link", { name: "材料ケース" })).toHaveAttribute(
      "href",
      "/gallery/case.materials",
    );
    expect(screen.getByText("どの候補を試すか")).toBeVisible();
  });
});
