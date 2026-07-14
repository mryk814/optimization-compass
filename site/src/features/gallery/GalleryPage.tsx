import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseGalleryIndex, type GalleryCase } from "../../contracts/gallery";
import { siteBaseUrl } from "../../data/base-url";
import { encodeAtlasState, type AtlasStateV1 } from "../../state/atlas-state";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";

export function GalleryPage() {
  const [cases, setCases] = useState<GalleryCase[]>([]); const [domain, setDomain] = useState("all"); const [error, setError] = useState<Error>();
  useEffect(() => { void loadGallery().then((index) => setCases(index.cases), (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, []);
  const domains = ["all", ...new Set(cases.map((item) => item.domain))]; const filtered = useMemo(() => cases.filter((item) => domain === "all" || item.domain === domain), [cases, domain]);
  return <section className="atlas-page gallery-page"><header className="atlas-page-header"><p className="eyebrow">Problem Gallery</p><h1>ケースギャラリー</h1><p>現実の問いから、問題分類・診断・候補手法・最小コードへ逆引きします。</p></header><label className="gallery-filter">Domain<select value={domain} onChange={(event) => setDomain(event.target.value)}>{domains.map((item) => <option key={item} value={item}>{item === "all" ? "すべて" : item}</option>)}</select></label>{error && <p className="atlas-error" role="alert">{error.message}</p>}<div className="gallery-card-grid">{filtered.map((item) => <Link className="gallery-card" key={item.case_id} to={`/gallery/${item.case_id}`}><span>{item.domain} · {item.difficulty}</span><h2>{item.title_ja}</h2><p>{item.question}</p><small>候補 {item.candidate_method_ids.length}件 · Reviewed {item.last_reviewed}</small></Link>)}</div></section>;
}

export function GalleryCasePage() {
  const { caseId = "" } = useParams(); const [item, setItem] = useState<GalleryCase>(); const [error, setError] = useState<Error>();
  useEffect(() => { setItem(undefined); setError(undefined); void loadGallery().then((index) => { const found = index.cases.find((candidate) => candidate.case_id === caseId); if (!found) { setError(new EntityNotFoundError("ケースID", caseId)); return; } setItem(found); }, (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, [caseId]);
  const state = item ? caseState(item) : undefined;
  const stateQuery = state ? `?state=${encodeAtlasState(state)}` : "";
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  return <section className="atlas-page gallery-detail"><p className="eyebrow">Problem Gallery</p><h1>{item?.title_ja ?? "ケース詳細"}</h1><p className="route-parameter">Case ID: <strong>{caseId}</strong></p>{error && <p className="atlas-error" role="alert">{error.message}</p>}{item && <><p className="content-lead">{item.question}</p><Detail label="意思決定変数" value={item.decision_variables} /><Detail label="目的関数" value={item.objective} /><Detail label="制約" value={item.constraints} /><section className="gallery-section"><h2>診断・地図</h2><p>Map node: <code>{item.map_node_id}</code></p><Link className="text-link" to={{ pathname: "/map", search: stateQuery }}>分類図上で見る</Link> <Link className="text-link" to={{ pathname: "/diagnose", search: stateQuery }}>この特徴で診断する</Link></section><section className="gallery-section"><h2>候補手法</h2><ul>{item.candidate_method_ids.map((id) => <li key={id}><Link to={`/methods/${id}`}>{id}</Link></li>)}</ul><h3>避ける／条件付き</h3><ul>{item.excluded_methods.map((entry) => <li key={entry.method_id}><strong>{entry.method_id}</strong> — {entry.reason}</li>)}</ul></section><section className="gallery-section"><h2>最小Python例</h2><pre><code>{item.python_example}</code></pre></section><p className="atlas-note">{item.practical_notes}</p><small>Last reviewed {item.last_reviewed} · Sources: {item.source_ids.join(", ")}</small></>}</section>;
}
function caseState(item: GalleryCase): AtlasStateV1 { return { stateVersion: 1, datasetVersion: "0.2.0", viewId: "problem-structure", viewVersion: "1.0.0", selectedNodeId: item.map_node_id, answers: Object.fromEntries(Object.entries(item.question_answers).map(([questionId, value]) => [questionId, value === "unknown" ? { status: "unknown", values: ["unknown"] } : { status: "answered", values: [value] }])) }; }
function Detail({ label, value }: { label: string; value: string }) { return <section className="gallery-section"><h2>{label}</h2><p>{value}</p></section>; }
async function loadGallery() { const response = await fetch(`${siteBaseUrl()}data/gallery.json`); if (!response.ok) throw new Error(`Gallery request failed (${response.status}).`); return parseGalleryIndex(await response.json()); }
