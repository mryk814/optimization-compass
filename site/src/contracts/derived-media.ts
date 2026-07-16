export type DerivedMediaKind = "thumbnail" | "static_png" | "static_svg" | "animated_gif" | "webm";

export interface DerivedMediaFile {
  media_kind: DerivedMediaKind;
  media_type: "image/png" | "image/svg+xml" | "image/gif" | "video/webm";
  path: string;
  width: number;
  height: number;
  frame_index: number;
  duration_seconds: number | null;
  bytes: number;
  sha256: string;
}

export interface DerivedMediaEntry {
  media_id: string;
  scenario_id: string;
  dataset_version: string;
  artifact_contract: string;
  artifact_contract_version: string;
  renderer_family: string;
  renderer_contract_version: string;
  source_artifact_path: string;
  source_artifact_sha256: string;
  frame_index: number;
  viewport_preset: string;
  camera_preset: string | null;
  narration_version: string | null;
  source_ids: string[];
  limitations_ja: string;
  limitations_en: string;
  alt_ja: string;
  alt_en: string;
  caption_ja: string;
  caption_en: string;
  license_spdx_id: "CC-BY-4.0";
  attribution: string;
  files: DerivedMediaFile[];
}

export interface DerivedMediaManifest {
  contract_version: "1.0.0";
  dataset_version: string;
  entries: DerivedMediaEntry[];
}

const mediaKinds = new Set<DerivedMediaKind>(["thumbnail", "static_png", "static_svg", "animated_gif", "webm"]);
const mediaTypes = new Set<DerivedMediaFile["media_type"]>(["image/png", "image/svg+xml", "image/gif", "video/webm"]);

export function parseDerivedMediaManifest(raw: unknown): DerivedMediaManifest {
  const data = record(raw, "DerivedMediaManifest");
  exact(data, ["contract_version", "dataset_version", "entries"], "DerivedMediaManifest");
  if (data.contract_version !== "1.0.0") throw new Error("DerivedMediaManifest version is unsupported.");
  const datasetVersion = text(data.dataset_version, "dataset_version");
  const entries = list(data.entries, "entries").map((item, index) => parseEntry(item, `entries[${index}]`));
  if (entries.length === 0) throw new Error("derived media entries must not be empty.");
  if (new Set(entries.map((entry) => entry.media_id)).size !== entries.length) {
    throw new Error("derived media IDs must be unique.");
  }
  if (entries.some((entry) => entry.dataset_version !== datasetVersion)) {
    throw new Error("derived media dataset versions must match the manifest.");
  }
  return { contract_version: "1.0.0", dataset_version: datasetVersion, entries };
}

function parseEntry(raw: unknown, field: string): DerivedMediaEntry {
  const data = record(raw, field);
  exact(data, [
    "media_id", "scenario_id", "dataset_version", "artifact_contract", "artifact_contract_version",
    "renderer_family", "renderer_contract_version", "source_artifact_path", "source_artifact_sha256",
    "frame_index", "viewport_preset", "camera_preset", "narration_version", "source_ids",
    "limitations_ja", "limitations_en", "alt_ja", "alt_en", "caption_ja", "caption_en",
    "license_spdx_id", "attribution", "files",
  ], field);
  if (data.license_spdx_id !== "CC-BY-4.0") throw new Error(`${field}.license_spdx_id is unsupported.`);
  const files = list(data.files, `${field}.files`).map((item, index) => parseFile(item, `${field}.files[${index}]`));
  if (files.length === 0) throw new Error(`${field}.files must not be empty.`);
  return {
    media_id: text(data.media_id, `${field}.media_id`),
    scenario_id: text(data.scenario_id, `${field}.scenario_id`),
    dataset_version: text(data.dataset_version, `${field}.dataset_version`),
    artifact_contract: text(data.artifact_contract, `${field}.artifact_contract`),
    artifact_contract_version: text(data.artifact_contract_version, `${field}.artifact_contract_version`),
    renderer_family: text(data.renderer_family, `${field}.renderer_family`),
    renderer_contract_version: text(data.renderer_contract_version, `${field}.renderer_contract_version`),
    source_artifact_path: safePath(data.source_artifact_path, `${field}.source_artifact_path`),
    source_artifact_sha256: hash(data.source_artifact_sha256, `${field}.source_artifact_sha256`),
    frame_index: nonNegativeInteger(data.frame_index, `${field}.frame_index`),
    viewport_preset: text(data.viewport_preset, `${field}.viewport_preset`),
    camera_preset: nullableText(data.camera_preset, `${field}.camera_preset`),
    narration_version: nullableText(data.narration_version, `${field}.narration_version`),
    source_ids: nonEmptyTextList(data.source_ids, `${field}.source_ids`),
    limitations_ja: text(data.limitations_ja, `${field}.limitations_ja`),
    limitations_en: text(data.limitations_en, `${field}.limitations_en`),
    alt_ja: text(data.alt_ja, `${field}.alt_ja`),
    alt_en: text(data.alt_en, `${field}.alt_en`),
    caption_ja: text(data.caption_ja, `${field}.caption_ja`),
    caption_en: text(data.caption_en, `${field}.caption_en`),
    license_spdx_id: "CC-BY-4.0",
    attribution: text(data.attribution, `${field}.attribution`),
    files,
  };
}

