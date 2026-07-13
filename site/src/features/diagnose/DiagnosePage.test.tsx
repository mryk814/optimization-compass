import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

import rawManifest from "../../../public/data/manifest.json";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import rawView from "../../../public/data/views/problem-structure.json";
import { decodeAtlasState, encodeAtlasState, type AtlasCompatibilityCatalog } from "../../state/atlas-state";
import { DiagnosePage } from "./DiagnosePage";

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

function renderDiagnose(entry = "/diagnose") {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <LocationProbe />
      <Routes>
        <Route path="/diagnose" element={<DiagnosePage />} />
        <Route path="/map" element={<p>MAP ROUTE</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

function tokenFromLocation(): string {
  const location = screen.getByTestId("location").textContent ?? "";
  return new URLSearchParams(location.split("?")[1] ?? "").get("state") ?? "";
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
    await screen.findByText("変数は連続・整数・0-1・カテゴリ・混合のどれですか？");
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

  test("keeps unanswered, unknown, N/A, single, and multi answers distinct in URL state", async () => {
    renderDiagnose();
    const q1 = await screen.findByRole("group", { name: rawSiteData.questions[0].question_ja });
    expect(within(q1).queryByRole("button", { name: /^わからない/u })).not.toBeInTheDocument();
    fireEvent.click(within(q1).getByRole("button", { name: "0-1" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q01).toEqual({
      status: "answered",
      values: ["binary"],
    });
    fireEvent.click(within(q1).getByRole("button", { name: "該当なし" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q01).toEqual({
      status: "not_applicable",
      values: [],
    });
    fireEvent.click(within(q1).getByRole("button", { name: "回答をクリア" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q01).toBeUndefined();

    const q2 = screen.getByRole("group", { name: rawSiteData.questions[1].question_ja });
    fireEvent.click(within(q2).getByRole("button", { name: /わからない/u }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q02).toEqual({
      status: "unknown",
      values: ["unknown"],
    });

    const q4 = screen.getByRole("group", { name: rawSiteData.questions[3].question_ja });
    fireEvent.click(within(q4).getByRole("button", { name: "上下限" }));
    fireEvent.click(within(q4).getByRole("button", { name: "線形" }));
    fireEvent.click(within(q4).getByRole("button", { name: "上下限" }));
    expect(decodeAtlasState(tokenFromLocation(), catalog()).state.answers.Q04).toEqual({
      status: "answered",
      values: ["linear"],
    });
    fireEvent.click(within(q4).getByRole("button", { name: "線形" }));
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
    expect(screen.getByRole("button", { name: "地図上で見る" })).toBeVisible();

    const methodButton = screen.getAllByRole("button", { name: "地図で見る" })[0];
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
    renderDiagnose();
    const q1 = await screen.findByRole("group", { name: rawSiteData.questions[0].question_ja });
    fireEvent.click(within(q1).getByRole("button", { name: "0-1" }));
    const token = tokenFromLocation();
    fireEvent.click(screen.getByRole("button", { name: "地図上で見る" }));
    await waitFor(() => expect(screen.getByText("MAP ROUTE")).toBeVisible());
    expect(tokenFromLocation()).toBe(token);
  });

  test("shows malformed URL recovery without silently resetting", async () => {
    renderDiagnose("/diagnose?state=bad");
    expect(await screen.findByRole("alert")).toHaveTextContent(/URL の状態を復元できません/u);
    expect(screen.getByRole("button", { name: "状態をリセット" })).toBeVisible();
    expect(tokenFromLocation()).toBe("bad");
  });

  test("restores answers at 375px after reload without losing state", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 375 });
    const first = renderDiagnose();
    const q1 = await screen.findByRole("group", { name: rawSiteData.questions[0].question_ja });
    fireEvent.click(within(q1).getByRole("button", { name: "0-1" }));
    const token = tokenFromLocation();
    first.unmount();

    renderDiagnose(`/diagnose?state=${token}`);
    const restored = await screen.findByRole("group", { name: rawSiteData.questions[0].question_ja });
    expect(within(restored).getByRole("button", { name: "0-1" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(tokenFromLocation()).toBe(token);
  });
});
