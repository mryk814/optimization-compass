import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import AdamStepRatio from "./AdamStepRatio";
import { AlgorithmReplay as BayesOptAcquisition } from "./BayesOptAcquisition";
import LeastSquaresBowl from "./LeastSquaresBowl";
import { ADAM_DEFAULTS, runAdam, runPlainDescent, seededNormal } from "./math/adam";
import { BO_INITIAL, gridMinimum, posterior, runBayesOpt, type Acquisition } from "./math/bayesOpt";
import { evaluateLine, fitLine } from "./math/leastSquares";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting } from "./scene";

afterEach(cleanup);

const ARTICLE_POINTS = [{ t: 0, y: 1 }, { t: 1, y: 2 }, { t: 2, y: 2 }, { t: 3, y: 4 }];
const VALLEY = { cx: 1, cy: -2, kappa: 20 } as const;

describe("least-squares math", () => {
  it("solves the article's four points exactly and makes the residuals orthogonal to [1, t]", () => {
    const line = fitLine(ARTICLE_POINTS)!;
    expect(line.a).toBeCloseTo(0.9, 12);
    expect(line.b).toBeCloseTo(0.9, 12);
    const fit = evaluateLine(ARTICLE_POINTS, line);
    expect(fit.sse).toBeCloseTo(0.7, 12);
    expect(fit.residuals.map((r) => Number(r.toFixed(10)))).toEqual([0.1, 0.2, -0.7, 0.4]);
    expect(fit.residualSum).toBeCloseTo(0, 12);
    expect(fit.residualMoment).toBeCloseTo(0, 12);
  });

  it("has no unique line when every t is the same", () => {
    expect(fitLine([{ t: 1, y: 0 }, { t: 1, y: 2 }])).toBeUndefined();
  });
});

describe("LeastSquaresBowl guided scene", () => {
  const beats = EXPLORABLE_META["least-squares-bowl"].beats;
  const pointsOf = (index: number) => ARTICLE_POINTS.map((p, i) => ({ ...p, y: numberSetting(beats[index].settings, `y${i}`, p.y) }));

  it("says only what each beat's computation shows", () => {
    const manual = evaluateLine(ARTICLE_POINTS, {
      a: numberSetting(beats[0].settings, "a", 0),
      b: numberSetting(beats[0].settings, "b", 0),
    });
    expect(manual.sse).toBeCloseTo(1.66, 10);

    const best = fitLine(pointsOf(1))!;
    expect([best.a, best.b].map((v) => Number(v.toFixed(10)))).toEqual([0.9, 0.9]);

    const pulled = fitLine(pointsOf(2))!;
    expect(numberSetting(beats[2].settings, "y3", 0)).toBe(8);
    expect([pulled.a, pulled.b].map((v) => Number(v.toFixed(10)))).toEqual([0.1, 2.1]);
  });
});

describe("LeastSquaresBowl", () => {
  it("starts with a hand-drawn line that is not the bottom of the bowl", () => {
    render(<LeastSquaresBowl />);
    expect(screen.getAllByText(/まだ底ではありません/).length).toBeGreaterThan(0);
  });

  it("snaps to the least-squares line and reports zero residual sums", () => {
    render(<LeastSquaresBowl />);
    fireEvent.click(screen.getByRole("radio", { name: "二乗和が最小の直線" }));
    expect(screen.getAllByText(/お椀の底です/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.700").length).toBeGreaterThan(0);
    const totals = screen.getByRole("rowheader", { name: "合計" }).closest("tr");
    expect(totals?.querySelectorAll("td")).toHaveLength(2);
    expect(totals?.textContent).toBe("合計0.000.00");
  });

  it("moves a data point with the keyboard and refits", () => {
    render(<LeastSquaresBowl />);
    fireEvent.click(screen.getByRole("radio", { name: "二乗和が最小の直線" }));
    const fourth = screen.getByRole("slider", { name: /^点4（/ });
    for (let press = 0; press < 4; press += 1) fireEvent.keyDown(fourth, { key: "ArrowUp", shiftKey: true });
    expect(screen.getAllByText(/y = 0\.10 \+ 2\.10 t/).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "点と直線を最初に戻す" }));
    expect(screen.getByRole("slider", { name: /^点4（/ })).toHaveAttribute("aria-valuenow", "4");
    expect(screen.getByRole("radio", { name: "自分で動かす" })).toBeChecked();
  });
});

