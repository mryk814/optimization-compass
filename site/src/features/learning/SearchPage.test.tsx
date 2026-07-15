import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, test, vi } from "vitest";

import fixture from "../../../public/data/learning-graph.json";
import { SearchPage } from "./SearchPage";

afterEach(() => vi.unstubAllGlobals());

describe("SearchPage", () => {
  test("shows every disambiguated candidate for a shared acronym", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(fixture))));
    render(<MemoryRouter initialEntries={["/search?q=IP"]}><SearchPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: /整数計画/u })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /内点法/u })).toBeInTheDocument();
    expect(screen.getAllByText(/別候補/u)).toHaveLength(2);
  });

  test("marks a deprecated term separately from current synonyms", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(fixture))));
    render(<MemoryRouter initialEntries={["/search?q=巡回セールスマン一般"]}><SearchPage /></MemoryRouter>);

    expect(await screen.findByText("非推奨語: 巡回セールスマン一般")).toBeInTheDocument();
  });
});