function parseFile(raw: unknown, field: string): DerivedMediaFile {
  const data = record(raw, field);
  exact(data, ["media_kind", "media_type", "path", "width", "height", "frame_index", "duration_seconds", "bytes", "sha256"], field);
  const kind = member(data.media_kind, mediaKinds, `${field}.media_kind`);
  const mediaType = member(data.media_type, mediaTypes, `${field}.media_type`);
  const path = safePath(data.path, `${field}.path`);
  if (!path.startsWith("media/") || !/\.(png|svg|gif|webm)$/u.test(path)) throw new Error(`${field}.path is invalid.`);
  return {
    media_kind: kind,
    media_type: mediaType,
    path,
    width: positiveInteger(data.width, `${field}.width`),
    height: positiveInteger(data.height, `${field}.height`),
    frame_index: nonNegativeInteger(data.frame_index, `${field}.frame_index`),
    duration_seconds: data.duration_seconds === null ? null : positiveNumber(data.duration_seconds, `${field}.duration_seconds`),
    bytes: positiveInteger(data.bytes, `${field}.bytes`),
    sha256: hash(data.sha256, `${field}.sha256`),
  };
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`);
  return value as Record<string, unknown>;
}
function list(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${field} must be an array.`);
  return value;
}
function text(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`);
  return value;
}
function nullableText(value: unknown, field: string): string | null {
  return value === null ? null : text(value, field);
}
function nonEmptyTextList(value: unknown, field: string): string[] {
  const values = list(value, field).map((item, index) => text(item, `${field}[${index}]`));
  if (values.length === 0) throw new Error(`${field} must not be empty.`);
  return values;
}
function nonNegativeInteger(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) throw new Error(`${field} is invalid.`);
  return value;
}
function positiveInteger(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value <= 0) throw new Error(`${field} is invalid.`);
  return value;
}
function positiveNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) throw new Error(`${field} is invalid.`);
  return value;
}
function hash(value: unknown, field: string): string {
  const candidate = text(value, field);
  if (!/^[0-9a-f]{64}$/u.test(candidate)) throw new Error(`${field} is invalid.`);
  return candidate;
}
function safePath(value: unknown, field: string): string {
  const candidate = text(value, field);
  if (candidate.startsWith("/") || candidate.includes("..") || candidate.includes("\\")) throw new Error(`${field} is unsafe.`);
  return candidate;
}
function member<T extends string>(value: unknown, options: ReadonlySet<T>, field: string): T {
  if (typeof value !== "string" || !options.has(value as T)) throw new Error(`${field} is invalid.`);
  return value as T;
}
function exact(data: Record<string, unknown>, expected: readonly string[], field: string): void {
  const keys = new Set(expected);
  const unknown = Object.keys(data).filter((key) => !keys.has(key));
  const missing = expected.filter((key) => !Object.prototype.hasOwnProperty.call(data, key));
  if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`);
  if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`);
}
