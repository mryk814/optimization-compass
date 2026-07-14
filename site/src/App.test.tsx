import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import App from "./App";
import type { EntityLinkIndex } from "./contracts/entity-links";

const routes = [
  ["#/", "Optimization Atlas"],
  ["#/map", "問題構造マップ"],
  ["#/diagnose", "診断"],
  ["#/compare/gradient-quadratic", "手法を比較する"],
  ["#/gallery", "ケースギャラリー"],
  ["#/learn", "手法・概念を学ぶ"],
] as const;

const testLinks: EntityLinkIndex = {
  contract_version: "1.0.0",
  dataset_version: "0.2.0",
  generated_at: "2026-07-13T00:00:00Z",
  entities: [
    { entity_type: "method", entity_id: "M_NELDER_MEAD", label: "Nelder–Mead", summary: "", canonical_url: "/methods/M_NELDER_MEAD", aliases: ["/learn/method.nelder-mead"], external_url: null, relations: [] },
    { entity_type: "trace", entity_id: "nelder-mead-quadratic", label: "Nelder–Mead trace", summary: "", canonical_url: "/traces/nelder-mead-quadratic", aliases: ["/theater/nelder-mead"], external_url: null, relations: [] },
    { entity_type: "comparison", entity_id: "COMPARE_GRADIENT_FAMILY", label: "Gradient comparison", summary: "", canonical_url: "/compare/COMPARE_GRADIENT_FAMILY", aliases: ["/compare/gradient-quadratic"], external_url: null, relations: [] },
  ],
};

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

const releaseIdentity = {
  schema_version: 1,
  dataset_version: "0.3.0",
  release_date: "2026-07-15",
  database_sha256: "6fd8851e805ebd4b396905ca33d50b7dd292bfba7a17c02a5d3726e18f3886cc",
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

  test("home exposes five clear entry points and both visualization routes in one operation", () => {
    render(<App initialEntityLinks={testLinks} />);

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
      "#/traces/nelder-mead-quadratic",
    );
    expect(within(entries).getByRole("link", { name: "Compare Labを開く" })).toHaveAttribute(
      "href",
      "#/compare/COMPARE_GRADIENT_FAMILY",
    );
    expect(within(entries).getByRole("link", { name: "ケースを見る" })).toHaveAttribute(
      "href",
      "#/gallery",
    );

    const footer = screen.getByRole("contentinfo");
    expect(within(footer).getByRole("link", { name: "Code: MIT" }).getAttribute("href"))
      .toMatch(/\/licenses\/LICENSE\.txt$/u);
    expect(within(footer).getByRole("link", { name: "Data: CC BY 4.0" })).toBeVisible();
    expect(within(footer).getByRole("link", { name: "Content: CC BY 4.0" })).toBeVisible();
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

  test("primary navigation and home entries stay reachable at 375px", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 375,
    });

    render(<App initialEntityLinks={testLinks} />);

    const navigation = screen.getByRole("navigation", { name: "主要ナビゲーション" });
    const links = within(navigation).getAllByRole("link");
    expect(links).toHaveLength(6);
    links.forEach((link) => expect(link).toBeVisible());
    within(screen.getByLabelText("Atlasの主要な入口"))
      .getAllByRole("link")
      .forEach((link) => expect(link).toBeVisible());
  });

  test("the methods navigation opens the real learning index and stays active on method pages", () => {
    render(<App initialEntityLinks={testLinks} />);
    expect(screen.getByRole("link", { name: "手法" })).toHaveAttribute("href", "#/learn");
    cleanup();

    window.location.hash = "#/methods/M_NELDER_MEAD";
    render(<App initialEntityLinks={testLinks} />);
    expect(screen.getByRole("link", { name: "手法" })).toHaveAttribute("aria-current", "page");
  });

  test("supports keyboard focus for the skip link and primary route links", () => {
    render(<App initialEntityLinks={testLinks} />);

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

    render(<App initialEntityLinks={testLinks} />);

    expect(screen.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toBeVisible();
    expect(screen.getByRole("main")).toBeVisible();
    expect(screen.getByRole("contentinfo")).toBeVisible();
  });

  test("an unknown method ID uses the common Not Found page after checking Gallery", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith("data/release.json")) return jsonResponse(releaseIdentity);
      if (url.endsWith("data/gallery.json")) {
        return jsonResponse({ contract_version: "1.0.0", dataset_version: "0.3.0", cases: [] });
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
    ["#/learn/missing", { contract_version: "1.0.0", dataset_version: "0.2.0", pages: [] }],
    ["#/gallery/missing", { contract_version: "1.0.0", dataset_version: "0.2.0", cases: [] }],
    [
      "#/compare/missing",
      { contract_version: "1.0.0", dataset_version: "0.2.0", comparisons: [] },
    ],
  ])("%s uses the common Not Found page for an unknown entity ID", async (hash, payload) => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (url: string) =>
      url.endsWith("data/release.json") ? jsonResponse(releaseIdentity) : jsonResponse(payload),
    ));
    window.location.hash = hash;

    render(<App initialEntityLinks={testLinks} />);

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
