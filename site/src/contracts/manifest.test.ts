import { describe, expect, test } from "vitest";

import { parseSiteManifest } from "./manifest";

const manifest = {
  version: "1.0.0",
  dataset_version: "0.2.0",
  generated_at: "2026-07-13T00:00:00Z",
  views: [{ view_id: "problem-structure", version: "1.0.0", path: "views/problem-structure.json" }],
  recommendation: { version: "1.0.0", path: "recommendation/site-data.json" },
  traces: {
    contract_version: "1.0.0",
    index_version: "1.0.0",
    path: "traces/index.json",
    bytes: 475,
    sha256: "a".repeat(64),
  },
};

describe("SiteManifest parser", () => {
  test("parses the versioned trace index asset exactly", () => {
    expect(parseSiteManifest(manifest).traces.path).toBe("traces/index.json");
  });

  test("rejects missing/unknown fields and malformed trace integrity metadata", () => {
    expect(() => parseSiteManifest({ ...manifest, legacy_traces: {} })).toThrow(/unknown/u);
    const withoutTraces = { ...manifest } as Record<string, unknown>;
    delete withoutTraces.traces;
    expect(() => parseSiteManifest(withoutTraces)).toThrow(/traces/u);
    expect(() => parseSiteManifest({
      ...manifest,
      traces: { ...manifest.traces, bytes: "475" },
    })).toThrow(/bytes/u);
    expect(() => parseSiteManifest({
      ...manifest,
      traces: { ...manifest.traces, sha256: "bad" },
    })).toThrow(/sha256/u);
  });
});
