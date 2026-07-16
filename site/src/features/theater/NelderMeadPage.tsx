import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import type { AlgorithmTrace, TraceFrame, TraceIndexEntry, TracePoint } from "../../contracts/trace";
import type { DerivedMediaEntry } from "../../contracts/derived-media";
import type { GuidedStoryStep, VisualizationScenario } from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import {
  contourSegments,
  mapX,
  mapY,
  objectivePlotSpec,
  type PlotBounds,
} from "../visualization/objectivePlot";
import { PlaybackControls } from "../playback/PlaybackControls";
import { usePlayback } from "../playback/usePlayback";
import { ObjectiveGoalCues } from "../visualization/ObjectiveGoalCues";
import { ScenarioLessonPanel } from "../visualization/ScenarioLessonPanel";
import { GuidedStoryPanel } from "../visualization/GuidedStoryPanel";
import { LinkedSurfaceView } from "../visualization/LinkedSurfaceView";
import { ScenarioContextPanel } from "./ScenarioContextPanel";

interface NelderMeadVisualizationProps {
  trace: AlgorithmTrace;
  scenario: VisualizationScenario;
  entries: readonly TraceIndexEntry[];
  onTraceChange(traceId: string): void;
  derivedMedia?: DerivedMediaEntry;
}

type RankedVertex = { point: TracePoint; rank: "best" | "second-worst" | "worst" };

const plot = { left: 46, right: 514, top: 24, bottom: 336 } as const;

