import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import comparisons from "../../../public/data/comparisons.json";
import { CompareLabIndexPage } from "./CompareLabIndexPage";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("CompareLabIndexPage", () => {
  test("loads and exposes every comparison preset", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => structuredClone(comparisons),
    }));

    render(<MemoryRouter><CompareLabIndexPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { level: 1, name: "条件を比較" })).toBeVisible();
    expect(screen.getByRole("link", { name: /細長い谷で一次法を比べる/u })).toHaveAttribute(
      "href",
      "/compare/COMPARE_GRADIENT_FAMILY",
    );
    expect(screen.getByRole("link", { name: /学習率を変えたときの発散を観察する/u })).toHaveAttribute(
      "href",
      "/compare/COMPARE_GRADIENT_DIVERGENCE",
    );
    expect(screen.getByRole("heading", { level: 2, name: "手法の違いから読む" })).toBeVisible();
    expect(screen.getByRole("heading", { level: 2, name: "失敗の違いから読む" })).toBeVisible();
    expect(screen.getAllByRole("heading", { level: 2 }).slice(1).map((heading) => heading.textContent)).toEqual([
      "手法の違いから読む",
      "条件の違いから読む",
      "初期条件の違いから読む",
      "失敗の違いから読む",
      "結果のトレードオフから読む",
      "戦略の違いから読む",
    ]);
    expect(screen.getAllByText("目的関数 · ほか3項目").length).toBeGreaterThan(0);
    expect(screen.getByText("更新則 · ほか1項目")).toBeVisible();
    expect(screen.getAllByText("順位ではなく差を見る").length).toBeGreaterThan(0);
    expect(screen.getAllByText("条件内で順位を読む").length).toBeGreaterThan(0);
    const moreMethodComparisons = screen.getByText("手法の違いの残り2件を見る");
    expect(moreMethodComparisons).toBeVisible();
    fireEvent.click(moreMethodComparisons);
    expect(screen.getByText("比較対象 2件 · 単体形状で見る")).toBeVisible();
    expect(screen.getByText("比較対象 2件 · 実行可能領域で見る")).toBeVisible();
    expect(screen.getByText("比較対象 2件 · 設計fieldの進化で見る")).toBeVisible();
  });
});
