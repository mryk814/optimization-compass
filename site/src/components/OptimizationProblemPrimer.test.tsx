import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { OptimizationProblemPrimer } from "./OptimizationProblemPrimer";

describe("OptimizationProblemPrimer", () => {
  test("connects the canonical formula to plain-language terms", () => {
    render(<OptimizationProblemPrimer />);

    expect(screen.getByRole("heading", { name: "現実の問題を、この形にそろえる" })).toBeVisible();
    expect(screen.getByLabelText(/xがXに属する範囲でf\(x\)を最小化/u)).toBeVisible();
    expect(screen.getByText("決めるもの")).toBeVisible();
    expect(screen.getByText(/良くしたいもの/u)).toBeVisible();
    expect(screen.getByText("守る条件")).toBeVisible();
    expect(screen.getByText(/選べる範囲/u)).toBeVisible();
  });

  test("defines continuous, discrete, categorical, and mixed variables", () => {
    const { container } = render(<OptimizationProblemPrimer />);
    const primer = within(container);

    fireEvent.click(primer.getByText("用語の意味を確認する"));
    expect(primer.getByText(/二つの候補の間の値も選べる/u)).toBeVisible();
    expect(primer.getByText(/Continuous variable/u)).toBeVisible();
    expect(primer.getByText(/Integer variable/u)).toBeVisible();
    expect(primer.getByText(/Categorical variable/u)).toBeVisible();
    expect(primer.getByText(/Permutation variable/u)).toBeVisible();
  });

  test("substitutes a case's variables, objective, domain, and constraints", () => {
    render(<OptimizationProblemPrimer caseFormulation={{ decisionVariables: "配合率", variableDomain: "連続", objective: "誤差を最小化", constraints: "合計100%" }} />);
    expect(screen.getByRole("heading", { name: "このケースを定式化すると" })).toBeVisible();
    expect(screen.getByText("配合率")).toBeVisible();
    expect(screen.getByText("誤差を最小化")).toBeVisible();
    expect(screen.getByText("合計100%")).toBeVisible();
  });

  test("mounts exported MathML in a case formulation", () => {
    const { container } = render(<OptimizationProblemPrimer caseFormulation={{ decisionVariables: "変数 <math><mi>x</mi></math>", variableDomain: "範囲", objective: "目的", constraints: "制約" }} />);
    expect(container.querySelector("math mi")?.textContent).toBe("x");
  });
});
