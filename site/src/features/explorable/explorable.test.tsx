import { readFileSync } from "node:fs";
import { join } from "node:path";

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { CompiledContent } from "../content/CompiledContent";
import ConvexityChord from "./ConvexityChord";
import GradientDescentValley from "./GradientDescentValley";
import LpVertexWalk from "./LpVertexWalk";
import { EXPLORABLE_META } from "./meta";
import { EXPLORABLE_COMPONENTS } from "./registry";

interface RegistryFile {
  explorables: Array<{
    id: string;
    question: string;
    fixed_conditions: string;
    not_implied: string;
  }>;
}

const registry = JSON.parse(
  readFileSync(join(process.cwd(), "..", "src", "optimization_compass", "resources", "explorables.json"), "utf8"),
) as RegistryFile;

afterEach(cleanup);

function slider(name: RegExp) {
  return screen.getByRole("slider", { name });
}

describe("explorable registry", () => {
  it("keeps the site components and framing in step with the Python registry", () => {
    const ids = registry.explorables.map((entry) => entry.id).sort();
    expect(Object.keys(EXPLORABLE_COMPONENTS).sort()).toEqual(ids);
    expect(Object.keys(EXPLORABLE_META).sort()).toEqual(ids);
    for (const entry of registry.explorables) {
      expect(EXPLORABLE_META[entry.id]).toEqual({
        question: entry.question,
        fixedConditions: entry.fixed_conditions,
        notImplied: entry.not_implied,
      });
    }
  });
});

describe("ExplorableMounts inside compiled content", () => {
  const figure = (id: string) => `<figure class="explorable" role="group" data-explorable-id="${id}" aria-label="図">`
    + '<div class="explorable-mount" data-explorable-mount><p class="explorable-fallback">静的な代替</p></div>'
    + '<figcaption class="explorable-caption"><p>説明</p></figcaption></figure>';

  it("replaces the static fallback with the live figure and keeps the caption", async () => {
    render(<CompiledContent page={{ html: figure("convexity-chord"), toc: [] }} />);

    expect(await screen.findByText("見る問い")).toBeInTheDocument();
    expect(screen.queryByText("静的な代替")).not.toBeInTheDocument();
    expect(screen.getByText("説明")).toBeInTheDocument();
  });

  it("leaves the fallback for an id the site does not know", () => {
    render(<CompiledContent page={{ html: figure("not-registered"), toc: [] }} />);

    expect(screen.getByText("静的な代替")).toBeInTheDocument();
  });
});

describe("GradientDescentValley", () => {
  it("starts at the article's step, which is stable but slow along the gentle axis", () => {
    render(<GradientDescentValley />);

    expect(screen.getAllByText(/回では収束していません/).length).toBeGreaterThan(0);
    expect(screen.getByText("安定限界は", { exact: false })).toBeInTheDocument();
    expect(screen.getAllByText("0.92").length).toBeGreaterThan(0);
    expect(screen.getAllByText("−0.60").length).toBeGreaterThan(0);
  });

  it("reports divergence when the step crosses the stability limit", () => {
    render(<GradientDescentValley />);

    fireEvent.change(slider(/learning rate/), { target: { value: "0.06" } });

    expect(screen.getAllByText(/発散しました/).length).toBeGreaterThan(0);
    expect(screen.getByText("誤差が増える（発散）")).toBeInTheDocument();
  });

  it("converges when a smaller step is chosen", () => {
    render(<GradientDescentValley />);

    fireEvent.change(slider(/learning rate/), { target: { value: "0.045" } });

    expect(screen.getAllByText(/収束しました/).length).toBeGreaterThan(0);
  });

  it("reports undamped error at the stability boundary instead of divergence", () => {
    render(<GradientDescentValley />);
    fireEvent.change(slider(/learning rate/), { target: { value: "0.05" } });

    expect(screen.getByText("誤差が縮まない（非減衰）")).toBeInTheDocument();
    expect(screen.queryByText("誤差が増える（発散）")).not.toBeInTheDocument();
  });

  it("labels momentum rates as asymptotic envelopes rather than per-step multipliers", () => {
    render(<GradientDescentValley />);
    fireEvent.click(screen.getByRole("radio", { name: "Momentum" }));

    expect(screen.getByText("方向ごとの漸近的な収束率（包絡線の目安）")).toBeInTheDocument();
    expect(screen.getAllByText(/漸近的な包絡線を1\/1000にする目安/)).toHaveLength(2);
    expect(screen.queryByText("方向ごとに、1回で誤差が何倍になるか")).not.toBeInTheDocument();
  });

  it("exposes momentum controls only for the momentum rule", () => {
    render(<GradientDescentValley />);
    expect(screen.queryByRole("slider", { name: /持ち越し/ })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: "Momentum" }));

    expect(slider(/持ち越し/)).toBeInTheDocument();
  });

  it("moves the start point with the keyboard", () => {
    render(<GradientDescentValley />);
    const handle = screen.getByRole("group", { name: /初期点/ });

    fireEvent.keyDown(handle, { key: "ArrowLeft" });

    expect(screen.getByRole("group", { name: /初期点 \(3\.75, 3\.00\)/ })).toBeInTheDocument();
  });

  it("does not autoplay under reduced motion and lets the reader step", () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query.includes("reduce"),
      media: query,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    })) as unknown as typeof window.matchMedia;
    try {
      render(<GradientDescentValley />);

      expect(screen.getByRole("button", { name: /再生/ })).toBeDisabled();
      expect(screen.getByText(/自動再生は止めています/)).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: "最初から" }));
      fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));
      expect(screen.getByText("k = 1 / 100")).toBeInTheDocument();
    } finally {
      window.matchMedia = original;
    }
  });
});

