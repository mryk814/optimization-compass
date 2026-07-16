import { describe, expect, test } from "vitest";

import { caseState, journeyCompletionLabel } from "./GalleryPage";

describe("gallery Atlas state", () => {
  test("uses the version carried by the gallery release", () => {
    const item = {
      map_node_id: "method:M_BAYESIAN_OPT_GP",
      question_answers: { Q01: "continuous", Q02: "unknown" },
    };

    const state = caseState(item, "0.3.0");

    expect(state.datasetVersion).toBe("0.3.0");
    expect(state.selectedNodeId).toBe("method:M_BAYESIAN_OPT_GP");
    expect(state.answers.Q01).toEqual({ status: "answered", values: ["continuous"] });
    expect(state.answers.Q02).toEqual({ status: "unknown", values: ["unknown"] });
  });
});

describe("gallery learning journey status", () => {
  test("translates missing canonical routes into reader-facing labels", () => {
    expect(journeyCompletionLabel("missing_primary_scenario")).toBe("primary Theater 未接続");
    expect(journeyCompletionLabel("missing_comparison")).toBe("canonical Compare 未接続");
  });
});
