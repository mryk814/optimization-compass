import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";

import manifest from "../../../public/data/manifest.json";
import scenarios from "../../../public/data/visualization-scenarios.json";
import exploreNoiseless from "../../../public/data/visualizations/bo-explore-noiseless.json";
import exploreSmallNoise from "../../../public/data/visualizations/bo-explore-small_noise.json";
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
    expect(await screen.findByRole("heading", { level: 1, name: "Bayesian Optimization Theater" })).toBeVisible();
    expect(await screen.findByText(/Expected Improvementによる次候補の選択/u)).toBeVisible();
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
});
