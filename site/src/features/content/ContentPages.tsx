import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { parseContentIndex, type AtlasContentPage } from "../../contracts/atlas-content";
import { siteBaseUrl } from "../../data/base-url";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";

export function ContentIndexPage() {
  const [pages, setPages] = useState<AtlasContentPage[]>([]); const [query, setQuery] = useState(""); const [error, setError] = useState<Error>();
  useEffect(() => { void loadContent().then((index) => setPages(index.pages), (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, []);
  const filtered = useMemo(() => pages.filter((page) => `${page.title_ja} ${page.title_en} ${page.summary}`.toLowerCase().includes(query.toLowerCase())), [pages, query]);
  return <section className="atlas-page content-page"><header className="atlas-page-header"><p className="eyebrow">Learn</p><h1>手法・概念を学ぶ</h1><p>直感、前提、1ステップ、可視化、コード、根拠をIDでつないだ教材です。</p></header><label className="content-search">検索<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nelder–Mead / convexity" /></label>{error && <p className="atlas-error" role="alert">{error.message}</p>}<div className="content-card-grid">{filtered.map((page) => <Link className="content-card" key={page.content_id} to={`/learn/${page.content_id}`}><span>{page.kind}</span><h2>{page.title_ja}</h2><p>{page.summary}</p><small>Reviewed {page.last_reviewed}</small></Link>)}</div>{!error && pages.length > 0 && filtered.length === 0 && <p>該当する教材がありません。</p>}</section>;
}

export function ContentPage() {
  const { contentId = "" } = useParams(); const [page, setPage] = useState<AtlasContentPage>(); const [error, setError] = useState<Error>();
  useEffect(() => { setPage(undefined); setError(undefined); void loadContent().then((index) => { const found = index.pages.find((item) => item.content_id === contentId); if (!found) { setError(new EntityNotFoundError("教材ID", contentId)); return; } setPage(found); }, (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, [contentId]);
  useEffect(() => { if (!page) return; document.title = `${page.title_ja} | Optimization Compass`; const meta = document.querySelector('meta[name="description"]') ?? document.head.appendChild(Object.assign(document.createElement("meta"), { name: "description" })); meta.setAttribute("content", page.summary); }, [page]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  return <section className="atlas-page content-detail"><p className="eyebrow">{page?.kind ?? "Learn"}</p><h1>{page?.title_ja ?? "教材を読み込み中…"}</h1>{error && <p className="atlas-error" role="alert">{error.message}</p>}{page && <><p className="content-lead">{page.summary}</p><MarkdownBody body={page.body} /><div className="content-links"><strong>Related</strong>{page.visualization_ids.map((id) => <Link key={id} to={visualizationRoute(id)}>{id}</Link>)}{page.comparison_ids.map((id) => <Link key={id} to="/compare/gradient-quadratic">{id}</Link>)}</div><small>Last reviewed {page.last_reviewed} · Sources: {page.source_ids.join(", ")}</small></>}</section>;
}

function visualizationRoute(id: string): string {
  if (id === "nelder-mead-quadratic") return "/theater/nelder-mead";
  if (id === "gradient-descent-quadratic") return "/compare/gradient-quadratic";
  return "/map";
}

function MarkdownBody({ body }: { body: string }) { const lines = body.split("\n"); let inCode = false; let code = ""; const blocks: ReactNode[] = []; lines.forEach((line, index) => { if (line.startsWith("```")) { if (inCode) blocks.push(<pre key={`code-${index}`}><code>{code}</code></pre>); inCode = !inCode; code = ""; return; } if (inCode) { code += `${line}\n`; return; } if (line.startsWith("## ")) blocks.push(<h2 key={index}>{line.slice(3)}</h2>); else if (line.startsWith("> ")) blocks.push(<blockquote key={index}>{line.slice(2)}</blockquote>); else if (line.trim()) blocks.push(<p key={index}>{line}</p>); }); return <div className="markdown-body">{blocks}</div>; }
async function loadContent() { const response = await fetch(`${siteBaseUrl()}data/content.json`); if (!response.ok) throw new Error(`Content request failed (${response.status}).`); return parseContentIndex(await response.json()); }
