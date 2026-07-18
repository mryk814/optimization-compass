import { describe, expect, test } from "vitest";

import payload from "../../public/data/visualizations/bo-explore-noiseless.json";
import ledgerPayload from "../../public/data/visualizations/bo-multi-fidelity-ledger.json";
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

  test("parses the bounded multi-fidelity evaluation ledger extension", () => {
    const parsed = parseSurrogateUncertaintyPayload(ledgerPayload);
    expect(parsed.contract_version).toBe("1.1.0");
    expect(parsed.evaluation_ledger?.calls).toHaveLength(14);
    expect(new Set(parsed.evaluation_ledger?.calls.map((call) => call.status))).toEqual(
      new Set(["ok", "failed", "censored", "timeout"]),
    );
    expect(parsed.evaluation_ledger?.calls.at(-1)?.accumulated_cost).toBe(36);
    expect(parsed.evaluation_ledger?.calls.at(-1)?.best_so_far).not.toBeNull();
  });
});