export function NelderMeadVisualization({
  trace,
  scenario,
  entries,
  derivedMedia,
  onTraceChange,
}: NelderMeadVisualizationProps) {
  const playback = usePlayback(trace.trace_id, trace.frames);
  const [guidedStep, setGuidedStep] = useState<GuidedStoryStep | null>(null);
  const frame = playback.currentFrame;
  const spec = useMemo(() => objectivePlotSpec(trace.objective), [trace.objective]);
  const contours = useMemo(() => contourSegments(spec), [spec]);
  const vertices = rankedVertices(frame);
  const centroid = frame.points.find((point) => point.role === "centroid");
  const candidate = frame.points.find((point) => point.role === "trial-point");
  const operationVector = frame.vectors.find((vector) => vector.role === "movement");
  const shifted = trace.trace_id.endsWith("-shifted");
  const relatedEntries = entries.filter((entry) => entry.profile_id === "PROFILE_NELDER_MEAD_2D");
  const chooseTrace = (objectiveId: string, useShifted: boolean) => {
    const next = relatedEntries.find(
      (entry) => entry.objective_id === objectiveId && entry.trace_id.endsWith("-shifted") === useShifted,
    );
    if (next) onTraceChange(next.trace_id);
  };
  const explanation = operationExplanation(frame);
  const visibleLayers = new Set(guidedStep?.visible_layers ?? scenario.artifact.observable_ids);
  const bestSoFar = trace.frames
    .flatMap((candidateFrame) => candidateFrame.points.map((point) => point.value))
    .filter((value): value is number => value !== null)
    .reduce((best, value) => Math.min(best, value), Number.POSITIVE_INFINITY);
  const thumbnail = derivedMedia?.files.find((file) => file.media_kind === "thumbnail");
  const staticPng = derivedMedia?.files.find((file) => file.media_kind === "static_png");
  const staticSvg = derivedMedia?.files.find((file) => file.media_kind === "static_svg");
  const animatedGif = derivedMedia?.files.find((file) => file.media_kind === "animated_gif");
  const webm = derivedMedia?.files.find((file) => file.media_kind === "webm");

  return (
    <article className="atlas-page nm-theater">
      <header className="atlas-page-header nm-page-header">
        <div>
          <p className="eyebrow">Method Theater · executable_trace</p>
          <h1>Nelder–Meadの幾何操作</h1>
          <p>等高線と単体の役割を重ね、候補をなぜ受理・却下したかまで追います。</p>
        </div>
        <div className="visualization-badges" aria-label="可視化artifact情報">
          <span>AlgorithmTrace {trace.contract_version}</span>
          <span>{scenario.artifact.artifact_kind}</span>
          <span>{scenario.artifact.renderer_family} {scenario.artifact.renderer_contract_version}</span>
        </div>
      </header>

      <section className="visualization-switches" aria-label="Nelder–Mead表示条件">
        <label>
          <span>目的関数 / Objective</span>
          <select
            aria-label="目的関数"
            onChange={(event) => chooseTrace(event.target.value, shifted)}
            value={trace.objective_id}
          >
            <option value="OBJECTIVE_QUADRATIC_2D">細長い二次関数 / Quadratic</option>
            <option value="OBJECTIVE_ROSENBROCK_2D">Rosenbrock関数 / Rosenbrock</option>
          </select>
        </label>
        <label>
          <span>初期simplex / Initial simplex</span>
          <select
            aria-label="初期simplex"
            onChange={(event) => chooseTrace(trace.objective_id, event.target.value === "shifted")}
            value={shifted ? "shifted" : "standard"}
          >
            <option value="standard">標準 / Standard</option>
            <option value="shifted">別の初期位置 / Shifted</option>
          </select>
        </label>
      </section>

      <ScenarioContextPanel scenario={scenario} />
      <ScenarioLessonPanel scenario={scenario} />
      <GuidedStoryPanel
        activeStep={guidedStep}
        onStepChange={setGuidedStep}
        playback={playback}
        scenario={scenario}
      />
      <section className="nm-contract" aria-label="現在の操作">
        <strong>{frame.event_label_ja} / {frame.event_label_en}</strong>
        <span>iteration {frame.iteration} · evaluations {frame.oracle_evaluations}</span>
        <span className={`decision-badge decision-${frame.decision}`}>{decisionLabel(frame)}</span>
        <span>best f = {objectiveMetric(frame)}</span>
      </section>
      <ObjectiveGoalCues
        bestValue={Number.isFinite(bestSoFar) ? bestSoFar : null}
        currentPoint={vertices[0]?.point.coordinates}
        initialPoint={initialPointArray(trace)}
        knownReferenceDisplay={scenario.lesson.known_reference_display}
        objective={trace.objective}
        terminalReason={trace.terminal_summary_ja}
      />
      <PlaybackControls playback={playback} />

      <div className="nm-layout">
        <figure className="explanatory-figure">
          <svg
            className={`nm-plot operation-${frame.event_type}${guidedStep ? " guided-active" : ""}`}
            data-guided-focus={guidedStep?.focus_target}
            data-viewport-preset={guidedStep?.viewport_preset}
            viewBox="0 0 560 360"
            role="img"
            aria-labelledby="nm-plot-title nm-plot-description"
            data-testid="nelder-mead-explanatory-plot"
          >
            <title id="nm-plot-title">{spec.expression}上のNelder–Mead単体</title>
            <desc id="nm-plot-description">{staticSummary(frame, vertices, centroid, candidate)}</desc>
            <defs>
              <marker id="nm-arrow" markerHeight="7" markerWidth="7" orient="auto" refX="6" refY="3.5">
                <path d="M0,0 L7,3.5 L0,7 z" className="nm-arrow-head" />
              </marker>
            </defs>
            <rect className="objective-background" x="0" y="0" width="560" height="360" rx="12" />
            {visibleLayers.has("objective_value") && <ContourLayer bounds={spec.bounds} contours={contours} />}
            <line className="plot-axis" x1={plot.left} x2={plot.right} y1={plot.bottom} y2={plot.bottom} />
            <line className="plot-axis" x1={plot.left} x2={plot.left} y1={plot.top} y2={plot.bottom} />
            <text className="plot-axis-label" x={plot.right - 4} y={plot.bottom - 7}>x</text>
            <text className="plot-axis-label" x={plot.left + 7} y={plot.top + 12}>y</text>
            <text className="plot-range-label" x={plot.left} y={plot.bottom + 17}>x [{spec.bounds.xMin}, {spec.bounds.xMax}]</text>
            <text className="plot-range-label" x={plot.right - 70} y={plot.top + 12}>minimize</text>
            <InitialMarker point={initialPointArray(trace)} bounds={spec.bounds} />
            {knownOptimum(trace.objective) && <KnownOptimumMarker point={knownOptimum(trace.objective)!} bounds={spec.bounds} />}
            {visibleLayers.has("simplex_vertices") && <polygon
              className="nm-simplex"
              points={vertices.map(({ point }) => pointCoordinates(point, spec.bounds)).join(" ")}
            />}
            {visibleLayers.has("accepted_operation") && operationVector && (
              <line
                className="nm-operation-vector"
                markerEnd="url(#nm-arrow)"
                x1={mapX(operationVector.origin[0], spec.bounds, plot.left, plot.right)}
                y1={mapY(operationVector.origin[1], spec.bounds, plot.top, plot.bottom)}
                x2={mapX(operationVector.origin[0] + operationVector.components[0], spec.bounds, plot.left, plot.right)}
                y2={mapY(operationVector.origin[1] + operationVector.components[1], spec.bounds, plot.top, plot.bottom)}
              />
            )}
            {visibleLayers.has("simplex_vertices") && vertices.map((vertex) => (
              <VertexMarker key={vertex.point.point_id} vertex={vertex} bounds={spec.bounds} />
            ))}
            {visibleLayers.has("accepted_operation") && centroid && <CentroidMarker point={centroid} bounds={spec.bounds} />}
            {visibleLayers.has("accepted_operation") && candidate && <CandidateMarker point={candidate} bounds={spec.bounds} accepted={frame.decision === "accepted"} />}
          </svg>
          <figcaption>
            objective metadataの表示範囲 x=[{spec.bounds.xMin}, {spec.bounds.xMax}], y=[{spec.bounds.yMin}, {spec.bounds.yMax}] から等高線を生成。
          </figcaption>
        </figure>

        <aside className="nm-explanation" aria-label="操作の説明">
          <p className="operation-kicker">{operationSymbol(frame.event_type)} {frame.event_type}</p>
          <h2>{frame.event_label_ja} / {frame.event_label_en}</h2>
          <p className="operation-reason">{explanation}</p>
          <dl>
            <div><dt>Objective</dt><dd>{spec.expression}</dd></div>
            <div><dt>Initial</dt><dd>{initialPoint(trace)}</dd></div>
            <div><dt>Parameters</dt><dd>{parameters(trace.parameters)}</dd></div>
            <div><dt>Candidate</dt><dd>{candidate ? `${formatPoint(candidate)} · ${decisionLabel(frame)}` : "このframeでは候補点なし"}</dd></div>
          </dl>
          <div className="shape-legend" aria-label="点の役割凡例">
            <span><i className="legend-circle" />Best</span>
            <span><i className="legend-square" />Second-worst</span>
            <span><i className="legend-triangle" />Worst</span>
            <span><i className="legend-diamond" />Candidate</span>
            <span><i className="legend-cross">＋</i>Centroid</span>
          </div>
          <p className="atlas-note">{scenario.lesson.limitations_ja}。初期simplexや目的関数を変えると経路は変わります。</p>
          <Link className="text-link" to={`/methods/${trace.method_id}`}>手法ページへ</Link>
        </aside>
      </div>

      <LinkedSurfaceView
        currentFrameIndex={playback.currentFrameIndex}
        onFrameSelect={playback.seekToFrame}
        trace={trace}
      />

      {derivedMedia && thumbnail && (
        <section className="derived-media-card" aria-labelledby="derived-media-heading">
          <div className="derived-media-preview">
            {webm ? (
              <video
                aria-label={derivedMedia.alt_ja}
                controls
                height={webm.height}
                poster={`${siteBaseUrl()}data/${thumbnail.path}`}
                preload="metadata"
                width={webm.width}
              >
                <source src={`${siteBaseUrl()}data/${webm.path}`} type={webm.media_type} />
                <track
                  default
                  kind="captions"
                  label="日本語 / English"
                  src={`${siteBaseUrl()}data/${derivedMedia.captions.path}`}
                  srcLang="ja"
                />
              </video>
            ) : (
              <img
                alt={derivedMedia.alt_ja}
                height={thumbnail.height}
                src={`${siteBaseUrl()}data/${thumbnail.path}`}
                width={thumbnail.width}
              />
            )}
          </div>
          <div>
            <p className="eyebrow">Derived media · deterministic</p>
            <h2 id="derived-media-heading">再利用できる静止画・animation</h2>
            <p>{derivedMedia.caption_ja}</p>
            <p className="atlas-note">frame {derivedMedia.frame_index + 1} · {derivedMedia.viewport_preset} · {derivedMedia.license_spdx_id}</p>
            <div className="derived-media-links">
              {staticPng && <a href={`${siteBaseUrl()}data/${staticPng.path}`}>PNGを開く</a>}
              {staticSvg && <a href={`${siteBaseUrl()}data/${staticSvg.path}`}>SVGを開く</a>}
              {animatedGif && <a href={`${siteBaseUrl()}data/${animatedGif.path}`}>GIFを開く</a>}
              {webm && <a href={`${siteBaseUrl()}data/${webm.path}`}>WebMを開く</a>}
              <a href={`${siteBaseUrl()}data/${derivedMedia.captions.path}`}>字幕を開く</a>
              <a href={`${siteBaseUrl()}data/${derivedMedia.transcript.path}`}>Transcriptを開く</a>
            </div>
            <small>{derivedMedia.attribution}</small>
          </div>
        </section>
      )}

      <details className="text-alternative" open>
        <summary>静的summary / Text alternative</summary>
        <p>{staticSummary(frame, vertices, centroid, candidate)}</p>
        <ul>
          {vertices.map(({ point, rank }) => (
            <li key={point.point_id}><strong>{rankLabel(rank)}</strong> {formatPoint(point)} · f={formatValue(point.value)}</li>
          ))}
        </ul>
      </details>
    </article>
  );
}

