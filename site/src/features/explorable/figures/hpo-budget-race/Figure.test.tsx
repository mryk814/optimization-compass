import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LessonContext, type LessonDrive } from "../../lessonContext";
import type { BeatSettings } from "../../scene";
import HpoBudgetRace from "./Figure";

afterEach(cleanup);
const summary = () => document.querySelector(".ex-sr-only")?.textContent ?? "";
const readout = () => document.querySelector(".hbr-readout")?.textContent ?? "";
const svgText = () => [...document.querySelectorAll("svg text")].map((node) => node.textContent).join("|");

/** The figure as one lesson step drives it, `local` seconds into the step. */
function renderStep(settings: BeatSettings, local = 6) {
  const drive: LessonDrive = {
    beats: [{ settings, durationS: 6, captionJa: "", narrationJa: "" }], index: 0, local, free: false,
  };
  return render(<LessonContext.Provider value={drive}><HpoBudgetRace /></LessonContext.Provider>);
}

const RACE = {
  mode: "race", d: 3, loglam: -3.5, evals: 16, grid: "edge", split: 0, score: "cv", seed: 0, spread: "off",
} as const;

describe("hpo budget race figure", () => {
  it("opens on the finished race with the numbers the article says", () => {
    render(<HpoBudgetRace />);
    expect(summary()).toContain("格子が0.192（次数6、log₁₀λ −3.67）");
    expect(summary()).toContain("ランダムが0.144（次数3、log₁₀λ −1.67）");
    expect(summary()).toContain("新しい5000点で測ると、0.175と0.173");
    expect(svgText()).toContain("λ 4種類");
    expect(svgText()).toContain("λ 16種類");
    expect(screen.getByRole("slider", { name: "評価の回数" })).toHaveValue("16");
  });

  it("re-measures the two chosen settings on the fresh points", () => {
    render(<HpoBudgetRace />);
    fireEvent.click(screen.getByRole("radio", { name: "新しい5000点" }));
    expect(readout()).toContain("選んだとき 0.048");
    expect(readout()).toContain("新しい5000点 0.002");
    expect(svgText()).toContain("新しい5000点 0.175");
    expect(svgText()).toContain("新しい5000点 0.173");
  });

  it("moves the grid, the split and the random seed", () => {
    render(<HpoBudgetRace />);
    fireEvent.click(screen.getByRole("radio", { name: "各区間の中心" }));
    expect(summary()).toContain("格子が0.137（次数3、log₁₀λ −3.38）");
    fireEvent.change(screen.getByRole("slider", { name: /30点の分け方/ }), { target: { value: "3" } });
    expect(summary()).toContain("12通りのうち4番目");
    expect(summary()).toContain("ランダムが0.135（次数7、log₁₀λ −2.96）");
    fireEvent.change(screen.getByRole("slider", { name: /ランダムの乱数の種/ }), { target: { value: "5" } });
    expect(summary()).toContain("乱数の種5");
  });

  it("shows one setting, its curve and its score", () => {
    render(<HpoBudgetRace />);
    fireEvent.click(screen.getByRole("radio", { name: "設定を1つ" }));
    fireEvent.change(screen.getByRole("slider", { name: /^次数/ }), { target: { value: "15" } });
    fireEvent.change(screen.getByRole("slider", { name: /罰則の強さ/ }), { target: { value: "-6" } });
    expect(readout()).toBe("次数 15、log₁₀λ −6.0 → 点数 4.486");
    fireEvent.change(screen.getByRole("slider", { name: /罰則の強さ/ }), { target: { value: "-1.5" } });
    expect(readout()).toContain("点数 0.230");
    expect(document.querySelectorAll(".hbr-truth")).toHaveLength(0);
    fireEvent.click(screen.getByRole("checkbox", { name: "真の曲線を重ねる" }));
    expect(document.querySelectorAll(".hbr-truth").length).toBeGreaterThan(0);
  });

  it("draws what a lesson step sets, without its own controls", () => {
    renderStep({ ...RACE, evals: 5 });
    expect(screen.queryByRole("slider")).toBeNull();
    expect(readout()).toContain("格子の最良 0.192");
    expect(readout()).toContain("ランダムの最良 0.172");
    expect(svgText()).toContain("λ 5種類");
    cleanup();
    renderStep({ ...RACE, evals: 0 });
    expect(readout()).toBe("まだ評価していません。");
  });

  it("slides the grid before the moved grid's scores count, and grows the fresh bars", () => {
    renderStep({ ...RACE, grid: "center", spread: "on" }, 0.5);
    expect(readout()).toContain("格子の最良 0.192");
    expect(svgText()).toContain("乱数200通り");
    cleanup();
    renderStep({ ...RACE, grid: "center", spread: "on" });
    expect(readout()).toContain("格子の最良 0.137");
    cleanup();
    renderStep({ ...RACE, score: "fresh" }, 0);
    expect(svgText()).toContain("新しい5000点 0.192");
    cleanup();
    renderStep({ ...RACE, score: "fresh" });
    expect(svgText()).toContain("新しい5000点 0.175");
  });
});
