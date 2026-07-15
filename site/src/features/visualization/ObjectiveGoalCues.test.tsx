import { describe, expect, test } from "vitest";
import { render, screen } from "@testing-library/react";

import { ObjectiveGoalCues } from "./ObjectiveGoalCues";

describe("ObjectiveGoalCues", () => {
  test("shows direction, initial/current/best, known optimum, and terminal reason", () => {
    render(
      <ObjectiveGoalCues
        bestValue={0.25}
        currentPoint={[0.5, -0.25]}
        initialPoint={[-2, 2]}
        objective={{ direction: "maximize", optimum: { point: [1, 1], value: 3 } }}
        terminalReason="budget reached"
      />,
    );
    expect(screen.getByText("maximize")).toBeVisible();
    expect(screen.getByText("[-2.000, 2.000]")).toBeVisible();
    expect(screen.getByText("[0.500, -0.250]")).toBeVisible();
    expect(screen.getByText(/\[1\.000, 1\.000\].*3\.0000/u)).toBeVisible();
    expect(screen.getByText("budget reached")).toBeVisible();
  });

  test("explains when optimum metadata is unavailable", () => {
    render(
      <ObjectiveGoalCues
        initialPoint={[]}
        objective={{}}
        terminalReason="unknown"
      />,
    );
    expect(screen.getByText("既知のreferenceなし")).toBeVisible();
    expect(screen.getByText("minimize")).toBeVisible();
  });
});