function ContourLayer({
  bounds,
  contours,
}: {
  bounds: PlotBounds;
  contours: ReturnType<typeof contourSegments>;
}) {
  return (
    <g className="objective-contours" aria-hidden="true">
      {contours.map((segment, index) => (
        <line
          key={`${segment.level}-${index}`}
          x1={mapX(segment.start.x, bounds, plot.left, plot.right)}
          y1={mapY(segment.start.y, bounds, plot.top, plot.bottom)}
          x2={mapX(segment.end.x, bounds, plot.left, plot.right)}
          y2={mapY(segment.end.y, bounds, plot.top, plot.bottom)}
        />
      ))}
    </g>
  );
}

function VertexMarker({ vertex, bounds }: { vertex: RankedVertex; bounds: PlotBounds }) {
  const x = mapX(vertex.point.coordinates[0], bounds, plot.left, plot.right);
  const y = mapY(vertex.point.coordinates[1], bounds, plot.top, plot.bottom);
  const label = vertex.rank === "best" ? "B" : vertex.rank === "second-worst" ? "S" : "W";
  return (
    <g className={`nm-vertex nm-vertex-${vertex.rank}`}>
      {vertex.rank === "best" && <circle cx={x} cy={y} r="9" />}
      {vertex.rank === "second-worst" && <rect x={x - 8} y={y - 8} width="16" height="16" />}
      {vertex.rank === "worst" && <polygon points={`${x},${y - 10} ${x - 10},${y + 8} ${x + 10},${y + 8}`} />}
      <text x={x + 11} y={y - 10}>{label}</text>
    </g>
  );
}

