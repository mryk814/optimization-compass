import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import paretoPayload from "../../../public/data/visualizations/biobjective-quadratic-pareto-front.json";
import feasiblePayload from "../../../public/data/visualizations/constrained-disk-feasible-region.json";
import topologyPayload from "../../../public/data/visualizations/topology-optimization-field-evolution.json";
import { parseLearningSliceArtifact } from "../../contracts/learning-slices";
import { projectTriObjective } from "./renderers";
import { LearningSliceRenderer } from "./renderer-registry";

describe("learning-slice renderer registry", () => {
  test("renders and scrubs the feasible-region teaching trace", () => {
    const artifact = parseLearningSliceArtifact(feasiblePayload);
    render(<LearningSliceRenderer artifact={artifact} />);

    expect(screen.getByRole("img", { name: artifact.text_alternative_ja })).toBeVisible();
    expect(screen.getByText("制約が有効")).toBeVisible();

    fireEvent.change(screen.getByRole("slider", { name: /現在の反復/u }), {
      target: { value: "0" },
    });
    expect(screen.getByText("実行不可能")).toBeVisible();
    expect(screen.getByText("Traceを進めて確認します。")).toBeVisible();
  });

  test("moves the selected Pareto point with the preference weight", () => {
    const artifact = parseLearningSliceArtifact(paretoPayload);
    if (artifact.renderer_family !== "pareto_front") throw new Error("Pareto fixture is invalid");
    render(<LearningSliceRenderer artifact={artifact} />);

    expect(screen.getByRole("heading", { name: /単一の最良解ではなく/u })).toBeVisible();
    expect(screen.getByText(/重み付き和 \(Weighted sum\) の注意/u)).toBeVisible();
    expect(screen.getByRole("heading", { name: /3目的のトレードオフ/u })).toBeVisible();
    expect(screen.getByTestId("triobjective-scatter")).toBeVisible();
    expect(screen.getByRole("img", { name: "3目的のparallel coordinates表示" })).toBeVisible();
    const coverage = screen.getByLabelText("パレート前線の集計");
    expect(coverage).toHaveTextContent(`サンプル数${artifact.points.length}`);
    expect(coverage).toHaveTextContent(`支配された点${artifact.points.filter((point) => point.dominated).length}`);
    expect(coverage).toHaveTextContent(`非支配のサンプル点${artifact.points.filter((point) => !point.dominated).length}`);
    expect(coverage).toHaveTextContent(`解析的な参照前線${artifact.pareto_front.length} · known_exact`);
    const before = screen.getByText("選択した f₁").nextElementSibling?.textContent;

    fireEvent.change(screen.getByRole("slider", { name: /f₁の重み/u }), {
      target: { value: "80" },
    });
    expect(screen.getByText("選択した f₁").nextElementSibling?.textContent).not.toBe(before);
  });

  test("rotates the tri-objective projection without changing objective data", () => {
    const first = projectTriObjective([1, 2, 3], [8, 8, 8], 315);
    const rotated = projectTriObjective([1, 2, 3], [8, 8, 8], 405);
    expect(first.x).not.toBe(rotated.x);
    expect(Number.isFinite(first.y)).toBe(true);
  });

  test("renders the field pilot with static facts and event markers", () => {
    const artifact = parseLearningSliceArtifact(topologyPayload);
    render(<LearningSliceRenderer artifact={artifact} />);

    expect(screen.getByRole("heading", { name: "静的な要点" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "イベントマーカー" })).toBeVisible();
    expect(screen.getAllByText(/checkerboard score/u).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/状態方程式/u)).toBeVisible();
    expect(document.querySelectorAll(".topology-field")).toHaveLength(3);
  });

  test("opens the field failure Theater on the failure run", () => {
    cleanup();
    const artifact = parseLearningSliceArtifact(topologyPayload);
    render(<LearningSliceRenderer artifact={artifact} initialRunRole="failure_contrast" />);

    expect(screen.getByRole("note")).toHaveTextContent("Failure Theater");
    expect(screen.getAllByRole("combobox", { name: /経路/u }).some((element) => (element as HTMLSelectElement).value === "topology-no-filter")).toBe(true);
    expect(screen.getByText("失敗を観察する順番:")).toBeVisible();
  });
});
