import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import {
  parseComparisonIndex,
  type ComparisonMember,
  type ComparisonSet,
} from "../../contracts/comparisons";
import { findEntity } from "../../contracts/entity-links";
import { parseLearningSliceArtifact, type LearningSliceArtifact } from "../../contracts/learning-slices";
import { parseSiteManifest } from "../../contracts/manifest";
import { parseAlgorithmTrace, type AlgorithmTrace, type TraceFrame } from "../../contracts/trace";
import {
  parseVisualizationScenarioIndex,
  type VisualizationScenario,
} from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";
import { buildAtlasNavigation } from "../../state/atlas-navigation";
import {
  atlasStateFromSearch,
  JourneyLink,
  patchJourneyState,
} from "../../state/journey-navigation";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { PlaybackControls } from "../playback/PlaybackControls";
import { usePlayback } from "../playback/usePlayback";
import { comparisonRoute } from "./compare-routes";
import { PageOrientation } from "../../components/PageOrientation";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { LearningSliceRenderer } from "../learning-slices/renderer-registry";
import { ObjectiveGoalCues } from "../visualization/ObjectiveGoalCues";
import { ScenarioLessonPanel } from "../visualization/ScenarioLessonPanel";
import { GenericMetricHistory } from "../visualization/GenericMetricHistory";
import {
  contourSegments,
  mapX,
  mapY,
  normalizedVectorEnd,
  objectivePlotSpec,
  type ObjectivePlotSpec,
} from "../visualization/objectivePlot";

type LoadedBase = {
  comparison: ComparisonSet;
  comparisons: ComparisonSet[];
};
type Loaded = LoadedBase & ({
  renderer: "trajectory";
  traces: AlgorithmTrace[];
  scenarios: VisualizationScenario[];
} | {
  renderer: "metric-history";
  traces: AlgorithmTrace[];
  scenarios: VisualizationScenario[];
} | {
  renderer: "learning-slice";
  artifact: LearningSliceArtifact;
  scenario: VisualizationScenario;
});

const trajectoryPlot = { left: 18, right: 282, top: 16, bottom: 176 } as const;
const historyPlot = { left: 46, right: 714, top: 22, bottom: 190 } as const;

export function ComparisonPage() {
  const { comparisonId = "" } = useParams();
  const location = useLocation();
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
          <p className="eyebrow">Compare Lab · fair case-bound comparison</p>
          <h1>{loaded?.comparison.title_ja ?? "比較条件を読み込み中"}</h1>
          <p>{loaded?.comparison.comparison_question ?? "何を固定し、何だけを変えた比較かを確認します。"}</p>
        </div>
      </header>
      <PageOrientation
        limits="表示される差はこのcase・instance・seed・budgetに限ります。ranking eligibilityがあっても普遍的な手法順位ではありません。"
        next={[{ label: "別の比較を選ぶ", to: "/compare" }, { label: "Caseへ戻る", to: loaded ? `/gallery/${loaded.comparison.case_id}` : "/gallery" }, { label: "1 runをTheaterで見る", to: "/theater" }]}
        purpose="同じもの・違うもの・見る指標を先に固定し、公平に解釈できる範囲だけを比較します。"
        readingSteps={["比較questionとcaseの定式化を確認します。", "fixed / changed / metricsとbudget alignmentを確認します。", "rendererで差を読み、単独run・Case・手法へ戻って理由を確かめます。"]}
      />
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!loaded && !error && <p role="status">比較条件を読み込み中…</p>}
      {loaded && <ComparisonExperience loaded={loaded} onPresetChange={(nextId) => {
        const state = atlasStateFromSearch(location.search);
        const nextState = state ? patchJourneyState(state, { comparisonId: nextId }) : undefined;
        const destination = nextState
          ? buildAtlasNavigation(comparisonRoute(nextId), location.search, nextState)
          : undefined;
        navigate(destination?.ok ? destination.to : comparisonRoute(nextId));
      }} />}
    </section>
  );
}

