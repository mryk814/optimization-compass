import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { FailureDiscoveryPage } from "./FailureDiscoveryPage";

const payload = {
  contract_version: "1.0.0",
  dataset_version: "test",
  generated_at: "2026-07-17T00:00:00Z",
  entries: [
    {
      entry_id: "failure:FM001",
      kind: "structured_failure",
      disposition: "warning",
      title: "勾配が不安定",
      summary: "符号が反復ごとに変わる",
      severity: "high",
      confidence: "high",
      trigger: "noiseが大きい",
      symptoms: ["符号が反復ごとに変わる"],
      diagnostics: ["同一点を再評価する"],
      mitigations: ["noise-awareな評価へ切り替える"],
      observable_ids: ["gradient_direction"],
      method_ids: ["M_BFGS"],
      implementation_ids: [],
      case_ids: [],
      scenario_ids: ["SCENARIO_NOISY_GRADIENT"],
      source_ids: ["S001"],
      canonical_url: "/failures?entry=FM001",
      search_text: "勾配が不安定 符号が反復ごとに変わる noise BFGS",
    },
    {
      entry_id: "exclusion:case-1:M_BFGS",
      kind: "case_exclusion",
      disposition: "excluded",
      title: "離散割当では除外",
      summary: "離散変数を直接扱えない",
      severity: "contextual",
      confidence: "authored",
      trigger: "0/1割当を決める",
      symptoms: ["離散変数を直接扱えない"],
      diagnostics: [],
      mitigations: [],
      observable_ids: [],
      method_ids: ["M_BFGS"],
      implementation_ids: [],
      case_ids: ["case-1"],
      scenario_ids: [],
      source_ids: ["S002"],
      canonical_url: "/gallery/case-1",
      search_text: "離散割当 BFGS 離散変数を直接扱えない",
    },
  ],
};

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => payload,
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("FailureDiscoveryPage", () => {
  test("shows compact warning and Case-exclusion paths", async () => {
    render(<MemoryRouter><FailureDiscoveryPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1, name: "失敗の兆候から探す" })).toBeVisible();
    expect(await screen.findByRole("heading", { level: 2, name: "勾配が不安定" })).toBeVisible();
    expect(screen.getByRole("heading", { level: 2, name: "離散割当では除外" })).toBeVisible();
    expect(screen.getByText("同一点を再評価する")).toBeVisible();
    expect(screen.getByText("noise-awareな評価へ切り替える")).toBeVisible();
    expect(screen.getByText("このCaseで選ばない理由")).toBeVisible();
  });

  test("filters contextual exclusions without presenting a universal blacklist", async () => {
    render(<MemoryRouter><FailureDiscoveryPage /></MemoryRouter>);
    await screen.findByRole("heading", { level: 2, name: "勾配が不安定" });

    fireEvent.click(screen.getByRole("radio", { name: "Case固有の除外" }));

    expect(screen.queryByRole("heading", { level: 2, name: "勾配が不安定" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "離散割当では除外" })).toBeVisible();
    expect(screen.getByText(/万能なblacklistではありません/u)).toBeVisible();
  });

  test("searches the generated normalized text", async () => {
    render(<MemoryRouter><FailureDiscoveryPage /></MemoryRouter>);
    await screen.findByRole("heading", { level: 2, name: "勾配が不安定" });

    const controls = screen.getByRole("region", { name: "失敗・除外の絞り込み" });
    fireEvent.change(within(controls).getByRole("searchbox"), { target: { value: "離散変数" } });

    expect(screen.queryByRole("heading", { level: 2, name: "勾配が不安定" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "離散割当では除外" })).toBeVisible();
  });
});
