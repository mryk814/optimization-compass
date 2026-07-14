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

export interface SiteManifest {
  version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  views: ManifestView[];
  recommendation: ManifestAsset;
  traces: ManifestTraceAsset;
}

export function parseSiteManifest(input: unknown): SiteManifest {
  const data = record(input, "SiteManifest");
  exactKeys(
    data,
    ["version", "dataset_version", "generated_at", "views", "recommendation", "traces"],
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
  };
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
