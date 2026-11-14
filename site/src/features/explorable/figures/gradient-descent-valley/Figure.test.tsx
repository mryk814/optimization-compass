import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { EXPLORABLE_META } from "../../figureMeta";
import { axisRate, runDescent, valleyCurvatures } from "../../math/descent";
import { numberSetting, stringSetting } from "../../scene";
import GradientDescentValley from "./Figure";

afterEach(cleanup);

function slider(name: RegExp) {
  return screen.getByRole("slider", { name });
}

describe("GradientDescentValley guided scene", () => {
  const beats = EXPLORABLE_META["gradient-descent-valley"].beats;
  const runOf = (index: number) => {
    const settings = beats[index].settings;
    const kappa = numberSetting(settings, "kappa", 20);
    const options = {
      eta: numberSetting(settings, "eta", 0.04),
      method: stringSetting(settings, "method", ["gd", "momentum"] as const, "gd"),
      beta: numberSetting(settings, "beta", 0.5),
      maxSteps: 100,
    };
    const problem = { cx: 1, cy: -2, kappa };
    const { gentle, steep } = valleyCurvatures(problem);
    return {
      run: runDescent(problem, [numberSetting(settings, "x0", 4), numberSetting(settings, "y0", 3)], options),
      gentle: axisRate(options.method, gentle, options.eta, options.beta),
      steep: axisRate(options.method, steep, options.eta, options.beta),
    };
  };

  // The captions make claims about the computation; these keep the claims true.
  it("says only what each beat's computation shows", () => {
    const slow = runOf(0);
    expect(slow.run.outcome).toBe("unfinished");
    expect(slow.gentle.factor).toBeCloseTo(0.96, 10);
    expect(slow.steep.rate).toBeLessThan(0.5);

    const swing = runOf(1);
    expect(swing.steep.oscillates).toBe(true);
    expect(swing.gentle.rate).toBeLessThan(slow.gentle.rate);

    const diverge = runOf(2);
    expect(diverge.run.outcome).toBe("diverged");
    expect(numberSetting(beats[2].settings, "eta", 0)).toBeGreaterThan(1 / 20);

    const round = runOf(3);
    expect(round.run.outcome).toBe("converged");
    expect(round.run.points.length).toBeLessThan(20);

    const momentum = runOf(4);
    expect(momentum.gentle.rate).toBeLessThan(slow.gentle.rate);
    expect(momentum.run.points.at(-1)!.f).toBeLessThan(slow.run.points.at(-1)!.f);
  });

  it("replaces the controls with captions and hands the last beat back on exit", () => {
    render(<GradientDescentValley />);

    fireEvent.click(screen.getByRole("button", { name: /解説付きで見る/ }));
    expect(screen.queryByRole("slider", { name: /学習率/ })).not.toBeInTheDocument();
    expect(screen.getByText(beats[0].captionJa)).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: /初期点/ })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "次へ ▶" }));
    expect(screen.getByText(beats[1].captionJa)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "解説を終えて、自分で動かす" }));
    expect(slider(/学習率/)).toHaveValue("0.045");
    expect(screen.getByRole("button", { name: /解説付きで見る/ })).toBeInTheDocument();
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

    fireEvent.change(slider(/学習率/), { target: { value: "0.06" } });

    expect(screen.getAllByText(/発散しました/).length).toBeGreaterThan(0);
    expect(screen.getByText("誤差が増える（発散）")).toBeInTheDocument();
  });

  it("converges when a smaller step is chosen", () => {
    render(<GradientDescentValley />);

    fireEvent.change(slider(/学習率/), { target: { value: "0.045" } });

    expect(screen.getAllByText(/収束しました/).length).toBeGreaterThan(0);
  });

  it("reports undamped error at the stability boundary instead of divergence", () => {
    render(<GradientDescentValley />);
    fireEvent.change(slider(/学習率/), { target: { value: "0.05" } });

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
