import { TRACE_CONTRACT_VERSION } from "./trace";

export interface ManifestView {
  view_id: string;
  version: "1.0.0";
  path: string;
}

export interface ManifestAsset {
  version: "1.0.0";
  path: string;
}

export interface ManifestTraceAsset {
  contract_version: typeof TRACE_CONTRACT_VERSION;
  index_version: typeof TRACE_CONTRACT_VERSION;
  path: string;
  bytes: number;
  sha256: string;
}

export interface ManifestLicenseAsset {
  spdx_id: "MIT" | "CC-BY-4.0";
  path: string;
}

export interface SiteLicenseManifest {
  code: ManifestLicenseAsset;
  data: ManifestLicenseAsset;
  content: ManifestLicenseAsset;
  legal_code_path: string;
  notice_path: string;
  attribution: string;
}

export interface SiteManifest {
  version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  views: ManifestView[];
  recommendation: ManifestAsset;
  traces: ManifestTraceAsset;
  entity_links: ManifestAsset;
  sources: ManifestAsset;
  licenses: SiteLicenseManifest;
}

export function parseSiteManifest(input: unknown): SiteManifest {
  const data = record(input, "SiteManifest");
  exactKeys(
    data,
    ["version", "dataset_version", "generated_at", "views", "recommendation", "traces", "entity_links", "sources", "licenses"],
    "SiteManifest",
  );
  if (data.version !== "1.0.0") throw new Error("Unsupported SiteManifest version.");

  const views = array(data.views, "views").map((value, index): ManifestView => {
    const view = record(value, `views[${index}]`);
    exactKeys(view, ["view_id", "version", "path"], `views[${index}]`);
    if (view.version !== "1.0.0") throw new Error(`views[${index}].version is unsupported.`);
    return {
      view_id: nonEmptyString(view.view_id, `views[${index}].view_id`),
      version: "1.0.0",
      path: safeRelativePath(view.path, `views[${index}].path`),
    };
  });
  if (views.length === 0) throw new Error("views must not be empty.");

  const recommendation = record(data.recommendation, "recommendation");
  exactKeys(recommendation, ["version", "path"], "recommendation");
  if (recommendation.version !== "1.0.0") throw new Error("recommendation.version is unsupported.");

  const traces = record(data.traces, "traces");
  exactKeys(
    traces,
    ["contract_version", "index_version", "path", "bytes", "sha256"],
    "traces",
  );
  if (traces.contract_version !== TRACE_CONTRACT_VERSION) {
    throw new Error("traces.contract_version is unsupported.");
  }
  if (traces.index_version !== TRACE_CONTRACT_VERSION) {
    throw new Error("traces.index_version is unsupported.");
  }
  const bytes = positiveInteger(traces.bytes, "traces.bytes");
  const sha256 = nonEmptyString(traces.sha256, "traces.sha256");
  if (!/^[0-9a-f]{64}$/u.test(sha256)) throw new Error("traces.sha256 is invalid.");

  const licenses = parseLicenses(data.licenses);
  const entityLinks = record(data.entity_links, "entity_links");
  exactKeys(entityLinks, ["version", "path"], "entity_links");
  if (entityLinks.version !== "1.0.0") throw new Error("entity_links.version is unsupported.");
  const sources = record(data.sources, "sources");
  exactKeys(sources, ["version", "path"], "sources");
  if (sources.version !== "1.0.0") throw new Error("sources.version is unsupported.");

  return {
    version: "1.0.0",
    dataset_version: nonEmptyString(data.dataset_version, "dataset_version"),
    generated_at: nonEmptyString(data.generated_at, "generated_at"),
    views,
    recommendation: {
      version: "1.0.0",
      path: safeRelativePath(recommendation.path, "recommendation.path"),
    },
    traces: {
      contract_version: TRACE_CONTRACT_VERSION,
      index_version: TRACE_CONTRACT_VERSION,
      path: safeRelativePath(traces.path, "traces.path"),
      bytes,
      sha256,
    },
    entity_links: {
      version: "1.0.0",
      path: safeRelativePath(entityLinks.path, "entity_links.path"),
    },
    sources: {
      version: "1.0.0",
      path: safeRelativePath(sources.path, "sources.path"),
    },
    licenses,
  };
}

function parseLicenses(value: unknown): SiteLicenseManifest {
  const data = record(value, "licenses");
  exactKeys(
    data,
    ["code", "data", "content", "legal_code_path", "notice_path", "attribution"],
    "licenses",
  );
  return {
    code: parseLicenseAsset(data.code, "licenses.code", "MIT"),
    data: parseLicenseAsset(data.data, "licenses.data", "CC-BY-4.0"),
    content: parseLicenseAsset(data.content, "licenses.content", "CC-BY-4.0"),
    legal_code_path: safeLicensePath(data.legal_code_path, "licenses.legal_code_path"),
    notice_path: safeLicensePath(data.notice_path, "licenses.notice_path"),
    attribution: nonEmptyString(data.attribution, "licenses.attribution"),
  };
}

function parseLicenseAsset(
  value: unknown,
  field: string,
  expectedSpdx: "MIT" | "CC-BY-4.0",
): ManifestLicenseAsset {
  const data = record(value, field);
  exactKeys(data, ["spdx_id", "path"], field);
  if (data.spdx_id !== expectedSpdx) throw new Error(`${field}.spdx_id is invalid.`);
  return { spdx_id: expectedSpdx, path: safeLicensePath(data.path, `${field}.path`) };
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${field} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function exactKeys(data: Record<string, unknown>, expected: readonly string[], field: string): void {
  const expectedSet = new Set(expected);
  const unknown = Object.keys(data).filter((key) => !expectedSet.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key));
  if (unknown.length > 0) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`);
  if (missing.length > 0) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`);
}

function array(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value;
}

function nonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${field} must be non-empty.`);
  }
  return value;
}

function positiveInteger(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value <= 0) {
    throw new Error(`${field} must be a positive integer.`);
  }
  return value;
}

function safeRelativePath(value: unknown, field: string): string {
  const path = nonEmptyString(value, field);
  if (!/^[a-z0-9][a-z0-9._/-]*\.json$/u.test(path) || path.includes("//") || path.split("/").includes("..")) {
    throw new Error(`${field} must be a safe relative JSON path.`);
  }
  return path;
}

function safeLicensePath(value: unknown, field: string): string {
  const path = nonEmptyString(value, field);
  if (!/^licenses\/[A-Z0-9._-]+\.txt$/u.test(path)) {
    throw new Error(`${field} must be a safe license text path.`);
  }
  return path;
}
