import { describe, expect, test } from "vitest";

import raw from "../../public/data/failure-modes.json";
import { parseFailureModeIndex } from "./failure-modes";

describe("failure mode contract", () => {
  test("parses twelve normalized failures and four scenario links", () => {
    const index = parseFailureModeIndex(raw);
    expect(index.failure_modes).toHaveLength(12);
    expect(index.failure_modes.filter((item) => item.scenario_ids.length > 0)).toHaveLength(4);
    expect(index.failure_modes.every((item) => item.diagnostics.length > 0)).toBe(true);
  });
});
