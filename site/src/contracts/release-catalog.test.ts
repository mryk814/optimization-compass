import { describe, expect, test } from "vitest";

import { parseReleaseCatalog } from "./release-catalog";

const release = {
  archival: null,
  bundle: {
    sha256: "c".repeat(64),
    size_bytes: 1234,
    url: "https://github.com/mryk814/optimization-compass/releases/download/v0.15.1/bundle.zip",
  },
  database_sha256: "a".repeat(64),
  manifest_sha256: "d".repeat(64),
  release_date: "2026-07-17",
  source_commit: "b".repeat(40),
  tag: "v0.15.1",
  version: "0.15.1",
};
const historicalRelease = {
  ...release,
  bundle: {
    ...release.bundle,
    url: "https://github.com/mryk814/optimization-compass/releases/download/v0.2.0/bundle.zip",
  },
  tag: "v0.2.0",
  version: "0.2.0",
};

describe("release catalog contract", () => {
  test("parses current and historical releases with explicit archival state", () => {
    const catalog = parseReleaseCatalog({
      schema_version: 1,
      current_version: "0.15.1",
      releases: [
        historicalRelease,
        release,
      ],
    });

    expect(catalog.current_version).toBe("0.15.1");
    expect(catalog.releases[0].archival).toBeNull();
  });

  test("rejects unknown fields, missing current identity, and unsorted versions", () => {
    expect(() => parseReleaseCatalog({
      schema_version: 1,
      current_version: "0.15.1",
      releases: [{ ...release, unknown: true }],
    })).toThrow(/unknown/u);
    expect(() => parseReleaseCatalog({
      schema_version: 1,
      current_version: "0.14.0",
      releases: [release],
    })).toThrow(/absent/u);
    expect(() => parseReleaseCatalog({
      schema_version: 1,
      current_version: "0.15.1",
      releases: [release, historicalRelease],
    })).toThrow(/sorted/u);
  });

  test("rejects mismatched tags, unsafe URLs, and malformed digests", () => {
    expect(() => parseReleaseCatalog({
      schema_version: 1,
      current_version: "0.15.1",
      releases: [{ ...release, tag: "v0.15.0" }],
    })).toThrow(/tag/u);
    expect(() => parseReleaseCatalog({
      schema_version: 1,
      current_version: "0.15.1",
      releases: [{ ...release, bundle: { ...release.bundle, url: "https://example.com/a.zip" } }],
    })).toThrow(/GitHub/u);
    expect(() => parseReleaseCatalog({
      schema_version: 1,
      current_version: "0.15.1",
      releases: [{ ...release, bundle: { ...release.bundle, sha256: "short" } }],
    })).toThrow(/SHA-256/u);
  });
});
