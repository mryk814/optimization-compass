export interface ReleaseBundleDescriptor {
  url: string;
  sha256: string;
  size_bytes: number;
}

export interface ReleaseArchiveDescriptor {
  provider: string;
  identifier: string;
  url: string;
}

export interface ReleaseCatalogEntry {
  version: string;
  release_date: string;
  database_sha256: string;
  manifest_sha256: string;
  source_commit: string;
  tag: string;
  bundle: ReleaseBundleDescriptor;
  archival: ReleaseArchiveDescriptor | null;
}

export interface ReleaseCatalog {
  schema_version: 1;
  current_version: string;
  releases: ReleaseCatalogEntry[];
}

export function parseReleaseCatalog(input: unknown): ReleaseCatalog {
  const data = record(input, "release catalog");
  exact(data, ["schema_version", "current_version", "releases"], "release catalog");
  if (data.schema_version !== 1) throw new Error("Unsupported release catalog schema.");
  const currentVersion = semanticVersion(data.current_version, "current_version");
  const releases = array(data.releases, "releases").map(parseRelease);
  if (releases.length === 0) throw new Error("Release catalog must not be empty.");

  const versions = new Set<string>();
  for (let index = 0; index < releases.length; index += 1) {
    const release = releases[index];
    if (versions.has(release.version)) throw new Error(`Duplicate release version: ${release.version}.`);
    versions.add(release.version);
    if (index > 0 && compareVersions(releases[index - 1].version, release.version) >= 0) {
      throw new Error("Release catalog versions must be semantically sorted.");
    }
  }
  if (!versions.has(currentVersion)) throw new Error("current_version is absent from releases.");

  return { schema_version: 1, current_version: currentVersion, releases };
}

function parseRelease(value: unknown, index: number): ReleaseCatalogEntry {
  const field = `releases[${index}]`;
  const data = record(value, field);
  exact(
    data,
    [
      "archival",
      "bundle",
      "database_sha256",
      "manifest_sha256",
      "release_date",
      "source_commit",
      "tag",
      "version",
    ],
    field,
  );
  const version = semanticVersion(data.version, `${field}.version`);
  const tag = text(data.tag, `${field}.tag`);
  if (tag !== `v${version}`) throw new Error(`${field}.tag must equal v<version>.`);

  const bundleData = record(data.bundle, `${field}.bundle`);
  exact(bundleData, ["sha256", "size_bytes", "url"], `${field}.bundle`);
  const bundleUrl = httpsUrl(bundleData.url, `${field}.bundle.url`);
  const parsedBundleUrl = new URL(bundleUrl);
  if (
    parsedBundleUrl.hostname !== "github.com"
    || !parsedBundleUrl.pathname.includes(`/releases/download/${tag}/`)
  ) {
    throw new Error(`${field}.bundle.url must target the matching GitHub Release.`);
  }

  return {
    version,
    release_date: isoDate(data.release_date, `${field}.release_date`),
    database_sha256: sha256(data.database_sha256, `${field}.database_sha256`),
    manifest_sha256: sha256(data.manifest_sha256, `${field}.manifest_sha256`),
    source_commit: commit(data.source_commit, `${field}.source_commit`),
    tag,
    bundle: {
      url: bundleUrl,
      sha256: sha256(bundleData.sha256, `${field}.bundle.sha256`),
      size_bytes: positiveInteger(bundleData.size_bytes, `${field}.bundle.size_bytes`),
    },
    archival: parseArchive(data.archival, `${field}.archival`),
  };
}

function parseArchive(value: unknown, field: string): ReleaseArchiveDescriptor | null {
  if (value === null) return null;
  const data = record(value, field);
  exact(data, ["identifier", "provider", "url"], field);
  return {
    provider: text(data.provider, `${field}.provider`),
    identifier: text(data.identifier, `${field}.identifier`),
    url: httpsUrl(data.url, `${field}.url`),
  };
}

function compareVersions(left: string, right: string): number {
  const leftParts = left.split(".").map(Number);
  const rightParts = right.split(".").map(Number);
  for (let index = 0; index < 3; index += 1) {
    if (leftParts[index] !== rightParts[index]) return leftParts[index] - rightParts[index];
  }
  return 0;
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${field} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function array(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value;
}

function exact(data: Record<string, unknown>, fields: string[], label: string): void {
  const expected = new Set(fields);
  const unknown = Object.keys(data).filter((field) => !expected.has(field));
  const missing = fields.filter((field) => !Object.prototype.hasOwnProperty.call(data, field));
  if (unknown.length > 0) throw new Error(`${label} has unknown fields: ${unknown.join(", ")}.`);
  if (missing.length > 0) throw new Error(`${label} is missing fields: ${missing.join(", ")}.`);
}

function text(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${field} must be non-empty.`);
  }
  return value;
}

function semanticVersion(value: unknown, field: string): string {
  const result = text(value, field);
  if (!/^\d+\.\d+\.\d+$/u.test(result)) throw new Error(`${field} must be a semantic version.`);
  return result;
}

function isoDate(value: unknown, field: string): string {
  const result = text(value, field);
  if (!/^\d{4}-\d{2}-\d{2}$/u.test(result)) throw new Error(`${field} must be an ISO date.`);
  return result;
}

function sha256(value: unknown, field: string): string {
  const result = text(value, field);
  if (!/^[0-9a-f]{64}$/u.test(result)) throw new Error(`${field} must be a SHA-256 digest.`);
  return result;
}

function commit(value: unknown, field: string): string {
  const result = text(value, field);
  if (!/^[0-9a-f]{40}$/u.test(result)) throw new Error(`${field} must be a full commit SHA.`);
  return result;
}

function positiveInteger(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value <= 0) {
    throw new Error(`${field} must be a positive integer.`);
  }
  return value;
}

function httpsUrl(value: unknown, field: string): string {
  const result = text(value, field);
  const url = new URL(result);
  if (
    url.protocol !== "https:"
    || url.username
    || url.password
    || url.search
    || url.hash
  ) {
    throw new Error(`${field} must be a plain HTTPS URL.`);
  }
  return result;
}
