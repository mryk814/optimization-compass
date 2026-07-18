import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { createHash, webcrypto } from "node:crypto";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, test, vi } from "vitest";

import {
  algorithmTraceFixture,
  traceFrameFixture,
} from "../../contracts/trace.fixtures";
import scenarioFixture from "../../contracts/visualization-scenarios.fixture.json";
import generatedMedia from "../../../public/data/media/manifest.json";
import { TraceDemoPage } from "./TraceDemoPage";

const trace = {
  ...algorithmTraceFixture,
  frames: [
    {
      ...traceFrameFixture,
      event_type: "initialize",
      explanation_key: "trace.dummy.initialize",
      decision: "accepted",
      event_label_ja: "初期状態",
      event_label_en: "Initialize",
    },
    {
      ...traceFrameFixture,
      frame_index: 1,
      iteration: 1,
      oracle_evaluations: 2,
      event_type: "stop",
      event_label_ja: "終了",
      event_label_en: "Stop",
    },
  ],
};

const index = {
  contract_version: "1.0.0",
  dataset_version: "0.2.0",
  data_version: "1.0.0",
  traces: [
    {
      trace_id: "dummy-educational",
      path: "dummy-educational.json",
      method_id: "M_EDUCATIONAL",
      profile_id: "profile-educational",
      objective_id: "objective-quadratic",
      scenario_id: "scenario-dummy",
      title_ja: "AlgorithmTrace 契約デモ",
      title_en: "AlgorithmTrace contract demo",
    },
  ],
};
const indexBytes = new TextEncoder().encode(JSON.stringify(index));
const mediaManifest = {
  ...generatedMedia,
  dataset_version: "0.2.0",
  entries: generatedMedia.entries.map((entry) => ({ ...entry, dataset_version: "0.2.0" })),
};
const manifest = {
  version: "1.3.0",
  dataset_version: "0.2.0",
  generated_at: "2026-07-13T00:00:00Z",
  views: [{ view_id: "problem-structure", version: "1.0.0", path: "views/problem-structure.json" }],
  recommendation: { version: "2.0.0", path: "recommendation/site-data.json" },
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
  search_index: { version: "1.0.0", path: "search-index.json" },
  retrieval_documents: { version: "1.0.0", path: "retrieval-documents.json" },
  search_benchmark: { version: "1.0.0", path: "search-benchmark.json" },
  coverage: { version: "1.0.0", path: "coverage.json", report_path: "coverage.md" },
  traces: {
    contract_version: "1.0.0",
    index_version: "1.0.0",
    path: "traces/catalog.json",
    bytes: indexBytes.byteLength,
    sha256: createHash("sha256").update(indexBytes).digest("hex"),
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

function jsonResponse(value: unknown) {
  return { ok: true, json: async () => value };
}

function byteResponse(bytes: Uint8Array) {
  return {
    ok: true,
    arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
  };
}

function renderPage(traceId = "dummy-educational") {
  return render(
    <MemoryRouter initialEntries={[`/traces/${traceId}?foo=bar`]}>
      <Routes>
        <Route path="/traces/:traceId" element={<TraceDemoPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("TraceDemoPage", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test("loads a strict index and trace into the common player", async () => {
    vi.stubGlobal("crypto", webcrypto as Crypto);
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(manifest))
      .mockResolvedValueOnce(jsonResponse(scenarioFixture))
      .mockResolvedValueOnce(jsonResponse(mediaManifest))
      .mockResolvedValueOnce(byteResponse(indexBytes))
      .mockResolvedValueOnce(jsonResponse(trace));
    vi.stubGlobal("fetch", fetchMock);
    renderPage();

    expect(screen.getByRole("status")).toHaveTextContent("読み込み中");
    expect(await screen.findByRole("heading", { level: 1, name: "AlgorithmTrace 契約デモ" })).toBeVisible();
    expect(screen.getByRole("region", { name: "アルゴリズム再生コントロール" })).toBeVisible();
    expect(screen.getByText("初期状態")).toBeVisible();
    expect(screen.getByLabelText("反復")).toHaveTextContent("0");
    expect(screen.getByLabelText("判定")).toHaveTextContent("受理");
    expect(screen.getByLabelText("イベント説明")).toHaveTextContent(
      "初期状態を評価し、完全なスナップショットを作成します。",
    );
    expect(screen.getByText("M_EDUCATIONAL")).toBeVisible();
    expect(screen.getByRole("link", { name: new RegExp(trace.source_ids[0], "u") }))
      .toHaveAttribute("href", `/sources/${trace.source_ids[0]}`);
    expect(fetchMock).toHaveBeenCalledTimes(5);
    expect(String(fetchMock.mock.calls[1][0])).toMatch(/data\/visualization-scenarios\.json$/u);
    expect(String(fetchMock.mock.calls[2][0])).toMatch(/data\/media\/manifest\.json$/u);
    expect(String(fetchMock.mock.calls[3][0])).toMatch(/data\/traces\/catalog\.json$/u);
    expect(String(fetchMock.mock.calls[4][0])).toMatch(/data\/traces\/dummy-educational\.json$/u);
  });

  test("reports missing IDs and reference mismatches instead of loading a fallback", async () => {
    vi.stubGlobal("crypto", webcrypto as Crypto);
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce(jsonResponse(manifest))
        .mockResolvedValueOnce(jsonResponse(scenarioFixture))
        .mockResolvedValueOnce(jsonResponse(mediaManifest))
        .mockResolvedValueOnce(byteResponse(indexBytes)),
    );
    renderPage("missing");
    expect(
      await screen.findByRole("heading", { level: 1, name: "ページが見つかりません" }),
    ).toBeVisible();
    expect(screen.getByText(/Trace ID/u)).toBeVisible();
    cleanup();

    const mismatch = { ...trace, dataset_version: "9.9.9" };
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce(jsonResponse(manifest))
        .mockResolvedValueOnce(jsonResponse(scenarioFixture))
        .mockResolvedValueOnce(jsonResponse(mediaManifest))
        .mockResolvedValueOnce(byteResponse(indexBytes))
        .mockResolvedValueOnce(jsonResponse(mismatch)),
    );
    renderPage();
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("dataset_version"));
  });
});
