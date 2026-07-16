import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { parseSiteManifest } from "../../contracts/manifest";
import {
  parseDerivedMediaManifest,
  type DerivedMediaEntry,
} from "../../contracts/derived-media";
import {
  parseVisualizationScenarioIndex,
  type GuidedStoryStep,
  type VisualizationScenario,
} from "../../contracts/visualization-scenarios";
import {
  parseAlgorithmTrace,
  parseTraceIndex,
  type AlgorithmTrace,
  type TraceIndexEntry,
} from "../../contracts/trace";
import { PlaybackControls } from "./PlaybackControls";
import { usePlayback } from "./usePlayback";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { NelderMeadVisualization } from "../theater/NelderMeadPage";
import { ScenarioLessonPanel } from "../visualization/ScenarioLessonPanel";
import { GuidedStoryPanel } from "../visualization/GuidedStoryPanel";
import { LinkedSurfaceView } from "../visualization/LinkedSurfaceView";
import { GenericMetricHistory } from "../visualization/GenericMetricHistory";
import { ScenarioContextPanel } from "../theater/ScenarioContextPanel";

type LoadedTrace = {
  trace: AlgorithmTrace;
  entry: TraceIndexEntry;
  entries: TraceIndexEntry[];
  scenario?: VisualizationScenario;
  derivedMedia?: DerivedMediaEntry;
};

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

  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
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

function TracePlayer({ trace, entry, entries, scenario, derivedMedia }: LoadedTrace) {
  const navigate = useNavigate();
  if (trace.profile_id === "PROFILE_NELDER_MEAD_2D" && trace.trace_id !== "dummy-educational") {
    if (!scenario) throw new Error(`Visualization scenario is missing for ${trace.trace_id}.`);
    return (
      <NelderMeadVisualization
        entries={entries}
        onTraceChange={(traceId) => navigate(`/traces/${traceId}`)}
        scenario={scenario}
        derivedMedia={derivedMedia}
        trace={trace}
      />
    );
  }
  return <GenericTracePlayer entry={entry} scenario={scenario} trace={trace} />;
}

function GenericTracePlayer({ trace, entry, scenario }: Omit<LoadedTrace, "entries">) {
  const playback = usePlayback(trace.trace_id, trace.frames);
  const [guidedStep, setGuidedStep] = useState<GuidedStoryStep | null>(null);
  const frame = playback.currentFrame;
  const visibleLayers = new Set(guidedStep?.visible_layers ?? scenario?.artifact.observable_ids ?? []);
  const showAll = guidedStep === null;
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
      {scenario && <>
        <ScenarioContextPanel scenario={scenario} />
        <ScenarioLessonPanel scenario={scenario} />
        <GuidedStoryPanel
          activeStep={guidedStep}
          onStepChange={setGuidedStep}
          playback={playback}
          scenario={scenario}
        />
      </>}
      <PlaybackControls playback={playback} />
      {scenario?.artifact.renderer_family === "generic_metric_history" && (
        <GenericMetricHistory
          budget={trace.evaluation_budget}
          evaluation={frame.oracle_evaluations}
          traces={[trace]}
        />
      )}
      {scenario?.artifact.renderer_family === "continuous_trajectory" && (
        <LinkedSurfaceView
          currentFrameIndex={playback.currentFrameIndex}
          onFrameSelect={playback.seekToFrame}
          trace={trace}
        />
      )}
      <div
        className="trace-snapshot"
        aria-label="現在の完全スナップショット"
        data-guided-focus={guidedStep?.focus_target}
        data-viewport-preset={guidedStep?.viewport_preset}
      >
        {(showAll || visibleLayers.has("current_point") || visibleLayers.has("parameter_estimate")) && <section>
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
        </section>}
        {(showAll || visibleLayers.has("gradient") || visibleLayers.has("update_vector")) && <section>
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
        </section>}
        {(showAll || visibleLayers.has("objective_value") || frame.metrics.some((metric) => visibleLayers.has(metric.metric_id))) && <section>
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
        </section>}
      </div>
      <footer className="trace-summary">
        <span>{trace.terminal_status}</span>
        <p>{trace.terminal_summary_ja}</p>
        <EvidenceLinks sourceIds={trace.source_ids} />
      </footer>
    </article>
  );
}

