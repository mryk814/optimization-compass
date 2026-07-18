import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";

import rawProblems from "../../../public/data/problems.json";
import {
  parseProblemCatalog,
  type ProblemDefinition,
  type ProblemInstance,
} from "../../contracts/problems";
import { buildReadableProblemFormulation, ProblemFormulation } from "./ProblemFormulation";

const catalog = parseProblemCatalog(rawProblems);

afterEach(cleanup);

describe("ProblemFormulation", () => {
  test("writes the constrained continuous Case from explicit objective, constraint, and bounds", () => {
    const { definition, instance } = problem("INSTANCE_CONSTRAINED_DISK_2D");

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

  test("derives binary knapsack objective and capacity from canonical items", () => {
    const { definition, instance } = problem("INSTANCE_BINARY_KNAPSACK_4");

    expect(buildReadableProblemFormulation(definition, instance)).toEqual({
      ariaLabel: "(A, B, D, C) ∈ {0, 1}⁴; maximize f(A, B, D, C) = 9A+6B+4D+5C; subject to 4A+3B+2D+3C ≤ 7; 0 ≤ A ≤ 1; 0 ≤ B ≤ 1; 0 ≤ D ≤ 1; 0 ≤ C ≤ 1",
      constraints: [
        "4A+3B+2D+3C ≤ 7",
        "0 ≤ A ≤ 1",
        "0 ≤ B ≤ 1",
        "0 ≤ D ≤ 1",
        "0 ≤ C ≤ 1",
      ],
      objective: "f(A, B, D, C) = 9A+6B+4D+5C",
      sense: "maximize",
      variables: "(A, B, D, C) ∈ {0, 1}⁴",
    });
  });

  test("keeps both canonical objectives for a multiobjective instance", () => {
    const { definition, instance } = problem("INSTANCE_BIOBJECTIVE_QUADRATIC_2D");

    expect(buildReadableProblemFormulation(definition, instance)).toMatchObject({
      constraints: ["0 ≤ x ≤ 2", "0 ≤ y ≤ 2"],
      objective: "f₁=x²+y²; f₂=(x−2)²+(y−2)²",
      sense: "objectives",
      variables: "(x, y) ∈ ℝ²",
    });
  });

  test("rejects structures that cannot be formatted without inventing semantics", () => {
    const assignment = problem("INSTANCE_ASSIGNMENT_3X3");
    const constrained = problem("INSTANCE_CONSTRAINED_DISK_2D");
    const structuredBounds: ProblemInstance = {
      ...constrained.instance,
      bounds: {
        lower: [0, 0, 0],
        upper: [5, 3, 2],
        parameter_names: ["a", "k", "c"],
      },
      dimension: 3,
      display: {
        expression: "min Σᵢ rᵢ(a,k,c)²; 0≤a≤5; 0≤k≤3; −1≤c≤2",
      },
    };
    const unknownDomain: ProblemDefinition = {
      ...constrained.definition,
      variable_domain: "categorical",
    };

    expect(buildReadableProblemFormulation(assignment.definition, assignment.instance)).toBeNull();
    expect(buildReadableProblemFormulation(constrained.definition, structuredBounds)).toBeNull();
    expect(buildReadableProblemFormulation(unknownDomain, constrained.instance)).toBeNull();
  });

  test("rejects a nonempty constraint without a canonical expression", () => {
    const { definition, instance } = problem("INSTANCE_CONSTRAINED_DISK_2D");
    expect(buildReadableProblemFormulation(definition, {
      ...instance,
      constraints: [{ constraint_id: "capacity", sense: "lte", rhs: 1 }],
    })).toBeNull();
  });

  test("renders a validated formula before the prose reading", () => {
    const { definition, instance } = problem("INSTANCE_CONSTRAINED_DISK_2D");
    const formulation = buildReadableProblemFormulation(definition, instance);
    if (!formulation) throw new Error("constrained disk formulation is unsupported");

    render(
      <ProblemFormulation
        constraintsSummary="許容領域を表す非線形不等式とdesign bounds。"
        decisionVariablesSummary="2つの連続design parameter。"
        formulation={formulation}
        objectiveSummary="重量に対応する二次目的を最小化する。"
      />,
    );

    expect(
      screen.getByRole("heading", { level: 3, name: "このケースを定式化すると" }),
    ).toBeVisible();
    expect(screen.getByText("f(x, y) = x²+y²")).toBeVisible();
    expect(screen.getByText("(x−1)²+(y−1)² ≤ 1")).toBeVisible();
    expect(screen.getByText(/決めるもの: 2つの連続design parameter/u)).toBeVisible();
  });
});

function problem(problemInstanceId: string): {
  definition: ProblemDefinition;
  instance: ProblemInstance;
} {
  const instance = catalog.instances.find(
    (item) => item.problem_instance_id === problemInstanceId,
  );
  const definition = instance && catalog.definitions.find(
    (item) => item.problem_definition_id === instance.problem_definition_id,
  );
  if (!instance || !definition) throw new Error(`${problemInstanceId} fixture is missing`);
  return { definition, instance };
}