function CandidateMarker({ point, bounds, accepted }: { point: TracePoint; bounds: PlotBounds; accepted: boolean }) {
  const x = mapX(point.coordinates[0], bounds, plot.left, plot.right);
  const y = mapY(point.coordinates[1], bounds, plot.top, plot.bottom);
  return (
    <g className={`nm-candidate ${accepted ? "candidate-accepted" : "candidate-rejected"}`}>
      <polygon points={`${x},${y - 10} ${x + 10},${y} ${x},${y + 10} ${x - 10},${y}`} />
      <text x={x + 12} y={y + 4}>C</text>
    </g>
  );
}

function CentroidMarker({ point, bounds }: { point: TracePoint; bounds: PlotBounds }) {
  const x = mapX(point.coordinates[0], bounds, plot.left, plot.right);
  const y = mapY(point.coordinates[1], bounds, plot.top, plot.bottom);
  return (
    <g className="nm-centroid">
      <line x1={x - 7} x2={x + 7} y1={y} y2={y} />
      <line x1={x} x2={x} y1={y - 7} y2={y + 7} />
      <text x={x + 9} y={y + 13}>centroid</text>
    </g>
  );
}

function InitialMarker({ point, bounds }: { point: readonly number[]; bounds: PlotBounds }) {
  const x = mapX(point[0], bounds, plot.left, plot.right);
  const y = mapY(point[1], bounds, plot.top, plot.bottom);
  return <g className="nm-initial-marker"><circle cx={x} cy={y} r="7" /><text x={x + 9} y={y - 8}>start</text></g>;
}

function KnownOptimumMarker({ point, bounds }: { point: readonly number[]; bounds: PlotBounds }) {
  const x = mapX(point[0], bounds, plot.left, plot.right);
  const y = mapY(point[1], bounds, plot.top, plot.bottom);
  return <g className="nm-optimum-marker"><line x1={x - 8} x2={x + 8} y1={y} y2={y} /><line x1={x} x2={x} y1={y - 8} y2={y + 8} /><text x={x + 9} y={y + 13}>optimum</text></g>;
}

