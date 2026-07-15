import { describe, expect, it } from "vitest";

import { parseContentIndex } from "./atlas-content";

const valid = {
  contract_version: "2.0.0",
  dataset_version: "0.3.0",
  pages: [{
    content_id: "concept.example", kind: "concept", canonical_entity_type: "feature", canonical_entity_id: "F_EXAMPLE", title_ja: "例", title_en: "Example",
    summary: "Summary.", html: '<h2 id="overview" tabindex="-1">Overview</h2><p>Summary.</p>',
    toc: [{ heading_id: "overview", label: "Overview", level: 2 }], prerequisites: [], related_ids: [],
    visualization_ids: [], comparison_ids: [], source_ids: ["S001"], status: "published",
    last_reviewed: "2026-07-15", seo_title: "例", seo_description: "Summary.",
  }],
};

describe("parseContentIndex", () => {
  it("accepts the compiled HTML contract", () => {
    expect(parseContentIndex(valid).pages[0].toc[0].heading_id).toBe("overview");
  });

  it("rejects the removed raw body contract", () => {
    expect(() => parseContentIndex({ ...valid, contract_version: "1.0.0" })).toThrow("Unsupported content contract");
  });

  it("rejects invalid heading levels", () => {
    const payload = structuredClone(valid);
    payload.pages[0].toc[0].level = 1;
    expect(() => parseContentIndex(payload)).toThrow("Unsupported heading level");
  });

  it("rejects empty navigation metadata", () => {
    const payload = structuredClone(valid);
    payload.pages[0].toc = [];
    expect(() => parseContentIndex(payload)).toThrow("Content TOC must not be empty");
  });
});
