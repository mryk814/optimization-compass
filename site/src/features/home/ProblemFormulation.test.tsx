import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";

import rawProblems from "../../../public/data/problems.json";
import { parseProblemCatalog } from "../../contracts/problems";
import { buildReadableProblemFormulation, ProblemFormulation } from "./ProblemFormulation";

const catalog = parseProblemCatalog(rawProblems);
const instance = catalog.instances.find(
  (item) => item.problem_instance_id === "INSTANCE_CONSTRAINED_DISK_2D",
);
const definition = instance && catalog.definitions.find(
  (item) => item.problem_definition_id === instance.problem_definition_id,
);

if (!instance || !definition) throw new Error("constrained disk fixture is missing");

afterEach(cleanup);

describe("ProblemFormulation", () => {
  test("writes the constrained Case as an explicit optimization problem", () => {
    expect(buildReadableProblemFormulation(definition, instance)).toEqual({
      ariaLabel: "(x, y) ∈ ℝ²; minimize f(x, y) = x²+y²; subject to (x−1)²+(y−1)² ≤ 1; −1 ≤ x ≤ 3; −1 ≤ y ≤ 3",
      constraints: [
        "(x−1)²+(y−1)² ≤ 1",
        "−1 ≤ x ≤ 3",
        "−1 ≤ y ≤ 3",
      ],
      objective: "f(x, y) = x²+y²",
      sense: "minimize",
      variables: "(x, y) ∈ ℝ²",
    });
  });

  test("renders the formula before the prose reading", () => {
    render(
      <ProblemFormulation
        constraintsSummary="許容領域を表す非線形不等式とdesign bounds。"
        decisionVariablesSummary="2つの連続design parameter。"
        definition={definition}
        instance={instance}
        objectiveSummary="重量に対応する二次目的を最小化する。"
      />,
    );

    expect(
      screen.getByRole("heading", { level: 3, name: "このケースを定式化すると" }),
    ).toBeVisible();
    expect(screen.getByText("f(x, y) = x²+y²")).toBeVisible();
    expect(screen.getByText("(x−1)²+(y−1)² ≤ 1")).toBeVisible();
    expect(screen.getByText(/選ぶもの: 2つの連続design parameter/u)).toBeVisible();
  });
});