describe("Adam math", () => {
  it("repeats the same noise for the same seed", () => {
    const first = seededNormal(7);
    const second = seededNormal(7);
    expect([first(), first(), first()]).toEqual([second(), second(), second()]);
  });

  it("moves every coordinate by η on the first step, whatever the gradient size", () => {
    const run = runAdam(VALLEY, [4, 3], { ...ADAM_DEFAULTS, eta: 0.08, noise: 0, seed: 1, maxSteps: 3 });
    expect(run.path[1][0]).toBeCloseTo(3.92, 6);
    expect(run.path[1][1]).toBeCloseTo(2.92, 6);
  });
});

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

describe("Bayesian optimisation math", () => {
  it("interpolates the observations and is uncertain far from them", () => {
    const xs = [0.1, 0.45, 0.6];
    const ys = [1, 0.5, 1.1];
    const post = posterior(xs, ys, 0.1, [0.1, 0.45, 0.95]);
    expect(post.mean[0]).toBeCloseTo(1, 3);
    expect(post.mean[1]).toBeCloseTo(0.5, 3);
    expect(post.sd[0]).toBeLessThan(0.01);
    expect(post.sd[2]).toBeGreaterThan(0.9 * Math.max(...post.sd));
  });

  it("places the answer key's minimum in the narrow basin", () => {
    const minimum = gridMinimum();
    expect(minimum.x).toBeCloseTo(0.84, 10);
    expect(minimum.value).toBeCloseTo(-0.1496, 3);
  });
});

describe("BayesOptAcquisition guided scene", () => {
  const beats = EXPLORABLE_META["bayes-opt-acquisition"].beats;
  const minimum = gridMinimum();
  const runOf = (index: number) => {
    const s = beats[index].settings;
    return runBayesOpt({
      acquisition: stringSetting(s, "acquisition", ["lcb", "ei"] as const, "lcb") as Acquisition,
      beta: numberSetting(s, "beta", 2),
      lengthScale: numberSetting(s, "lengthScale", 0.1),
    });
  };
  /** 1-based choice that first reaches the deep basin's grid minimum. */
  const firstHit = (states: ReturnType<typeof runBayesOpt>) => (
    states.findIndex((state) => Math.abs(state.nextX - minimum.x) < 1e-9) + 1
  );

  it("says only what each beat's computation shows", () => {
    const greedy = runOf(0);
    expect(firstHit(greedy)).toBe(0);
    expect(greedy.at(-1)!.best).toBeCloseTo(0.152, 3);
    expect(greedy.at(-1)!.xs.slice(BO_INITIAL.length).filter((x) => Math.abs(x - 0.355) < 1e-9).length).toBeGreaterThan(3);
    expect(greedy.every((state) => state.nextX < 0.6)).toBe(true);

    const balanced = runOf(1);
    expect(balanced.slice(0, 7).map((state) => state.nextX)).toEqual(expect.arrayContaining([1, 0.8]));
    expect(firstHit(balanced)).toBe(7);

    expect(firstHit(runOf(2))).toBe(9);

    const longScale = runOf(3);
    expect(firstHit(longScale)).toBe(0);
    expect(longScale.at(-1)!.bestX).toBeCloseTo(0.355, 10);

    expect(firstHit(runOf(4))).toBe(8);
  });
});

describe("BayesOptAcquisition", () => {
  it("lists the initial design and every chosen point", () => {
    render(<BayesOptAcquisition />);
    expect(screen.getByText("初期 1")).toBeInTheDocument();
    expect(screen.getByText("10 回目")).toBeInTheDocument();
  });

  it("flags a repeated proposal as a stopping signal", () => {
    render(<BayesOptAcquisition />);
    fireEvent.change(screen.getByRole("slider", { name: /探索の重み/ }), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "最後まで進める" }));
    expect(screen.getAllByText(/停止の合図/).length).toBeGreaterThan(0);
  });

  it("hides β when Expected Improvement is chosen", () => {
    render(<BayesOptAcquisition />);
    fireEvent.click(screen.getByRole("radio", { name: "Expected Improvement" }));
    expect(screen.queryByRole("slider", { name: /探索の重み/ })).not.toBeInTheDocument();
  });
});
