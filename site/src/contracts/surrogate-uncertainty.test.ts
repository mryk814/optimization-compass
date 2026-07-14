import { describe, expect, test } from "vitest";

import payload from "../../public/data/visualizations/bo-explore-noiseless.json";
import { parseSurrogateUncertaintyPayload } from "./surrogate-uncertainty";

describe("SurrogateUncertainty renderer payload", () => {
  test("parses the generated fixed-seed geometry without scenario metadata", () => {
    const parsed = parseSurrogateUncertaintyPayload(payload);
    expect(parsed.strategy).toBe("explore");
    expect(parsed.frames.at(-1)?.oracle_evaluations).toBe(10);
    expect(payload).not.toHaveProperty("title_ja");
    expect(payload).not.toHaveProperty("method_id");
    expect(payload).not.toHaveProperty("evaluation_budget");
    expect(payload).not.toHaveProperty("source_ids");
    expect(payload).not.toHaveProperty("limitations_ja");
  });

  test("rejects unknown fields and invalid versions", () => {
    expect(() => parseSurrogateUncertaintyPayload({ ...payload, legacy: true })).toThrow(/unknown/u);
    expect(() => parseSurrogateUncertaintyPayload({ ...payload, contract_version: "2.0.0" })).toThrow(/unsupported/iu);
  });
});
