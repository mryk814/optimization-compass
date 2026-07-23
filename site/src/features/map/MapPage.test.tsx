import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { decodeAtlasState, encodeAtlasState } from "../../state/atlas-state";
import { MapPage } from "./MapPage";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import rawManifest from "../../../public/data/manifest.json";
import rawProblemView from "../../../public/data/views/problem-structure.json";
import rawOracleView from "../../../public/data/views/available-information.json";
import rawGuaranteeView from "../../../public/data/views/guarantee-outcome.json";
import rawMechanismView from "../../../public/data/views/method-mechanism.json";

function siteFixture() {
  return { ...structuredClone(rawSiteData), dataset_version: "0.2.0" };
}

function mapFixture() {
  const nodes = [
    node("opaque-root-a", null, "分岐 A", 0, true, "root A"),
    node("opaque-root-b", null, "分岐 B", 1, true, "root B"),
    node("opaque-root-c", null, "分岐 C", 2, true, "root C"),
    node("opaque-root-d", null, "分岐 D", 3, true, "root D"),
    node("opaque-root-e", null, "分岐 E", 4, true, "root E"),
    node("opaque-question", "opaque-root-a", "質問", 0, true, "question summary", {
      node_type: "question",
      question_id: "Q01",
      answer_type: "single_choice",
      allowed_answers: ["binary"],
    }),
    node("totally-opaque-leaf", "opaque-question", "0-1", 0, false, "binary summary", {
      node_type: "answer",
      answer_bindings: [{ question_id: "Q01", answer_value: "binary" }],
      related_entities: [
        { entity_type: "method", entity_id: "M_CP_SAT" },
        { entity_type: "method", entity_id: "M_BRANCH_CUT" },
      ],
      source_ids: ["S1"],
    }),
  ];
  return {
    dataset_version: "0.2.0",
    generated_at: "2026-07-13T00:00:00Z",
    view_id: "problem-structure",
    preset_id: "VIEW_PROBLEM_STRUCTURE",
    version: "1.0.0",
    title: "問題構造マップ",
    description: "構造をたどる",
    limitations: "手法を順位付けしない",
    axis: "problem_structure",
    relation_types: ["hierarchy"],
    max_depth: 3,
    filter_policy: {
      mode: "authored_groups",
      groups: [{ group_id: "root", label: "Root", label_en: "Root", question_ids: ["Q01"], feature_ids: [], method_ids: [], alternative_ids: [] }],
    },
    focus_fallback_entity_types: ["feature", "method"],
    root_node_ids: ["opaque-root-a", "opaque-root-b", "opaque-root-c", "opaque-root-d", "opaque-root-e"],
    nodes,
    edges: nodes.slice(5).map((item, index) => ({
      edge_id: `edge-${index}`,
      edge_type: "hierarchy",
      source_node_id: item.parent_node_id,
      target_node_id: item.node_id,
      label: "",
      explanation: "親分岐から展開する項目。",
    })),
    entities: [
      entity("M_CP_SAT", "method", "CP-SAT", "SATを利用", ["S1"]),
      entity("M_BRANCH_CUT", "method", "branch-and-cut", "cutを統合", ["S1"]),
      entity("S1", "source", "根拠", "source summary", [], "https://example.com/source"),
    ],
  };
}

function node(
  node_id: string,
  parent_node_id: string | null,
  label: string,
  display_order: number,
  default_collapsed: boolean,
  summary: string,
  overrides: Record<string, unknown> = {},
) {
  return {
    node_id,
    node_type: "branch",
    parent_node_id,
    label,
    label_en: label,
    summary,
    display_order,
    default_collapsed,
    emphasis: "normal",
    question_id: null,
    answer_type: null,
    allowed_answers: [],
    answer_bindings: [],
    related_entities: [],
    source_ids: [],
    ...overrides,
  };
}

function entity(
  entity_id: string,
  entity_type: string,
  label: string,
  summary: string,
  source_ids: string[],
  url = "",
) {
  return { entity_id, entity_type, label, label_en: label, summary, source_ids, url };
}

