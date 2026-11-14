import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { EXPLORABLE_META } from "../../figureMeta";
import { BO_INITIAL, gridMinimum, runBayesOpt, type Acquisition } from "../../math/bayesOpt";
import { numberSetting, stringSetting } from "../../scene";
import { AlgorithmReplay as BayesOptAcquisition } from "./Figure";

afterEach(cleanup);

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
