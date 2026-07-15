import { useRef, useState } from "react";

import type { GalleryCase } from "../../contracts/gallery";
import type { SiteManifest } from "../../contracts/manifest";
import type { SiteData } from "../../contracts/site-data";
import type { AtlasStateV1 } from "../../state/atlas-state";
import type { RecommendationResult } from "../diagnose/recommend";
import {
  createDiagnosePromptDraft,
  createGalleryPromptDraft,
  type ImplementationPromptDraft,
} from "./implementation-prompt";
import { PromptExportDialog } from "./PromptExportDialog";
import { loadPromptSupportData } from "./support-data";

type PromptSource =
  | {
      kind: "diagnose";
      state: AtlasStateV1;
      result: RecommendationResult;
      manifest: SiteManifest;
      data: SiteData;
    }
  | {
      kind: "gallery";
      item: GalleryCase;
      datasetVersion: string;
    };

export function PromptExportLauncher({ source }: { source: PromptSource }) {
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [draft, setDraft] = useState<ImplementationPromptDraft>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error>();

  const open = async () => {
    setLoading(true);
    setError(undefined);
    const generatedAt = new Date().toISOString();
    try {
      if (source.kind === "diagnose") {
        const support = await loadPromptSupportData(source.data.dataset_version, {
          manifest: source.manifest,
          data: source.data,
        });
        setDraft(createDiagnosePromptDraft({
          state: source.state,
          result: source.result,
          support,
          generatedAt,
        }));
      } else {
        const support = await loadPromptSupportData(source.datasetVersion);
        setDraft(createGalleryPromptDraft({
          item: source.item,
          datasetVersion: source.datasetVersion,
          support,
          generatedAt,
        }));
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught : new Error(String(caught)));
    } finally {
      setLoading(false);
    }
  };

  const close = () => {
    setDraft(undefined);
    triggerRef.current?.focus({ preventScroll: true });
  };

  return (
    <div className="prompt-export-launcher">
      <button disabled={loading} onClick={() => void open()} ref={triggerRef} type="button">
        {loading ? "プロンプトを準備中…" : "実装用プロンプトを作る"}
      </button>
      {error && <p className="prompt-export-error" role="alert">{error.message}</p>}
      {draft && <PromptExportDialog draft={draft} onClose={close} />}
    </div>
  );
}
