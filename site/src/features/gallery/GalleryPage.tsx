import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseGalleryIndex, type GalleryCase } from "../../contracts/gallery";
import { findEntity } from "../../contracts/entity-links";
import { siteBaseUrl } from "../../data/base-url";
import { encodeAtlasState, type AtlasStateV1 } from "../../state/atlas-state";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { useEntityLinks } from "../../state/entity-links";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { THEATER_ROUTES } from "../theater/theater-routes";
import { PageOrientation } from "../../components/PageOrientation";

export function GalleryPage() {
  const [cases, setCases] = useState<GalleryCase[]>([]); const [domain, setDomain] = useState("all"); const [error, setError] = useState<Error>();
  useEffect(() => { void loadGallery().then((index) => setCases(index.cases), (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, []);
  const domains = ["all", ...new Set(cases.map((item) => item.domain))]; const filtered = useMemo(() => cases.filter((item) => domain === "all" || item.domain === domain), [cases, domain]);
  return <section className="atlas-page gallery-page"><header className="atlas-page-header"><p className="eyebrow">Problem Gallery</p><h1>ケースギャラリー</h1><p>現実の問いから、問題分類・診断・候補手法・最小コードへ逆引きします。</p></header><PageOrientation limits="Galleryは代表的な問題設定を学ぶためのcurated casesです。掲載ケースの結果や最小例を、そのまま実問題の保証として扱いません。" next={[{ label: "この条件で診断する", to: "/diagnose" }, { label: "問題構造Mapを見る", to: "/map" }, { label: "手法の教材を読む", to: "/learn" }]} purpose="実問題の問いから、問題型・診断・候補手法・可視化・最小コードへ逆引きします。" readingSteps={["Domainで近い問題設定を絞ります。", "ケース詳細で目的・制約・候補手法を読みます。", "Map・Diagnose・Theaterへ同じケースの状態を引き継ぎます。"]} /><label className="gallery-filter">Domain<select value={domain} onChange={(event) => setDomain(event.target.value)}>{domains.map((item) => <option key={item} value={item}>{item === "all" ? "すべて" : item}</option>)}</select></label>{error && <p className="atlas-error" role="alert">{error.message}</p>}<div className="gallery-card-grid">{filtered.map((item) => <Link className="gallery-card" key={item.case_id} to={`/gallery/${item.case_id}`}><span>{item.domain} · {item.difficulty}</span><h2>{item.title_ja}</h2><p>{item.question}</p><small>候補 {item.candidate_method_ids.length}件 · Reviewed {item.last_reviewed}</small></Link>)}</div></section>;
}

export function GalleryCasePage() {
  const links = useEntityLinks();
  const { caseId = "" } = useParams(); const [item, setItem] = useState<GalleryCase>(); const [datasetVersion, setDatasetVersion] = useState<string>(); const [error, setError] = useState<Error>();
  useEffect(() => { setItem(undefined); setDatasetVersion(undefined); setError(undefined); void loadGallery().then((index) => { const found = index.cases.find((candidate) => candidate.case_id === caseId); if (!found) { setError(new EntityNotFoundError("ケースID", caseId)); return; } setItem(found); setDatasetVersion(index.dataset_version); }, (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, [caseId]);
  const state = item && datasetVersion ? caseState(item, datasetVersion) : undefined;
  const stateQuery = state ? `?state=${encodeAtlasState(state)}` : "";
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  const method = (id: string) => links.status === "ready" ? findEntity(links.index, "method", id) : undefined;
  const visualization = (id: string) => links.status === "ready" ? findEntity(links.index, "trace", id) : undefined;
  const theaterLinks = item?.visualization_ids.flatMap((id) => {
    const target = visualization(id);
    return target?.canonical_url?.startsWith("/theater/") ? [target] : [];
  }) ?? [];
  const showBoTheater = item
    ? item.candidate_method_ids.includes("M_BAYESIAN_OPT_GP")
      || item.conditional_methods.some((entry) => entry.method_id === "M_BAYESIAN_OPT_GP")
    : false;
  return <section className="atlas-page gallery-detail"><p className="eyebrow">Problem Gallery</p><h1>{item?.title_ja ?? "ケース詳細"}</h1><p className="route-parameter">Case ID: <strong>{caseId}</strong></p>{error && <p className="atlas-error" role="alert">{error.message}</p>}{item && <><p className="content-lead">{item.question}</p><Detail label="意思決定変数" value={item.decision_variables} /><Detail label="目的関数" value={item.objective} /><Detail label="制約" value={item.constraints} /><section className="gallery-section"><h2>診断・地図</h2><p>Map node: <code>{item.map_node_id}</code></p><Link className="text-link" to={{ pathname: "/map", search: stateQuery }}>分類図上で見る</Link> <Link className="text-link" to={{ pathname: "/diagnose", search: stateQuery }}>この特徴で診断する</Link></section>{(theaterLinks.length > 0 || showBoTheater) && <section className="gallery-section"><h2>動きを見る</h2><ul>{theaterLinks.map((target) => <li key={target.entity_id}><Link className="text-link" to={target.canonical_url!}>Search-tree Theaterで再生</Link></li>)}{showBoTheater && <li><Link className="text-link" to={THEATER_ROUTES.bayesianOptimization}>BO Theaterで点選択を見る</Link></li>}</ul></section>}<section className="gallery-section"><h2>候補手法</h2><ul>{item.candidate_method_ids.map((id) => { const target = method(id); return <li key={id}>{target?.canonical_url ? <Link to={target.canonical_url}>{target.label}</Link> : id}</li>; })}</ul><h3>条件付き</h3><ul>{item.conditional_methods.map((entry) => { const target = method(entry.method_id); return <li key={entry.method_id}>{target?.canonical_url ? <Link to={target.canonical_url}>{target.label}</Link> : <strong>{entry.method_id}</strong>} — {entry.reason}</li>; })}</ul><h3>避ける</h3><ul>{item.excluded_methods.map((entry) => { const target = method(entry.method_id); return <li key={entry.method_id}>{target?.canonical_url ? <Link to={target.canonical_url}>{target.label}</Link> : <strong>{entry.method_id}</strong>} — {entry.reason}</li>; })}</ul></section><section className="gallery-section"><h2>最小Python例</h2><pre><code>{item.python_example}</code></pre></section><p className="atlas-note">{item.practical_notes}</p><small>Last reviewed {item.last_reviewed}</small><EvidenceLinks sourceIds={item.source_ids} /></>}</section>;
}
export function caseState(item: Pick<GalleryCase, "map_node_id" | "question_answers">, datasetVersion: string): AtlasStateV1 { return { stateVersion: 1, datasetVersion, viewId: "problem-structure", viewVersion: "1.0.0", selectedNodeId: item.map_node_id, answers: Object.fromEntries(Object.entries(item.question_answers).map(([questionId, value]) => [questionId, value === "unknown" ? { status: "unknown", values: ["unknown"] } : { status: "answered", values: [value] }])) }; }
function Detail({ label, value }: { label: string; value: string }) { return <section className="gallery-section"><h2>{label}</h2><p>{value}</p></section>; }
async function loadGallery() { const response = await fetch(`${siteBaseUrl()}data/gallery.json`); if (!response.ok) throw new Error(`Gallery request failed (${response.status}).`); return parseGalleryIndex(await response.json()); }
