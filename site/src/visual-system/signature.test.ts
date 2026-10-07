import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { parseSiteData } from "../contracts/site-data";
import { buildMethodLens } from "./method-lens";
import { buildSignature, caseAnswers, SIGNATURE_AXES, SIGNATURE_SLOTS } from "./signature";

const siteData = parseSiteData(JSON.parse(readFileSync(join(process.cwd(), "public", "data", "recommendation", "site-data.json"), "utf8")));

describe("problem signature", () => {
  it("uses the diagnosis questions as axes, and every choice except unknown as a slot", () => {
    expect(SIGNATURE_AXES.map((axis) => axis.questionId)).toEqual(siteData.questions.map((question) => question.question_id));
    for (const question of siteData.questions) {
      expect(SIGNATURE_SLOTS[question.question_id]).toEqual(
        question.choices.map((choice) => choice.value).filter((value) => value !== "unknown"),
      );
    }
  });

  it("keeps missing, unknown, and not applicable distinct", () => {
    const axes = buildSignature({
      Q01: { status: "answered", values: ["continuous"] },
      Q03: { status: "unknown", values: ["unknown"] },
      Q04: { status: "not_applicable", values: [] },
    });
    const state = (id: string) => axes.find((axis) => axis.questionId === id)?.state;
    expect(state("Q01")).toBe("known");
    expect(state("Q02")).toBe("missing");
    expect(state("Q03")).toBe("unknown");
    expect(state("Q04")).toBe("not_applicable");
  });

  it("reads a Case's recorded unknown as unknown, not as missing", () => {
    const axes = buildSignature(caseAnswers({ Q03: "unknown", Q06: "hours_or_more" }));
    expect(axes.find((axis) => axis.questionId === "Q03")?.state).toBe("unknown");
    expect(axes.find((axis) => axis.questionId === "Q06")?.ordinal).toEqual({ index: 3, length: 4 });
  });
});

describe("method lens", () => {
  it("marks the axis whose exclude rule matched, with the rule as evidence", () => {
    const lens = buildMethodLens("M_BFGS", { Q07: { status: "answered", values: ["large_noise"] } }, siteData);
    const axis = lens.axes.find((item) => item.questionId === "Q07");
    expect(axis?.status).toBe("blocks");
    expect(axis?.evidence.map((item) => item.id)).toContain("R042");
  });

  it("shows a violated assumption predicate as a block on its axis", () => {
    const lens = buildMethodLens("M_GRADIENT_DESCENT", { Q05: { status: "answered", values: ["unreliable_or_none"] } }, siteData);
    expect(lens.blockingAxes.map((axis) => axis.questionId)).toEqual(["Q05"]);
    expect(lens.axes.find((axis) => axis.questionId === "Q05")?.flipValues).toContain("analytic_gradient");
  });

  it("leaves an axis open when the method reads it but the answer is missing", () => {
    const lens = buildMethodLens("M_BFGS", {}, siteData);
    expect(lens.openAxes.map((axis) => axis.questionId)).toContain("Q05");
    expect(lens.blockingAxes).toHaveLength(0);
  });

  it("blocks BFGS on the gradient axis through its derivative-access assumption", () => {
    // Dataset 0.18.20 added P_M_BFGS_DERIVATIVE; the Case's editorial exclusion now has an axis.
    const lens = buildMethodLens("M_BFGS", caseAnswers({ Q05: "unreliable_or_none" }), siteData);
    const axis = lens.axes.find((item) => item.questionId === "Q05");
    expect(axis?.status).toBe("blocks");
    expect(axis?.evidence.map((item) => item.id)).toContain("P_M_BFGS_DERIVATIVE");
  });

  it("does not invent an exclusion where no rule or predicate reads the axis", () => {
    const lens = buildMethodLens("M_NELDER_MEAD", caseAnswers({ Q05: "unreliable_or_none" }), siteData);
    expect(lens.axes.find((axis) => axis.questionId === "Q05")?.status).toBe("unread");
    expect(lens.blockingAxes).toHaveLength(0);
  });
});
