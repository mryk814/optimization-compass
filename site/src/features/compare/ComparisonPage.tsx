import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  parseComparisonIndex,
  type ComparisonMember,
  type ComparisonSet,
} from "../../contracts/comparisons";
import { findEntity } from "../../contracts/entity-links";
import { parseSiteManifest } from "../../contracts/manifest";
import { parseAlgorithmTrace, type AlgorithmTrace, type TraceFrame } from "../../contracts/trace";
import {
  parseVisualizationScenarioIndex,
  type VisualizationScenario,
} from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { PlaybackControls } from "../playback/PlaybackControls";
import { usePlayback } from "../playback/usePlayback";
import { comparisonRoute } from "./compare-routes";
import {
  contourSegments,
  mapX,
  mapY,
  normalizedVectorEnd,
  objectivePlotSpec,
  type ObjectivePlotSpec,
} from "../visualization/objectivePlot";

type Loaded = {
  comparison: ComparisonSet;
  comparisons: ComparisonSet[];
  traces: AlgorithmTrace[];
  scenarios: VisualizationScenario[];
};

const trajectoryPlot = { left: 18, right: 282, top: 16, bottom: 176 } as const;
const historyPlot = { left: 46, right: 714, top: 22, bottom: 190 } as const;

export function ComparisonPage() {
  const { comparisonId = "" } = useParams();
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState<Loaded>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    const controller = new AbortController();
    setLoaded(undefined);
    setError(undefined);
    void loadComparison(comparisonId, controller.signal).then(setLoaded, (caught: unknown) => {
      if (!controller.signal.aborted) {
        setError(caught instanceof Error ? caught : new Error(String(caught)));
      }
    });
    return () => controller.abort();
  }, [comparisonId]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  return (
    <section className="atlas-page comparison-page">
      <header className="atlas-page-header comparison-page-header">
        <div>
          <p className="eyebrow">Compare Lab · executable_trace</p>
          <h1>手法を比較する</h1>
          <p>同じ等高線とoracle evaluation軸で、更新方向と目的値の推移を同期します。</p>
        </div>
      </header>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!loaded && !error && <p role="status">比較条件を読み込み中…</p>}
      {loaded && (
        <ComparisonPlayer
          {...loaded}
          onPresetChange={(nextId) => navigate(comparisonRoute(nextId))}
        />
      )}
    </section>
  );
}

function ComparisonPlayer({
  comparison,
  comparisons,
  traces,
  scenarios,
  onPresetChange,
}: Loaded & { onPresetChange(comparisonId: string): void }) {
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
  const spec = useMemo(() => objectivePlotSpec(traces[0].objective), [traces]);
  const contours = useMemo(() => contourSegments(spec, 22, 18), [spec]);
  const artifactKind = scenarios[0].artifact.artifact_kind;
  return (
    <>
      <section className="visualization-switches comparison-switches" aria-label="比較preset">
        <label>
          <span>現象preset / Phenomenon</span>
          <select
            aria-label="比較preset"
            onChange={(event) => onPresetChange(event.target.value)}
            value={comparison.comparison_id}
          >
            {comparisons.map((item) => (
              <option key={item.comparison_id} value={item.comparison_id}>
                {item.preset_id === "elongated-valley"
                  ? "細長い谷の振動 / Valley oscillation"
                  : "学習率過大の発散 / Divergence"}
              </option>
            ))}
          </select>
        </label>
      </section>
      <div className="visualization-badges comparison-artifact-badges" aria-label="比較artifact情報">
        <span>AlgorithmTrace 1.0.0</span>
        <span>{artifactKind}</span>
        <span>{comparison.renderer_families.join(" + ")} 1.0.0</span>
      </div>
      <section className="comparison-contract" aria-label="比較条件">
        <strong>{comparison.title_ja}</strong>
        <span>{comparison.title_en}</span>
        <span>{comparison.objective_expression}</span>
        <span>初期点 [{comparison.initial_point.join(", ")}] · budget {comparison.budget}</span>
        <span>{comparison.comparability} · sync={comparison.synchronization}</span>
        <p>{comparison.fairness_note}</p>
        <p className="comparison-caveat">{comparison.caveat}</p>
        <p className="comparison-caveat">{scenarios[0].lesson.limitations_ja}</p>
      </section>
      <PlaybackControls playback={playback} />
      <div className="comparison-grid">
        {traces.map((trace, index) => (
          <ComparisonMemberCard
            key={trace.trace_id}
            comparisonMember={comparison.members.find((member) => member.trace_id === trace.trace_id)!}
            contours={contours}
            evaluation={evaluation}
            markerIndex={index}
            spec={spec}
            trace={trace}
          />
        ))}
      </div>
      <ObjectiveHistory
        comparison={comparison}
        evaluation={evaluation}
        traces={traces}
      />
      <p className="atlas-note comparison-ranking-warning">
        この比較で一般的な優劣は断定できません。初期条件、parameter、oracle費用、停止条件が変われば挙動と比較可能性も変わります。
      </p>
    </>
  );
}

