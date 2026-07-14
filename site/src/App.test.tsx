import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import App from "./App";

const routes = [
  ["#/", "Optimization Atlas"],
  ["#/map", "問題構造マップ"],
  ["#/diagnose", "診断"],
  ["#/compare/gradient-quadratic", "手法を比較する"],
  ["#/gallery", "ケースギャラリー"],
  ["#/learn", "手法・概念を学ぶ"],
  ["#/theater/nelder-mead", "Nelder–Meadの幾何操作"],
] as const;

const emptyView = {
  dataset_version: "0.2.0",
  generated_at: "2026-07-13T00:00:00Z",
  view_id: "problem-structure",
  version: "1.0.0",
  title: "Map",
  description: "",
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

    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  });

  test("home exposes five clear entry points and both visualization routes in one operation", () => {
    render(<App />);

    const entries = screen.getByLabelText("Atlasの主要な入口");
    expect(within(entries).getAllByRole("article")).toHaveLength(5);
    expect(within(entries).getByRole("link", { name: "地図を見る" })).toHaveAttribute(
      "href",
      "#/map",
    );
    expect(within(entries).getByRole("link", { name: "診断を始める" })).toHaveAttribute(
      "href",
      "#/diagnose",
    );
    expect(within(entries).getByRole("link", { name: "教材を探す" })).toHaveAttribute(
      "href",
      "#/learn",
    );
    expect(within(entries).getByRole("link", { name: "Theaterを開く" })).toHaveAttribute(
      "href",
      "#/theater/nelder-mead",
    );
    expect(within(entries).getByRole("link", { name: "Compare Labを開く" })).toHaveAttribute(
      "href",
      "#/compare/gradient-quadratic",
    );
    expect(within(entries).getByRole("link", { name: "ケースを見る" })).toHaveAttribute(
      "href",
      "#/gallery",
    );
  });

  test("primary navigation and home entries stay reachable at 375px", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 375,
    });

    render(<App />);

    const navigation = screen.getByRole("navigation", { name: "主要ナビゲーション" });
    const links = within(navigation).getAllByRole("link");
    expect(links).toHaveLength(6);
    links.forEach((link) => expect(link).toBeVisible());
    within(screen.getByLabelText("Atlasの主要な入口"))
      .getAllByRole("link")
      .forEach((link) => expect(link).toBeVisible());
  });

  test("the methods navigation opens the real learning index and stays active on method pages", () => {
    render(<App />);
    expect(screen.getByRole("link", { name: "手法" })).toHaveAttribute("href", "#/learn");
    cleanup();

    window.location.hash = "#/methods/M_NELDER_MEAD";
    render(<App />);
    expect(screen.getByRole("link", { name: "手法" })).toHaveAttribute("aria-current", "page");
  });

  test("supports keyboard focus for the skip link and primary route links", () => {
    render(<App />);

    const skipLink = screen.getByRole("link", { name: "本文へ移動" });
    skipLink.focus();
    expect(skipLink).toHaveFocus();
    fireEvent.click(skipLink);
    expect(screen.getByRole("main")).toHaveFocus();

    const learnLink = screen.getByRole("link", { name: "手法" });
    learnLink.focus();
    expect(learnLink).toHaveFocus();
    fireEvent.click(learnLink);
    expect(window.location.hash).toBe("#/learn");
  });

  test("unknown routes render the common Not Found page inside the shell", () => {
    window.location.hash = "#/unknown";

    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toBeVisible();
    expect(screen.getByRole("main")).toBeVisible();
    expect(screen.getByRole("contentinfo")).toBeVisible();
  });

  test("an unknown method ID uses the common Not Found page after checking Gallery", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce(jsonResponse(emptyView))
        .mockResolvedValueOnce(
          jsonResponse({ contract_version: "1.0.0", dataset_version: "0.2.0", cases: [] }),
        ),
    );
    window.location.hash = "#/methods/missing";

    render(<App />);

    expect(
      await screen.findByRole("heading", { level: 1, name: "ページが見つかりません" }),
    ).toBeVisible();
  });

  test.each([
    ["#/learn/missing", { contract_version: "1.0.0", dataset_version: "0.2.0", pages: [] }],
    ["#/gallery/missing", { contract_version: "1.0.0", dataset_version: "0.2.0", cases: [] }],
    [
      "#/compare/missing",
      { contract_version: "1.0.0", dataset_version: "0.2.0", comparisons: [] },
    ],
  ])("%s uses the common Not Found page for an unknown entity ID", async (hash, payload) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(payload)));
    window.location.hash = hash;

    render(<App />);

    expect(
      await screen.findByRole("heading", { level: 1, name: "ページが見つかりません" }),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "Atlasへ戻る" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Mapを見る" })).toBeVisible();
  });

  test.each(["#/mapping", "#/diagnose-old", "#/gallery-old"])(
    "%s does not activate a prefix-colliding navigation item",
    (hash) => {
      window.location.hash = hash;

      render(<App />);

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
