import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import rawCoverage from "../../../public/data/coverage.json";
import rawManifest from "../../../public/data/manifest.json";
import { CoveragePage } from "./CoveragePage";

describe("CoveragePage", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => ({
    ok: true,
    json: async () => String(input).endsWith("manifest.json")
      ? structuredClone(rawManifest)
      : structuredClone(rawCoverage),
  }) as Response)));
  afterEach(() => vi.unstubAllGlobals());

  test("shows priority reasons and filters the full inventory", async () => {
    render(<MemoryRouter><CoveragePage /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Atlas Coverage" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Artifact inventory table" })).toHaveAttribute("tabindex", "0");
    expect(screen.getAllByText(/12$/u).length).toBeGreaterThan(0);
    fireEvent.change(screen.getByLabelText("Subject"), { target: { value: "feature_family" } });
    expect(screen.getAllByRole("row")).toHaveLength(11);
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "missing" } });
    expect(screen.getAllByRole("row")).toHaveLength(1);
  });
});
