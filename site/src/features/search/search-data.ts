import { parseSiteManifest } from "../../contracts/manifest";
import { parseSearchIndex, type SearchIndex } from "../../contracts/search-index";
import { siteBaseUrl } from "../../data/base-url";

let cache: Promise<SearchIndex> | undefined;

export function loadSearchIndex(): Promise<SearchIndex> {
  cache ??= fetchSearchIndex();
  return cache;
}

export function resetSearchIndexCache(): void {
  cache = undefined;
}

async function fetchSearchIndex(): Promise<SearchIndex> {
  const base = `${siteBaseUrl()}data/`;
  const manifestResponse = await fetch(`${base}manifest.json`);
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());
  const response = await fetch(`${base}${manifest.search_index.path}`);
  if (!response.ok) throw new Error(`Search index request failed (${response.status}).`);
  const index = parseSearchIndex(await response.json());
  if (index.dataset_version !== manifest.dataset_version) {
    throw new Error("Search index dataset version does not match the manifest.");
  }
  return index;
}
