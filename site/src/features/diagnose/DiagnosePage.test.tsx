import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

import rawManifest from "../../../public/data/manifest.json";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import rawView from "../../../public/data/views/problem-structure.json";
import { decodeAtlasState, encodeAtlasState, type AtlasCompatibilityCatalog } from "../../state/atlas-state";
import { DiagnosePage } from "./DiagnosePage";
import { MapPage } from "../map/MapPage";

function catalog(): AtlasCompatibilityCatalog {
  return {
    datasetVersion: rawSiteData.dataset_version,
    viewId: rawView.view_id,
    viewVersion: rawView.version,
    nodeIds: new Set(rawView.nodes.map((node) => node.node_id)),
    questions: Object.fromEntries(
      rawSiteData.questions.map((question) => [
        question.question_id,
        {
          answerType: question.answer_type as "single_choice" | "multi_choice",
          allowedAnswers: question.allowed_answers,
        },
      ]),
    ),
  };
}

function mockArtifacts(overrides: { manifest?: unknown; siteData?: unknown; view?: unknown } = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      const body = url.endsWith("data/manifest.json")
        ? (overrides.manifest ?? rawManifest)
        : url.endsWith("data/recommendation/site-data.json")
          ? (overrides.siteData ?? rawSiteData)
          : url.endsWith("data/views/problem-structure.json")
            ? (overrides.view ?? rawView)
            : undefined;
      if (body === undefined) return { ok: false, status: 404 } as Response;
      return { ok: true, json: async () => structuredClone(body) } as Response;
    }),
  );
}

function LocationProbe() {
  return <output data-testid="location">{useLocation().pathname + useLocation().search}</output>;
}

