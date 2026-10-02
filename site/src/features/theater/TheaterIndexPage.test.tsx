import { fireEvent, render, screen } from "@testing-library/react";
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
    expect(screen.queryByRole("heading", { name: "形と動きを3Dで読む" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "トポロジー最適化を読む" })).toHaveAttribute("href", "/learn/topology-optimization");
    expect(screen.getByRole("link", { name: "制約付き非線形計画を読む" })).toHaveAttribute("href", "/learn/concept.constrained-nlp");
    expect(screen.getByRole("link", { name: "最適制御を読む" })).toHaveAttribute("href", "/learn/concept.optimal-control");
    const scenarioCount = scenarios.scenarios.length;
    const representativeCount = new Set(scenarios.scenarios.map((scenario) => scenario.artifact.renderer_family)).size;
    expect(await screen.findByText(`${representativeCount}件を表示 · 条件一致 ${scenarioCount}件 · 公開 ${scenarioCount}件`)).toBeVisible();
    const advancedGuide = screen.getByText("nested・equilibrium・hybrid の run で分けて見る値");
    expect(advancedGuide).toBeVisible();
    expect(screen.getByText(/outer progress · inner residual · solve tolerance/u)).not.toBeVisible();
    fireEvent.click(advancedGuide);
    expect(screen.getByText(/outer progress · inner residual · solve tolerance/u)).toBeVisible();
    expect(screen.getAllByText(/観測: /u).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /共通診断probe · TRF適用条件/u })).toHaveAttribute("href", "/traces/exponential-fit-trf");
    expect(screen.getAllByRole("link", { name: /Nelder–Meadの幾何操作/u })[0]).toHaveAttribute("href", "/traces/nelder-mead-quadratic");
    expect(screen.getByRole("link", { name: /0-1 knapsack: 最適性証明/u })).toHaveAttribute("href", "/theater/search-tree/binary-knapsack-bnb-complete");
    expect(screen.getByRole("link", { name: /高価な1次元black-box: explore \/ noiseless/u })).toHaveAttribute("href", "/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS");
    expect(screen.queryByText(/問題: INSTANCE_/u)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("表示範囲"), { target: { value: "all" } });
    expect(screen.getByText(`${scenarioCount}件を表示 · 条件一致 ${scenarioCount}件 · 公開 ${scenarioCount}件`)).toBeVisible();
    expect(screen.queryByText("sensitivity_variant")).not.toBeInTheDocument();
    expect(screen.getAllByText(/条件差/u).length).toBeGreaterThan(0);

    fireEvent.change(screen.getByLabelText("見る目的"), { target: { value: "application_result" } });
    fireEvent.change(screen.getByLabelText("問題領域"), { target: { value: "discrete" } });
    expect(screen.getByRole("link", {
      name: /同じ希望充足数から負荷の偏りが小さい勤務表を選ぶ/u,
    })).toBeVisible();
    fireEvent.change(screen.getByLabelText("表示範囲"), { target: { value: "representative" } });
    fireEvent.change(screen.getByLabelText("見る目的"), { target: { value: "all" } });
    fireEvent.change(screen.getByLabelText("問題領域"), { target: { value: "all" } });
    expect(screen.getByText(`${representativeCount}件を表示 · 条件一致 ${scenarioCount}件 · 公開 ${scenarioCount}件`)).toBeVisible();
  });
});
