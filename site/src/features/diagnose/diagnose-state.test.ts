import { describe, expect, test } from "vitest";

import type { AtlasStateV1 } from "../../state/atlas-state";
import { updateDiagnosticAnswer } from "./diagnose-state";

const base: AtlasStateV1 = {
  stateVersion: 1,
  datasetVersion: "0.2.0",
  viewId: "problem-structure",
  viewVersion: "1.0.0",
  answers: {},
};

describe("diagnostic answer state", () => {
  test("keeps unanswered as key absence and N/A outside recommendation projection", () => {
    const answered = updateDiagnosticAnswer(base, "Q01", "single_choice", "set", "binary");
    const notApplicable = updateDiagnosticAnswer(answered, "Q01", "single_choice", "not_applicable");
    const cleared = updateDiagnosticAnswer(notApplicable, "Q01", "single_choice", "clear");

    expect(notApplicable.answers.Q01).toEqual({ status: "not_applicable", values: [] });
    expect(cleared.answers).not.toHaveProperty("Q01");
  });

  test("replaces single values and stable-merges multi values until the last is removed", () => {
    const single = updateDiagnosticAnswer(base, "Q01", "single_choice", "set", "binary");
    const replaced = updateDiagnosticAnswer(single, "Q01", "single_choice", "set", "continuous");
    const first = updateDiagnosticAnswer(replaced, "Q05", "multi_choice", "toggle", "hvp");
    const merged = updateDiagnosticAnswer(first, "Q05", "multi_choice", "toggle", "autodiff");
    const oneLeft = updateDiagnosticAnswer(merged, "Q05", "multi_choice", "toggle", "hvp");
    const noneLeft = updateDiagnosticAnswer(oneLeft, "Q05", "multi_choice", "toggle", "autodiff");

    expect(replaced.answers.Q01).toEqual({ status: "answered", values: ["continuous"] });
    expect(merged.answers.Q05).toEqual({ status: "answered", values: ["hvp", "autodiff"] });
    expect(noneLeft.answers).not.toHaveProperty("Q05");
  });

  test("uses unknown status only for the canonical unknown value", () => {
    const unknown = updateDiagnosticAnswer(base, "Q02", "single_choice", "set", "unknown");
    const structured = updateDiagnosticAnswer(
      unknown,
      "Q02",
      "single_choice",
      "set",
      "structured_or_unknown",
    );

    expect(unknown.answers.Q02).toEqual({ status: "unknown", values: ["unknown"] });
    expect(structured.answers.Q02).toEqual({
      status: "answered",
      values: ["structured_or_unknown"],
    });
  });
});
