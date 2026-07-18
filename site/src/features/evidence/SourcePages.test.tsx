import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import rawManifest from "../../../public/data/manifest.json";
import { SourceDetailPage, SourceIndexPage } from "./SourcePages";

const target = {
  evidence_link_id: "EL1", target_table: "methods", target_id: "M1", target_type: "method",
  label: "Nelder–Mead", canonical_url: "/methods/M1", external_url: null, supported_field: "row",
  claim_summary: "Method definition", evidence_role: "primary", confidence: "high", last_verified: "2026-07-13",
};
const sourceIndex = {
  contract_version: "1.0.0", dataset_version: rawManifest.dataset_version, generated_at: rawManifest.generated_at,
  freshness_policy: [{ source_type: "official_documentation", max_age_days: 90 }],
  sources: [{ source_id: "S1", source_type: "official_documentation", title: "Official docs", publisher: "Project", publication_date: null, last_verified: "2026-07-13", official_url: "https://example.com/docs", license: "unknown", access_note: "Check official terms.", supported_claim: "API", source_quality: "primary", currentness_status: "verified_current", evidence_targets: [target] }],
};

describe("source pages", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => ({ ok: true, json: async () => String(input).endsWith("manifest.json") ? structuredClone(rawManifest) : structuredClone(sourceIndex) }) as Response)));
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

  test("lists source title and verification date", async () => {
    render(<MemoryRouter><SourceIndexPage /></MemoryRouter>);
    expect(await screen.findByRole("link", { name: "Official docs" })).toHaveAttribute("href", "/sources/S1");
    expect(screen.getByText(/確認日 2026-07-13/u)).toBeVisible();
  });

  test("shows official metadata and backlink to the evidence target", async () => {
    render(<MemoryRouter initialEntries={["/sources/S1"]}><Routes><Route path="/sources/:sourceId" element={<SourceDetailPage />} /></Routes></MemoryRouter>);
    expect(await screen.findByRole("heading", { level: 1, name: "Official docs" })).toBeVisible();
    expect(screen.getByText("2026-07-13")).toBeVisible();
    expect(screen.getByText("不明")).toBeVisible();
    expect(screen.getByRole("link", { name: /Nelder–Mead/u })).toHaveAttribute("href", "/methods/M1");
    expect(screen.getByRole("link", { name: "公式資料を開く" })).toHaveAttribute("href", "https://example.com/docs");
  });
});
