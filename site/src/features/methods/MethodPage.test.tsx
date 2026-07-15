import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

import { decodeAtlasState, encodeAtlasState } from "../../state/atlas-state";
import type { EntityLinkIndex, LinkedEntity } from "../../contracts/entity-links";
import { EntityLinkProvider } from "../../state/entity-links";
import { MethodPage } from "./MethodPage";
import rawSiteData from "../../../public/data/recommendation/site-data.json";

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

function fetchArtifacts(currentView: typeof view) {
  return vi.fn().mockImplementation(async (input: string) => ({
    ok: true,
    json: async () => input.includes("recommendation/site-data.json")
      ? { ...structuredClone(rawSiteData), dataset_version: currentView.dataset_version }
      : currentView,
  }));
}

function Probe() { return <output data-testid="location">{useLocation().search}</output>; }

function linkIndex(methodId: string, relations: LinkedEntity["relations"] = [], extras: LinkedEntity[] = []): EntityLinkIndex {
  return {
    contract_version: "1.0.0", dataset_version: "0.2.0", generated_at: "2026-07-13T00:00:00Z",
    entities: [{ entity_type: "method", entity_id: methodId, label: methodId, summary: "", canonical_url: `/methods/${methodId}`, aliases: [], external_url: null, relations }, ...extras],
  };
}

describe("MethodPage Map deep link", () => {
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

  test("uses related_entities display order with opaque node IDs and preserves answers", async () => {
    vi.stubGlobal("fetch", fetchArtifacts(view));
    const token = encodeAtlasState({
      stateVersion: 1, datasetVersion: "0.2.0", viewId: "problem-structure", viewVersion: "1.0.0",
      answers: { Q01: { status: "answered", values: ["binary"] } },
    });
    render(
      <MemoryRouter initialEntries={[`/methods/M_TARGET?keep=1&tag=a&tag=b&state=${token}`]}>
        <EntityLinkProvider initialIndex={linkIndex("M_TARGET")}>
        <Probe />
        <Routes>
          <Route path="/methods/:methodId" element={<MethodPage />} />
          <Route path="/map" element={<p>MAP ROUTE</p>} />
        </Routes>
        </EntityLinkProvider>
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
    vi.stubGlobal("fetch", fetchArtifacts(hugeView));
    render(
      <MemoryRouter initialEntries={["/methods/M_TARGET?keep=1"]}>
        <EntityLinkProvider initialIndex={linkIndex("M_TARGET")}>
        <Probe />
        <Routes>
          <Route path="/methods/:methodId" element={<MethodPage />} />
          <Route path="/map" element={<p>MAP ROUTE</p>} />
        </Routes>
        </EntityLinkProvider>
      </MemoryRouter>,
    );

    const before = screen.getByTestId("location").textContent;
    fireEvent.click(await screen.findByRole("button", { name: "地図上で見る" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/maximum is 1800/u);
    expect(screen.getByTestId("location")).toHaveTextContent(before ?? "");
    expect(screen.queryByText("MAP ROUTE")).not.toBeInTheDocument();
  });

  test("uses generated Gallery relations for candidate methods outside the Map view", async () => {
    vi.stubGlobal("fetch", fetchArtifacts({ ...view, entities: [] }));
    const caseEntity: LinkedEntity = {
      entity_type: "case", entity_id: "case.materials", label: "材料ケース",
      summary: "どの候補を試すか", canonical_url: "/gallery/case.materials", aliases: [],
      external_url: null, relations: [],
    };
    const index = linkIndex(
      "M_GALLERY",
      [{ relation_type: "case", target_type: "case", target_id: "case.materials" }],
      [caseEntity],
    );

    render(
      <MemoryRouter initialEntries={["/methods/M_GALLERY"]}>
        <EntityLinkProvider initialIndex={index}>
        <Routes>
          <Route path="/methods/:methodId" element={<MethodPage />} />
        </Routes>
        </EntityLinkProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { level: 1, name: "M_GALLERY" })).toBeVisible();
    expect(screen.getByRole("link", { name: "材料ケース" })).toHaveAttribute(
      "href",
      "/gallery/case.materials",
    );
  });
});
