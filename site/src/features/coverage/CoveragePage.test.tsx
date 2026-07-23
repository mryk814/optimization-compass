import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import rawCoverage from "../../../public/data/coverage.json";
import rawJourneys from "../../../public/data/learning-journeys.json";
import rawManifest from "../../../public/data/manifest.json";
import { CoveragePage } from "./CoveragePage";

describe("CoveragePage", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => ({
    ok: true,
    json: async () => String(input).endsWith("manifest.json")
      ? structuredClone(rawManifest)
      : String(input).endsWith("learning-journeys.json")
        ? structuredClone(rawJourneys)
        : structuredClone(rawCoverage),
  }) as Response)));
  afterEach(() => vi.unstubAllGlobals());

  test("shows priority reasons and filters the full inventory", async () => {
    render(<MemoryRouter><CoveragePage /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Atlasの接続状況" })).toBeVisible();
    expect(screen.getByText(/言語範囲:/u)).toBeVisible();
    expect(screen.getByText(/日本語の説明を基準に監査します/u)).toBeVisible();
    expect(screen.getByRole("heading", { name: "学習経路の接続状況" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "参照整合性" })).toBeVisible();
    expect(screen.getByText(/これは学習経路が完了しているという意味ではありません/u)).toBeVisible();
    expect(screen.getByText(`${rawJourneys.summary.status_counts.complete}件完了`)).toBeVisible();
    expect(screen.getByText(/目標5件を達成/u)).toBeVisible();
    expect(screen.getByRole("region", { name: "学習経路の接続状況一覧" })).toBeVisible();
    expect(screen.getByText(/未接続の成果物:/u)).toBeVisible();
    expect(screen.queryByText(new RegExp(rawJourneys.orphan_assets[0].asset_id, "u"))).not.toBeInTheDocument();
    expect(screen.getByText(`${rawCoverage.subjects.length}件中24件を表示`)).toBeVisible();
    const inventory = screen.getByRole("region", { name: "成果物一覧の表" });
    expect(inventory).toHaveAttribute("tabindex", "0");
    expect(inventory.querySelectorAll("tr")).toHaveLength(25);
    expect(screen.getAllByText(/\/9$/u).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "技術情報を表示" }));
    expect(screen.getByText(new RegExp(rawJourneys.orphan_assets[0].asset_id, "u"))).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("対象種別"), { target: { value: "feature_family" } });
    expect(inventory.querySelectorAll("tr")).toHaveLength(11);
    fireEvent.change(screen.getByLabelText("状態"), { target: { value: "missing" } });
    expect(inventory.querySelectorAll("tr")).toHaveLength(1);
  });
});
