import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import SimplexShadowPrice from "./SimplexShadowPrice";

afterEach(cleanup);

const verdict = (container: HTMLElement) => container.querySelector(".ex-verdict")?.textContent ?? "";
const row = (container: HTMLElement) => [...container.querySelectorAll(".ex-table tbody td, .ex-table tbody th")].map((c) => c.textContent);
const summary = (container: HTMLElement) => container.querySelector("[aria-live='polite']")?.textContent ?? "";

describe("SimplexShadowPrice", () => {
  it("starts at the article's stock b = 18 with the optimum (4, 3) and value 24", () => {
    const { container } = render(<SimplexShadowPrice />);
    expect(screen.getByText("頂点と辺")).toBeTruthy();
    expect(screen.getByText("見積もりと実際")).toBeTruthy();
    expect(row(container)).toEqual(["18", "{x₁, x₂}", "(4, 3)", "24", "24"]);
    expect(container.querySelector(".ex-tone-good")).not.toBeNull();
  });

  it("b = 19 stays on the same basis: (31/7, 20/7), value 173/7, estimate exact", () => {
    const { container } = render(<SimplexShadowPrice />);
    fireEvent.click(screen.getByRole("button", { name: "b = 19" }));
    expect(row(container)).toEqual(["19", "{x₁, x₂}", "(31/7, 20/7)", "173/7", "173/7"]);
    expect(verdict(container)).toContain("実際の最適値 173/7 ≈ 24.71 と 5/7 の見積もり 173/7 ≈ 24.71 が一致");
    expect(summary(container)).toContain("173/7");
    expect(screen.getByRole("button", { name: "b = 19" }).getAttribute("aria-pressed")).toBe("true");
  });

  it("the slider moves in thirds, and the range ends 26/3 and 39 are exact points", () => {
    const { container } = render(<SimplexShadowPrice />);
    const slider = screen.getByRole("slider", { name: /小麦粉の在庫 b/ });
    fireEvent.change(slider, { target: { value: "26" } });
    expect(row(container)).toEqual(["26/3", "{x₁, x₂}", "(0, 13/3)", "52/3", "52/3"]);
    expect(verdict(container)).toContain("範囲の端");
    fireEvent.change(slider, { target: { value: "117" } });
    expect(row(container)).toEqual(["39", "{x₁, x₂}", "(13, 0)", "39", "39"]);
    expect(slider.getAttribute("aria-valuetext")).toBe("小麦粉の在庫 39");
  });

  it("b = 40 is outside the range: true value 39 at (13, 0), the estimate overshoots", () => {
    const { container } = render(<SimplexShadowPrice />);
    fireEvent.click(screen.getByRole("button", { name: "b = 40" }));
    expect(row(container)).toEqual(["40", "{x₁, s₁}", "(13, 0)", "39", "278/7"]);
    expect(verdict(container)).toContain("範囲 26/3 ≤ b ≤ 39 の上の外");
    expect(verdict(container)).toContain("5/7 の見積もり 278/7 ≈ 39.71");
    expect(container.querySelector(".ex-tone-swing")).not.toBeNull();
    expect(container.querySelector(".live-math")?.getAttribute("aria-label")).toBe("0 かける 40 たす 3 かける 13 は 39");
  });

  it("b below 26/3 changes the basis to {x₂, s₂}", () => {
    const { container } = render(<SimplexShadowPrice />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "18" } });
    expect(row(container)).toEqual(["6", "{x₂, s₂}", "(0, 3)", "12", "108/7"]);
    expect(verdict(container)).toContain("の下の外");
    expect(container.querySelector(".live-math")?.getAttribute("aria-label")).toBe("2 かける 6 たす 0 かける 13 は 12");
  });
});