function ComparisonExperience({ loaded, onPresetChange }: { loaded: Loaded; onPresetChange(comparisonId: string): void }) {
  const { comparison, comparisons } = loaded;
  const links = useEntityLinks();
  const entity = (type: "case" | "method" | "scenario" | "trace", id: string) => (
    links.status === "ready" ? findEntity(links.index, type, id) : undefined
  );
  return (
    <>
      <section className="visualization-switches comparison-switches" aria-label="比較preset">
        <label>
          <span>比較question / Comparison</span>
          <select aria-label="比較preset" onChange={(event) => onPresetChange(event.target.value)} value={comparison.comparison_id}>
            {comparisons.map((item) => <option key={item.comparison_id} value={item.comparison_id}>{item.title_ja}</option>)}
          </select>
        </label>
      </section>
      <div className="visualization-badges comparison-artifact-badges" aria-label="比較artifact情報">
        <span>{comparison.mode}</span>
        <span>{[...new Set(comparison.members.map((member) => member.artifact.renderer_family))].join(" + ")}</span>
        <span>{comparison.identity_status} · {comparison.comparability}</span>
      </div>
      <ComparisonContract comparison={comparison} />
      {loaded.renderer === "trajectory" ? (
        <TrajectoryComparison comparison={comparison} scenarios={loaded.scenarios} traces={loaded.traces} />
      ) : loaded.renderer === "metric-history" ? (
        <MetricHistoryComparison comparison={comparison} scenarios={loaded.scenarios} traces={loaded.traces} />
      ) : (
        <ScenarioComparison artifact={loaded.artifact} comparison={comparison} scenario={loaded.scenario} />
      )}
      <section className="comparison-return-links" aria-label="比較の関連導線">
        <h2>同じcontextから確認する</h2>
        <JourneyLink journeyPatch={{ comparisonId: comparison.comparison_id }} to={comparison.canonical_url}>この比較の共有URL</JourneyLink>
        <JourneyLink to={entity("case", comparison.case_id)?.canonical_url ?? `/gallery/${comparison.case_id}`}>Case: {entity("case", comparison.case_id)?.label ?? comparison.case_id}</JourneyLink>
        {[...new Map(comparison.members.map((member) => [member.scenario_id, member])).values()].map((member) => {
          const scenario = entity("scenario", member.scenario_id);
          const theaterUrl = scenario?.canonical_url ?? entity("trace", member.artifact.artifact_id)?.canonical_url;
          return theaterUrl ? <JourneyLink journeyPatch={{ scenarioId: member.scenario_id, memberId: member.member_id, methodId: member.method_id }} key={member.scenario_id} to={theaterUrl}>Theater: {scenario?.label ?? member.label_ja}</JourneyLink> : null;
        })}
        {[...new Set(comparison.members.map((member) => member.method_id))].map((id) => (
          <JourneyLink journeyPatch={{ methodId: id }} key={id} to={entity("method", id)?.canonical_url ?? `/methods/${id}`}>手法: {entity("method", id)?.label ?? id}</JourneyLink>
        ))}
      </section>
      <EvidenceLinks sourceIds={comparison.source_ids} />
    </>
  );
}

function ComparisonContract({ comparison }: { comparison: ComparisonSet }) {
  return (
    <section className="comparison-contract-v2" aria-label="比較条件">
      <header><span>{comparison.mode}</span><h2>{comparison.comparison_question}</h2><p>{comparison.formulation_summary}</p></header>
      <div className="comparison-factor-grid">
        <article><h3>同じもの / Fixed</h3><ul>{comparison.fixed_factors.map((factor) => <li key={factor}>{factor}</li>)}</ul></article>
        <article><h3>違うもの / Changed</h3><ul>{comparison.changed_factors.map((factor) => <li key={factor}>{factor}</li>)}</ul></article>
        <article><h3>見る指標 / Metrics</h3><ul>{comparison.metrics.map((metric) => <li key={metric.metric_id}><strong>{metric.label_ja}</strong> · {metric.direction} · {metric.unit}</li>)}</ul></article>
      </div>
      <dl className="comparison-policy-grid">
        <div><dt>Budget / sync</dt><dd>{comparison.budget.metric} = {comparison.budget.value}</dd></div>
        <div><dt>Seed</dt><dd>{comparison.seed_policy}</dd></div>
        <div><dt>Stopping</dt><dd>{comparison.stopping_policy}</dd></div>
        <div><dt>Tuning</dt><dd>{comparison.tuning_policy}</dd></div>
        <div><dt>Ranking</dt><dd>{comparison.ranking_eligible ? "eligible in this context" : "forbidden"}</dd></div>
        <div><dt>Benchmark context</dt><dd>{comparison.benchmark_context_id}</dd></div>
      </dl>
      <p className="comparison-fairness"><strong>Fairness</strong> {comparison.fairness_note}</p>
      <p className="comparison-caveat">{comparison.caveat}</p>
    </section>
  );
}