function ComparisonMemberCard({
  trace,
  comparisonMember,
  evaluation,
  markerIndex,
  spec,
  contours,
}: {
  trace: AlgorithmTrace;
  comparisonMember: ComparisonMember;
  evaluation: number;
  markerIndex: number;
  spec: ObjectivePlotSpec;
  contours: ReturnType<typeof contourSegments>;
}) {
  const links = useEntityLinks();
  const traceEntity = links.status === "ready" ? findEntity(links.index, "trace", trace.trace_id) : undefined;
  const frame = latestFrame(trace.frames, evaluation);
  const point = frame?.points.find((item) => item.point_id === "current");
  const gradient = frame?.vectors.find((vector) => vector.role === "gradient");
  const update = frame?.vectors.find((vector) => vector.role === "movement");
  const pointOutsideBounds = point ? isOutsideBounds(point.coordinates, spec) : false;
  const markerPoint = point ? clampToBounds(point.coordinates, spec) : undefined;
  const visibleFrames = trace.frames.filter((candidate) => candidate.oracle_evaluations <= evaluation);
  const trail = visibleFrames
    .map((candidate) => candidate.points.find((item) => item.point_id === "current"))
    .filter((candidate): candidate is NonNullable<typeof candidate> => candidate !== undefined);
  return (
    <article className={`comparison-card method-${markerIndex}`}>
      <header>
        <div>
          <h2>{comparisonMember.label_ja}</h2>
          <small>{comparisonMember.label_en}</small>
        </div>
        <span>{trace.terminal_status}</span>
      </header>
      <p className="method-parameters">{parameterText(comparisonMember.parameters)}</p>
      <p className="comparison-event">
        {frame ? `${frame.event_label_ja ?? frame.event_type} · evaluation ${frame.oracle_evaluations}` : "evaluation 0 · 未評価"}
      </p>
      <figure className="explanatory-figure comparison-figure">
        <svg
          className="comparison-plot"
          viewBox="0 0 300 194"
          role="img"
          aria-label={`${comparisonMember.label_ja}の等高線・軌跡・gradient・update vector`}
        >
          <defs>
            <marker id={`gradient-arrow-${markerIndex}`} markerHeight="6" markerWidth="6" orient="auto" refX="5" refY="3">
              <path d="M0,0 L6,3 L0,6 z" className="gradient-arrow-head" />
            </marker>
            <marker id={`update-arrow-${markerIndex}`} markerHeight="6" markerWidth="6" orient="auto" refX="5" refY="3">
              <path d="M0,0 L6,3 L0,6 z" className="update-arrow-head" />
            </marker>
          </defs>
          <rect className="objective-background" x="0" y="0" width="300" height="194" rx="8" />
          <g className="objective-contours" aria-hidden="true">
            {contours.map((segment, index) => (
              <line
                key={`${segment.level}-${index}`}
                x1={mapX(segment.start.x, spec.bounds, trajectoryPlot.left, trajectoryPlot.right)}
                y1={mapY(segment.start.y, spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}
                x2={mapX(segment.end.x, spec.bounds, trajectoryPlot.left, trajectoryPlot.right)}
                y2={mapY(segment.end.y, spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}
              />
            ))}
          </g>
          {trail.length > 1 && (
            <polyline
              className={`trajectory-line trajectory-${markerIndex}`}
              fill="none"
              points={trail.map((candidate) => `${mapX(candidate.coordinates[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)},${mapY(candidate.coordinates[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}`).join(" ")}
            />
          )}
          {!pointOutsideBounds && gradient && <VectorLine vector={gradient} spec={spec} className="gradient-vector" marker={`url(#gradient-arrow-${markerIndex})`} />}
          {!pointOutsideBounds && update && <VectorLine vector={update} spec={spec} className="update-vector" marker={`url(#update-arrow-${markerIndex})`} />}
          {markerPoint && <MethodMarker index={markerIndex} x={mapX(markerPoint[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)} y={mapY(markerPoint[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)} />}
          <g className="vector-labels" aria-hidden="true">
            <text x="20" y="188">∇ gradient</text>
            <text x="116" y="188">→ update</text>
          </g>
        </svg>
        <figcaption>{memberSummary(comparisonMember, frame, point, gradient, update)}</figcaption>
      </figure>
      {pointOutsideBounds && <p className="plot-boundary-note">表示範囲外 / Outside objective display bounds（境界markerで表示）</p>}
      <dl className="comparison-metrics">
        <div><dt>f(x)</dt><dd>{frame ? objectiveMetric(frame) : "未評価"}</dd></div>
        <div><dt>position</dt><dd>{point ? point.coordinates.map((value) => value.toFixed(3)).join(", ") : "未評価"}</dd></div>
      </dl>
      {traceEntity?.canonical_url && <Link className="text-link" to={traceEntity.canonical_url}>このTraceを単独再生</Link>}
    </article>
  );
}

function VectorLine({
  vector,
  spec,
  className,
  marker,
}: {
  vector: TraceFrame["vectors"][number];
  spec: ObjectivePlotSpec;
  className: string;
  marker: string;
}) {
  const end = normalizedVectorEnd(vector.origin, vector.components, spec.bounds);
  return (
    <line
      className={className}
      markerEnd={marker}
      x1={mapX(vector.origin[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)}
      y1={mapY(vector.origin[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}
      x2={mapX(end[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)}
      y2={mapY(end[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}
    />
  );
}

function MethodMarker({ index, x, y }: { index: number; x: number; y: number }) {
  if (index === 0) return <circle className="method-marker" cx={x} cy={y} r="6" />;
  if (index === 1) return <rect className="method-marker" x={x - 6} y={y - 6} width="12" height="12" />;
  return <polygon className="method-marker" points={`${x},${y - 7} ${x - 7},${y + 6} ${x + 7},${y + 6}`} />;
}

function ObjectiveHistory({
  comparison,
  traces,
  evaluation,
}: {
  comparison: ComparisonSet;
  traces: AlgorithmTrace[];
  evaluation: number;
}) {
  const values = traces.flatMap((trace) => trace.frames.map((frame) => Math.log10(objectiveValue(frame) + 1)));
  const maximum = Math.max(...values, 1);
  const x = (value: number) => historyPlot.left + (value / comparison.budget) * (historyPlot.right - historyPlot.left);
  const y = (value: number) => historyPlot.bottom - (Math.log10(value + 1) / maximum) * (historyPlot.bottom - historyPlot.top);
  return (
    <figure className="objective-history explanatory-figure">
      <h2>目的値 vs oracle evaluations</h2>
      <svg viewBox="0 0 760 216" role="img" aria-label="3手法の目的関数値を同じoracle evaluation軸で比較">
        <rect className="objective-background" x="0" y="0" width="760" height="216" rx="8" />
        <line className="plot-axis" x1={historyPlot.left} x2={historyPlot.right} y1={historyPlot.bottom} y2={historyPlot.bottom} />
        <line className="plot-axis" x1={historyPlot.left} x2={historyPlot.left} y1={historyPlot.top} y2={historyPlot.bottom} />
        <line className="history-cursor" x1={x(evaluation)} x2={x(evaluation)} y1={historyPlot.top} y2={historyPlot.bottom} />
        {traces.map((trace, index) => {
          const visible = trace.frames.filter((frame) => frame.oracle_evaluations <= evaluation);
          const member = comparison.members.find((candidate) => candidate.trace_id === trace.trace_id)!;
          return (
            <g key={trace.trace_id} className={`history-series history-${index}`}>
              <polyline points={visible.map((frame) => `${x(frame.oracle_evaluations)},${y(objectiveValue(frame))}`).join(" ")} />
              <text x={historyPlot.right - 160} y={historyPlot.top + 15 + index * 16}>{historySymbol(index)} {member.label_en}</text>
            </g>
          );
        })}
        <text className="plot-axis-label" x={historyPlot.right - 90} y={historyPlot.bottom - 8}>oracle evaluations</text>
        <text className="plot-axis-label" x={historyPlot.left + 7} y={historyPlot.top + 10}>log₁₀(f+1)</text>
      </svg>
      <figcaption>縦軸は大きな発散も同時に読めるようlog₁₀(f+1)表示。線種・記号・直接labelを併用し、色だけに依存しません。</figcaption>
      <details className="text-alternative" open>
        <summary>同期値のtext alternative</summary>
        <ul>
          {traces.map((trace) => {
            const member = comparison.members.find((candidate) => candidate.trace_id === trace.trace_id)!;
            const frame = latestFrame(trace.frames, evaluation);
            return <li key={trace.trace_id}><strong>{member.label_ja} / {member.label_en}</strong>: evaluation {frame?.oracle_evaluations ?? 0}, f={frame ? objectiveMetric(frame) : "未評価"}, status={trace.terminal_status}</li>;
          })}
        </ul>
      </details>
    </figure>
  );
}

async function loadComparison(comparisonId: string, signal: AbortSignal): Promise<Loaded> {
  const manifestResponse = await fetch(`${siteBaseUrl()}data/manifest.json`, { signal });
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());
  const [response, scenarioResponse] = await Promise.all([
    fetch(`${siteBaseUrl()}data/comparisons.json`, { signal }),
    fetch(`${siteBaseUrl()}data/${manifest.visualization_scenarios.path}`, { signal }),
  ]);
  if (!response.ok) throw new Error(`Comparison request failed (${response.status}).`);
  if (!scenarioResponse.ok) throw new Error(`Visualization scenario request failed (${scenarioResponse.status}).`);
  const index = parseComparisonIndex(await response.json());
  const scenarioIndex = parseVisualizationScenarioIndex(await scenarioResponse.json());
  if (scenarioIndex.dataset_version !== manifest.dataset_version) {
    throw new Error("Visualization scenario dataset version does not match the manifest.");
  }
  const comparison = index.comparisons.find((item) => item.comparison_id === comparisonId);
  if (!comparison) throw new EntityNotFoundError("比較ID", comparisonId);
  const traces = await Promise.all(comparison.members.map(async (member) => {
    const traceResponse = await fetch(`${siteBaseUrl()}data/traces/${member.trace_id}.json`, { signal });
    if (!traceResponse.ok) throw new Error(`Trace request failed (${traceResponse.status}).`);
    return parseAlgorithmTrace(await traceResponse.json());
  }));
  const scenarios = traces.map((trace) => {
    const scenario = scenarioIndex.scenarios.find((candidate) => candidate.scenario_id === trace.scenario_id);
    if (!scenario || !scenario.runs.some((run) => run.artifact_id === trace.trace_id)) {
      throw new Error(`Visualization scenario is missing for ${trace.trace_id}.`);
    }
    return scenario;
  });
  return { comparison, comparisons: index.comparisons, traces, scenarios };
}

function latestFrame(frames: readonly TraceFrame[], evaluation: number): TraceFrame | undefined {
  let match: TraceFrame | undefined;
  for (const frame of frames) {
    if (frame.oracle_evaluations > evaluation) break;
    match = frame;
  }
  return match;
}

function objectiveValue(frame: TraceFrame): number {
  return frame.metrics.find((metric) => metric.metric_id === "objective")?.value ?? 0;
}

function objectiveMetric(frame: TraceFrame): string {
  return objectiveValue(frame).toPrecision(5);
}

function parameterText(parameters: Record<string, number>): string {
  return Object.entries(parameters).map(([key, value]) => `${key}=${value}`).join(" · ");
}

function memberSummary(
  member: ComparisonMember,
  frame: TraceFrame | undefined,
  point: TraceFrame["points"][number] | undefined,
  gradient: TraceFrame["vectors"][number] | undefined,
  update: TraceFrame["vectors"][number] | undefined,
): string {
  if (!frame || !point) return `${member.label_ja}はまだ初期点を評価していません。`;
  const vector = (value: typeof gradient) => value ? `[${value.components.map((item) => item.toPrecision(3)).join(", ")}]` : "なし";
  return `${member.label_ja} / ${member.label_en}。evaluation ${frame.oracle_evaluations}、位置 [${point.coordinates.map((item) => item.toFixed(3)).join(", ")}], f=${objectiveMetric(frame)}。gradient ${vector(gradient)}、update ${vector(update)}。`;
}

function historySymbol(index: number): string {
  return index === 0 ? "●" : index === 1 ? "■" : "▲";
}

function isOutsideBounds(coordinates: readonly number[], spec: ObjectivePlotSpec): boolean {
  return coordinates[0] < spec.bounds.xMin
    || coordinates[0] > spec.bounds.xMax
    || coordinates[1] < spec.bounds.yMin
    || coordinates[1] > spec.bounds.yMax;
}

function clampToBounds(coordinates: readonly number[], spec: ObjectivePlotSpec): [number, number] {
  return [
    Math.min(spec.bounds.xMax, Math.max(spec.bounds.xMin, coordinates[0])),
    Math.min(spec.bounds.yMax, Math.max(spec.bounds.yMin, coordinates[1])),
  ];
}
