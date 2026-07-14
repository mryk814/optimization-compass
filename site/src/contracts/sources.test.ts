import { describe, expect, test } from "vitest";

import { parseSourceEvidenceIndex } from "./sources";

const target = {
  evidence_link_id: "EL1", target_table: "methods", target_id: "M1", target_type: "method",
  label: "Method", canonical_url: "/methods/M1", external_url: null, supported_field: "row",
  claim_summary: "Claim", evidence_role: "primary", confidence: "high", last_verified: "2026-07-13",
};
const source = {
  source_id: "S1", source_type: "official_documentation", title: "Official docs", publisher: "Project",
  publication_date: null, last_verified: "2026-07-13", official_url: "https://example.com/docs", license: "unknown",
  access_note: "Check official terms.", supported_claim: "API", source_quality: "primary",
  currentness_status: "verified_current", evidence_targets: [target],
};
const index = {
  contract_version: "1.0.0", dataset_version: "0.3.0", generated_at: "2026-07-13T00:00:00Z",
  freshness_policy: [{ source_type: "official_documentation", max_age_days: 90 }], sources: [source],
};

describe("source evidence contract", () => {
  test("parses source metadata and backlink targets", () => {
    const parsed = parseSourceEvidenceIndex(index);
    expect(parsed.sources[0].title).toBe("Official docs");
    expect(parsed.sources[0].evidence_targets[0].canonical_url).toBe("/methods/M1");
  });

  test("rejects unsafe official URLs and duplicate evidence IDs", () => {
    expect(() => parseSourceEvidenceIndex({ ...index, sources: [{ ...source, official_url: "javascript:alert(1)" }] })).toThrow(/HTTP/u);
    expect(() => parseSourceEvidenceIndex({ ...index, sources: [source, { ...source, source_id: "S2" }] })).toThrow(/evidence link/u);
  });
});
