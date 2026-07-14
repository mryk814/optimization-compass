import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  parseAlgorithmTrace,
  parseTraceIndex,
  type AlgorithmTrace,
  type TraceIndexEntry,
} from "../../contracts/trace";
import { PlaybackControls } from "./PlaybackControls";
import { usePlayback } from "./usePlayback";

type LoadedTrace = { trace: AlgorithmTrace; entry: TraceIndexEntry };

export function TraceDemoPage() {
  const { traceId = "" } = useParams();
  const [loaded, setLoaded] = useState<LoadedTrace>();
  const [error, setError] = useState<Error>();

  useEffect(() => {
    const controller = new AbortController();
    setLoaded(undefined);
    setError(undefined);
    void loadIndexedTrace(traceId, controller.signal).then(setLoaded, (caught: unknown) => {
      if (!controller.signal.aborted) {
        setError(caught instanceof Error ? caught : new Error(String(caught)));
      }
    });
    return () => controller.abort();
  }, [traceId]);

  if (error) {
    return (
      <section className="trace-page">
        <h1>AlgorithmTraceを開けません</h1>
        <p role="alert">{error.message}</p>
      </section>
    );
  }
  if (!loaded) return <p role="status">AlgorithmTraceを読み込み中…</p>;
  return <TracePlayer key={loaded.trace.trace_id} {...loaded} />;
}

function TracePlayer({ trace, entry }: LoadedTrace) {
  const playback = usePlayback(trace.trace_id, trace.frames);
  const frame = playback.currentFrame;
  return (
    <article className="trace-page">
      <header className="trace-header">
        <div>
          <p className="eyebrow">AlgorithmTrace {trace.contract_version}</p>
          <h1>{entry.title_ja}</h1>
          <p>{entry.title_en}</p>
        </div>
        <dl className="trace-identity">
          <div><dt>Method</dt><dd>{trace.method_id}</dd></div>
          <div><dt>Objective</dt><dd>{trace.objective_id}</dd></div>
          <div><dt>Dataset</dt><dd>{trace.dataset_version}</dd></div>
        </dl>
      </header>
      <PlaybackControls playback={playback} />
      <div className="trace-snapshot" aria-label="現在の完全スナップショット">
        <section>
          <h2>Points</h2>
          {frame.points.length === 0 ? <p>点データなし</p> : (
            <ul>
              {frame.points.map((point) => (
                <li key={point.point_id}>
                  <strong>{point.label_ja}</strong>
                  <code>[{point.coordinates.join(", ")}]</code>
                  {point.value !== null && <span>f = {point.value}</span>}
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h2>Vectors</h2>
          {frame.vectors.length === 0 ? <p>ベクトルなし</p> : (
            <ul>
              {frame.vectors.map((vector) => (
                <li key={vector.vector_id}>
                  <strong>{vector.label_ja}</strong>
                  <code>[{vector.components.join(", ")}]</code>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h2>Metrics</h2>
          {frame.metrics.length === 0 ? <p>指標なし</p> : (
            <ul>
              {frame.metrics.map((metric) => (
                <li key={metric.metric_id}>
                  <strong>{metric.label_ja}</strong>
                  <span>{metric.value}{metric.unit ? ` ${metric.unit}` : ""}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
      <footer className="trace-summary">
        <span>{trace.terminal_status}</span>
        <p>{trace.terminal_summary_ja}</p>
        <small>Sources: {trace.source_ids.join(", ")}</small>
      </footer>
    </article>
  );
}

async function loadIndexedTrace(traceId: string, signal: AbortSignal): Promise<LoadedTrace> {
  if (!traceId.trim()) throw new Error("Trace IDが指定されていません。");
  const baseUrl = (import.meta as ImportMeta & { env: { BASE_URL: string } }).env.BASE_URL;
  const indexResponse = await fetch(`${baseUrl}data/traces/index.json`, { signal });
  if (!indexResponse.ok) throw new Error(`Trace index request failed (${indexResponse.status}).`);
  const index = parseTraceIndex(await indexResponse.json());
  const entry = index.traces.find((candidate) => candidate.trace_id === traceId);
  if (!entry) throw new Error(`Trace ID「${traceId}」は公開indexに存在しません。`);

  const response = await fetch(`${baseUrl}data/traces/${entry.path}`, { signal });
  if (!response.ok) throw new Error(`AlgorithmTrace request failed (${response.status}).`);
  const trace = parseAlgorithmTrace(await response.json());
  const references = {
    trace_id: entry.trace_id,
    dataset_version: index.dataset_version,
    data_version: index.data_version,
    method_id: entry.method_id,
    profile_id: entry.profile_id,
    objective_id: entry.objective_id,
    scenario_id: entry.scenario_id,
  } as const;
  for (const [field, expected] of Object.entries(references)) {
    if (trace[field as keyof typeof references] !== expected) {
      throw new Error(`AlgorithmTrace ${field} does not match its index entry.`);
    }
  }
  return { trace, entry };
}
