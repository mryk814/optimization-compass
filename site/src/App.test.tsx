import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import App from "./App";
import type { EntityLinkIndex } from "./contracts/entity-links";
import rawLearningJourneys from "../public/data/learning-journeys.json";
import rawManifest from "../public/data/manifest.json";
import rawProblems from "../public/data/problems.json";
import rawVisualizationScenarios from "../public/data/visualization-scenarios.json";

const routes = [
  ["#/", "最適化したい問いを、問題の形にする"],
  ["#/map", "問題構造マップ"],
  ["#/diagnose", "診断"],
  ["#/theater", "Method Theater"],
  ["#/compare", "比較ラボ"],
  ["#/compare/gradient-quadratic", "比較条件を読み込み中"],
  ["#/gallery", "ケースギャラリー"],
  ["#/learn", "手法・概念を学ぶ"],
] as const;

const testLinks: EntityLinkIndex = {
  contract_version: "1.0.0",
  dataset_version: "0.2.0",
  generated_at: "2026-07-13T00:00:00Z",
  entities: [
    { entity_type: "method", entity_id: "M_NELDER_MEAD", label: "Nelder–Mead", summary: "", canonical_url: "/methods/M_NELDER_MEAD", aliases: ["/learn/method.nelder-mead"], external_url: null, relations: [] },
    { entity_type: "method", entity_id: "M_BFGS", label: "BFGS", summary: "", canonical_url: "/methods/M_BFGS", aliases: [], external_url: null, relations: [] },
    { entity_type: "trace", entity_id: "nelder-mead-quadratic", label: "Nelder–Mead trace", summary: "", canonical_url: "/traces/nelder-mead-quadratic", aliases: ["/theater/nelder-mead"], external_url: null, relations: [] },
    { entity_type: "comparison", entity_id: "COMPARE_GRADIENT_FAMILY", label: "Gradient comparison", summary: "", canonical_url: "/compare/COMPARE_GRADIENT_FAMILY", aliases: ["/compare/gradient-quadratic"], external_url: null, relations: [] },
  ],
};

const emptyView = {
  dataset_version: "0.2.0",
  generated_at: "2026-07-13T00:00:00Z",
  view_id: "problem-structure",
  preset_id: "VIEW_PROBLEM_STRUCTURE",
  version: "1.0.0",
  title: "Map",
  description: "Map",
  limitations: "No ranking",
  axis: "problem_structure",
  relation_types: ["hierarchy"],
  max_depth: 3,
  filter_policy: { mode: "authored_groups", groups: [{ group_id: "root", label: "Root", label_en: "Root", question_ids: [], feature_ids: ["F1"], method_ids: [], alternative_ids: [] }] },
  focus_fallback_entity_types: ["feature"],
  root_node_ids: ["root"],
  edges: [],
  entities: [],
  nodes: [
    {
      node_id: "root",
      node_type: "category",
      parent_node_id: null,
      label: "Root",
      label_en: "Root",
      summary: "",
      display_order: 1,
      default_collapsed: false,
      emphasis: "normal",
      related_entities: [],
      source_ids: [],
      question_id: null,
      answer_type: null,
      allowed_answers: [],
      answer_bindings: [],
    },
  ],
};

const releaseIdentity = {
  schema_version: 1,
  dataset_version: "0.3.0",
  release_date: "2026-07-15",
  database_sha256: "6fd8851e805ebd4b396905ca33d50b7dd292bfba7a17c02a5d3726e18f3886cc",
};

const featuredGallery = {
  contract_version: "2.0.0",
  dataset_version: rawLearningJourneys.dataset_version,
  cases: [
    {
      case_id: "EC017",
      title_ja: "観測に合うモデルを推定する",
      title_en: "Estimate a model from observations",
      domain: "science",
      problem_archetype_id: "PA033",
      feature_values: [{ feature_id: "F_VARIABLE_DOMAIN", value: "continuous" }],
      question_answers: { Q01: "continuous" },
      candidate_methods: [{
        method_id: "M_NELDER_MEAD",
        reason: "勾配を使わず、観測残差を直接評価できるため",
      }],
      conditional_methods: [{ method_id: "M_BFGS", reason: "滑らかで勾配が信頼できる場合" }],
      excluded_methods: [{ method_id: "M_BFGS", reason: "離散的な観測欠損があり、現在の前提には合わない" }],
      implementation_ids: ["I_SCIPY"],
      visualization_ids: ["VIEW_PROBLEM_STRUCTURE"],
      comparison_ids: [],
      source_ids: ["S001"],
      difficulty: "intro",
      status: "published",
      last_reviewed: "2026-07-16",
      question: "観測データに合うモデルパラメータを推定したい。",
      variable_domain: "X=[0,5]×[0,3]×[−1,2]⊂ℝ³。",
      decision_variables: "モデルの連続パラメータ。",
      objective: "観測残差を小さくする。",
      constraints: "物理的に妥当な上下限。",
      map_node_id: "answer:Q01:continuous",
      python_example: "print('example')",
      practical_notes: "初期値依存性を確認する。",
      limitations: ["この固定データだけで実問題での性能を保証しません。"],
    },
  ],
};

