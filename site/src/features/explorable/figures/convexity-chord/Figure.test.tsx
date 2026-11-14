import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import ConvexityChord from "./Figure";

afterEach(cleanup);

describe("ConvexityChord", () => {
  it("accepts every pair of points for a convex function", () => {
    render(<ConvexityChord />);

    expect(screen.getAllByText(/この関数は凸なので/).length).toBeGreaterThan(0);
  });

  it("finds a violation for the double well", () => {
    render(<ConvexityChord />);

    fireEvent.click(screen.getByRole("radio", { name: /二つの谷/ }));

    expect(screen.getAllByText(/この関数は凸ではありません/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/θ が 0\.\d+ から [\d.]+ のあたり/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/e-3/)).toBeNull();
  });

  it("plays theta from 0 to 1 and flags the moment the chord dips below the graph", () => {
    render(<ConvexityChord />);
    fireEvent.click(screen.getByRole("radio", { name: /二つの谷/ }));
    fireEvent.click(screen.getByRole("button", { name: /θを0から1へ動かして再生/ }));
    const scrub = screen.getByLabelText("θの動き");

    fireEvent.change(scrub, { target: { value: "0" } });
    expect(screen.queryByText(/0を下回った/)).toBeNull();

    fireEvent.change(scrub, { target: { value: "5" } });
    expect(screen.getByText(/0を下回った/)).toBeTruthy();
    expect(screen.getAllByText(/θ = 0\.50/).length).toBeGreaterThan(0);
  });

  it("builds the hump 0.35 theta (1 - theta) (a - b)^2 for the convex quadratic", () => {
    render(<ConvexityChord />);
    fireEvent.click(screen.getByRole("button", { name: /θを0から1へ動かして再生/ }));
    fireEvent.change(screen.getByLabelText("θの動き"), { target: { value: "5" } });

    expect(screen.getByText(/0\.35 × 0\.25 × 16\.00 = 1\.40/)).toBeTruthy();
    expect(screen.queryByText(/0を下回った/)).toBeNull();
  });

  it("starts at a = -2 and b = 2 and moves by 0.1 on the keyboard", () => {
    render(<ConvexityChord />);
    const a = screen.getByRole("slider", { name: "点aの位置" });
    expect(a.getAttribute("aria-valuenow")).toBe("-2");
    expect(screen.getByRole("slider", { name: "点bの位置" }).getAttribute("aria-valuenow")).toBe("2");
    fireEvent.keyDown(a, { key: "ArrowRight" });
    expect(a.getAttribute("aria-valuenow")).toBe("-1.9");
  });

  it("greys out the mixed point when it falls outside the feasible set", () => {
    render(<ConvexityChord />);
    fireEvent.click(screen.getByRole("radio", { name: /C=\[−2,−1\]∪\[2,3\]/ }));
    expect(screen.getAllByText(/混ぜた入力 x=0\.50 は可行集合 C の外です/).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /下ってみる/ }));
    expect(screen.getAllByText(/可行集合の中で x=−1\.00/).length).toBeGreaterThan(0);
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
