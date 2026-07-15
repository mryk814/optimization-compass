import { parseEntityLinkIndex, type EntityLinkIndex } from "../../contracts/entity-links";
import { parseFailureModeIndex, type FailureModeIndex } from "../../contracts/failure-modes";
import { parseSiteManifest, type SiteManifest } from "../../contracts/manifest";
import { parseSiteData, type SiteData } from "../../contracts/site-data";
import { siteBaseUrl } from "../../data/base-url";

export interface PromptSupportData {
  manifest: SiteManifest;
  data: SiteData;
  failureModes: FailureModeIndex;
  entityLinks: EntityLinkIndex;
}

export interface PreloadedPromptData {
  manifest?: SiteManifest;
  data?: SiteData;
}

async function fetchJson(path: string): Promise<unknown> {
  const response = await fetch(`${siteBaseUrl()}data/${path}`);
  if (!response.ok) throw new Error(`Prompt support data request failed (${response.status}): ${path}`);
  return response.json() as Promise<unknown>;
}

export async function loadPromptSupportData(
  expectedDatasetVersion: string,
  preloaded: PreloadedPromptData = {},
): Promise<PromptSupportData> {
  const manifest = preloaded.manifest ?? parseSiteManifest(await fetchJson("manifest.json"));
  if (manifest.dataset_version !== expectedDatasetVersion) {
    throw new Error(
      `Prompt dataset version mismatch: expected ${expectedDatasetVersion}, manifest is ${manifest.dataset_version}.`,
    );
  }

  const [data, failureModes, entityLinks] = await Promise.all([
    preloaded.data
      ? Promise.resolve(preloaded.data)
      : fetchJson(manifest.recommendation.path).then(parseSiteData),
    fetchJson(manifest.failure_modes.path).then(parseFailureModeIndex),
    fetchJson(manifest.entity_links.path).then(parseEntityLinkIndex),
  ]);

  const versions = {
    recommendation: data.dataset_version,
    failure_modes: failureModes.dataset_version,
    entity_links: entityLinks.dataset_version,
  };
  const mismatch = Object.entries(versions).find(([, version]) => version !== expectedDatasetVersion);
  if (mismatch) {
    throw new Error(
      `Prompt dataset version mismatch: ${mismatch[0]} is ${mismatch[1]}, expected ${expectedDatasetVersion}.`,
    );
  }

  return { manifest, data, failureModes, entityLinks };
}
