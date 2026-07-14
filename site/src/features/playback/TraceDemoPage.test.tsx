import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, test, vi } from "vitest";

import {
  algorithmTraceFixture,
  traceFrameFixture,
} from "../../contracts/trace.fixtures";
import { TraceDemoPage } from "./TraceDemoPage";

const trace = {
  ...algorithmTraceFixture,
  frames: [
    { ...traceFrameFixture, event_type: "initialize", event_label_ja: "初期状態", event_label_en: "Initialize" },
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
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => index })
      .mockResolvedValueOnce({ ok: true, json: async () => trace });
    vi.stubGlobal("fetch", fetchMock);
    renderPage();

    expect(screen.getByRole("status")).toHaveTextContent("読み込み中");
    expect(await screen.findByRole("heading", { level: 1, name: "AlgorithmTrace 契約デモ" })).toBeVisible();
    expect(screen.getByRole("region", { name: "アルゴリズム再生コントロール" })).toBeVisible();
    expect(screen.getByText("初期状態")).toBeVisible();
    expect(screen.getByText("M_EDUCATIONAL")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[1][0])).toMatch(/data\/traces\/dummy-educational\.json$/u);
  });

  test("reports missing IDs and reference mismatches instead of loading a fallback", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => index }));
    renderPage("missing");
    expect(await screen.findByRole("alert")).toHaveTextContent("Trace ID");
    cleanup();

    const mismatch = { ...trace, dataset_version: "9.9.9" };
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce({ ok: true, json: async () => index })
        .mockResolvedValueOnce({ ok: true, json: async () => mismatch }),
    );
    renderPage();
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("dataset_version"));
  });
});
