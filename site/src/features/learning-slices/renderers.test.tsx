import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import paretoPayload from "../../../public/data/visualizations/biobjective-quadratic-pareto-front.json";
import feasiblePayload from "../../../public/data/visualizations/constrained-disk-feasible-region.json";
import { parseLearningSliceArtifact } from "../../contracts/learning-slices";
import { LearningSliceRenderer } from "./renderer-registry";

describe("learning-slice renderer registry", () => {
  test("renders and scrubs the feasible-region teaching trace", () => {
    const artifact = parseLearningSliceArtifact(feasiblePayload);
    render(<LearningSliceRenderer artifact={artifact} />);

    expect(screen.getByRole("img", { name: artifact.text_alternative_ja })).toBeVisible();
    expect(screen.getByText("active constraint")).toBeVisible();

    fireEvent.change(screen.getByRole("slider", { name: /現在の反復/u }), {
      target: { value: "0" },
    });
    expect(screen.getByText("infeasible")).toBeVisible();
    expect(screen.getByText("Traceを進めて確認します。")).toBeVisible();
  });

  test("moves the selected Pareto point with the preference weight", () => {
    const artifact = parseLearningSliceArtifact(paretoPayload);
    render(<LearningSliceRenderer artifact={artifact} />);

    expect(screen.getByRole("heading", { name: /単一bestではなく/u })).toBeVisible();
    expect(screen.getByText(/Weighted sumの注意/u)).toBeVisible();
    const before = screen.getByText("Selected f₁").nextElementSibling?.textContent;

    fireEvent.change(screen.getByRole("slider", { name: /f₁のweight/u }), {
      target: { value: "80" },
    });
    expect(screen.getByText("Selected f₁").nextElementSibling?.textContent).not.toBe(before);
  });
});