function jsonResponse(value: unknown) {
  return { ok: true, json: async () => value };
}

describe("application routes", () => {
  beforeEach(() => {
    window.location.hash = "#/";
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test.each(routes)("%s renders %s", (hash, heading) => {
    window.location.hash = hash;

    render(<App initialEntityLinks={testLinks} />);

    expect(screen.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  });

  test("home foregrounds one problem, its formulation, and an exclusion reason", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith("data/release.json")) return jsonResponse(releaseIdentity);
      if (url.endsWith("data/gallery.json")) return jsonResponse(featuredGallery);
      if (url.endsWith("data/learning-journeys.json")) return jsonResponse(rawLearningJourneys);
      if (url.endsWith("data/problems.json")) return jsonResponse(rawProblems);
      return jsonResponse(emptyView);
    }));

    render(<App initialEntityLinks={testLinks} />);

    expect(screen.getByRole("link", { name: "条件から診断を始める" })).toHaveAttribute(
      "href",
      "#/diagnose",
    );
    expect(screen.getByRole("link", { name: "実例から探す" })).toHaveAttribute(
      "href",
      "#/gallery",
    );
    expect(
      await screen.findByRole("heading", { level: 2, name: "観測に合うモデルを推定する" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { level: 3, name: "このケースを定式化すると" }),
    ).toBeVisible();
    expect(screen.getByText("f₁=x²+y²; f₂=(x−2)²+(y−2)²")).toBeVisible();
    expect(screen.getByText("0 ≤ x ≤ 2")).toBeVisible();
    expect(screen.getByText("Nelder–Mead")).toBeVisible();
    expect(screen.getByText("勾配を使わず、観測残差を直接評価できるため")).toBeVisible();
    expect(screen.getByText("選ばない理由")).toBeVisible();
    expect(screen.getByText("離散的な観測欠損があり、現在の前提には合わない")).toBeVisible();
    expect(screen.getByRole("link", { name: "このCaseの詳細を見る →" })).toHaveAttribute(
      "href",
      "#/gallery/EC017",
    );
    expect(screen.queryByLabelText("Atlasの主要な入口")).not.toBeInTheDocument();

    const secondary = screen.getByRole("navigation", { name: "次に進む入口" });
    expect(within(secondary).getByRole("link", { name: "問題構造をたどる" })).toHaveAttribute(
      "href",
      "#/map",
    );
    expect(within(secondary).getByRole("link", { name: "比較条件を揃える" })).toHaveAttribute(
      "href",
      "#/compare",
    );

    const footer = screen.getByRole("contentinfo");
    expect(within(footer).getByRole("link", { name: "コード: MIT" }).getAttribute("href"))
      .toMatch(/\/licenses\/LICENSE\.txt$/u);
    expect(within(footer).getByRole("link", { name: "データ: CC BY 4.0" })).toBeVisible();
    expect(within(footer).getByRole("link", { name: "本文: CC BY 4.0" })).toBeVisible();
  });

  test("footer renders the dataset version from the release identity", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(releaseIdentity)));

    render(<App initialEntityLinks={testLinks} />);

    expect(await screen.findByText("Dataset 0.3.0")).toBeVisible();
  });

  test("deprecated Theater alias redirects to its generated canonical Trace URL", async () => {
    window.location.hash = "#/theater/nelder-mead";
    render(<App initialEntityLinks={testLinks} />);
    await waitFor(() => expect(window.location.hash).toBe("#/traces/nelder-mead-quadratic"));
  });

  test("primary navigation and problem-first Home stay reachable at 375px", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 375,
    });

    render(<App initialEntityLinks={testLinks} />);

    const navigation = screen.getByRole("navigation", { name: "主要ナビゲーション" });
    const links = within(navigation).getAllByRole("link");
    expect(links).toHaveLength(9);
    links.forEach((link) => expect(link).toBeVisible());
    expect(screen.getByRole("link", { name: "条件から診断を始める" })).toBeVisible();
    expect(screen.getByRole("link", { name: "実例から探す" })).toBeVisible();
    within(screen.getByRole("navigation", { name: "次に進む入口" }))
      .getAllByRole("link")
      .forEach((link) => expect(link).toBeVisible());
  });

  test("the methods navigation opens the real learning index and stays active on method pages", () => {
    render(<App initialEntityLinks={testLinks} />);
    expect(screen.getByRole("link", { name: "手法を学ぶ" })).toHaveAttribute("href", "#/learn");
    cleanup();

    window.location.hash = "#/methods/M_NELDER_MEAD";
    render(<App initialEntityLinks={testLinks} />);
    expect(screen.getByRole("link", { name: "手法を学ぶ" })).toHaveAttribute("aria-current", "page");
  });

  test("keeps Theater and Compare as separate primary navigation destinations", () => {
    render(<App initialEntityLinks={testLinks} />);
    const navigation = screen.getByRole("navigation", { name: "主要ナビゲーション" });
    expect(within(navigation).getByRole("link", { name: "動きを見る" })).toHaveAttribute("href", "#/theater");
    expect(within(navigation).getByRole("link", { name: "条件を比較" })).toHaveAttribute("href", "#/compare");
  });

  test("the back control uses a safe in-app fallback on a direct entry", () => {
    window.history.replaceState({ idx: 0 }, "", "#/map");
    render(<App initialEntityLinks={testLinks} />);

    fireEvent.click(screen.getByRole("button", { name: "← ホームに戻る" }));

    expect(window.location.hash).toBe("#/");
  });

  test("supports keyboard focus for the skip link and primary route links", () => {
    render(<App initialEntityLinks={testLinks} />);

    const skipLink = screen.getByRole("link", { name: "本文へ移動" });
    skipLink.focus();
    expect(skipLink).toHaveFocus();
    fireEvent.click(skipLink);
    expect(screen.getByRole("main")).toHaveFocus();

    const learnLink = screen.getByRole("link", { name: "手法を学ぶ" });
    learnLink.focus();
    expect(learnLink).toHaveFocus();
    fireEvent.click(learnLink);
    expect(window.location.hash).toBe("#/learn");
  });

  test("unknown routes render the common Not Found page inside the shell", () => {
    window.location.hash = "#/unknown";

    render(<App initialEntityLinks={testLinks} />);

    expect(screen.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toBeVisible();
    expect(screen.getByRole("main")).toBeVisible();
    expect(screen.getByRole("contentinfo")).toBeVisible();
  });

  test("an unknown method ID uses the common Not Found page after checking Gallery", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith("data/release.json")) return jsonResponse(releaseIdentity);
      if (url.endsWith("data/gallery.json")) {
        return jsonResponse({ contract_version: "2.0.0", dataset_version: "0.3.0", cases: [] });
      }
      return jsonResponse(emptyView);
    }));
    window.location.hash = "#/methods/missing";

    render(<App initialEntityLinks={testLinks} />);

    expect(
      await screen.findByRole("heading", { level: 1, name: "ページが見つかりません" }),
    ).toBeVisible();
  });

  test.each([
    ["#/learn/missing", { contract_version: "2.0.0", dataset_version: rawManifest.dataset_version, pages: [] }],
    ["#/gallery/missing", { contract_version: "2.0.0", dataset_version: rawManifest.dataset_version, cases: [] }],
    [
      "#/compare/missing",
      { contract_version: "2.0.0", dataset_version: rawManifest.dataset_version, comparisons: [] },
    ],
  ])("%s uses the common Not Found page for an unknown entity ID", async (hash, payload) => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith("data/release.json")) return jsonResponse(releaseIdentity);
      if (url.endsWith("data/manifest.json")) return jsonResponse(rawManifest);
      if (url.endsWith("data/visualization-scenarios.json")) {
        return jsonResponse(rawVisualizationScenarios);
      }
      return jsonResponse(payload);
    }));
    window.location.hash = hash;

    render(<App initialEntityLinks={testLinks} />);

    expect(
      await screen.findByRole("heading", { level: 1, name: "ページが見つかりません" }),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Atlasへ戻る" })).toBeVisible();
    expect(screen.getByRole("link", { name: "問題構造を見る" })).toBeVisible();
  });

  test.each(["#/mapping", "#/diagnose-old", "#/gallery-old"])(
    "%s does not activate a prefix-colliding navigation item",
    (hash) => {
      window.location.hash = hash;

      render(<App initialEntityLinks={testLinks} />);

      expect(
        screen.getByRole("heading", { level: 1, name: "ページが見つかりません" }),
      ).toBeVisible();
      expect(
        within(screen.getByRole("navigation", { name: "主要ナビゲーション" })).queryByRole(
          "link",
          { current: "page" },
        ),
      ).not.toBeInTheDocument();
    },
  );
});
