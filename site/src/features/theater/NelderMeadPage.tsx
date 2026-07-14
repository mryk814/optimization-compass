import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { parseAlgorithmTrace, type AlgorithmTrace } from "../../contracts/trace";
import { siteBaseUrl } from "../../data/base-url";
import { PlaybackControls } from "../playback/PlaybackControls";
import { usePlayback } from "../playback/usePlayback";

export function NelderMeadPage() {
  const [trace, setTrace] = useState<AlgorithmTrace>(); const [error, setError] = useState<Error>();
  useEffect(() => { void fetch(`${siteBaseUrl()}data/traces/nelder-mead-quadratic.json`).then(async (response) => { if (!response.ok) throw new Error(`Nelder–Mead Trace request failed (${response.status}).`); return parseAlgorithmTrace(await response.json()); }).then(setTrace, (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, []);
  return <section className="atlas-page nm-theater"><header className="atlas-page-header"><p className="eyebrow">Method Theater</p><h1>Nelder–Meadの幾何操作</h1><p>反射・膨張・収縮・縮小を、目的関数上の単体の動きとして追います。</p></header>{error && <p className="atlas-error" role="alert">{error.message}</p>}{!trace && !error && <p role="status">Traceを読み込み中…</p>}{trace && <Theater trace={trace} />}</section>;
}

function Theater({ trace }: { trace: AlgorithmTrace }) {
  const playback = usePlayback(trace.trace_id, trace.frames); const frame = playback.currentFrame; const vertices = frame.points.filter((point) => point.role === "simplex-vertex"); const candidate = frame.points.find((point) => point.role === "trial-point");
  return <><section className="nm-contract"><strong>{frame.event_label_ja ?? frame.event_type}</strong><span>iteration {frame.iteration} · evaluations {frame.oracle_evaluations}</span><span>best f = {frame.metrics[0]?.value.toPrecision(5)}</span></section><PlaybackControls playback={playback} /><div className="nm-layout"><svg className="nm-plot" viewBox="0 0 520 360" role="img" aria-label="Nelder–Mead simplex plot"><rect x="0" y="0" width="520" height="360" rx="12" />{Array.from({ length: 9 }, (_, index) => <line key={`grid-x-${index}`} x1={40 + index * 55} x2={40 + index * 55} y1="20" y2="340" className="nm-grid" />)}{Array.from({ length: 7 }, (_, index) => <line key={`grid-y-${index}`} x1="40" x2="480" y1={20 + index * 53} y2={20 + index * 53} className="nm-grid" />)}<polygon points={vertices.map((point) => `${mapX(point.coordinates[0])},${mapY(point.coordinates[1])}`).join(" ")} className="nm-simplex" />{vertices.map((point) => <circle key={point.point_id} cx={mapX(point.coordinates[0])} cy={mapY(point.coordinates[1])} r="7" className="nm-vertex" />)}{candidate && <circle cx={mapX(candidate.coordinates[0])} cy={mapY(candidate.coordinates[1])} r="8" className="nm-candidate" />}</svg><aside className="nm-explanation"><h2>このステップ</h2><p>{frame.event_label_ja ?? frame.event_type}</p><p>点は各frameの完全snapshotです。候補点が採用されたかは判定表示で確認できます。</p><dl><div><dt>Method</dt><dd>{trace.method_id}</dd></div><div><dt>Objective</dt><dd>{trace.objective.display_expression as string}</dd></div></dl><p className="atlas-note">Nelder–Meadは局所探索です。制約・高次元・大域保証が必要な問題では、診断で別の候補も確認してください。</p><Link className="text-link" to={`/methods/${trace.method_id}`}>手法ページへ</Link></aside></div></>;
}
function mapX(value: number) { return 40 + ((value + 4) / 8) * 440; }
function mapY(value: number) { return 340 - ((value + 4) / 8) * 320; }
