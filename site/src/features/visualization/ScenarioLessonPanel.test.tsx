import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import fixture from "../../contracts/visualization-scenarios.fixture.json";
import { parseVisualizationScenarioIndex } from "../../contracts/visualization-scenarios";
import {
  ScenarioLessonPanel,
  scenarioDerivedMediaCaption,
  scenarioStaticSummary,
  scenarioTextAlternative,
} from "./ScenarioLessonPanel";

describe("ScenarioLessonPanel", () => {
  test("renders reading cues and reuses authored derived text", () => {
    const scenario = parseVisualizationScenarioIndex(fixture).scenarios[0];
    render(<ScenarioLessonPanel scenario={scenario} />);

    expect(screen.getByRole("heading", { name: scenario.lesson.learning_objective.ja })).toBeVisible();
    expect(screen.getByText(/単体の頂点/u)).toBeVisible();
    expect(screen.getByText("start")).toBeVisible();
    expect(scenarioStaticSummary(scenario)).toBe(scenario.lesson.static_summary.ja);
    expect(scenarioTextAlternative(scenario)).toBe(scenario.lesson.text_alternative.ja);
    expect(scenarioDerivedMediaCaption(scenario)).toBe(scenario.lesson.derived_media_caption.ja);
  });
});
