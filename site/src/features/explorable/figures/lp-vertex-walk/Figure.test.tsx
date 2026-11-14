import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LessonContext } from "../../lessonContext";
import type { BeatSettings, SceneBeat } from "../../scene";
import LpVertexWalk from "./Figure";

afterEach(cleanup);

function slider(name: RegExp) {
  return screen.getByRole("slider", { name });
}

describe("LpVertexWalk", () => {
  it("shows the best plan (4 breads, 3 croissants) with revenue 24 and the table of corners", () => {
    render(<LpVertexWalk />);

    expect(
      screen.getAllByText(/売上がいちばん大きい計画は 食パン 4個・クロワッサン 3個 で、売上は 24 です/).length,
    ).toBeGreaterThan(0);
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(5);
    expect(within(table).getByText("最良")).toBeInTheDocument();
  });

  it("matches the lesson's price cut: croissants at 1 and at 2", () => {
    render(<LpVertexWalk />);

    fireEvent.change(slider(/クロワッサン1個の売上/), { target: { value: "1" } });
    expect(
      screen.getAllByText(/売上がいちばん大きい計画は 食パン 6個・クロワッサン 0個 で、売上は 18 です/).length,
    ).toBeGreaterThan(0);

    fireEvent.change(slider(/クロワッサン1個の売上/), { target: { value: "2" } });
    expect(screen.getAllByText(/を結ぶ辺のどこでも、売上は 18 で最大です/).length).toBeGreaterThan(0);
  });

  it("reports a whole optimal edge when the equal-revenue line is parallel to it", () => {
    render(<LpVertexWalk />);

    fireEvent.change(slider(/食パン1個の売上/), { target: { value: "1" } });
    fireEvent.change(slider(/クロワッサン1個の売上/), { target: { value: "3" } });

    expect(screen.getAllByText(/を結ぶ辺のどこでも、売上は 13 で最大です/).length).toBeGreaterThan(0);
  });

  // The plan may leave the stock on purpose: that is how the reader asks "can I bake this?".
  it("reports the shortage when the plan is moved outside the stock by keyboard", () => {
    render(<LpVertexWalk />);
    const plan = () => screen.getByRole("group", { name: /いまの計画/ });
    expect(plan().getAttribute("aria-label")).toMatch(/食パン 2個・クロワッサン 1\.5個。在庫の中に収まっています/);

    for (let press = 0; press < 30; press += 1) fireEvent.keyDown(plan(), { key: "ArrowRight", shiftKey: true });

    // 8 breads and 1.5 croissants need 27 of flour and 12.5 of butter.
    expect(plan().getAttribute("aria-label")).toMatch(/食パン 8個・クロワッサン 1\.5個。不足：小麦粉 9。/);
    expect(screen.getByRole("img", { name: /小麦粉は 18 のうち 27 を使います。超過/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /バターは 13 のうち 12\.5 を使います。$/ })).toBeInTheDocument();
  });

  it("sends the plan to the best corner, where both stocks are used up", () => {
    render(<LpVertexWalk />);

    fireEvent.click(screen.getByRole("button", { name: "いちばん良い角へ" }));

    expect(screen.getByRole("group", { name: /いまの計画/ }).getAttribute("aria-label"))
      .toMatch(/食パン 4個・クロワッサン 3個。小麦粉もバターも使い切りです/);
    expect(screen.getByRole("math", { name: "売上は 3 × 4 + 4 × 3 = 24" })).toBeInTheDocument();
  });
});

describe("LpVertexWalk in a lesson", () => {
  const step = (settings: BeatSettings): SceneBeat => ({ settings, durationS: 6, captionJa: "", narrationJa: "" });
  const base = { x1: 2, x2: 1.5, c1: 3, c2: 4, follow: "off" };
  const beats = [
    step({ ...base, layers: "plan", x1: { from: 1, to: 5 }, x2: 1 }),
    step({ ...base, layers: "revenue" }),
    step({ ...base, layers: "answer", x1: 4, x2: 3, c2: { from: 2, to: 1 }, follow: "best" }),
  ];
  const show = (index: number, local: number, free = false) => render(
    <LessonContext.Provider value={{ beats, index, local, free }}>
      <LpVertexWalk />
    </LessonContext.Provider>,
  );
  const planLabel = () => screen.getByRole("group", { name: /いまの計画/ }).getAttribute("aria-label");

  it("draws only the plan in the first layer, with no controls and nothing that gives the answer away", () => {
    const { container } = show(0, 6);

    expect(planLabel()).toBe("いまの計画。食パン 5個・クロワッサン 1個。");
    expect(screen.queryByRole("slider")).toBeNull();
    expect(screen.queryByRole("table")).toBeNull();
    expect(container.querySelector(".ex-feasible, .lpw-usage, .lpw-line, .lpw-plan-revenue")).toBeNull();
  });

  it("keeps the corners' revenues and the table out of the layer the prediction is made on", () => {
    const { container } = show(1, 6);

    expect(screen.getByRole("math", { name: "売上は 3 × 2 + 4 × 1.5 = 12" })).toBeInTheDocument();
    expect(screen.getByText("売上が増える向き")).toBeInTheDocument();
    expect(container.querySelector(".lpw-best-ring")).toBeNull();
    expect(container.querySelector(".lpw-corner-value")).toBeNull();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("follows the best corner: on the tie it stays, below it the plan is bread only", () => {
    const { container, unmount } = show(2, 0);
    expect(planLabel()).toMatch(/食パン 4個・クロワッサン 3個/);
    expect(container.querySelectorAll(".lpw-best-ring")).toHaveLength(2);
    unmount();

    show(2, 6);
    expect(planLabel()).toMatch(/食パン 6個・クロワッサン 0個/);
    expect(screen.getByRole("math", { name: "売上は 3 × 6 + 1 × 0 = 18" })).toBeInTheDocument();
    // The corner left behind now says what it would sell for.
    expect(screen.getByText("売上 15")).toBeInTheDocument();
  });

  it("hands the last step's plan and prices to the reader's controls", () => {
    const { rerender } = show(2, 6);

    rerender(
      <LessonContext.Provider value={{ beats, index: 2, local: 6, free: true }}>
        <LpVertexWalk />
      </LessonContext.Provider>,
    );

    expect(slider(/クロワッサン1個の売上/)).toHaveValue("1");
    expect(planLabel()).toMatch(/食パン 6個・クロワッサン 0個.*ドラッグか矢印キーで動かせます/);
    expect(within(screen.getByRole("table")).getByText("最良")).toBeInTheDocument();
  });
});
