import { TRACE_CONTRACT_VERSION } from "./trace";

export interface ManifestView {
  view_id: string;
  version: "1.0.0";
  path: string;
}

export interface ManifestAsset<Version extends string = "1.0.0"> {
  version: Version;
  path: string;
}

export interface ManifestRecommendationAsset {
  version: "2.0.0";
  path: string;
}

export interface ManifestTraceAsset {
  contract_version: typeof TRACE_CONTRACT_VERSION;
  index_version: typeof TRACE_CONTRACT_VERSION;
  path: string;
  bytes: number;
  sha256: string;
}

export interface ManifestCoverageAsset extends ManifestAsset {
  path: "coverage.json";
  report_path: "coverage.md";
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
  version: "1.4.0";
  dataset_version: string;
  generated_at: string;
  views: ManifestView[];
  recommendation: ManifestRecommendationAsset;
  traces: ManifestTraceAsset;
  problems: ManifestAsset;
  learning_journeys: ManifestAsset<"1.1.0">;
  formulation_primer: ManifestAsset;
  visualization_scenarios: ManifestAsset<"1.2.0">;
  derived_media: ManifestAsset<"1.1.0">;
  entity_links: ManifestAsset;
  sources: ManifestAsset;
  implementation_claims: ManifestAsset;
  benchmark_contexts: ManifestAsset;
  failure_modes: ManifestAsset;
  failure_discovery: ManifestAsset;
  release_catalog: ManifestAsset;
  search_index: ManifestAsset;
  retrieval_documents: ManifestAsset;
  search_benchmark: ManifestAsset;
  coverage: ManifestCoverageAsset;
  licenses: SiteLicenseManifest;
}

