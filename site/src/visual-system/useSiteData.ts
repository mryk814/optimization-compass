import { useEffect, useState } from "react";

import { parseSiteData, type SiteData } from "../contracts/site-data";
import { siteBaseUrl } from "../data/base-url";

let cached: Promise<SiteData> | undefined;

/** The recommendation site data (questions, rules, predicates), fetched once per page load. */
export function loadSiteData(): Promise<SiteData> {
  cached ??= fetch(`${siteBaseUrl()}data/recommendation/site-data.json`)
    .then((response) => {
      if (!response.ok) throw new Error(`site-data request failed (${response.status}).`);
      return response.json() as Promise<unknown>;
    })
    .then(parseSiteData)
    .catch((error: unknown) => {
      cached = undefined;
      throw error;
    });
  return cached;
}

/** Undefined while loading or when the data cannot be read: lenses then show no overlay. */
export function useSiteData(): SiteData | undefined {
  const [data, setData] = useState<SiteData>();
  useEffect(() => {
    let active = true;
    void loadSiteData().then((value) => { if (active) setData(value); }, () => undefined);
    return () => { active = false; };
  }, []);
  return data;
}