async function loadIndexedTrace(traceId: string, signal: AbortSignal): Promise<LoadedTrace> {
  if (!traceId.trim()) throw new Error("Trace IDが指定されていません。");
  const baseUrl = (import.meta as ImportMeta & { env: { BASE_URL: string } }).env.BASE_URL;
  const manifestResponse = await fetch(`${baseUrl}data/manifest.json`, { signal });
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());

  const scenarioResponse = await fetch(`${baseUrl}data/${manifest.visualization_scenarios.path}`, { signal });
  if (!scenarioResponse.ok) throw new Error(`Visualization scenario request failed (${scenarioResponse.status}).`);
  const scenarioIndex = parseVisualizationScenarioIndex(await scenarioResponse.json());
  if (scenarioIndex.dataset_version !== manifest.dataset_version) {
    throw new Error("Visualization scenario dataset version does not match the manifest.");
  }
  const mediaResponse = await fetch(`${baseUrl}data/${manifest.derived_media.path}`, { signal });
  if (!mediaResponse.ok) throw new Error(`Derived media request failed (${mediaResponse.status}).`);
  const mediaManifest = parseDerivedMediaManifest(await mediaResponse.json());
  if (mediaManifest.dataset_version !== manifest.dataset_version) {
    throw new Error("Derived media dataset version does not match the manifest.");
  }

  const indexResponse = await fetch(`${baseUrl}data/${manifest.traces.path}`, { signal });
  if (!indexResponse.ok) throw new Error(`Trace index request failed (${indexResponse.status}).`);
  const indexBytes = new Uint8Array(await indexResponse.arrayBuffer());
  if (indexBytes.byteLength !== manifest.traces.bytes) {
    throw new Error("Trace index byte length does not match the manifest.");
  }
  const indexHash = await sha256Hex(indexBytes);
  if (indexHash !== manifest.traces.sha256) {
    throw new Error("Trace index SHA-256 does not match the manifest.");
  }
  const index = parseTraceIndex(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(indexBytes)));
  if (index.contract_version !== manifest.traces.index_version) {
    throw new Error("Trace index contract version does not match the manifest.");
  }
  if (index.dataset_version !== manifest.dataset_version) {
    throw new Error("Trace index dataset version does not match the manifest.");
  }
  const entry = index.traces.find((candidate) => candidate.trace_id === traceId);
  if (!entry) throw new EntityNotFoundError("Trace ID", traceId);

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
  const scenario = scenarioIndex.scenarios.find((candidate) => candidate.scenario_id === trace.scenario_id);
  const derivedMedia = mediaManifest.entries.find((candidate) => candidate.scenario_id === trace.scenario_id);
  if (trace.trace_id !== "dummy-educational") {
    if (!scenario) throw new Error(`Visualization scenario is missing for ${trace.trace_id}.`);
    if (!scenario.runs.some((run) => run.artifact_id === trace.trace_id)) {
      throw new Error(`Visualization scenario does not reference ${trace.trace_id}.`);
    }
    if (scenario.problem_instance_id !== trace.objective_id) {
      throw new Error(`Visualization scenario objective does not match ${trace.trace_id}.`);
    }
    if (derivedMedia && (
      derivedMedia.source_artifact_path !== scenario.artifact.payload_path
      || derivedMedia.source_artifact_sha256 !== scenario.artifact.payload_sha256
      || derivedMedia.renderer_family !== scenario.artifact.renderer_family
      || derivedMedia.renderer_contract_version !== scenario.artifact.renderer_contract_version
    )) {
      throw new Error("Derived media provenance does not match the visualization scenario.");
    }
  }
  return { trace, entry, entries: index.traces, scenario, derivedMedia };
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", Uint8Array.from(bytes).buffer);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}