export function parseSiteManifest(input: unknown): SiteManifest {
  const data = record(input, "SiteManifest");
  exactKeys(
    data,
    [
      "version",
      "dataset_version",
      "generated_at",
      "views",
      "recommendation",
      "traces",
      "problems",
      "learning_journeys",
      "formulation_primer",
      "visualization_scenarios",
      "derived_media",
      "entity_links",
      "sources",
      "implementation_claims",
      "benchmark_contexts",
      "failure_modes",
      "failure_discovery",
      "release_catalog",
      "search_index",
      "retrieval_documents",
      "search_benchmark",
      "coverage",
      "licenses",
    ],
    "SiteManifest",
  );
  if (data.version !== "1.4.0") throw new Error("Unsupported SiteManifest version.");

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
  if (recommendation.version !== "2.0.0") throw new Error("recommendation.version is unsupported.");

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
  const problems = record(data.problems, "problems");
  exactKeys(problems, ["version", "path"], "problems");
  if (problems.version !== "1.0.0") throw new Error("problems.version is unsupported.");
  const learningJourneys = record(data.learning_journeys, "learning_journeys");
  exactKeys(learningJourneys, ["version", "path"], "learning_journeys");
  if (learningJourneys.version !== "1.1.0") throw new Error("learning_journeys.version is unsupported.");
  const formulationPrimer = record(data.formulation_primer, "formulation_primer");
  exactKeys(formulationPrimer, ["version", "path"], "formulation_primer");
  if (formulationPrimer.version !== "1.0.0") throw new Error("formulation_primer.version is unsupported.");
  const entityLinks = record(data.entity_links, "entity_links");
  exactKeys(entityLinks, ["version", "path"], "entity_links");
  if (entityLinks.version !== "1.0.0") throw new Error("entity_links.version is unsupported.");
  const sources = record(data.sources, "sources");
  exactKeys(sources, ["version", "path"], "sources");
  if (sources.version !== "1.0.0") throw new Error("sources.version is unsupported.");
  const implementationClaims = record(data.implementation_claims, "implementation_claims");
  exactKeys(implementationClaims, ["version", "path"], "implementation_claims");
  if (implementationClaims.version !== "1.0.0") {
    throw new Error("implementation_claims.version is unsupported.");
  }
  const benchmarkContexts = record(data.benchmark_contexts, "benchmark_contexts");
  exactKeys(benchmarkContexts, ["version", "path"], "benchmark_contexts");
  if (benchmarkContexts.version !== "1.0.0") {
    throw new Error("benchmark_contexts.version is unsupported.");
  }
  const failureModes = record(data.failure_modes, "failure_modes");
  exactKeys(failureModes, ["version", "path"], "failure_modes");
  if (failureModes.version !== "1.0.0") throw new Error("failure_modes.version is unsupported.");
  const failureDiscovery = record(data.failure_discovery, "failure_discovery");
  exactKeys(failureDiscovery, ["version", "path"], "failure_discovery");
  if (failureDiscovery.version !== "1.0.0") throw new Error("failure_discovery.version is unsupported.");
  const releaseCatalog = record(data.release_catalog, "release_catalog");
  exactKeys(releaseCatalog, ["version", "path"], "release_catalog");
  if (releaseCatalog.version !== "1.0.0") throw new Error("release_catalog.version is unsupported.");
  const searchIndex = record(data.search_index, "search_index");
  exactKeys(searchIndex, ["version", "path"], "search_index");
  if (searchIndex.version !== "1.0.0") throw new Error("search_index.version is unsupported.");
  const retrievalDocuments = record(data.retrieval_documents, "retrieval_documents");
  exactKeys(retrievalDocuments, ["version", "path"], "retrieval_documents");
  if (retrievalDocuments.version !== "1.0.0") throw new Error("retrieval_documents.version is unsupported.");
  const searchBenchmark = record(data.search_benchmark, "search_benchmark");
  exactKeys(searchBenchmark, ["version", "path"], "search_benchmark");
  if (searchBenchmark.version !== "1.0.0") throw new Error("search_benchmark.version is unsupported.");
  const visualizationScenarios = record(data.visualization_scenarios, "visualization_scenarios");
  exactKeys(visualizationScenarios, ["version", "path"], "visualization_scenarios");
  if (visualizationScenarios.version !== "1.2.0") {
    throw new Error("visualization_scenarios.version is unsupported.");
  }
  const derivedMedia = record(data.derived_media, "derived_media");
  exactKeys(derivedMedia, ["version", "path"], "derived_media");
  if (derivedMedia.version !== "1.1.0" || derivedMedia.path !== "media/manifest.json") {
    throw new Error("derived_media is unsupported.");
  }
  const coverage = record(data.coverage, "coverage");
  exactKeys(coverage, ["version", "path", "report_path"], "coverage");
  if (coverage.version !== "1.0.0") throw new Error("coverage.version is unsupported.");
  if (coverage.path !== "coverage.json" || coverage.report_path !== "coverage.md") {
    throw new Error("coverage paths are invalid.");
  }

  return {
    version: "1.4.0",
    dataset_version: nonEmptyString(data.dataset_version, "dataset_version"),
    generated_at: nonEmptyString(data.generated_at, "generated_at"),
    views,
    recommendation: {
      version: "2.0.0",
      path: safeRelativePath(recommendation.path, "recommendation.path"),
    },
    traces: {
      contract_version: TRACE_CONTRACT_VERSION,
      index_version: TRACE_CONTRACT_VERSION,
      path: safeRelativePath(traces.path, "traces.path"),
      bytes,
      sha256,
    },
    problems: {
      version: "1.0.0",
      path: safeRelativePath(problems.path, "problems.path"),
    },
    learning_journeys: {
      version: "1.1.0",
      path: safeRelativePath(learningJourneys.path, "learning_journeys.path"),
    },
    formulation_primer: {
      version: "1.0.0",
      path: safeRelativePath(formulationPrimer.path, "formulation_primer.path"),
    },
    visualization_scenarios: {
      version: "1.2.0",
      path: safeRelativePath(visualizationScenarios.path, "visualization_scenarios.path"),
    },
    derived_media: {
      version: "1.1.0",
      path: safeRelativePath(derivedMedia.path, "derived_media.path"),
    },
    entity_links: {
      version: "1.0.0",
      path: safeRelativePath(entityLinks.path, "entity_links.path"),
    },
    sources: {
      version: "1.0.0",
      path: safeRelativePath(sources.path, "sources.path"),
    },
    implementation_claims: {
      version: "1.0.0",
      path: safeRelativePath(implementationClaims.path, "implementation_claims.path"),
    },
    benchmark_contexts: {
      version: "1.0.0",
      path: safeRelativePath(benchmarkContexts.path, "benchmark_contexts.path"),
    },
    failure_modes: {
      version: "1.0.0",
      path: safeRelativePath(failureModes.path, "failure_modes.path"),
    },
    failure_discovery: {
      version: "1.0.0",
      path: safeRelativePath(failureDiscovery.path, "failure_discovery.path"),
    },
    release_catalog: {
      version: "1.0.0",
      path: safeRelativePath(releaseCatalog.path, "release_catalog.path"),
    },
    search_index: {
      version: "1.0.0",
      path: safeRelativePath(searchIndex.path, "search_index.path"),
    },
    retrieval_documents: {
      version: "1.0.0",
      path: safeRelativePath(retrievalDocuments.path, "retrieval_documents.path"),
    },
    search_benchmark: {
      version: "1.0.0",
      path: safeRelativePath(searchBenchmark.path, "search_benchmark.path"),
    },
    coverage: { version: "1.0.0", path: "coverage.json", report_path: "coverage.md" },
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
