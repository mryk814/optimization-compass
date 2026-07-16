import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import rawFailureModes from "../../../public/data/failure-modes.json";
import App from "../../App";
import type { EntityLinkIndex } from "../../contracts/entity-links";

const emptyLinks: EntityLinkIndex = {
  contract_version: "1.0.0",
  dataset_version: "0.11.0",
  generated_at: "2026-07-16T00:00:00Z",
  entities: [],
};

beforeEach(() => {
  window.location.hash = "#/failures";
  vi.stubGlobal("fetch", vi.fn().mockImplementation(async (input: string | URL | Request) => {
    const url = String(input);
    if (url.endsWith("data/failure-modes.json")) {
      return { ok: true, json: async () => rawFailureModes };
    }
    return {
      ok: true,
      json: async () => ({
        schema_version: 1,
        dataset_version: "0.11.0",
        release_date: "2026-07-16",
        database_sha256: "0e26a12b2f276dcf53ffce5626199a7fc9c7727c1feb2fe0de72f65a59864f7b",
      }),
    };
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("renders the public failure discovery route", async () => {
  render(<App initialEntityLinks={emptyLinks} />);

  expect(
    screen.getByRole("heading", { level: 1, name: "失敗の兆候から探す" }),
  ).toBeVisible();
  expect(
    await screen.findByRole("heading", { level: 2, name: "noiseが微分を支配" }),
  ).toBeVisible();
});
