import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import SimplexPivot from "./SimplexPivot";

afterEach(cleanup);

const verdict = (container: HTMLElement) => container.querySelector(".ex-verdict")?.textContent ?? "";

describe("SimplexPivot", () => {
  it("follows the article: x2 in, butter out, then x1 in, flour out, optimum 24", () => {
    const { container } = render(<SimplexPivot />);
    expect(screen.getByRole("button", { name: /x₂（クロワッサン）を増やす/ }).textContent).toContain("+4");

    fireEvent.click(screen.getByRole("button", { name: /x₂（クロワッサン）を増やす/ }));
    expect(verdict(container)).toContain("θ を 13/3 まで増やせます");
    fireEvent.click(screen.getByRole("button", { name: "比の最小値 θ=13/3 まで進めて s₂ と入れ替える" }));

    // The buttons after the first pivot carry the reduced costs of the article table.
    expect(screen.getByRole("button", { name: /x₁（食パン）を増やす/ }).textContent).toContain("+5/3");
    expect(screen.getByRole("button", { name: /s₂（バターの余り）を増やす/ }).textContent).toContain("−4/3");

    fireEvent.click(screen.getByRole("button", { name: /x₁（食パン）を増やす/ }));
    fireEvent.click(screen.getByRole("button", { name: "比の最小値 θ=4 まで進めて s₁ と入れ替える" }));
    expect(verdict(container)).toBe("どの変数を増やしても売上は増えません。頂点 (4, 3) が最適で、売上は 24 です。");
    expect(container.querySelector(".ex-table tbody")?.textContent).toContain("x₁, x₂(4, 3)24");
    expect(screen.getByRole("button", { name: /s₁（小麦粉の余り）を増やす/ }).textContent).toContain("−5/7");
  });

  it("marks the butter leftover negative past the minimum ratio", () => {
    const { container } = render(<SimplexPivot />);
    fireEvent.click(screen.getByRole("button", { name: /x₂（クロワッサン）を増やす/ }));
    fireEvent.change(screen.getByRole("slider"), { target: { value: "5" } });
    expect(verdict(container)).toBe("バターの余りが負になりました。θ=5.00 は実行可能領域の外です。");
    const negative = container.querySelector(".spx-bars li.is-negative");
    expect(negative?.textContent).toContain("−2.00");
    expect(container.querySelector(".spx-probe.is-infeasible")).not.toBeNull();
  });

  it("goes back one pivot and resets to the origin", () => {
    render(<SimplexPivot />);
    fireEvent.click(screen.getByRole("button", { name: /x₁（食パン）を増やす/ }));
    fireEvent.click(screen.getByRole("button", { name: "比の最小値 θ=6 まで進めて s₁ と入れ替える" }));
    expect(screen.getByRole("button", { name: /x₂（クロワッサン）を増やす/ }).textContent).toContain("+2");
    fireEvent.click(screen.getByRole("button", { name: "一手戻す" }));
    expect(screen.getByRole("button", { name: /x₁（食パン）を増やす/ }).textContent).toContain("+3");
    expect(screen.getByRole("button", { name: "原点に戻す" })).toHaveProperty("disabled", true);
  });
});
