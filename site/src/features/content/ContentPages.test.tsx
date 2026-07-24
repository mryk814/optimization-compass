import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import rawContent from "../../../public/data/content.json";
import rawEntityLinks from "../../../public/data/entity-links.json";
import { parseContentIndex } from "../../contracts/atlas-content";
import { parseEntityLinkIndex } from "../../contracts/entity-links";
import { EntityLinkProvider } from "../../state/entity-links";
import {
  ContentPage,
  ContentIndexPage,
  contentFilterCounts,
  filterAndRankContentPages,
} from "./ContentPages";

const content = parseContentIndex(structuredClone(rawContent));
const entityLinks = parseEntityLinkIndex(structuredClone(rawEntityLinks));

function renderPage() {
  return render(
    <EntityLinkProvider initialIndex={entityLinks}>
      <MemoryRouter>
        <ContentIndexPage />
      </MemoryRouter>
    </EntityLinkProvider>,
  );
}

function renderDetail(contentId: string) {
  return render(
    <EntityLinkProvider initialIndex={entityLinks}>
      <MemoryRouter initialEntries={[`/learn/${contentId}`]}>
        <Routes>
          <Route element={<ContentPage />} path="/learn/:contentId" />
        </Routes>
      </MemoryRouter>
    </EntityLinkProvider>,
  );
}

describe("ContentIndexPage", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => structuredClone(rawContent),
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test("starts with connected learning and keeps the complete catalog available", async () => {
    renderPage();

    expect(await screen.findByText("37件")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "動き・比較で学ぶ 37件" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByRole("article")).toHaveLength(37);
    expect(screen.getByRole("button", { name: "すべて 128件" })).toBeVisible();
    expect(screen.getByRole("button", { name: "手法 106件" })).toBeVisible();
    expect(screen.getByRole("button", { name: "概念 22件" })).toBeVisible();

    const firstCard = screen.getAllByRole("article")[0];
    expect(within(firstCard).getByText("手法")).toBeVisible();
    expect(within(firstCard).getByText("教材を読む →")).toBeVisible();
    expect(within(firstCard).getByRole("navigation")).toBeVisible();
  });

  test("filters by kind, connected learning, query, and empty results", async () => {
    renderPage();
    await screen.findByText("37件");

    fireEvent.click(screen.getByRole("button", { name: "概念 22件" }));
    expect(screen.getByText("22件")).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(22);

    fireEvent.click(screen.getByRole("button", { name: "動き・比較で学ぶ 37件" }));
    expect(screen.getByText("37件")).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(37);

    fireEvent.click(screen.getByRole("button", { name: "すべて 128件" }));
    fireEvent.change(screen.getByRole("searchbox", { name: "教材を検索" }), {
      target: { value: "Chance constraint・CVaR・robustness" },
    });
    expect(screen.getByText("1件")).toBeInTheDocument();

    fireEvent.change(screen.getByRole("searchbox", { name: "教材を検索" }), {
      target: { value: "該当しない検索語xyz" },
    });
    await waitFor(() => expect(screen.getByText("0件")).toBeInTheDocument());
    expect(screen.getByText("一致する教材が見つかりません。種類か検索語を変えてください。"))
      .toBeVisible();
  });

  test("hides an empty related-links row and labels connected routes for readers", async () => {
    renderDetail("concept.spd-matrix-geometry");
    expect(await screen.findByRole("heading", { name: "SPD matrixの表現と境界" }))
      .toBeVisible();
    expect(screen.queryByText("関連する動き・比較")).not.toBeInTheDocument();
    cleanup();

    renderDetail("concept.pde-constrained-optimization");
    expect(await screen.findByRole("heading", { name: "PDE制約付き最適化" })).toBeVisible();

    const page = content.pages.find(
      (item) => item.content_id === "concept.pde-constrained-optimization",
    );
    const trace = entityLinks.entities.find(
      (entity) => entity.entity_type === "trace"
        && entity.entity_id === page?.visualization_ids[0],
    );
    expect(trace).toBeDefined();
    expect(screen.getByRole("link", { name: `動きを見る: ${trace!.label}` })).toBeVisible();
    expect(screen.getByRole("link", { name: "比較条件を見る" })).toBeVisible();
    expect(screen.queryByText(page!.visualization_ids[0])).not.toBeInTheDocument();
    expect(screen.queryByText(page!.comparison_ids[0])).not.toBeInTheDocument();
  });
});

describe("content index ranking", () => {
  test("counts filters and ranks connected methods before disconnected content", () => {
    expect(contentFilterCounts(content.pages)).toEqual({
      all: 128,
      method: 106,
      concept: 22,
      connected: 37,
    });

    const ranked = filterAndRankContentPages(content.pages, "", "all");
    expect(ranked[0].kind).toBe("method");
    expect(ranked[0].visualization_ids.length + ranked[0].comparison_ids.length).toBeGreaterThan(0);
  });
});
