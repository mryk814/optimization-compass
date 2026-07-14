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
  licenses: {
    code: { spdx_id: "MIT", path: "licenses/LICENSE.txt" },
    data: { spdx_id: "CC-BY-4.0", path: "licenses/DATA_LICENSE.txt" },
    content: { spdx_id: "CC-BY-4.0", path: "licenses/CONTENT_LICENSE.txt" },
    legal_code_path: "licenses/CC-BY-4.0.txt",
    notice_path: "licenses/NOTICE.txt",
    attribution: "Optimization Compass contributors",
  },
};

describe("SiteManifest parser", () => {
  test("parses the versioned trace index asset exactly", () => {
    expect(parseSiteManifest(manifest).traces.path).toBe("traces/index.json");
    expect(parseSiteManifest(manifest).licenses.data.spdx_id).toBe("CC-BY-4.0");
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
    expect(() => parseSiteManifest({
      ...manifest,
      licenses: { ...manifest.licenses, code: { spdx_id: "CC-BY-4.0", path: "licenses/LICENSE.txt" } },
    })).toThrow(/spdx/u);
  });
});
