import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import rawContent from "../../../public/data/content.json";
import rawEntityLinks from "../../../public/data/entity-links.json";
import { parseContentIndex } from "../../contracts/atlas-content";
import { parseEntityLinkIndex } from "../../contracts/entity-links";
import { EntityLinkProvider } from "../../state/entity-links";
import {
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

    expect(await screen.findByText("25件")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "動き・比較で学ぶ 25件" }))
      .toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByRole("article")).toHaveLength(25);
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
    await screen.findByText("25件");

    fireEvent.click(screen.getByRole("button", { name: "概念 22件" }));
    expect(screen.getByText("22件")).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(22);

    fireEvent.click(screen.getByRole("button", { name: "動き・比較で学ぶ 25件" }));
    expect(screen.getByText("25件")).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(25);

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
});

describe("content index ranking", () => {
  test("counts filters and ranks connected methods before disconnected content", () => {
    expect(contentFilterCounts(content.pages)).toEqual({
      all: 128,
      method: 106,
      concept: 22,
      connected: 25,
    });

    const ranked = filterAndRankContentPages(content.pages, "", "all");
    expect(ranked[0].kind).toBe("method");
    expect(ranked[0].visualization_ids.length + ranked[0].comparison_ids.length).toBeGreaterThan(0);
  });
});
