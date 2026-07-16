import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, test, vi } from "vitest";

import rawFailureModes from "../../../public/data/failure-modes.json";
import type { EntityLinkIndex } from "../../contracts/entity-links";
import { EntityLinkProvider } from "../../state/entity-links";
import { FailureModePage } from "./FailureModePage";

const emptyLinks: EntityLinkIndex = {
  contract_version: "1.0.0",
  dataset_version: "0.11.0",
  generated_at: "2026-07-16T00:00:00Z",
  entities: [],
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("FailureModePage", () => {
  test("starts from symptoms and keeps detailed relations collapsed", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => rawFailureModes,
    }));

    render(
      <MemoryRouter>
        <EntityLinkProvider initialIndex={emptyLinks}>
          <FailureModePage />
        </EntityLinkProvider>
      </MemoryRouter>,
    );

    const card = (await screen.findByRole("heading", {
      level: 2,
      name: "noiseが微分を支配",
    })).closest("article");
    expect(card).not.toBeNull();
    expect(within(card!).getByText("gradient符号がreplicateで変わる")).toBeVisible();
    expect(within(card!).getByText("replication/CRN")).toBeVisible();
    expect(within(card!).getByText("sample average、SPSA、noise-aware method")).toBeVisible();
    expect(within(card!).getByText("影響する手法・可視化・根拠")).not.toHaveAttribute("open");
  });

  test("filters the canonical failure list by symptom or title", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => rawFailureModes,
    }));

    render(
      <MemoryRouter>
        <EntityLinkProvider initialIndex={emptyLinks}>
          <FailureModePage />
        </EntityLinkProvider>
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { level: 2, name: "noiseが微分を支配" });
    fireEvent.change(screen.getByRole("searchbox", { name: "失敗の兆候を検索" }), {
      target: { value: "悪条件" },
    });

    expect(screen.getByRole("heading", { level: 2, name: "悪条件" })).toBeVisible();
    expect(screen.queryByRole("heading", { level: 2, name: "noiseが微分を支配" })).not.toBeInTheDocument();
  });
});
