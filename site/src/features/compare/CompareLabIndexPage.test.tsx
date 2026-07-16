import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import comparisons from "../../../public/data/comparisons.json";
import { CompareLabIndexPage } from "./CompareLabIndexPage";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("CompareLabIndexPage", () => {
  test("loads and exposes every comparison preset", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => structuredClone(comparisons),
    }));

    render(<MemoryRouter><CompareLabIndexPage /></MemoryRouter>);

    expect(await screen.findByRole("heading", { level: 1, name: "Compare Lab" })).toBeVisible();
    expect(screen.getByRole("link", { name: /細長い谷で一次法を比べる/u })).toHaveAttribute(
      "href",
      "/compare/COMPARE_GRADIENT_FAMILY",
    );
    expect(screen.getByRole("link", { name: /学習率を変えたときの発散を観察する/u })).toHaveAttribute(
      "href",
      "/compare/COMPARE_GRADIENT_DIVERGENCE",
    );
  });
});
