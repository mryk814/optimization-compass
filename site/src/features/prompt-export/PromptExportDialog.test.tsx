import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import rawEntityLinks from "../../../public/data/entity-links.json";
import rawFailureModes from "../../../public/data/failure-modes.json";
import rawGallery from "../../../public/data/gallery.json";
import rawManifest from "../../../public/data/manifest.json";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import { parseEntityLinkIndex } from "../../contracts/entity-links";
import { parseFailureModeIndex } from "../../contracts/failure-modes";
import { parseGalleryIndex } from "../../contracts/gallery";
import { parseSiteManifest } from "../../contracts/manifest";
import { parseSiteData } from "../../contracts/site-data";
import { createGalleryPromptDraft } from "./implementation-prompt";
import { PromptExportDialog } from "./PromptExportDialog";

function draft() {
  const gallery = parseGalleryIndex(structuredClone(rawGallery));
  const item = gallery.cases.find((entry) => entry.case_id === "EC019");
  if (!item) throw new Error("EC019 fixture is missing.");
  const data = parseSiteData(structuredClone(rawSiteData));
  return createGalleryPromptDraft({
    item,
    datasetVersion: gallery.dataset_version,
    generatedAt: "2026-07-15T05:00:00.000Z",
    support: {
      manifest: parseSiteManifest(structuredClone(rawManifest)),
      data,
      failureModes: parseFailureModeIndex(structuredClone(rawFailureModes)),
      entityLinks: parseEntityLinkIndex(structuredClone(rawEntityLinks)),
    },
  });
}

describe("PromptExportDialog", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("keeps direct Markdown edits until explicit regeneration and copies the visible text", async () => {
    const writeText = vi.fn(async () => undefined);
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
    render(<PromptExportDialog draft={draft()} onClose={vi.fn()} />);

    const dialog = screen.getByRole("dialog", { name: "実装用プロンプトを作る" });
    const presets = within(dialog).getByRole("group", { name: /作成するもの/u });
    expect(within(presets).getAllByRole("checkbox", { checked: true })).toHaveLength(3);
    expect(screen.getByLabelText("やりたいこと")).toHaveFocus();

    const preview = screen.getByLabelText("実装用プロンプトのMarkdownプレビュー");
    fireEvent.change(screen.getByLabelText(/プログラミング言語/u), { target: { value: "Python 3.12" } });
    expect((preview as HTMLTextAreaElement).value).toContain("Programming language: Python 3.12");

    fireEvent.change(preview, { target: { value: "manual final prompt" } });
    fireEvent.change(screen.getByLabelText(/問題の規模/u), { target: { value: "10,000 variables" } });
    expect(preview).toHaveValue("manual final prompt");
    expect(screen.getByRole("status")).toHaveTextContent("未反映");

    fireEvent.click(screen.getByRole("button", { name: "入力から再生成" }));
    expect((preview as HTMLTextAreaElement).value).toContain("10,000 variables");
    expect(preview).not.toHaveValue("manual final prompt");

    fireEvent.change(preview, { target: { value: "copy this exact text" } });
    fireEvent.click(screen.getByRole("button", { name: "Markdownをコピー" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("copy this exact text"));
    expect(screen.getByText("実装用プロンプトをコピーしました。")).toBeVisible();
  });

  test("reports Clipboard API failures through the live status", async () => {
    vi.stubGlobal("navigator", { ...navigator, clipboard: undefined });
    render(<PromptExportDialog draft={draft()} onClose={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Markdownをコピー" }));
    expect(await screen.findByText(/コピーできませんでした/u)).toBeVisible();
  });
});
