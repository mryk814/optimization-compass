import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { parseEntityLinkIndex, type EntityLinkIndex } from "../contracts/entity-links";
import { parseSiteManifest } from "../contracts/manifest";
import { siteBaseUrl } from "../data/base-url";

type EntityLinkState =
  | { status: "loading"; index?: undefined; error?: undefined }
  | { status: "ready"; index: EntityLinkIndex; error?: undefined }
  | { status: "error"; index?: undefined; error: Error };

const EntityLinkContext = createContext<EntityLinkState>({ status: "loading" });

export function EntityLinkProvider({ children, initialIndex }: { children: ReactNode; initialIndex?: EntityLinkIndex }) {
  const [state, setState] = useState<EntityLinkState>(
    initialIndex ? { status: "ready", index: initialIndex } : { status: "loading" },
  );
  useEffect(() => {
    if (initialIndex) return;
    const controller = new AbortController();
    void loadEntityLinks(controller.signal).then(
      (index) => setState({ status: "ready", index }),
      (caught: unknown) => {
        if (!controller.signal.aborted) {
          setState({ status: "error", error: caught instanceof Error ? caught : new Error(String(caught)) });
        }
      },
    );
    return () => controller.abort();
  }, [initialIndex]);
  const value = useMemo(() => state, [state]);
  return <EntityLinkContext.Provider value={value}>{children}</EntityLinkContext.Provider>;
}

export function useEntityLinks(): EntityLinkState {
  return useContext(EntityLinkContext);
}

async function loadEntityLinks(signal: AbortSignal): Promise<EntityLinkIndex> {
  const manifestResponse = await fetch(`${siteBaseUrl()}data/manifest.json`, { signal });
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());
  const response = await fetch(`${siteBaseUrl()}data/${manifest.entity_links.path}`, { signal });
  if (!response.ok) throw new Error(`Entity link index request failed (${response.status}).`);
  const index = parseEntityLinkIndex(await response.json());
  if (index.dataset_version !== manifest.dataset_version) {
    throw new Error("Entity link index dataset version does not match the manifest.");
  }
  return index;
}
