import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import entityLinks from "../../../public/data/entity-links.json";
import scenarios from "../../../public/data/visualization-scenarios.json";
import { parseEntityLinkIndex } from "../../contracts/entity-links";
import { EntityLinkProvider } from "../../state/entity-links";
import { TheaterIndexPage } from "./TheaterIndexPage";

describe("TheaterIndexPage", () => {
  test("generates every published scenario from canonical data", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => structuredClone(scenarios) }));
    render(<MemoryRouter><EntityLinkProvider initialIndex={parseEntityLinkIndex(entityLinks)}><TheaterIndexPage /></EntityLinkProvider></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1, name: "手法の動きを見る" })).toBeVisible();
    expect(screen.getByRole("heading", { level: 2, name: "nested・equilibrium・hybrid の run で分けて見る値" })).toBeVisible();
    expect(screen.getByText(/outer progress · inner residual · solve tolerance/u)).toBeVisible();
    expect(await screen.findByText("29 / 29 シナリオ")).toBeVisible();
    expect(screen.getAllByText(/観測: /u).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /共通診断probe · TRF適用条件/u })).toHaveAttribute("href", "/traces/exponential-fit-trf");
    expect(screen.getAllByRole("link", { name: /Nelder–Meadの幾何操作/u })[0]).toHaveAttribute("href", "/traces/nelder-mead-quadratic");
    expect(screen.getByRole("link", { name: /0-1 knapsack: 最適性証明/u })).toHaveAttribute("href", "/theater/search-tree/binary-knapsack-bnb-complete");
    expect(screen.getByRole("link", { name: /高価な1次元black-box: explore \/ noiseless/u })).toHaveAttribute("href", "/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS");
  });
});
