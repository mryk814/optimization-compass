import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, test, vi } from "vitest";

import manifest from "../../../public/data/manifest.json";
import searchIndex from "../../../public/data/search-index.json";
import { SearchPage } from "./SearchPage";
import { resetSearchIndexCache } from "./search-data";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); resetSearchIndexCache(); });

function mockSearchData(): void {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    return new Response(JSON.stringify(url.endsWith("manifest.json") ? manifest : searchIndex));
  }));
}

describe("SearchPage", () => {
  test("links to symptom-first failure guidance without adding another primary filter", () => {
    mockSearchData();
    render(<MemoryRouter initialEntries={["/search"]}><SearchPage /></MemoryRouter>);

    expect(screen.getByRole("link", { name: "失敗の兆候・除外理由から探す →" })).toHaveAttribute(
      "href",
      "/failures",
    );
  });

  test("resolves an English alias and explains why it matched", async () => {
    mockSearchData();
    render(<MemoryRouter initialEntries={["/search?q=BO&type=method"]}><SearchPage /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: /ベイズ最適化/u })).toBeInTheDocument();
    expect(screen.getAllByText(/一致: 別名・略語/u).length).toBeGreaterThan(0);
    expect(screen.getByRole("checkbox", { name: /手法/u })).toBeChecked();
  });

  test("keeps query and filters in URL state while narrowing results", async () => {
    mockSearchData();
    render(<MemoryRouter initialEntries={["/search?q=配送順を決めたい"]}><SearchPage /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: /配送・経路最適化/u })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: /ケース/u }));
    await waitFor(() => expect(screen.getByRole("checkbox", { name: /ケース/u })).toBeChecked());
    expect(screen.getByRole("searchbox", { name: "検索" })).toHaveValue("配送順を決めたい");
  });

  test("focuses global search with the slash shortcut", async () => {
    mockSearchData();
    render(<MemoryRouter initialEntries={["/search"]}><SearchPage /></MemoryRouter>);
    const input = await screen.findByRole("searchbox", { name: "検索" });
    fireEvent.keyDown(window, { key: "/" });
    expect(input).toHaveFocus();
  });

  test("keeps Japanese IME composition local until conversion is confirmed", async () => {
    mockSearchData();
    render(<MemoryRouter initialEntries={["/search"]}><SearchPage /></MemoryRouter>);
    const input = await screen.findByRole("searchbox", { name: "検索" });
    expect(screen.getByText(/件を検索できます/u)).toBeInTheDocument();

    fireEvent.compositionStart(input);
    fireEvent.change(input, { target: { value: "ベイズ" } });

    expect(input).toHaveValue("ベイズ");
    expect(screen.getByText(/件を検索できます/u)).toBeInTheDocument();

    fireEvent.compositionEnd(input);
    expect((await screen.findAllByRole("heading", { name: /ベイズ最適化/u })).length).toBeGreaterThan(0);
  });
});
