import { describe, expect, test } from "vitest";

import fixture from "../../public/data/search-index.json";
import { lexicalTokens, parseSearchIndex, searchDocuments } from "./search-index";

describe("global SearchIndex", () => {
  test("parses the generated deterministic index", () => {
    const index = parseSearchIndex(fixture);
    expect(index.documents.length).toBeGreaterThan(500);
    expect(new Set(index.documents.map((document) => document.entity_type))).toEqual(expect.objectContaining(new Set(["method", "problem", "implementation", "content", "case", "trace", "comparison", "source", "glossary"])));
  });

  test("normalizes width, punctuation and Japanese terms", () => {
    expect(lexicalTokens("ＣＰ－ＳＡＴ 論理制約")).toEqual(expect.arrayContaining(["cp", "sat", "論理", "理制", "制約"]));
  });

  test("ranks an alias deterministically with a type filter", () => {
    const index = parseSearchIndex(fixture);
    const hits = searchDocuments(index, "BO", { entityTypes: new Set(["method"]) });
    expect(hits[0]?.document.document_id).toBe("method:M_BAYESIAN_OPT_GP");
    expect(hits[0]?.matchedFields).toContain("alias");
  });
});