function rankedVertices(frame: TraceFrame): RankedVertex[] {
  const vertices = frame.points.filter(
    (point): point is TracePoint & { value: number } =>
      point.role === "simplex-vertex" && point.value !== null,
  );
  return [...vertices]
    .sort((left, right) => left.value - right.value)
    .map((point, index) => ({
      point,
      rank: index === 0 ? "best" : index === 1 ? "second-worst" : "worst",
    }));
}

function pointCoordinates(point: TracePoint, bounds: PlotBounds): string {
  return `${mapX(point.coordinates[0], bounds, plot.left, plot.right)},${mapY(point.coordinates[1], bounds, plot.top, plot.bottom)}`;
}

function decisionLabel(frame: TraceFrame): string {
  if (frame.decision === "accepted") return "受理 / Accepted";
  if (frame.decision === "rejected") return "却下 / Rejected";
  return "判定なし / N/A";
}

function operationExplanation(frame: TraceFrame): string {
  const accepted = frame.decision === "accepted";
  const copy: Record<string, string> = {
    initialize: "初期simplexの3頂点を評価し、best / second-worst / worstを決めます。",
    order: "目的関数値の小さい順に頂点を並べ、次の操作の基準を作ります。",
    reflect: accepted
      ? "最悪点を重心の反対側へ反射した候補が改善したため受理しました。"
      : "反射候補が十分に改善しなかったため、次の収縮判断へ進みます。",
    expand: "反射点よりさらに先の拡大候補が改善したため、拡大点を受理しました。",
    outside_contract: "反射点側へ外側収縮し、最悪点より改善した候補を受理しました。",
    inside_contract: "重心側へ内側収縮し、最悪点より改善した候補を受理しました。",
    shrink: "収縮候補が最悪点を改善しなかったため却下し、bestへ向けて単体全体を縮小しました。",
    stop: "収束条件または評価予算に達したため、このTraceを停止しました。",
  };
  return copy[frame.event_type] ?? `未登録の操作です: ${frame.event_type}`;
}

function operationSymbol(eventType: string): string {
  return {
    initialize: "◎",
    order: "≡",
    reflect: "↔",
    expand: "⇢",
    outside_contract: "↘",
    inside_contract: "↙",
    shrink: "⇥",
    stop: "■",
  }[eventType] ?? "•";
}

function staticSummary(
  frame: TraceFrame,
  vertices: readonly RankedVertex[],
  centroid: TracePoint | undefined,
  candidate: TracePoint | undefined,
): string {
  const ranked = vertices.map(({ point, rank }) => `${rankLabel(rank)} ${formatPoint(point)}`).join("、");
  return `${frame.event_label_ja}。${ranked}。重心 ${centroid ? formatPoint(centroid) : "なし"}。候補 ${candidate ? formatPoint(candidate) : "なし"}。${decisionLabel(frame)}。${operationExplanation(frame)}`;
}

function rankLabel(rank: RankedVertex["rank"]): string {
  return rank === "best" ? "Best" : rank === "second-worst" ? "Second-worst" : "Worst";
}

function formatPoint(point: TracePoint): string {
  return `[${point.coordinates.map((value) => value.toFixed(3)).join(", ")}]`;
}

function formatValue(value: number | null): string {
  return value === null ? "n/a" : value.toPrecision(5);
}

function objectiveMetric(frame: TraceFrame): string {
  return frame.metrics.find((metric) => metric.metric_id === "objective")?.value.toPrecision(5) ?? "n/a";
}

function initialPoint(trace: AlgorithmTrace): string {
  const point = initialPointArray(trace);
  return point.length ? `[${point.join(", ")}]` : "n/a";
}

function initialPointArray(trace: AlgorithmTrace): number[] {
  const point = trace.initial_state.point;
  return Array.isArray(point) && point.every((value): value is number => typeof value === "number") ? point : [];
}

function knownOptimum(objective: AlgorithmTrace["objective"]): number[] | undefined {
  const optimum = objective.optimum;
  if (typeof optimum !== "object" || optimum === null || Array.isArray(optimum)) return undefined;
  const point = optimum.point;
  return Array.isArray(point) && point.every((value): value is number => typeof value === "number") ? point : undefined;
}

function parameters(values: AlgorithmTrace["parameters"]): string {
  return Object.entries(values).map(([key, value]) => `${key}=${String(value)}`).join(" · ");
}
