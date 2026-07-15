import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import rawEntityLinks from "../../../public/data/entity-links.json";
import rawFailureModes from "../../../public/data/failure-modes.json";
import rawGallery from "../../../public/data/gallery.json";
import rawManifest from "../../../public/data/manifest.json";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import { parseGalleryIndex } from "../../contracts/gallery";
import { parseSiteManifest } from "../../contracts/manifest";
import { parseSiteData } from "../../contracts/site-data";
import { toRecommendationAnswers } from "../../state/atlas-state";
import { recommend } from "../diagnose/recommend";
import { caseState } from "../gallery/GalleryPage";
import { PromptExportLauncher } from "./PromptExportLauncher";

function item() {
  const found = parseGalleryIndex(structuredClone(rawGallery)).cases.find((entry) => entry.case_id === "EC019");
  if (!found) throw new Error("EC019 fixture is missing.");
  return found;
}

function mockPromptData() {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    const body = url.endsWith("manifest.json")
      ? rawManifest
      : url.endsWith("recommendation/site-data.json")
        ? rawSiteData
        : url.endsWith("failure-modes.json")
          ? rawFailureModes
          : url.endsWith("entity-links.json")
            ? rawEntityLinks
            : undefined;
    return body
      ? { ok: true, json: async () => structuredClone(body) } as Response
      : { ok: false, status: 404 } as Response;
  }));
}

describe("PromptExportLauncher", () => {
  beforeEach(mockPromptData);
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("opens a prefilled Gallery pack without sending user data and restores trigger focus", async () => {
    const galleryItem = item();
    render(<PromptExportLauncher source={{ kind: "gallery", item: galleryItem, datasetVersion: rawGallery.dataset_version }} />);
    const trigger = screen.getByRole("button", { name: "実装用プロンプトを作る" });
    trigger.focus();
    fireEvent.click(trigger);

    expect(await screen.findByRole("dialog", { name: "実装用プロンプトを作る" })).toBeVisible();
    expect(screen.getByLabelText("やりたいこと")).toHaveValue(galleryItem.question);
    expect(screen.getByLabelText("Programming language")).toHaveValue("unknown");
    expect(vi.mocked(fetch).mock.calls.every((call) => call.length === 1)).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "実装用プロンプトを閉じる" }));
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  test("uses the exact current Diagnose state and recommendation result", async () => {
    const data = parseSiteData(structuredClone(rawSiteData));
    const manifest = parseSiteManifest(structuredClone(rawManifest));
    const state = caseState(item(), data.dataset_version);
    const result = recommend(data, toRecommendationAnswers(state), { expected_dataset_version: data.dataset_version });
    render(<PromptExportLauncher source={{ kind: "diagnose", state, result, manifest, data }} />);

    fireEvent.click(screen.getByRole("button", { name: "実装用プロンプトを作る" }));
    const preview = await screen.findByLabelText("実装用プロンプトのMarkdown preview");
    expect((preview as HTMLTextAreaElement).value).toContain(`Atlas origin: Diagnose (${result.answered_question_count} answered)`);
    expect((preview as HTMLTextAreaElement).value).toContain("Alternative-first checks");
    expect((preview as HTMLTextAreaElement).value).toContain("Excluded methods");
  });
});
