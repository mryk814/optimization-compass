import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import manifest from "../../../public/data/manifest.json";
import scenarios from "../../../public/data/visualization-scenarios.json";
import exploreNoiseless from "../../../public/data/visualizations/bo-explore-noiseless.json";
import exploreSmallNoise from "../../../public/data/visualizations/bo-explore-small_noise.json";
import { BayesianOptimizationPage } from "./BayesianOptimizationPage";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function renderPage() {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    const body = url.endsWith("data/manifest.json") ? manifest
      : url.endsWith("visualization-scenarios.json") ? scenarios
        : url.endsWith("bo-explore-noiseless.json") ? exploreNoiseless
          : url.endsWith("bo-explore-small_noise.json") ? exploreSmallNoise
            : undefined;
    return body ? { ok: true, json: async () => structuredClone(body) } : { ok: false, status: 404 };
  }));
  return render(<MemoryRouter><BayesianOptimizationPage /></MemoryRouter>);
}

describe("BayesianOptimizationPage", () => {
  test("renders the generated trace, rationale, equal-budget table, and keyboard playback", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { level: 1, name: "Bayesian Optimization Theater" })).toBeVisible();
    expect(await screen.findByText(/Expected Improvementで次点選択/u)).toBeVisible();
    expect(await screen.findByText(/方向 \/ Direction: minimize/u)).toBeVisible();
    expect(screen.getByText("このpayloadには既知referenceなし")).toBeVisible();
    expect(screen.getByRole("img", { name: /surrogate平均/u })).toBeVisible();
    expect(screen.getByRole("table", { name: /best-so-far/u })).toBeVisible();
    const player = screen.getByLabelText(/左右矢印で移動/u);
    fireEvent.keyDown(player, { key: "ArrowRight" });
    expect(screen.getByText("Frame 2/8")).toBeVisible();
    fireEvent.keyDown(player, { key: " " });
    expect(screen.getByRole("button", { name: "一時停止" })).toBeVisible();
  });

  test("switches to the small-noise generated preset", async () => {
    renderPage();
    await screen.findByText(/noise σ=0/u);
    fireEvent.change(screen.getByRole("combobox", { name: "観測noise" }), { target: { value: "small_noise" } });
    await waitFor(() => expect(screen.getByText(/noise σ=0.08/u)).toBeVisible());
  });
});
