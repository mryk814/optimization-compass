import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseComparisonIndex, type ComparisonSet } from "../../contracts/comparisons";
import { parseAlgorithmTrace, type AlgorithmTrace, type TraceFrame } from "../../contracts/trace";
import { PlaybackControls } from "../playback/PlaybackControls";
import { usePlayback } from "../playback/usePlayback";
import { siteBaseUrl } from "../../data/base-url";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";

type Loaded = { comparison: ComparisonSet; traces: AlgorithmTrace[] };

export function ComparisonPage() {
  const { comparisonId = "" } = useParams();
  const [loaded, setLoaded] = useState<Loaded>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    const controller = new AbortController();
    setLoaded(undefined);
    setError(undefined);
    void loadComparison(comparisonId, controller.signal).then(setLoaded, (caught: unknown) => {
      if (!controller.signal.aborted) setError(caught instanceof Error ? caught : new Error(String(caught)));
    });
    return () => controller.abort();
  }, [comparisonId]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  return <section className="atlas-page comparison-page"><header className="atlas-page-header"><p className="eyebrow">Compare Lab</p><h1>手法を比較する</h1><p>同じ目的関数・初期点・評価予算で、更新則の違いを再生します。</p></header><p className="route-parameter">Comparison ID: <strong>{comparisonId}</strong></p>{error && <p className="atlas-error" role="alert">{error.message}</p>}{!loaded && !error && <p role="status">比較条件を読み込み中…</p>}{loaded && <ComparisonPlayer {...loaded} />}</section>;
}

function ComparisonPlayer({ comparison, traces }: Loaded) {
  const timeline = useMemo(() => {
    const template = traces[0].frames[0];
    return Array.from({ length: comparison.budget + 1 }, (_, evaluation) => ({
      ...template,
      frame_index: evaluation,
      iteration: evaluation,
      oracle_evaluations: evaluation,
      elapsed_steps: evaluation,
      elapsed_time_ms: evaluation * 120,
      event_type: evaluation === 0 ? "initialize" : "comparison-tick",
      event_label_ja: evaluation === 0 ? "比較を開始" : "比較タイムライン",
      event_label_en: evaluation === 0 ? "Start comparison" : "Comparison timeline",
    }));
  }, [comparison.budget, traces]);
  const playback = usePlayback(comparison.comparison_id, timeline);
  const evaluation = playback.currentFrame.oracle_evaluations;
  return <><section className="comparison-contract"><strong>{comparison.title_ja}</strong><span>{comparison.objective_expression}</span><span>初期点 [{comparison.initial_point.join(", ")}] · budget {comparison.budget}</span><p>{comparison.fairness_note}</p></section><PlaybackControls playback={playback} /><div className="comparison-grid">{traces.map((trace) => <ComparisonMember key={trace.trace_id} trace={trace} evaluation={evaluation} />)}</div><p className="atlas-note">この比較は教育用の同一条件再生です。初期値・学習率・停止条件が変われば結論も変わります。</p></>;
}

function ComparisonMember({ trace, evaluation }: { trace: AlgorithmTrace; evaluation: number }) {
  const frame = latestFrame(trace.frames, evaluation);
  const point = frame.points.find((item) => item.point_id === "current");
  return <article className="comparison-card"><header><h2>{trace.method_id}</h2><span>{trace.terminal_status}</span></header><p className="comparison-event">{frame.event_label_ja ?? frame.event_type} · evaluation {frame.oracle_evaluations}</p><svg className="comparison-plot" viewBox="0 0 240 150" role="img" aria-label={`${trace.method_id}の軌跡`}><rect x="0" y="0" width="240" height="150" rx="8" />{trace.frames.map((candidate, index) => { const current = candidate.points.find((item) => item.point_id === "current"); if (!current) return null; return <circle key={`${candidate.frame_index}-${index}`} cx={mapCoordinate(current.coordinates[0], -2, 2, 12, 228)} cy={mapCoordinate(current.coordinates[1], -1, 3, 138, 12)} r={candidate.frame_index === frame.frame_index ? 5 : 2.2} className={candidate.frame_index === frame.frame_index ? "plot-current" : "plot-trail"} />; })}</svg><dl className="comparison-metrics"><div><dt>f(x)</dt><dd>{frame.metrics.find((metric) => metric.metric_id === "objective")?.value.toPrecision(5)}</dd></div><div><dt>position</dt><dd>{point?.coordinates.map((value) => value.toFixed(3)).join(", ")}</dd></div></dl><Link className="text-link" to={`/traces/${trace.trace_id}`}>このTraceを単独再生</Link></article>;
}

async function loadComparison(comparisonId: string, signal: AbortSignal): Promise<Loaded> {
  const response = await fetch(`${siteBaseUrl()}data/comparisons.json`, { signal });
  if (!response.ok) throw new Error(`Comparison request failed (${response.status}).`);
  const index = parseComparisonIndex(await response.json());
  const comparison = index.comparisons.find((item) => item.comparison_id === comparisonId);
  if (!comparison) throw new EntityNotFoundError("比較ID", comparisonId);
  const traces = await Promise.all(comparison.members.map(async (member) => { const traceResponse = await fetch(`${siteBaseUrl()}data/traces/${member.trace_id}.json`, { signal }); if (!traceResponse.ok) throw new Error(`Trace request failed (${traceResponse.status}).`); return parseAlgorithmTrace(await traceResponse.json()); }));
  return { comparison, traces };
}
function latestFrame(frames: readonly TraceFrame[], evaluation: number): TraceFrame { return frames.reduce((current, candidate) => candidate.oracle_evaluations <= evaluation ? candidate : current, frames[0]); }
function mapCoordinate(value: number, min: number, max: number, start: number, end: number): number { return start + ((value - min) / (max - min)) * (end - start); }
