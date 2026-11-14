import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { EXPLORABLE_META } from "../../figureMeta";
import { numberSetting, stringSetting } from "../../scene";
import AdamStepRatio from "./Figure";
import { ADAM_DEFAULTS, runAdam, runPlainDescent } from "./math";

afterEach(cleanup);

const VALLEY = { cx: 1, cy: -2, kappa: 20 } as const;

describe("AdamStepRatio guided scene", () => {
  const beats = EXPLORABLE_META["adam-step-ratio"].beats;
  const runOf = (index: number) => {
    const s = beats[index].settings;
    return runAdam(VALLEY, [4, 3], {
      ...ADAM_DEFAULTS,
      eta: numberSetting(s, "eta", 0.1),
      beta1: numberSetting(s, "beta1", 0.9),
      noise: numberSetting(s, "noise", 0),
      seed: 7,
      maxSteps: 120,
    });
  };
  const meanAbs = (values: number[]) => values.reduce((total, v) => total + Math.abs(v), 0) / values.length;

  it("says only what each beat's computation shows", () => {
    const diagonal = runOf(0);
    expect(diagonal.steps[0].cx.g).toBe(6);
    expect(diagonal.steps[0].cy.g).toBe(200);
    for (let t = 0; t < 3; t += 1) {
      expect(Math.abs(diagonal.steps[t].cx.move)).toBeCloseTo(0.1, 2);
      expect(Math.abs(diagonal.steps[t].cy.move)).toBeCloseTo(0.1, 2);
    }

    expect(stringSetting(beats[1].settings, "compare", ["none", "gd"] as const, "none")).toBe("gd");
    const plain = runPlainDescent(VALLEY, [4, 3], 0.1, 120);
    expect(plain.path[1][1]).toBeCloseTo(-17, 10);
    expect(plain.diverged).toBe(true);

    const overshoot = runOf(2);
    expect(Math.min(...overshoot.steps.map((s) => s.y))).toBeLessThan(-2.35);
    expect(Math.abs(overshoot.steps[79].cy.ratio)).toBeLessThan(0.05);

    const noisy = runOf(3);
    const window = noisy.steps.slice(10, 60);
    expect(meanAbs(window.map((s) => s.cx.ratio))).toBeLessThan(0.5 * meanAbs(window.map((s) => s.cy.ratio)));
    expect(noisy.steps[59].x).toBeGreaterThan(2);
    expect(diagonal.steps[59].x).toBeLessThan(1);
  });
});

describe("AdamStepRatio", () => {
  it("shows both coordinates moving by about η at the start", () => {
    render(<AdamStepRatio />);
    fireEvent.click(screen.getByRole("button", { name: "最初から" }));
    expect(screen.getAllByText(/斜め45°に進みます/).length).toBeGreaterThan(0);
  });

  it("draws the plain gradient descent overlay as diverging for the same η", () => {
    render(<AdamStepRatio />);
    fireEvent.click(screen.getByRole("radio", { name: "同じηの勾配降下法" }));
    expect(screen.getByText(/同じ η の勾配降下法（発散）/)).toBeInTheDocument();
  });
});