function TrajectoryComparison({ comparison, traces, scenarios }: { comparison: ComparisonSet; traces: AlgorithmTrace[]; scenarios: VisualizationScenario[] }) {
  const timeline = useMemo(() => {
    const template = traces[0].frames[0];
    return Array.from({ length: comparison.budget.value + 1 }, (_, evaluation) => ({
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
  return (
    <>
      <ScenarioLessonPanel scenario={scenarios[0]} />
      <PlaybackControls playback={playback} />
      <div className="comparison-grid">
        {traces.map((trace, index) => (
          <ComparisonMemberCard
            key={trace.trace_id}
            comparisonMember={comparison.members.find((member) => member.artifact.artifact_id === trace.trace_id)!}
            contours={contours}
            evaluation={evaluation}
            markerIndex={index}
            scenario={scenarios[index]}
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

function ScenarioComparison({ artifact, comparison, scenario }: { artifact: LearningSliceArtifact; comparison: ComparisonSet; scenario: VisualizationScenario }) {
  return (
    <section className="scenario-comparison" aria-labelledby="scenario-comparison-title">
      <header><h2 id="scenario-comparison-title">{scenario.lesson.learning_objective.ja}</h2><p>{scenario.lesson.text_alternative.ja}</p></header>
      <LearningSliceRenderer artifact={artifact} />
      <div className="comparison-scenario-members">
        {comparison.members.map((member) => <article key={member.member_id}><span>{member.role}</span><h3>{member.label_ja}</h3><p>{parameterText(member.parameters)}</p></article>)}
      </div>
      <ScenarioLessonPanel scenario={scenario} />
      <p className="atlas-note"><strong>Takeaway:</strong> {comparison.takeaway}</p>
      <ul className="comparison-limitations">{comparison.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
    </section>
  );
}

function MetricHistoryComparison({
  comparison,
  traces,
  scenarios,
}: {
  comparison: ComparisonSet;
  traces: AlgorithmTrace[];
  scenarios: VisualizationScenario[];
}) {
  const timeline = useMemo(() => {
    const template = traces[0].frames[0];
    return Array.from({ length: comparison.budget.value + 1 }, (_, evaluation) => ({
      ...template,
      frame_index: evaluation,
      iteration: evaluation,
      oracle_evaluations: evaluation,
      elapsed_steps: evaluation,
      elapsed_time_ms: evaluation * 100,
      event_type: evaluation === 0 ? "initialize" : "comparison_tick",
      event_label_ja: evaluation === 0 ? "比較を開始" : "metric比較timeline",
      event_label_en: evaluation === 0 ? "Start comparison" : "Metric comparison timeline",
    }));
  }, [comparison.budget.value, traces]);
  const playback = usePlayback(comparison.comparison_id, timeline);
  const evaluation = playback.currentFrame.oracle_evaluations;
  const labels = Object.fromEntries(comparison.members.map((member) => [
    member.artifact.artifact_id,
    member.label_ja,
  ]));
  return (
    <>
      <ScenarioLessonPanel scenario={scenarios[0]} />
      <PlaybackControls playback={playback} />
      <p className="atlas-note comparison-probe-note">
        <strong>線が同じなのは意図どおりです。</strong> 3本とも1つのsolver非依存診断probeであり、solver別の実行結果ではありません。
      </p>
      <GenericMetricHistory
        budget={comparison.budget.value}
        evaluation={evaluation}
        labels={labels}
        metricIds={comparison.metrics.map((metric) => metric.metric_id)}
        traces={traces}
      />
      <div className="comparison-grid metric-comparison-members">
        {traces.map((trace) => {
          const member = comparison.members.find((candidate) => candidate.artifact.artifact_id === trace.trace_id)!;
          const frame = latestFrame(trace.frames, evaluation);
          const estimate = frame?.points.find((point) => point.point_id === "parameters");
          return (
            <article className="comparison-card" key={trace.trace_id}>
              <header><div><h2>{member.label_ja}</h2><small>{member.label_en}</small></div><span>{trace.terminal_status}</span></header>
              <p className="method-parameters">{parameterText(member.parameters)}</p>
              <dl className="comparison-metrics">
                <div><dt>evaluation</dt><dd>{frame?.oracle_evaluations ?? 0}</dd></div>
                <div><dt>[a, k, c]</dt><dd>{estimate?.coordinates.map((value) => value.toFixed(4)).join(", ") ?? "未評価"}</dd></div>
                {comparison.metrics.map((metric) => {
                  const value = frame?.metrics.find((candidate) => candidate.metric_id === metric.metric_id);
                  return <div key={metric.metric_id}><dt>{metric.label_ja}</dt><dd>{value ? value.value.toPrecision(5) : "未評価"}</dd></div>;
                })}
              </dl>
            </article>
          );
        })}
      </div>
      <p className="atlas-note"><strong>Takeaway:</strong> {comparison.takeaway}</p>
      <ul className="comparison-limitations">{comparison.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
      <p className="atlas-note comparison-ranking-warning">
        TRF・LM・L-BFGS-Bは実行していません。この表示から到達解、収束速度、wall-clock、一般的なsolver順位は比較できません。
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
  scenario,
}: {
  trace: AlgorithmTrace;
  comparisonMember: ComparisonMember;
  evaluation: number;
  markerIndex: number;
  spec: ObjectivePlotSpec;
  contours: ReturnType<typeof contourSegments>;
  scenario: VisualizationScenario;
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
      <ObjectiveGoalCues
        bestValue={bestSoFarValue(trace.frames, evaluation)}
        currentPoint={point?.coordinates}
        initialPoint={initialPoint(trace)}
        knownReferenceDisplay={scenario.lesson.known_reference_display}
        objective={trace.objective}
        terminalReason={trace.terminal_summary_ja}
      />
      {traceEntity?.canonical_url && <JourneyLink className="text-link" journeyPatch={{ scenarioId: comparisonMember.scenario_id, memberId: comparisonMember.member_id, methodId: comparisonMember.method_id }} to={traceEntity.canonical_url}>このTraceを単独再生</JourneyLink>}
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
  const x = (value: number) => historyPlot.left + (value / comparison.budget.value) * (historyPlot.right - historyPlot.left);
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
          const member = comparison.members.find((candidate) => candidate.artifact.artifact_id === trace.trace_id)!;
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
            const member = comparison.members.find((candidate) => candidate.artifact.artifact_id === trace.trace_id)!;
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
  const comparison = index.comparisons.find(
    (item) => item.comparison_id === comparisonId || item.aliases.includes(comparisonId),
  );
  if (!comparison) throw new EntityNotFoundError("比較ID", comparisonId);
  const families = new Set(comparison.members.map((member) => member.artifact.renderer_family));
  const isTraceComparison = [...families].every((family) => (
    family === "continuous_trajectory" || family === "generic_metric_history"
  ));
  if (isTraceComparison) {
    const traces = await Promise.all(comparison.members.map(async (member) => {
      const traceResponse = await fetch(`${siteBaseUrl()}data/${member.artifact.payload_path}`, { signal });
      if (!traceResponse.ok) throw new Error(`Trace request failed (${traceResponse.status}).`);
      const trace = parseAlgorithmTrace(await traceResponse.json());
      if (trace.trace_id !== member.artifact.artifact_id || trace.scenario_id !== member.scenario_id) {
        throw new Error(`Trace identity differs from comparison member ${member.member_id}.`);
      }
      return trace;
    }));
    const scenarios = comparison.members.map((member) => {
      const scenario = scenarioIndex.scenarios.find((candidate) => candidate.scenario_id === member.scenario_id);
      if (!scenario || !scenario.runs.some((run) => run.artifact_id === member.artifact.artifact_id)) {
        throw new Error(`Visualization scenario is missing for ${member.artifact.artifact_id}.`);
      }
      if (scenario.artifact.renderer_family !== member.artifact.renderer_family) {
        throw new Error(`Visualization renderer differs from comparison member ${member.member_id}.`);
      }
      return scenario;
    });
    return {
      comparison,
      comparisons: index.comparisons,
      renderer: families.has("generic_metric_history") ? "metric-history" : "trajectory",
      traces,
      scenarios,
    };
  }
  const family = comparison.members[0].artifact.renderer_family;
  if (family !== "feasible_region" && family !== "pareto_front") {
    throw new Error(`Comparison renderer is not implemented: ${family}.`);
  }
  const scenarioId = comparison.members[0].scenario_id;
  const scenario = scenarioIndex.scenarios.find((candidate) => candidate.scenario_id === scenarioId);
  if (!scenario || comparison.members.some((member) => member.scenario_id !== scenarioId)) {
    throw new Error("Scenario comparison members must share one canonical scenario.");
  }
  const artifactDescriptor = comparison.members[0].artifact;
  if (comparison.members.some((member) => member.artifact.payload_path !== artifactDescriptor.payload_path)) {
    throw new Error("Scenario comparison members must share one canonical artifact.");
  }
  const artifactResponse = await fetch(`${siteBaseUrl()}data/${artifactDescriptor.payload_path}`, { signal });
  if (!artifactResponse.ok) throw new Error(`Comparison artifact request failed (${artifactResponse.status}).`);
  const artifact = parseLearningSliceArtifact(await artifactResponse.json());
  if (artifact.artifact_id !== artifactDescriptor.artifact_id || artifact.renderer_family !== family) {
    throw new Error("Comparison artifact identity differs from its contract.");
  }
  return { comparison, comparisons: index.comparisons, renderer: "learning-slice", artifact, scenario };
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

function initialPoint(trace: AlgorithmTrace): number[] {
  const point = trace.initial_state.point;
  return Array.isArray(point) && point.every((value): value is number => typeof value === "number") ? point : [];
}

function bestSoFarValue(frames: readonly TraceFrame[], evaluation: number): number | null {
  const values = frames
    .filter((frame) => frame.oracle_evaluations <= evaluation)
    .flatMap((frame) => frame.points.map((point) => point.value))
    .filter((value): value is number => value !== null);
  return values.length ? Math.min(...values) : null;
}

function parameterText(parameters: Record<string, string | number | boolean>): string {
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