function renderMap(entry = "/map") {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <LocationProbe />
      <Routes>
        <Route path="/map" element={<MapPage />} />
        <Route path="/diagnose" element={<p>DIAGNOSE ROUTE</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

function LocationProbe() {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output data-testid="location-search">{location.search}</output>
      <button onClick={() => navigate(-1)} type="button">テスト履歴戻る</button>
    </>
  );
}

function currentSearch(): string {
  return screen.getByTestId("location-search").textContent ?? "";
}

async function loadedTree() {
  return screen.findByRole("tree", { name: "最適化問題の構造" });
}

function mockFirstView(response: Partial<Response>) {
  vi.mocked(fetch)
    .mockResolvedValueOnce({ ok: true, json: async () => rawManifest } as Response)
    .mockResolvedValueOnce(response as Response);
}

describe("MapPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (input: string) => ({
      ok: true,
      json: async () => input.includes("manifest.json")
        ? rawManifest
        : input.includes("recommendation/site-data.json") ? siteFixture() : mapFixture(),
    })));
    Element.prototype.scrollIntoView = vi.fn();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("fetches the base-aware ViewSpec and canonical predicate data", async () => {
    renderMap();
    const tree = await loadedTree();
    expect(fetch).toHaveBeenCalledTimes(6);
    expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/data\/manifest\.json$/u));
    expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/data\/views\/problem-structure\.json$/u));
    expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/data\/recommendation\/site-data\.json$/u));
    expect(within(tree).getAllByRole("treeitem")).toHaveLength(5);
    expect(within(tree).queryByText("質問")).not.toBeInTheDocument();
  });

  test("switches semantic Views in the shared URL and restores focus through a canonical entity", async () => {
    const viewsByPath = new Map<string, unknown>([
      ["views/problem-structure.json", rawProblemView],
      ["views/available-information.json", rawOracleView],
      ["views/guarantee-outcome.json", rawGuaranteeView],
      ["views/method-mechanism.json", rawMechanismView],
    ]);
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (input: string) => ({
      ok: true,
      json: async () => {
        if (input.includes("manifest.json")) return rawManifest;
        if (input.includes("recommendation/site-data.json")) return rawSiteData;
        const match = [...viewsByPath].find(([path]) => input.endsWith(path));
        return match?.[1];
      },
    })));
    const token = encodeAtlasState({
      stateVersion: 1,
      datasetVersion: rawProblemView.dataset_version,
      viewId: rawProblemView.view_id,
      viewVersion: rawProblemView.version,
      selectedNodeId: "question:Q05",
      answers: {},
    });
    renderMap(`/map?state=${token}`);

    const selector = await screen.findByRole("combobox", { name: "表示" });
    fireEvent.change(selector, { target: { value: "available-information" } });
    expect(await screen.findByRole("heading", { level: 1, name: "Oracle View" })).toBeVisible();

    const params = new URLSearchParams(currentSearch());
    expect(params.get("view")).toBe("available-information");
    const decoded = decodeAtlasState(params.get("state")!, {
      datasetVersion: rawOracleView.dataset_version,
      viewId: rawOracleView.view_id,
      viewVersion: rawOracleView.version,
      nodeIds: new Set(rawOracleView.nodes.map((node) => node.node_id)),
      questions: Object.fromEntries(rawSiteData.questions.map((question) => [question.question_id, {
        answerType: question.answer_type as "single_choice" | "multi_choice",
        allowedAnswers: question.allowed_answers,
      }])),
    }).state;
    expect(decoded.selectedNodeId).toBe("entity:feature:F_DERIVATIVE_ACCESS");
  });

  test("explains map states and exposes root/current/detail cues", async () => {
    renderMap();
    const tree = await loadedTree();
    expect(screen.getByRole("heading", { level: 2, name: "この条件は、どの問題構造に位置づく？" })).toBeVisible();
    fireEvent.click(screen.getByText("地図の読み方"));
    expect(screen.getByText(/倍率は文字の大きさです/u)).toBeVisible();
    const root = within(tree).getAllByRole("treeitem")[0];
    expect(root).toHaveClass("map-tree-item-root");
    expect(root).toHaveAttribute("title", "root A");
    expect(root).toHaveAttribute("aria-current", "location");
  });

  test("expands three levels and selection updates detail without changing answers", async () => {
    renderMap();
    const tree = await loadedTree();
    fireEvent.click(within(tree).getByRole("treeitem", { name: /分岐 A/u }));
    const question = within(tree).getByRole("treeitem", { name: /質問/u });
    expect(question).toHaveAttribute("aria-level", "2");
    fireEvent.click(question);
    const leaf = within(tree).getByRole("treeitem", { name: /0-1/u });
    expect(leaf).toHaveAttribute("aria-level", "3");
    expect(screen.getByText("関連項目")).toBeVisible();
    expect(screen.getAllByText("0-1").length).toBeGreaterThan(1);
    fireEvent.click(leaf);

    expect(leaf).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("分岐 A / 質問 / 0-1")).toBeVisible();
    expect(screen.getByText("binary summary")).toBeVisible();
    screen.getByTestId("map-detail-pane")
      .querySelectorAll<HTMLDetailsElement>("details:not([open]) > summary")
      .forEach((summary) => fireEvent.click(summary));
    expect(screen.getByText("Q01 = binary")).toBeVisible();
    expect(screen.getByText("CP-SAT")).toBeVisible();
    expect(screen.getByText("branch-and-cut")).toBeVisible();
    expect(screen.getAllByRole("heading", { level: 2, name: "構造化された適用前提" })).toHaveLength(2);
    expect(screen.getByRole("link", { name: "根拠" })).toHaveAttribute("href", "https://example.com/source");
    expect(within(tree).getByRole("treeitem", { name: /分岐 A/u })).toHaveClass("map-tree-item-ancestor");
    expect(within(tree).getByRole("treeitem", { name: "分岐 B" })).toHaveClass("map-tree-item-unrelated");

    const encoded = new URLSearchParams(currentSearch()).get("state");
    expect(encoded).not.toBeNull();
    expect(
      decodeAtlasState(encoded!, {
        datasetVersion: "0.2.0",
        viewId: "problem-structure",
        viewVersion: "1.0.0",
        nodeIds: new Set(mapFixture().nodes.map((item) => item.node_id)),
        questions: { Q01: { answerType: "single_choice", allowedAnswers: ["binary"] } },
      }).state.answers,
    ).toEqual({});
  });

  test("applies leaf bindings only through the explicit diagnosis action", async () => {
    renderMap("/map?keep=1&tag=a&tag=b");
    const tree = await loadedTree();
    fireEvent.click(within(tree).getByRole("button", { name: /分岐 A を展開/u }));
    const question = within(tree).getByRole("treeitem", { name: /質問/u });
    fireEvent.click(within(question).getByRole("button", { name: /質問 を展開/u }));
    fireEvent.click(within(tree).getByRole("treeitem", { name: /0-1/u }));
    let token = new URLSearchParams(currentSearch()).get("state")!;
    expect(decodeAtlasState(token, {
      datasetVersion: "0.2.0", viewId: "problem-structure", viewVersion: "1.0.0",
      nodeIds: new Set(mapFixture().nodes.map((item) => item.node_id)),
      questions: { Q01: { answerType: "single_choice", allowedAnswers: ["binary"] } },
    }).state.answers).toEqual({});

    fireEvent.click(screen.getByRole("button", { name: "この条件で診断する" }));
    expect(await screen.findByText("DIAGNOSE ROUTE")).toBeVisible();
    token = new URLSearchParams(currentSearch()).get("state")!;
    expect(decodeAtlasState(token, {
      datasetVersion: "0.2.0", viewId: "problem-structure", viewVersion: "1.0.0",
      nodeIds: new Set(mapFixture().nodes.map((item) => item.node_id)),
      questions: { Q01: { answerType: "single_choice", allowedAnswers: ["binary"] } },
    }).state.answers.Q01).toEqual({ status: "answered", values: ["binary"] });
    expect(new URLSearchParams(currentSearch()).get("keep")).toBe("1");
    expect(new URLSearchParams(currentSearch()).getAll("tag")).toEqual(["a", "b"]);
  });

  test("highlights every node whose exact bindings match Diagnose answers", async () => {
    const token = encodeAtlasState({
      stateVersion: 1,
      datasetVersion: "0.2.0",
      viewId: "problem-structure",
      viewVersion: "1.0.0",
      answers: { Q01: { status: "answered", values: ["binary"] } },
    });
    renderMap(`/map?state=${token}`);
    const tree = await loadedTree();
    const match = await within(tree).findByRole("treeitem", { name: /0-1/u });
    expect(match).toHaveClass(
      "map-tree-item-answer-match",
    );
    await waitFor(() => expect(match).toHaveAttribute("aria-selected", "true"));
    expect(screen.getByRole("heading", { level: 2, name: "0-1" })).toBeVisible();
    const canonical = new URLSearchParams(currentSearch()).get("state")!;
    const decoded = decodeAtlasState(canonical, {
      datasetVersion: "0.2.0", viewId: "problem-structure", viewVersion: "1.0.0",
      nodeIds: new Set(mapFixture().nodes.map((item) => item.node_id)),
      questions: { Q01: { answerType: "single_choice", allowedAnswers: ["binary"] } },
    }).state;
    expect(decoded.selectedNodeId).toBe("totally-opaque-leaf");
    expect(decoded.answers.Q01).toEqual({ status: "answered", values: ["binary"] });
  });

  test("shows a recoverable error when the explicit Map CTA cannot encode state", async () => {
    const fixture = mapFixture();
    const huge = "answer".repeat(350);
    const question = fixture.nodes.find((item) => item.node_id === "opaque-question") as unknown as {
      allowed_answers: string[];
    };
    question.allowed_answers = [huge];
    const leaf = fixture.nodes.find((item) => item.node_id === "totally-opaque-leaf") as unknown as {
      answer_bindings: Array<{ question_id: string; answer_value: string }>;
    };
    leaf.answer_bindings = [{ question_id: "Q01", answer_value: huge }];
    mockFirstView({ ok: true, json: async () => fixture });
    renderMap("/map?keep=1");
    const tree = await loadedTree();
    fireEvent.click(within(tree).getByRole("button", { name: /分岐 A を展開/u }));
    const questionItem = within(tree).getByRole("treeitem", { name: /質問/u });
    fireEvent.click(within(questionItem).getByRole("button", { name: /質問 を展開/u }));
    fireEvent.click(within(tree).getByRole("treeitem", { name: /0-1/u }));
    const before = currentSearch();

    fireEvent.click(screen.getByRole("button", { name: "この条件で診断する" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/maximum is 1800/u);
    expect(currentSearch()).toBe(before);
    expect(screen.queryByText("DIAGNOSE ROUTE")).not.toBeInTheDocument();
  });

  test("implements visible-tree keyboard movement without selecting on focus", async () => {
    renderMap();
    const tree = await loadedTree();
    const first = within(tree).getAllByRole("treeitem")[0];
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(within(tree).getAllByRole("treeitem")[1]).toHaveFocus();
    expect(currentSearch()).not.toContain("state=");
    fireEvent.keyDown(within(tree).getAllByRole("treeitem")[1], { key: "End" });
    expect(within(tree).getAllByRole("treeitem")[4]).toHaveFocus();
    fireEvent.keyDown(within(tree).getAllByRole("treeitem")[4], { key: "Home" });
    expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: "ArrowRight" });
    expect(first).toHaveAttribute("aria-expanded", "true");
    fireEvent.keyDown(first, { key: "ArrowRight" });
    expect(within(tree).getByRole("treeitem", { name: /質問/u })).toHaveFocus();
    fireEvent.keyDown(within(tree).getByRole("treeitem", { name: /質問/u }), { key: "ArrowLeft" });
    expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: "ArrowLeft" });
    expect(first).toHaveAttribute("aria-expanded", "false");
    fireEvent.keyDown(first, { key: " " });
    expect(first).toHaveAttribute("aria-selected", "true");
    const second = within(tree).getAllByRole("treeitem")[1];
    second.focus();
    fireEvent.keyDown(second, { key: "Enter" });
    expect(second).toHaveAttribute("aria-selected", "true");
  });

  test("restores deep links, expands ancestors, warns and canonicalizes stale tokens", async () => {
    const token = encodeAtlasState({
      stateVersion: 1,
      datasetVersion: "old",
      viewId: "problem-structure",
      viewVersion: "old",
      selectedNodeId: "totally-opaque-leaf",
      answers: {},
    });
    renderMap(`/map?state=${token}`);
    const tree = await loadedTree();
    expect(await within(tree).findByRole("treeitem", { name: /0-1/u })).toHaveAttribute("aria-selected", "true");
    expect(screen.getAllByText(/更新しました/u)).toHaveLength(2);
    await waitFor(() => expect(new URLSearchParams(currentSearch()).get("state")).not.toBe(token));
  });

  test("mobile pane, zoom, and focus-current preserve the AtlasState token", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 375 });
    renderMap();
    const tree = await loadedTree();
    fireEvent.click(within(tree).getByRole("button", { name: /分岐 A を展開/u }));
    const question = within(tree).getByRole("treeitem", { name: /質問/u });
    fireEvent.click(within(question).getByRole("button", { name: /質問 を展開/u }));
    fireEvent.click(within(tree).getByRole("treeitem", { name: /0-1/u }));
    fireEvent.click(within(tree).getByRole("button", { name: /分岐 A を折りたたむ/u }));
    expect(within(tree).queryByRole("treeitem", { name: /0-1/u })).not.toBeInTheDocument();
    const before = currentSearch();
    fireEvent.click(screen.getByRole("button", { name: "詳細" }));
    expect(screen.getByTestId("map-detail-pane")).toHaveAttribute("data-active", "true");
    fireEvent.click(screen.getByRole("button", { name: "拡大" }));
    fireEvent.click(screen.getByRole("button", { name: "縮小" }));
    fireEvent.click(screen.getByRole("button", { name: "倍率をリセット" }));
    fireEvent.click(screen.getByRole("button", { name: "現在地へ" }));
    expect(currentSearch()).toBe(before);
    await waitFor(() => expect(screen.getByTestId("map-tree-pane")).toHaveAttribute("data-active", "true"));
    expect(screen.getByTestId("map-detail-pane")).toHaveAttribute("data-active", "false");
    const restoredLeaf = await within(tree).findByRole("treeitem", { name: /0-1/u });
    await waitFor(() => expect(restoredLeaf).toHaveFocus());
    expect(restoredLeaf).toHaveAttribute("aria-selected", "true");
    await waitFor(() => expect(Element.prototype.scrollIntoView).toHaveBeenCalled());
  });

  test.each(["broken parent", "unreachable cycle"])(
    "keeps a %s deep link while normalizing roving focus to the visible tree",
    async (caseName) => {
      const fixture = mapFixture();
      const selectedId = caseName === "broken parent" ? "orphan-selected" : "cycle-selected";
      if (caseName === "broken parent") {
        fixture.nodes.push(node(selectedId, "missing-parent", "孤立した選択", 0, true, "orphan detail"));
      } else {
        fixture.nodes.push(
          node(selectedId, "cycle-peer", "循環した選択", 0, true, "cycle detail"),
          node("cycle-peer", selectedId, "循環相手", 0, true, "cycle peer"),
        );
      }
      mockFirstView({ ok: true, json: async () => fixture });
      const token = encodeAtlasState({
        stateVersion: 1,
        datasetVersion: fixture.dataset_version,
        viewId: fixture.view_id,
        viewVersion: fixture.version,
        selectedNodeId: selectedId,
        answers: {},
      });
      renderMap(`/map?state=${token}`);

      const tree = await loadedTree();
      expect(await screen.findByRole("heading", { level: 2, name: caseName === "broken parent" ? "孤立した選択" : "循環した選択" })).toBeVisible();
    expect(screen.getByText(/データの確認/u)).toBeVisible();
      const visibleItems = within(tree).getAllByRole("treeitem");
      expect(visibleItems.filter((item) => item.tabIndex === 0)).toEqual([visibleItems[0]]);
      expect(visibleItems.some((item) => item.tabIndex === -1)).toBe(true);
      const before = currentSearch();
      visibleItems[0].focus();
      fireEvent.keyDown(visibleItems[0], { key: "ArrowDown" });
      expect(visibleItems[1]).toHaveFocus();
      expect(visibleItems[0]).toHaveAttribute("tabindex", "-1");
      expect(visibleItems[1]).toHaveAttribute("tabindex", "0");
      expect(currentSearch()).toBe(before);
      expect(screen.getByRole("heading", { level: 2, name: caseName === "broken parent" ? "孤立した選択" : "循環した選択" })).toBeVisible();
    },
  );

  test("browser back restores the previous selection in tree, detail, and focus-current", async () => {
    renderMap();
    const tree = await loadedTree();
    const roots = within(tree).getAllByRole("treeitem");
    fireEvent.click(roots[0]);
    fireEvent.click(roots[1]);
    expect(roots[1]).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("button", { name: "テスト履歴戻る" }));
    await waitFor(() => expect(roots[0]).toHaveAttribute("aria-selected", "true"));
    expect(screen.getByRole("heading", { level: 2, name: "分岐 A" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "現在地へ" }));
    await waitFor(() => expect(roots[0]).toHaveFocus());
  });

  test.each([
    ["empty", { ...mapFixture(), nodes: [], edges: [], root_node_ids: [] }, "表示する項目がありません"],
    ["malformed", { ...mapFixture(), title: null }, "地図データを読み込めませんでした"],
  ])("renders a safe %s state", async (_label, fixture, message) => {
    mockFirstView({ ok: true, json: async () => fixture });
    renderMap();
    expect(await screen.findByText(new RegExp(message, "u"))).toBeVisible();
  });

  test("renders fetch failure and malformed URL state with reset", async () => {
    mockFirstView({ ok: false, status: 500 });
    const first = renderMap();
    expect(await screen.findByText("地図データを読み込めませんでした")).toBeVisible();
    first.unmount();

    mockFirstView({ ok: true, json: async () => mapFixture() });
    renderMap("/map?state=bad");
    expect(await screen.findByText(/URLの状態を復元できませんでした/u)).toBeVisible();
    expect(screen.getByRole("button", { name: "状態をリセット" })).toBeVisible();
  });

  test("keeps broken roots and references visible as diagnostics without recursing", async () => {
    const fixture = mapFixture();
    fixture.root_node_ids = ["missing-root"];
    fixture.nodes[0].parent_node_id = "missing-parent";
    mockFirstView({ ok: true, json: async () => fixture });
    renderMap();
    expect(await screen.findByText(/データの確認/u)).toBeVisible();
    expect(screen.getByText(/missing-root/u)).toBeVisible();
    expect(screen.getByText(/表示する項目がありません/u)).toBeVisible();
  });

  test("renders unknown entity types generically and unsafe URLs as text", async () => {
    const fixture = mapFixture() as unknown as {
      nodes: Array<{ related_entities: Array<{ entity_type: string; entity_id: string }> }>;
      entities: Array<ReturnType<typeof entity>>;
    };
    fixture.nodes[0].related_entities = [{ entity_type: "future", entity_id: "X" }];
    fixture.entities.push(entity("X", "future", "未知の対象", "unknown summary", [], "javascript:bad"));
    mockFirstView({ ok: true, json: async () => fixture });
    renderMap();
    const tree = await loadedTree();
    fireEvent.click(within(tree).getAllByRole("treeitem")[0]);
    fireEvent.click(screen.getByText("future（未分類）"));
    expect(screen.getByText("未知の対象")).toBeVisible();
    expect(screen.queryByRole("link", { name: "未知の対象" })).not.toBeInTheDocument();
  });
});
