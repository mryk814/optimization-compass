import { describe, expect, test } from "vitest";

import { parseDatasetReleaseIdentity } from "./release";

const identity = {
  schema_version: 1,
  dataset_version: "0.3.0",
  release_date: "2026-07-15",
  database_sha256: "a".repeat(64),
};

describe("dataset release identity", () => {
  test("accepts the generated release contract", () => {
    expect(parseDatasetReleaseIdentity(identity)).toEqual(identity);
  });

  test("rejects legacy and unknown fields", () => {
    expect(() => parseDatasetReleaseIdentity({ ...identity, legacy_version: "0.2.0" })).toThrow(
      "fields",
    );
  });

  test("rejects malformed release identity values", () => {
    expect(() => parseDatasetReleaseIdentity({ ...identity, database_sha256: "short" })).toThrow(
      "database_sha256",
    );
  });
});
