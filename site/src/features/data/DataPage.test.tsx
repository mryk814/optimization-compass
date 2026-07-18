import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { DataPage } from "./DataPage";

const manifest = {
  version: "1.4.0",
  dataset_version: "0.15.1",
  generated_at: "2026-07-17T00:00:00Z",
  views: [{ view_id: "map", version: "1.0.0", path: "views/map.json" }],
  recommendation: { version: "2.0.0", path: "recommendation.json" },
  traces: { contract_version: "1.0.0", index_version: "1.0.0", path: "traces.json", bytes: 1, sha256: "a".repeat(64) },
  problems: { version: "1.0.0", path: "problems.json" },
  learning_journeys: { version: "1.1.0", path: "learning-journeys.json" },
  formulation_primer: { version: "1.0.0", path: "formulation-primer.json" },
  visualization_scenarios: { version: "1.2.0", path: "visualization-scenarios.json" },
  derived_media: { version: "1.1.0", path: "media/manifest.json" },
  entity_links: { version: "1.0.0", path: "entity-links.json" },
  sources: { version: "1.0.0", path: "sources.json" },
  implementation_claims: { version: "1.0.0", path: "implementation-claims.json" },
  benchmark_contexts: { version: "1.0.0", path: "benchmark-contexts.json" },
  failure_modes: { version: "1.0.0", path: "failure-modes.json" },
  release_catalog: { version: "1.0.0", path: "release-catalog.json" },
  search_index: { version: "1.0.0", path: "search-index.json" },
  retrieval_documents: { version: "1.0.0", path: "retrieval-documents.json" },
  search_benchmark: { version: "1.0.0", path: "search-benchmark.json" },
  coverage: { version: "1.0.0", path: "coverage.json", report_path: "coverage.md" },
  licenses: {
    code: { spdx_id: "MIT", path: "licenses/LICENSE.txt" },
    data: { spdx_id: "CC-BY-4.0", path: "licenses/DATA-LICENSE.txt" },
    content: { spdx_id: "CC-BY-4.0", path: "licenses/CONTENT-LICENSE.txt" },
    legal_code_path: "licenses/CC-BY-4.0.txt",
    notice_path: "licenses/NOTICE.txt",
    attribution: "Optimization Compass contributors",
  },
};

const catalog = {
  schema_version: 1,
  current_version: "0.15.1",
  releases: [
    release("0.2.0", "2026-07-13", "a"),
    release("0.15.1", "2026-07-17", "b"),
  ],
};

describe("DataPage", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test("lists the current and historical bundles newest first", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(response(manifest))
      .mockResolvedValueOnce(response(catalog)));

    render(<DataPage />);

    expect(await screen.findByRole("heading", { level: 1, name: "Data" })).toBeVisible();
    expect(screen.getAllByText("v0.15.1", { selector: "strong" })).toHaveLength(2);
    const table = screen.getByRole("table", { name: "公開済みデータセット（新しい順）" });
    const rows = within(table).getAllByRole("row");
    expect(within(rows[1]).getByRole("rowheader")).toHaveTextContent("v0.15.1現行");
    expect(within(rows[2]).getByRole("rowheader")).toHaveTextContent("v0.2.0履歴");
    expect(within(rows[1]).getByRole("link", { name: /ZIP/u })).toHaveAttribute(
      "href",
      expect.stringContaining("/releases/download/v0.15.1/"),
    );
    expect(within(rows[2]).getByRole("link", { name: "v0.2.0" })).toHaveAttribute(
      "href",
      "https://github.com/mryk814/optimization-compass/tree/v0.2.0",
    );
    expect(rows[2].querySelector("details.data-source summary")).toHaveTextContent(
      "commit aaaaaaaaaaaa…",
    );
    expect(rows[2].querySelector("details.data-source a")).toHaveAttribute(
      "href",
      "https://github.com/mryk814/optimization-compass/commit/" + "a".repeat(40),
    );
    expect(within(rows[1]).getByText("未登録")).toBeVisible();
  });

  test("shows a visible error when the catalog asset is missing", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(response(manifest))
      .mockResolvedValueOnce({ ok: false, status: 404 }));

    render(<DataPage />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Release catalog request failed (404)",
    );
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  test("rejects a catalog published for another current dataset", async () => {
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(response(manifest))
      .mockResolvedValueOnce(response({ ...catalog, current_version: "0.2.0" })));

    render(<DataPage />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Release catalog current version does not match the manifest",
    );
  });
});

function release(version: string, date: string, digestSeed: string) {
  return {
    version,
    release_date: date,
    database_sha256: digestSeed.repeat(64),
    manifest_sha256: digestSeed.repeat(64),
    source_commit: digestSeed.repeat(40),
    tag: `v${version}`,
    bundle: {
      url: `https://github.com/mryk814/optimization-compass/releases/download/v${version}/bundle.zip`,
      sha256: digestSeed.repeat(64),
      size_bytes: 2_595_952,
    },
    archival: null,
  };
}

function response(value: unknown) {
  return { ok: true, status: 200, json: async () => value };
}
