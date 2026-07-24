import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  parseContentIndex,
  type AtlasContentPage,
  type ContentKind,
} from "../../contracts/atlas-content";
import { findEntity, relatedEntities } from "../../contracts/entity-links";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { CompiledContent } from "./CompiledContent";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { LearningRelations } from "../learning/LearningRelations";

export function ContentIndexPage() {
  const links = useEntityLinks();
  const [pages, setPages] = useState<AtlasContentPage[]>([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<ContentFilter>("connected");
  const [error, setError] = useState<Error>();

  useEffect(() => {
    void loadContent().then(
      (index) => setPages(index.pages),
      (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught))),
    );
  }, []);

  const counts = useMemo(() => contentFilterCounts(pages), [pages]);
  const filtered = useMemo(
    () => filterAndRankContentPages(pages, query, filter),
    [filter, pages, query],
  );
  const pageUrl = (page: AtlasContentPage) => {
    if (links.status !== "ready") return `/learn/${page.content_id}`;
    const entity = findEntity(links.index, "content", page.content_id);
    return entity?.canonical_url
      ?? (entity ? relatedEntities(links.index, entity, "explains")[0]?.canonical_url : undefined)
      ?? `/learn/${page.content_id}`;
  };

  const relatedUrl = (
    type: "trace" | "comparison",
    ids: string[],
  ): string | undefined => {
    if (links.status !== "ready") return undefined;
    return ids
      .map((id) => findEntity(links.index, type, id)?.canonical_url)
      .find((url): url is string => Boolean(url));
  };

  return (
    <section className="atlas-page content-page">
      <header className="atlas-page-header">
        <p className="eyebrow">教材</p>
        <h1>手法・概念を学ぶ</h1>
        <p>まず直感をつかみ、前提・動き・実装・根拠へ順番に進む教材です。</p>
      </header>

      <section aria-label="教材を絞り込む" className="content-tools">
        <label className="content-search">
          教材を検索
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="手法名、概念、困りごと…"
            type="search"
            value={query}
          />
        </label>
        <div aria-label="教材の種類" className="content-filter-bar" role="group">
          {contentFilters.map(({ label, value }) => (
            <button
              aria-label={`${label} ${counts[value]}件`}
              aria-pressed={filter === value}
              key={value}
              onClick={() => setFilter(value)}
              type="button"
            >
              <span>{label}</span>
              <strong>{counts[value]}</strong>
            </button>
          ))}
        </div>
        <output aria-live="polite" className="content-result-count">{filtered.length}件</output>
      </section>

      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      <div className="content-card-grid">
        {filtered.map((page) => {
          const visualizationUrl = relatedUrl("trace", page.visualization_ids);
          const comparisonUrl = relatedUrl("comparison", page.comparison_ids);
          return (
            <article className="content-card" key={page.content_id}>
              <Link className="content-card-main" to={pageUrl(page)}>
                <span>{page.kind === "method" ? "手法" : "概念"}</span>
                <h2>{page.title_ja}</h2>
                <p>{page.summary}</p>
                <strong className="content-card-action">教材を読む →</strong>
              </Link>
              {(visualizationUrl || comparisonUrl) && (
                <nav aria-label={`${page.title_ja}の関連教材`} className="content-card-related">
                  {visualizationUrl && (
                    <Link to={visualizationUrl}>
                      動きを見る{page.visualization_ids.length > 1 ? ` (${page.visualization_ids.length})` : ""}
                    </Link>
                  )}
                  {comparisonUrl && (
                    <Link to={comparisonUrl}>
                      比較する{page.comparison_ids.length > 1 ? ` (${page.comparison_ids.length})` : ""}
                    </Link>
                  )}
                </nav>
              )}
            </article>
          );
        })}
      </div>
      {!error && pages.length > 0 && filtered.length === 0 && (
        <p className="content-empty">一致する教材が見つかりません。種類か検索語を変えてください。</p>
      )}
    </section>
  );
}

export type ContentFilter = "all" | ContentKind | "connected";

const contentFilters: Array<{ label: string; value: ContentFilter }> = [
  { label: "動き・比較で学ぶ", value: "connected" },
  { label: "すべて", value: "all" },
  { label: "手法", value: "method" },
  { label: "概念", value: "concept" },
];

export function contentFilterCounts(
  pages: AtlasContentPage[],
): Record<ContentFilter, number> {
  return {
    all: pages.length,
    method: pages.filter((page) => page.kind === "method").length,
    concept: pages.filter((page) => page.kind === "concept").length,
    connected: pages.filter(hasConnectedLearning).length,
  };
}

export function filterAndRankContentPages(
  pages: AtlasContentPage[],
  query: string,
  filter: ContentFilter,
): AtlasContentPage[] {
  const normalizedQuery = query.trim().toLocaleLowerCase();
  return pages
    .filter((page) => (
      (filter === "all"
        || page.kind === filter
        || (filter === "connected" && hasConnectedLearning(page)))
      && (
        normalizedQuery.length === 0
        || [
          page.content_id,
          page.title_ja,
          page.title_en,
          page.summary,
        ].join(" ").toLocaleLowerCase().includes(normalizedQuery)
      )
    ))
    .sort((left, right) => (
      Number(hasConnectedLearning(right)) - Number(hasConnectedLearning(left))
      || Number(right.kind === "method") - Number(left.kind === "method")
      || left.title_ja.localeCompare(right.title_ja, "ja")
    ));
}

function hasConnectedLearning(page: AtlasContentPage): boolean {
  return page.visualization_ids.length > 0 || page.comparison_ids.length > 0;
}

export function ContentPage() {
  const links = useEntityLinks();
  const { contentId = "" } = useParams(); const [page, setPage] = useState<AtlasContentPage>(); const [error, setError] = useState<Error>();
  useEffect(() => { setPage(undefined); setError(undefined); void loadContent().then((index) => { const found = index.pages.find((item) => item.content_id === contentId); if (!found) { setError(new EntityNotFoundError("教材ID", contentId)); return; } setPage(found); }, (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, [contentId]);
  useEffect(() => { if (!page) return; document.title = `${page.title_ja} | Optimization Compass`; const meta = document.querySelector('meta[name="description"]') ?? document.head.appendChild(Object.assign(document.createElement("meta"), { name: "description" })); meta.setAttribute("content", page.summary); }, [page]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  const destination = (type: "trace" | "comparison", id: string) => links.status === "ready"
    ? findEntity(links.index, type, id)?.canonical_url
    : undefined;
  return <section className="atlas-page content-detail"><p className="eyebrow">{page ? (page.kind === "method" ? "手法" : "概念") : "教材"}</p><h1>{page?.title_ja ?? "教材を読み込み中…"}</h1>{error && <p className="atlas-error" role="alert">{error.message}</p>}{page && <><CompiledContent page={page} /><LearningRelations entityId={page.canonical_entity_id} entityType={page.canonical_entity_type} /><div className="content-links"><strong>関連リンク</strong>{page.visualization_ids.map((id) => destination("trace", id) ? <Link key={id} to={destination("trace", id)!}>{id}</Link> : null)}{page.comparison_ids.map((id) => destination("comparison", id) ? <Link key={id} to={destination("comparison", id)!}>{id}</Link> : null)}</div><small>確認日 {page.last_reviewed}</small><EvidenceLinks sourceIds={page.source_ids} /></>}</section>;
}

async function loadContent() { const response = await fetch(`${siteBaseUrl()}data/content.json`); if (!response.ok) throw new Error(`Content request failed (${response.status}).`); return parseContentIndex(await response.json()); }