function renderDiagnose(entry = "/diagnose", realMap = false) {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <LocationProbe />
      <Routes>
        <Route path="/diagnose" element={<DiagnosePage />} />
        <Route path="/map" element={realMap ? <MapPage /> : <p>MAP ROUTE</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

function tokenFromLocation(): string {
  const location = screen.getByTestId("location").textContent ?? "";
  return new URLSearchParams(location.split("?")[1] ?? "").get("state") ?? "";
}

function encodeRawState(value: unknown): string {
  const bytes = new TextEncoder().encode(JSON.stringify(value));
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

describe("DiagnosePage", () => {
  beforeEach(() => mockArtifacts());
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("loads only manifest, SiteData, and ViewSpec without API or SQLite requests", async () => {
    renderDiagnose();

    expect(await screen.findByRole("heading", { level: 1, name: "診断" })).toBeVisible();
    await screen.findByText(/変数は連続・整数・0-1・カテゴリ・混合のどれですか/u);
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(vi.mocked(fetch).mock.calls.map(([url]) => String(url))).toEqual(
      expect.arrayContaining([
        expect.stringMatching(/data\/manifest\.json$/u),
        expect.stringMatching(/data\/recommendation\/site-data\.json$/u),
        expect.stringMatching(/data\/views\/problem-structure\.json$/u),
      ]),
    );
    expect(vi.mocked(fetch).mock.calls.some(([url]) => /api|sqlite/u.test(String(url)))).toBe(false);
    expect(screen.queryAllByRole("button", { pressed: true })).toHaveLength(0);
  });

  test("treats manifest, SiteData, and ViewSpec dataset mismatch as fatal", async () => {
    const mismatched = { ...rawView, dataset_version: "stale" };
    mockArtifacts({ view: mismatched });
    renderDiagnose();

    expect(await screen.findByRole("alert")).toHaveTextContent(/データ版.*一致しません/u);
    expect(screen.queryByText(rawSiteData.questions[0].question_ja)).not.toBeInTheDocument();
  });

  test.each([
    ["top-level version", { ...rawManifest, version: "9.9.9" }],
    [
      "recommendation path traversal",
      { ...rawManifest, recommendation: { ...rawManifest.recommendation, path: "../site-data.json" } },
    ],
    [
      "alternate ViewSpec path",
      { ...rawManifest, views: [{ ...rawManifest.views[0], path: "views/alternate.json" }] },
    ],
    [
      "recommendation entry version",
      { ...rawManifest, recommendation: { ...rawManifest.recommendation, version: "9.9.9" } },
    ],
    [
      "ViewSpec entry version",
      { ...rawManifest, views: [{ ...rawManifest.views[0], version: "9.9.9" }] },
    ],
  ])("rejects manifest %s mismatch", async (_label, invalidManifest) => {
    mockArtifacts({ manifest: invalidManifest });
    renderDiagnose();

    expect(await screen.findByRole("alert")).toHaveTextContent(/manifest/u);
    expect(screen.queryByText(rawSiteData.questions[0].question_ja)).not.toBeInTheDocument();
  });

  test("rejects an unsupported ViewSpec version even when the manifest entry matches it", async () => {
    mockArtifacts({
      manifest: {
        ...rawManifest,
        views: [{ ...rawManifest.views[0], version: "9.9.9" }],
      },
      view: { ...rawView, version: "9.9.9" },
    });
    renderDiagnose();

    expect(await screen.findByRole("alert")).toHaveTextContent(/ViewSpec.*version/u);
    expect(screen.queryByText(rawSiteData.questions[0].question_ja)).not.toBeInTheDocument();
  });

  test("keeps unanswered, unknown, N/A, single, and multi answers distinct in URL state", async () => {
    renderDiagnose();
    const q1 = await screen.findByRole("group", { name: /x（決めるもの）はどの種類ですか/u });
    expect(within(q1).queryByRole("button", { name: /^わからない/u })).not.toBeInTheDocument();
    fireEvent.click(within(q1).getByRole("button", { name: /^0-1/u }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q01).toEqual({
      status: "answered",
      values: ["binary"],
    });
    fireEvent.click(within(q1).getByRole("button", { name: "該当なし" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q01).toEqual({
      status: "not_applicable",
      values: [],
    });
    fireEvent.click(within(q1).getByRole("button", { name: "選択を解除" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q01).toBeUndefined();

    const q2 = screen.getByRole("group", { name: /f\(x\)や制約は、式や計算手順として書けますか/u });
    fireEvent.click(within(q2).getByRole("button", { name: /まだ分からない/u }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q02).toEqual({
      status: "unknown",
      values: ["unknown"],
    });

    const q4 = screen.getByRole("group", { name: /守る条件（制約）はありますか/u });
    fireEvent.click(within(q4).getByRole("button", { name: "各xの上下限" }));
    fireEvent.click(within(q4).getByRole("button", { name: "直線的な条件" }));
    fireEvent.click(within(q4).getByRole("button", { name: "各xの上下限" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q04).toEqual({
      status: "answered",
      values: ["linear"],
    });
    fireEvent.click(within(q4).getByRole("button", { name: "直線的な条件" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q04).toBeUndefined();
  });

  test("renders all result bands, implementations, problems, follow-ups, trace, and safe sources", async () => {
    const answers = {
      Q01: ["binary"], Q02: ["explicit_algebraic"], Q03: ["linear"],
      Q04: ["linear", "logical_or_combinatorial"], Q05: ["unreliable_or_none"],
      Q06: ["milliseconds_or_less"], Q07: ["deterministic_reliable"],
      Q08: ["100_to_10000"], Q09: ["global_candidate_desired"], Q10: ["gap_desired"],
      Q11: ["scheduling_routing"], Q12: ["one_off"],
    };
    const token = encodeAtlasState({
      stateVersion: 1,
      datasetVersion: rawSiteData.dataset_version,
      viewId: rawView.view_id,
      viewVersion: rawView.version,
      answers: Object.fromEntries(
        Object.entries(answers).map(([questionId, values]) => [questionId, { status: "answered", values }]),
      ),
    });
    renderDiagnose(`/diagnose?state=${token}`);

    for (const heading of ["代替解法", "第一候補", "条件付き候補", "除外候補"]) {
      expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
    }
    expect(screen.getAllByText("実装候補").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "関連する問題型" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "追加確認" })).toBeVisible();
    expect(screen.getByText(/R\d{3}/u)).toBeVisible();
    expect(screen.getAllByRole("link", { name: /根拠/u }).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "地図を開く" })).toBeVisible();

    const methodButton = screen.getAllByRole("button", { name: "地図で確認" })[0];
    const card = methodButton.closest("article");
    expect(card).not.toBeNull();
    const methodName = within(card!).getByRole("heading", { level: 3 }).textContent;
    const methodId = rawSiteData.methods.find((method) => method.name_ja === methodName)?.method_id;
    fireEvent.click(methodButton);
    expect(await screen.findByText("MAP ROUTE")).toBeVisible();
    const selectedNodeId = decodeAtlasState(tokenFromLocation(), catalog()).state.selectedNodeId;
    const selected = rawView.nodes.find((node) => node.node_id === selectedNodeId);
    expect(selected?.related_entities).toContainEqual({ entity_type: "method", entity_id: methodId });
  });

  test("preserves the token when navigating to Map", async () => {
    renderDiagnose("/diagnose?keep=1&tag=a&tag=b");
    const q1 = await screen.findByRole("group", { name: /x（決めるもの）はどの種類ですか/u });
    fireEvent.click(within(q1).getByRole("button", { name: /^0-1/u }));
    const token = tokenFromLocation();
    fireEvent.click(screen.getByRole("button", { name: "地図を開く" }));
    await waitFor(() => expect(screen.getByText("MAP ROUTE")).toBeVisible());
    expect(tokenFromLocation()).toBe(token);
    const location = screen.getByTestId("location").textContent ?? "";
    const params = new URLSearchParams(location.split("?")[1] ?? "");
    expect(params.get("keep")).toBe("1");
    expect(params.getAll("tag")).toEqual(["a", "b"]);
  });

  test("transitions answers-only Diagnose state into a visible deterministic Map selection", async () => {
    renderDiagnose("/diagnose?keep=1", true);
    const q1 = await screen.findByRole("group", { name: /x（決めるもの）はどの種類ですか/u });
    fireEvent.click(within(q1).getByRole("button", { name: /^0-1/u }));
    fireEvent.click(screen.getByRole("button", { name: "地図を開く" }));

    const tree = await screen.findByRole("tree", { name: "最適化問題の構造" });
    const match = await within(tree).findByRole("treeitem", { name: /^0-1answer$/u });
    expect(match).toHaveClass("map-tree-item-answer-match");
    await waitFor(() => expect(match).toHaveAttribute("aria-selected", "true"));
    expect(screen.getByRole("heading", { level: 2, name: "0-1" })).toBeVisible();
    expect(new URLSearchParams((screen.getByTestId("location").textContent ?? "").split("?")[1]).get("keep")).toBe("1");
  });

  test("shows a recoverable candidate navigation error without changing route or token", async () => {
    const hugeId = "0".repeat(2000);
    const hugeView = structuredClone(rawView);
    const nodes = hugeView.nodes as unknown as Array<Record<string, unknown>>;
    nodes.push({
      ...hugeView.nodes[0],
      node_id: hugeId,
      parent_node_id: null,
      display_order: 0,
      answer_bindings: [],
      related_entities: rawSiteData.methods.map((method) => ({
        entity_type: "method",
        entity_id: method.method_id,
      })),
    });
    mockArtifacts({ view: hugeView });
    const token = encodeAtlasState({
      stateVersion: 1,
      datasetVersion: rawSiteData.dataset_version,
      viewId: rawView.view_id,
      viewVersion: rawView.version,
      answers: {
        Q01: { status: "answered", values: ["continuous"] },
        Q05: { status: "answered", values: ["autodiff"] },
      },
    });
    renderDiagnose(`/diagnose?keep=1&state=${token}`);
    const before = screen.getByTestId("location").textContent;

    fireEvent.click((await screen.findAllByRole("button", { name: "地図で確認" }))[0]);

    expect(await screen.findByText(/maximum is 1800/u)).toBeVisible();
    expect(screen.getByTestId("location")).toHaveTextContent(before ?? "");
    expect(screen.queryByText("MAP ROUTE")).not.toBeInTheDocument();
  });

  test("recovers from a duplicate multi-choice URL token before recommendation render", async () => {
    const token = encodeRawState({
      stateVersion: 1,
      datasetVersion: rawSiteData.dataset_version,
      viewId: rawView.view_id,
      viewVersion: rawView.version,
      answers: { Q04: { status: "answered", values: ["linear", "linear"] } },
    });
    renderDiagnose(`/diagnose?state=${token}`);

    expect(await screen.findByRole("alert")).toHaveTextContent(/Q04.*duplicate/u);
    expect(screen.getByRole("button", { name: "状態をリセット" })).toBeVisible();
  });

  test("shows malformed URL recovery without silently resetting", async () => {
    renderDiagnose("/diagnose?state=bad");
    expect(await screen.findByRole("alert")).toHaveTextContent(/URLの状態を復元できませんでした/u);
    expect(screen.getByRole("button", { name: "状態をリセット" })).toBeVisible();
    expect(tokenFromLocation()).toBe("bad");
  });

  test("restores answers at 375px after reload without losing state", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 375 });
    const first = renderDiagnose();
    const q1 = await screen.findByRole("group", { name: /x（決めるもの）はどの種類ですか/u });
    fireEvent.click(within(q1).getByRole("button", { name: /^0-1/u }));
    const token = tokenFromLocation();
    first.unmount();

    renderDiagnose(`/diagnose?state=${token}`);
    const restored = await screen.findByRole("group", { name: /x（決めるもの）はどの種類ですか/u });
    expect(within(restored).getByRole("button", { name: /^0-1/u })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(tokenFromLocation()).toBe(token);
  });
});