describe("LpVertexWalk", () => {
  it("shows the article LP's optimum and that vertices are enough", () => {
    render(<LpVertexWalk />);

    expect(screen.getAllByText(/最適解は頂点 \(1\.0, 3\.0\)/).length).toBeGreaterThan(0);
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(5);
    expect(within(table).getByText("最良")).toBeInTheDocument();
  });

  it("reports a whole optimal edge when the cost is perpendicular to it", () => {
    render(<LpVertexWalk />);

    fireEvent.change(slider(/係数 c₁/), { target: { value: "1" } });
    fireEvent.change(slider(/係数 c₂/), { target: { value: "1" } });

    expect(screen.getAllByText(/辺全体が最適です/).length).toBeGreaterThan(0);
  });

  it("keeps the probe inside the feasible region when moved by keyboard", () => {
    render(<LpVertexWalk />);
    const probe = screen.getByRole("group", { name: /動かせる点/ });

    for (let press = 0; press < 30; press += 1) fireEvent.keyDown(probe, { key: "ArrowRight", shiftKey: true });

    const label = screen.getByRole("group", { name: /動かせる点/ }).getAttribute("aria-label") ?? "";
    const [, x, y] = /\(([\d.−-]+), ([\d.−-]+)\)/u.exec(label) ?? [];
    expect(Number(x.replace("−", "-")) + Number(y.replace("−", "-"))).toBeLessThanOrEqual(4.001);
  });
});

describe("ConvexityChord", () => {
  it("accepts every pair of points for a convex function", () => {
    render(<ConvexityChord />);

    expect(screen.getAllByText(/この関数は凸なので/).length).toBeGreaterThan(0);
  });

  it("finds a violation for the double well", () => {
    render(<ConvexityChord />);

    fireEvent.click(screen.getByRole("radio", { name: /二つの谷/ }));

    expect(screen.getAllByText(/この関数は凸ではありません/).length).toBeGreaterThan(0);
  });

  it("shows that a local stop is not the global minimum", () => {
    render(<ConvexityChord />);
    fireEvent.click(screen.getByRole("radio", { name: /二つの谷/ }));
    const a = screen.getByRole("slider", { name: "点aの位置" });
    for (let press = 0; press < 4; press += 1) fireEvent.keyDown(a, { key: "ArrowRight", shiftKey: true });

    fireEvent.click(screen.getByRole("button", { name: /下ってみる/ }));

    expect(screen.getAllByText(/全体の最小とは限りません/).length).toBeGreaterThan(0);
  });
});
