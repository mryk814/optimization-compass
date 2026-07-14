import { describe, expect, test } from "vitest";

import { parseEntityLinkIndex } from "./entity-links";

const method = {
  entity_type: "method",
  entity_id: "M_EXAMPLE",
  label: "Example",
  summary: "",
  canonical_url: "/methods/M_EXAMPLE",
  aliases: ["/learn/method.example"],
  external_url: null,
  relations: [{ relation_type: "visualization", target_type: "trace", target_id: "trace-example" }],
};
const trace = {
  entity_type: "trace",
  entity_id: "trace-example",
  label: "Trace",
  summary: "",
  canonical_url: "/traces/trace-example",
  aliases: [],
  external_url: null,
  relations: [],
};
const index = {
  contract_version: "1.0.0",
  dataset_version: "0.2.0",
  generated_at: "2026-07-13T00:00:00Z",
  entities: [method, trace],
};

describe("EntityLinkIndex parser", () => {
  test("accepts a canonical graph", () => {
    expect(parseEntityLinkIndex(index).entities).toHaveLength(2);
  });

  test("rejects dangling relations and duplicate routes", () => {
    expect(() => parseEntityLinkIndex({ ...index, entities: [method] })).toThrow(/Dangling/u);
    expect(() => parseEntityLinkIndex({
      ...index,
      entities: [method, { ...trace, canonical_url: method.canonical_url }],
    })).toThrow(/Duplicate canonical/u);
  });
});
