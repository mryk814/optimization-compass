import { afterEach, describe, expect, test, vi } from "vitest";

import rawEntityLinks from "../../../public/data/entity-links.json";
import rawFailureModes from "../../../public/data/failure-modes.json";
import rawManifest from "../../../public/data/manifest.json";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import { loadPromptSupportData } from "./support-data";

function mockArtifacts(entityVersion = rawEntityLinks.dataset_version) {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    const body = url.endsWith("manifest.json")
      ? rawManifest
      : url.endsWith("recommendation/site-data.json")
        ? rawSiteData
        : url.endsWith("failure-modes.json")
          ? rawFailureModes
          : url.endsWith("entity-links.json")
            ? { ...rawEntityLinks, dataset_version: entityVersion }
            : undefined;
    return body
      ? { ok: true, json: async () => structuredClone(body) } as Response
      : { ok: false, status: 404 } as Response;
  }));
}

describe("loadPromptSupportData", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("rejects a manifest dataset mismatch before loading dependent artifacts", async () => {
    mockArtifacts();
    await expect(loadPromptSupportData("stale")).rejects.toThrow(/manifest is/u);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  test("rejects a dependent artifact dataset mismatch", async () => {
    mockArtifacts("stale");
    await expect(loadPromptSupportData(rawManifest.dataset_version)).rejects.toThrow(/entity_links is stale/u);
  });
});
