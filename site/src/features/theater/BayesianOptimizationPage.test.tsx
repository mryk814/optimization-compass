import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

import manifest from "../../../public/data/manifest.json";
import scenarios from "../../../public/data/visualization-scenarios.json";
import exploreNoiseless from "../../../public/data/visualizations/bo-explore-noiseless.json";
import exploreSmallNoise from "../../../public/data/visualizations/bo-explore-small_noise.json";
import ledgerPayload from "../../../public/data/visualizations/bo-multi-fidelity-ledger.json";
import { BayesianOptimizationPage } from "./BayesianOptimizationPage";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function LocationProbe() {
  const location = useLocation();
  return <output aria-label="current route">{location.pathname + location.search}</output>;
}

function renderPage(entry = "/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS") {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    const body = url.endsWith("data/manifest.json") ? manifest
      : url.endsWith("visualization-scenarios.json") ? scenarios
            : url.endsWith("bo-explore-noiseless.json") ? exploreNoiseless
              : url.endsWith("bo-explore-small_noise.json") ? exploreSmallNoise
                : url.endsWith("bo-multi-fidelity-ledger.json") ? ledgerPayload
                : undefined;
    return body ? { ok: true, json: async () => structuredClone(body) } : { ok: false, status: 404 };
  }));
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <Routes>
        <Route path="/theater/bayesian-optimization/:scenarioId" element={<><BayesianOptimizationPage /><LocationProbe /></>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("BayesianOptimizationPage", () => {
  test("renders the generated trace, rationale, equal-budget table, and keyboard playback", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { level: 1, name: "ベイズ最適化の1回の実行" })).toBeVisible();
    expect(await screen.findByText(/再生を押すと、観測/u)).toBeVisible();
    expect(screen.getByRole("heading", { level: 2, name: "再生して、次の評価点が選ばれるまでを見る" })).toBeVisible();
    expect(await screen.findByText(/最適化方向: minimize/u)).toBeVisible();
    expect(screen.getByText(/optimizerが参照しない真の目的関数/u)).toBeVisible();
    expect(screen.getByRole("img", { name: /surrogateの平均/u })).toBeVisible();
    expect(screen.getByRole("table", { name: /best-so-far/u })).toBeVisible();
    const player = screen.getByLabelText(/左右矢印で移動/u);
    fireEvent.keyDown(player, { key: "ArrowRight" });
    expect(screen.getByText("フレーム 2/8 · 1倍")).toBeVisible();
    fireEvent.keyDown(player, { key: " " });
    expect(screen.getByRole("button", { name: "一時停止" })).toBeVisible();
  });

  test("switches to the small-noise generated preset", async () => {
    renderPage();
    await screen.findByText(/noise σ=0/u);
    fireEvent.change(screen.getByRole("combobox", { name: /観測ノイズ/u }), { target: { value: "small_noise" } });
    await waitFor(() => expect(screen.getByText(/noise σ=0.08/u)).toBeVisible());
    expect(screen.getByLabelText("current route")).toHaveTextContent(
      "/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_SMALL_NOISE",
    );
  });

  test("rejects an unknown scenario ID instead of falling back by substring", async () => {
    renderPage("/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLOIT_UNKNOWN");

    expect(await screen.findByRole("heading", { level: 1, name: "ページが見つかりません" })).toBeVisible();
    expect(screen.getByText(/scenario ID「SCENARIO_BO_1D_EXPLOIT_UNKNOWN」/u)).toBeVisible();
  });

  test("renders the multi-fidelity evaluation ledger without a cost-aligned Compare", async () => {
    renderPage("/theater/bayesian-optimization/SCENARIO_BO_1D_MULTIFIDELITY_LEDGER");
    expect(await screen.findByRole("heading", { level: 2, name: "Simulator evaluation ledger" })).toBeVisible();
    const ledgerTable = screen.getByRole("table", { name: "Simulator evaluation ledger" });
    expect(ledgerTable).toBeVisible();
    fireEvent.change(screen.getByLabelText("評価位置"), { target: { value: "11" } });
    expect(ledgerTable).toHaveTextContent("14/14");
    expect(screen.getByText("censored")).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2, name: /同じ予算での比較/u })).toBeNull();
    expect(screen.getByText(/cost-aligned Compareではありません/u)).toBeVisible();
  });
});
