import { render, screen, within } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { OptimizationProblemPrimer } from "./OptimizationProblemPrimer";

describe("OptimizationProblemPrimer", () => {
  test("connects the canonical formula to plain-language terms", () => {
    render(<OptimizationProblemPrimer />);

    expect(screen.getByRole("heading", { name: "まず、現実の問題をこの形に置きます" })).toBeVisible();
    expect(screen.getByLabelText("xがXに属する範囲でf(x)を最小化する")).toBeVisible();
    expect(screen.getByText("決めるもの")).toBeVisible();
    expect(screen.getByText("比べるもの")).toBeVisible();
    expect(screen.getByText("守る条件")).toBeVisible();
    expect(screen.getByText("選べる範囲")).toBeVisible();
  });

  test("defines continuous, discrete, categorical, and mixed variables", () => {
    const { container } = render(<OptimizationProblemPrimer />);
    const primer = within(container);

    expect(primer.getByText(/飛び飛びの候補から選ぶ総称/u)).toBeVisible();
    expect(primer.getByText("連続 (continuous)")).toBeVisible();
    expect(primer.getByText("整数・0-1")).toBeVisible();
    expect(primer.getByText("カテゴリ (categorical)")).toBeVisible();
    expect(primer.getByText("混合 (mixed)")).toBeVisible();
  });
});
