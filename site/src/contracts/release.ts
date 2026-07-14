import { siteBaseUrl } from "../data/base-url";

export interface DatasetReleaseIdentity {
  schema_version: 1;
  dataset_version: string;
  release_date: string;
  database_sha256: string;
}

const RELEASE_FIELDS = [
  "schema_version",
  "dataset_version",
  "release_date",
  "database_sha256",
] as const;

export function parseDatasetReleaseIdentity(value: unknown): DatasetReleaseIdentity {
  if (!isRecord(value)) throw new Error("release identity must be an object");
  const actualFields = Object.keys(value).sort();
  const expectedFields = [...RELEASE_FIELDS].sort();
  if (actualFields.join("\n") !== expectedFields.join("\n")) {
    throw new Error("release identity fields do not match schema");
  }
  if (value.schema_version !== 1) throw new Error("unsupported release identity schema");
  const datasetVersion = nonEmptyString(value.dataset_version, "dataset_version");
  const releaseDate = nonEmptyString(value.release_date, "release_date");
  const databaseSha256 = nonEmptyString(value.database_sha256, "database_sha256");
  if (!/^\d+\.\d+\.\d+$/.test(datasetVersion)) throw new Error("invalid dataset_version");
  if (!/^\d{4}-\d{2}-\d{2}$/.test(releaseDate)) throw new Error("invalid release_date");
  if (!/^[0-9a-f]{64}$/.test(databaseSha256)) throw new Error("invalid database_sha256");
  return {
    schema_version: 1,
    dataset_version: datasetVersion,
    release_date: releaseDate,
    database_sha256: databaseSha256,
  };
}

export async function loadDatasetReleaseIdentity(
  signal?: AbortSignal,
): Promise<DatasetReleaseIdentity> {
  const response = await fetch(`${siteBaseUrl()}data/release.json`, { signal });
  if (!response.ok) throw new Error(`Release identity request failed (${response.status}).`);
  return parseDatasetReleaseIdentity(await response.json());
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function nonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.length === 0) throw new Error(`${field} must be set`);
  return value;
}
