export type ContentKind = "method" | "concept";

export interface AtlasContentPage {
  content_id: string;
  kind: ContentKind;
  canonical_entity_type: "method" | "problem" | "feature" | "implementation";
  canonical_entity_id: string;
  title_ja: string;
  title_en: string;
  summary: string;
  html: string;
  toc: ContentHeading[];
  prerequisites: string[];
  related_ids: string[];
  visualization_ids: string[];
  comparison_ids: string[];
  source_ids: string[];
  status: "published" | "draft";
  last_reviewed: string;
  seo_title: string;
  seo_description: string;
}

export interface ContentHeading {
  heading_id: string;
  label: string;
  level: 2 | 3 | 4 | 5 | 6;
}

export interface AtlasContentIndex {
  contract_version: "2.0.0";
  dataset_version: string;
  pages: AtlasContentPage[];
}

export function parseContentIndex(raw: unknown): AtlasContentIndex {
  const data = record(raw, "content index");
  if (data.contract_version !== "2.0.0") throw new Error("Unsupported content contract.");
  const pages = array(data.pages, "content pages").map((item, index) => {
    const page = record(item, `content page ${index}`);
    const kind = string(page.kind, "content kind");
    if (kind !== "method" && kind !== "concept") throw new Error(`Unsupported content kind: ${kind}`);
    return {
      content_id: nonEmpty(page.content_id, "content_id"), kind,
      canonical_entity_type: canonicalEntityType(page.canonical_entity_type),
      canonical_entity_id: nonEmpty(page.canonical_entity_id, "canonical_entity_id"),
      title_ja: nonEmpty(page.title_ja, "title_ja"), title_en: nonEmpty(page.title_en, "title_en"),
      summary: string(page.summary, "summary"), html: nonEmpty(page.html, "html"),
      toc: parseToc(page.toc),
      prerequisites: strings(page.prerequisites, "prerequisites"), related_ids: strings(page.related_ids, "related_ids"),
      visualization_ids: strings(page.visualization_ids, "visualization_ids"), comparison_ids: strings(page.comparison_ids, "comparison_ids"),
      source_ids: strings(page.source_ids, "source_ids"), status: contentStatus(page.status),
      last_reviewed: nonEmpty(page.last_reviewed, "last_reviewed"), seo_title: nonEmpty(page.seo_title, "seo_title"),
      seo_description: nonEmpty(page.seo_description, "seo_description"),
    } satisfies AtlasContentPage;
  });
  if (new Set(pages.map((page) => page.content_id)).size !== pages.length) throw new Error("Duplicate content ID.");
  return { contract_version: "2.0.0", dataset_version: nonEmpty(data.dataset_version, "dataset_version"), pages };
}

function parseHeading(value: unknown, index: number): ContentHeading {
  const heading = record(value, `heading ${index}`);
  const level = heading.level;
  if (level !== 2 && level !== 3 && level !== 4 && level !== 5 && level !== 6) throw new Error(`Unsupported heading level: ${String(level)}`);
  return { heading_id: nonEmpty(heading.heading_id, "heading_id"), label: nonEmpty(heading.label, "heading label"), level };
}

function parseToc(value: unknown): ContentHeading[] {
  const headings = array(value, "toc").map((heading, index) => parseHeading(heading, index));
  if (headings.length === 0) throw new Error("Content TOC must not be empty.");
  if (new Set(headings.map((heading) => heading.heading_id)).size !== headings.length) throw new Error("Duplicate heading ID.");
  return headings;
}

function record(value: unknown, owner: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`);
  return value as Record<string, unknown>;
}
function array(value: unknown, owner: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`);
  return value;
}
function string(value: unknown, owner: string): string {
  if (typeof value !== "string") throw new Error(`${owner} must be a string.`);
  return value;
}
function nonEmpty(value: unknown, owner: string): string {
  const result = string(value, owner);
  if (!result.trim()) throw new Error(`${owner} must not be blank.`);
  return result;
}
function strings(value: unknown, owner: string): string[] {
  return array(value, owner).map((item, index) => nonEmpty(item, `${owner}[${index}]`));
}
function contentStatus(value: unknown): "published" | "draft" { if (value === "published" || value === "draft") return value; throw new Error(`Unsupported content status: ${String(value)}`); }
function canonicalEntityType(value: unknown): AtlasContentPage["canonical_entity_type"] {
  if (value === "method" || value === "problem" || value === "feature" || value === "implementation") return value;
  throw new Error(`Unsupported canonical entity type: ${String(value)}`);
}
