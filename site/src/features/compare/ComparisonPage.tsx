import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import {
  parseComparisonIndex,
  type ComparisonMember,
  type ComparisonSet,
} from "../../contracts/comparisons";
import { findEntity } from "../../contracts/entity-links";
import {
  parseLearningSliceArtifact,
  type LearningSliceArtifact,
  type ParetoFrontArtifact,
} from "../../contracts/learning-slices";
import { parseSiteManifest } from "../../contracts/manifest";
import {
  parseSearchTreeArtifact,
  parseSearchTreeFramePayload,
  parseSearchTreeIndex,
  type SearchTreeArtifact,
} from "../../contracts/search-tree";
import {
  parseSurrogateUncertaintyPayload,
  type SurrogateUncertaintyPayload,
} from "../../contracts/surrogate-uncertainty";
import { parseAlgorithmTrace, type AlgorithmTrace, type TraceFrame, type TracePoint } from "../../contracts/trace";
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
import { comparisonRoute, firstMemberPerScenario } from "./compare-routes";
import { comparisonModeLabel, rendererFamilyLabel } from "./compare-catalog";
import { PageOrientation } from "../../components/PageOrientation";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { LearningSliceRenderer } from "../learning-slices/renderer-registry";
import { SearchTreeRenderer } from "../search-tree/SearchTreeRenderer";
import { ObjectiveGoalCues } from "../visualization/ObjectiveGoalCues";
import { GenericMetricHistory } from "../visualization/GenericMetricHistory";
import { SurrogatePlot } from "../visualization/SurrogatePlot";
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
  renderer: "simplex";
  traces: AlgorithmTrace[];
  scenarios: VisualizationScenario[];
} | {
  renderer: "metric-history";
  traces: AlgorithmTrace[];
  scenarios: VisualizationScenario[];
} | {
  renderer: "surrogate";
  payloads: SurrogateUncertaintyPayload[];
  scenarios: VisualizationScenario[];
} | {
  renderer: "search-tree";
  artifacts: SearchTreeArtifact[];
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
          <p className="eyebrow">比較 · 何をそろえ、何が違うかを見る</p>
          <h1>{loaded?.comparison.title_ja ?? "比較条件を読み込み中"}</h1>
          <p>{loaded ? readableComparisonText(loaded.comparison.comparison_question) : "何を同じにして、何を変えた比較かを確認します。"}</p>
        </div>
      </header>
      <PageOrientation
        limits="表示される差は、このケース・問題・seed・予算の範囲に限られます。順位付けの条件を満たしていても、普遍的な手法順位ではありません。"
        next={[{ label: "別の比較を選ぶ", to: "/compare" }, { label: "ケースへ戻る", to: loaded ? `/gallery/${loaded.comparison.case_id}` : "/gallery" }, { label: "1回の実行をTheaterで見る", to: "/theater" }]}
        purpose="同じもの・違うもの・見る指標を先に固定し、公平に解釈できる範囲だけを比較します。"
        readingSteps={["比較の問いとケースの定式化を確認します。", "固定条件・変更条件・指標・予算のそろい方を確認します。", "表示された差を読み、単独の実行・ケース・手法に戻って理由を確かめます。"]}
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
  const primaryScenario = "scenario" in loaded ? loaded.scenario : loaded.scenarios[0];
  const links = useEntityLinks();
  const entity = (type: "case" | "method" | "scenario" | "trace", id: string) => (
    links.status === "ready" ? findEntity(links.index, type, id) : undefined
  );
  return (
    <>
      <section className="visualization-switches comparison-switches" aria-label="比較preset">
        <label>
          <span>比較の問い</span>
          <select aria-label="比較preset" onChange={(event) => onPresetChange(event.target.value)} value={comparison.comparison_id}>
            {comparisons.map((item) => <option key={item.comparison_id} value={item.comparison_id}>{item.title_ja}</option>)}
          </select>
        </label>
      </section>
      <div className="visualization-badges comparison-artifact-badges" aria-label="比較データの概要">
        <span>{comparisonModeLabel(comparison.mode)}</span>
        <span>{[...new Set(comparison.members.map((member) => rendererFamilyLabel(member.artifact.renderer_family)))].join(" + ")}</span>
        <span>{identityStatusLabel(comparison.identity_status)} · {comparabilityLabel(comparison.comparability)}</span>
      </div>
      <ComparisonContract comparison={comparison} scenario={primaryScenario} />
      {loaded.renderer === "trajectory" ? (
        <TrajectoryComparison comparison={comparison} scenarios={loaded.scenarios} traces={loaded.traces} />
      ) : loaded.renderer === "simplex" ? (
        <SimplexGeometryComparison comparison={comparison} scenarios={loaded.scenarios} traces={loaded.traces} />
      ) : loaded.renderer === "metric-history" ? (
        <MetricHistoryComparison comparison={comparison} traces={loaded.traces} />
      ) : loaded.renderer === "surrogate" ? (
        <SurrogateComparison comparison={comparison} payloads={loaded.payloads} scenarios={loaded.scenarios} />
      ) : loaded.renderer === "search-tree" ? (
        <SearchTreeComparison artifacts={loaded.artifacts} comparison={comparison} scenarios={loaded.scenarios} />
      ) : (
        <ScenarioComparison artifact={loaded.artifact} comparison={comparison} scenario={loaded.scenario} />
      )}
      <section className="comparison-return-links" aria-label="比較の関連導線">
        <h2>同じ条件から確認する</h2>
        <JourneyLink journeyPatch={{ comparisonId: comparison.comparison_id }} to={comparison.canonical_url}>この比較の共有URL</JourneyLink>
        <JourneyLink to={entity("case", comparison.case_id)?.canonical_url ?? `/gallery/${comparison.case_id}`}>ケース: {entity("case", comparison.case_id)?.label ?? comparison.case_id}</JourneyLink>
        {firstMemberPerScenario(comparison.members).map((member) => {
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

function SearchTreeComparison({
  artifacts,
  comparison,
  scenarios,
}: {
  artifacts: SearchTreeArtifact[];
  comparison: ComparisonSet;
  scenarios: VisualizationScenario[];
}) {
  const timeline = useMemo(() => {
    const template = artifacts[0].trace.frames[0];
    return Array.from({ length: comparison.budget.value + 1 }, (_, evaluation): TraceFrame => ({
      ...template,
      frame_index: evaluation,
      iteration: evaluation,
      oracle_evaluations: evaluation,
      elapsed_steps: evaluation,
      elapsed_time_ms: evaluation * 100,
      event_type: evaluation === 0 ? "initialize" : "comparison_tick",
      event_label_ja: evaluation === 0 ? "比較を開始" : `評価 ${evaluation} に同期`,
      event_label_en: evaluation === 0 ? "Start comparison" : `Align at evaluation ${evaluation}`,
    }));
  }, [artifacts, comparison.budget.value]);
  const playback = usePlayback(comparison.comparison_id, timeline);
  const evaluation = playback.currentFrame.oracle_evaluations;
  return (
    <section className="search-tree-comparison" aria-labelledby="search-tree-comparison-heading">
      <header>
        <h2 id="search-tree-comparison-heading">同じ評価回数で探索状態を比べる</h2>
        <p>各比較対象について、現在の評価回数以下で最後に記録されたイベントを表示します。</p>
      </header>
      <PlaybackControls playback={playback} />
      <div className="comparison-grid search-tree-comparison-grid">
        {artifacts.map((artifact, index) => {
          const member = comparison.members[index];
          const frame = latestFrame(artifact.trace.frames, evaluation);
          if (!frame) throw new Error(`Search-tree member ${member.member_id} has no aligned frame.`);
          const payload = parseSearchTreeFramePayload(frame.payload);
          return (
            <article className="comparison-card search-tree-comparison-card" key={member.member_id}>
              <header>
                <div><h2>{member.label_ja}</h2><small>{member.label_en}</small></div>
                <span>{searchTreeTerminalLabel(payload.terminal_state)}</span>
              </header>
              <p className="method-parameters">{parameterText(member.parameters)}</p>
              <p className="comparison-event">
                {frame.event_label_ja ?? frame.event_type} · evaluation {frame.oracle_evaluations}
              </p>
              <dl className="comparison-search-tree-metrics" aria-label={`${member.label_ja}の同期指標`}>
                <div><dt>Terminal status</dt><dd>{searchTreeTerminalLabel(payload.terminal_state)}</dd></div>
                <div><dt>最良値</dt><dd>{payload.incumbent?.value ?? "未発見"}</dd></div>
                <div><dt>Feasibility</dt><dd>{searchTreeFeasibilityLabel(payload)}</dd></div>
                <div><dt>Global bound</dt><dd>{payload.global_bound.toFixed(2)}</dd></div>
                <div><dt>Absolute gap</dt><dd>{payload.absolute_gap === null ? "—" : payload.absolute_gap.toFixed(2)}</dd></div>
                <div><dt>Explored nodes</dt><dd>{payload.progress.explored_nodes}</dd></div>
                <div><dt>Open nodes</dt><dd>{payload.progress.open_nodes}</dd></div>
              </dl>
              <SearchTreeRenderer
                headingId={`comparison-search-tree-heading-${index}`}
                headingLabel={`${member.label_ja}の探索木`}
                payload={payload}
                visibleLayers={["search_nodes", "prune_reason"]}
              />
            </article>
          );
        })}
      </div>
      <p className="atlas-note"><strong>Takeaway:</strong> {comparison.takeaway}</p>
      <ul className="comparison-limitations">{comparison.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
    </section>
  );
}

function ComparisonContract({ comparison, scenario }: { comparison: ComparisonSet; scenario: VisualizationScenario }) {
  return (
    <section className="comparison-contract-v2" aria-label="比較条件">
      <header className="comparison-contract-lead">
        <span>{comparisonModeLabel(comparison.mode)}</span>
        <h2>この比較で確かめること</h2>
        <p className="comparison-question">{readableComparisonText(comparison.comparison_question)}</p>
        <p>{readableComparisonText(comparison.formulation_summary)}</p>
      </header>
      <div className="comparison-factor-grid">
        <article className="comparison-factor-fixed"><h3>ここまで同じ</h3><ul>{comparison.fixed_factors.map((factor) => <li key={factor}>{readableComparisonText(factor)}</li>)}</ul></article>
        <article className="comparison-factor-changed"><h3>ここだけ違う</h3><ul>{comparison.changed_factors.map((factor) => <li key={factor}>{readableComparisonText(factor)}</li>)}</ul></article>
        <article className="comparison-factor-observe">
          <h3>まず見る</h3>
          <ul>{comparison.metrics.map((metric) => <li key={metric.metric_id}><strong>{metric.label_ja}</strong><span>{metricDirectionLabel(metric.direction)} · {metricUnitLabel(metric.unit)}</span></li>)}</ul>
          {scenario.lesson.success_signals.length > 0 && <p><strong>良い変化</strong>{scenario.lesson.success_signals.map((item) => item.label_ja).join(" · ")}</p>}
          {scenario.lesson.failure_signals.length > 0 && <p><strong>違いが出るところ</strong>{scenario.lesson.failure_signals.map((item) => item.label_ja).join(" · ")}</p>}
        </article>
      </div>
      <div className="comparison-member-strip" aria-label="比較する対象">
        <strong>比べる対象</strong>
        {comparison.members.map((member) => <span key={member.member_id}>{member.label_ja}</span>)}
      </div>
      <details className="comparison-policy-details">
        <summary>評価条件の詳細を開く</summary>
        <dl className="comparison-policy-grid">
          <div><dt>評価予算・同期</dt><dd>{comparison.budget.metric} = {comparison.budget.value}</dd></div>
          <div><dt>乱数seed</dt><dd>{comparison.seed_policy}</dd></div>
          <div><dt>停止条件</dt><dd>{comparison.stopping_policy}</dd></div>
          <div><dt>パラメータ調整</dt><dd>{comparison.tuning_policy}</dd></div>
          <div><dt>順位づけ</dt><dd>{comparison.ranking_eligible ? "この条件内で可" : "しない"}</dd></div>
          <div><dt>ベンチマーク</dt><dd>{comparison.benchmark_context_id}</dd></div>
        </dl>
        <p className="comparison-fairness"><strong>公平性</strong> {readableComparisonText(comparison.fairness_note)}</p>
      </details>
      <p className="comparison-caveat"><strong>読み方の注意</strong> {readableComparisonText(comparison.caveat)}</p>
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
        この比較で一般的な優劣は断定できません。初期条件、パラメータ、oracle費用、停止条件が変われば挙動と比較可能性も変わります。
      </p>
    </>
  );
}

function SimplexGeometryComparison({ comparison, traces, scenarios }: { comparison: ComparisonSet; traces: AlgorithmTrace[]; scenarios: VisualizationScenario[] }) {
  const timeline = useMemo(() => {
    const template = traces[0].frames[0];
    const firstEvaluation = Math.min(...traces.map((trace) => trace.frames[0].oracle_evaluations));
    return Array.from({ length: comparison.budget.value - firstEvaluation + 1 }, (_, offset) => {
      const evaluation = firstEvaluation + offset;
      return {
      ...template,
      frame_index: evaluation,
      iteration: evaluation,
      oracle_evaluations: evaluation,
      elapsed_steps: evaluation,
      elapsed_time_ms: evaluation * 120,
      event_type: evaluation === 0 ? "initialize" : "comparison-tick",
      event_label_ja: evaluation === firstEvaluation ? "比較を開始" : "初期simplexを同期比較",
      event_label_en: evaluation === firstEvaluation ? "Start comparison" : "Align initial-simplex comparison",
      };
    });
  }, [comparison.budget.value, traces]);
  const playback = usePlayback(comparison.comparison_id, timeline);
  const evaluation = playback.currentFrame.oracle_evaluations;
  const spec = useMemo(() => objectivePlotSpec(traces[0].objective), [traces]);
  const contours = useMemo(() => contourSegments(spec, 22, 18), [spec]);
  return (
    <>
      <PlaybackControls playback={playback} />
      <div className="comparison-grid simplex-comparison-grid">
        {traces.map((trace, index) => (
          <SimplexComparisonMemberCard
            comparisonMember={comparison.members.find((member) => member.artifact.artifact_id === trace.trace_id)!}
            contours={contours}
            evaluation={evaluation}
            key={trace.trace_id}
            scenario={scenarios[index]}
            spec={spec}
            trace={trace}
          />
        ))}
      </div>
      <ObjectiveHistory comparison={comparison} evaluation={evaluation} traces={traces} />
      <p className="atlas-note comparison-ranking-warning">
        これは初期条件の違いを学ぶための比較です。どちらが一般に速い・頑健とは判定せず、同じ評価回数で単体の位置と操作を読みます。
      </p>
    </>
  );
}

function SimplexComparisonMemberCard({
  comparisonMember,
  contours,
  evaluation,
  scenario,
  spec,
  trace,
}: {
  comparisonMember: ComparisonMember;
  contours: ReturnType<typeof contourSegments>;
  evaluation: number;
  scenario: VisualizationScenario;
  spec: ObjectivePlotSpec;
  trace: AlgorithmTrace;
}) {
  const frame = latestFrame(trace.frames, evaluation);
  const vertices = frame ? rankedSimplexVertices(frame) : [];
  const centroid = frame?.points.find((point) => point.role === "centroid");
  const candidate = frame?.points.find((point) => point.role === "trial-point");
  const operation = frame?.vectors.find((vector) => vector.role === "movement");
  const best = vertices[0]?.point;
  const initial = initialPoint(trace);
  return (
    <article className="comparison-card simplex-comparison-card">
      <header>
        <div><h2>{comparisonMember.label_ja}</h2><small>{comparisonMember.label_en}</small></div>
        <span>{trace.terminal_status}</span>
      </header>
      <p className="method-parameters">{parameterText(comparisonMember.parameters)}</p>
      <p className="comparison-event">
        {frame ? `${frame.event_label_ja ?? frame.event_type} · 評価回数 ${frame.oracle_evaluations}` : "評価回数 0 · 未評価"}
      </p>
      <figure className="explanatory-figure comparison-figure">
        <svg
          className={`comparison-plot simplex-comparison-plot operation-${frame?.event_type ?? "initialize"}`}
          viewBox="0 0 300 194"
          role="img"
          aria-label={`${comparisonMember.label_ja}の等高線、simplex頂点、重心、候補点`}
        >
          <defs>
            <marker id={`simplex-operation-arrow-${comparisonMember.member_id}`} markerHeight="7" markerWidth="7" orient="auto" refX="6" refY="3.5">
              <path d="M0,0 L7,3.5 L0,7 z" className="nm-arrow-head" />
            </marker>
          </defs>
          <rect className="objective-background" x="0" y="0" width="300" height="194" rx="8" />
          <g className="objective-contours" aria-hidden="true">
            {contours.map((segment, index) => <line key={`${segment.level}-${index}`}
              x1={mapX(segment.start.x, spec.bounds, trajectoryPlot.left, trajectoryPlot.right)}
              y1={mapY(segment.start.y, spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}
              x2={mapX(segment.end.x, spec.bounds, trajectoryPlot.left, trajectoryPlot.right)}
              y2={mapY(segment.end.y, spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)} />)}
          </g>
          <line className="plot-axis" x1={trajectoryPlot.left} x2={trajectoryPlot.right} y1={trajectoryPlot.bottom} y2={trajectoryPlot.bottom} />
          <line className="plot-axis" x1={trajectoryPlot.left} x2={trajectoryPlot.left} y1={trajectoryPlot.top} y2={trajectoryPlot.bottom} />
          <g className="nm-initial-marker"><circle cx={mapX(initial[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)} cy={mapY(initial[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)} r="4" /><text x={mapX(initial[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right) + 6} y={mapY(initial[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom) - 5}>start</text></g>
          {vertices.length === 3 && <polygon className="nm-simplex" points={vertices.map(({ point }) => simplexCoordinates(point, spec)).join(" ")} />}
          {operation && <line className="nm-operation-vector" markerEnd={`url(#simplex-operation-arrow-${comparisonMember.member_id})`}
            x1={mapX(operation.origin[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)} y1={mapY(operation.origin[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}
            x2={mapX(operation.origin[0] + operation.components[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)} y2={mapY(operation.origin[1] + operation.components[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)} />}
          {vertices.map((vertex) => <SimplexVertexMarker key={vertex.point.point_id} spec={spec} vertex={vertex} />)}
          {centroid && <SimplexCentroidMarker point={centroid} spec={spec} />}
          {candidate && <SimplexCandidateMarker accepted={frame?.decision === "accepted"} point={candidate} spec={spec} />}
        </svg>
        <figcaption>{simplexSummary(frame, vertices, centroid, candidate)}</figcaption>
      </figure>
      <dl className="comparison-metrics">
        <div><dt>best f(x)</dt><dd>{frame ? objectiveMetric(frame) : "未評価"}</dd></div>
        <div><dt>simplex diameter</dt><dd>{simplexDiameter(vertices).toFixed(3)}</dd></div>
        <div><dt>best vertex</dt><dd>{best ? best.coordinates.map((value) => value.toFixed(3)).join(", ") : "未評価"}</dd></div>
      </dl>
      <ObjectiveGoalCues
        bestValue={bestSoFarValue(trace.frames, evaluation)}
        currentPoint={best?.coordinates}
        initialPoint={initial}
        knownReferenceDisplay={scenario.lesson.known_reference_display}
        objective={trace.objective}
        terminalReason={trace.terminal_summary_ja}
      />
    </article>
  );
}

type RankedSimplexVertex = { point: TracePoint; rank: "best" | "second-worst" | "worst" };

function rankedSimplexVertices(frame: TraceFrame): RankedSimplexVertex[] {
  return frame.points
    .filter((point): point is TracePoint & { value: number } => point.role === "simplex-vertex" && point.value !== null)
    .sort((left, right) => left.value - right.value)
    .map((point, index) => ({ point, rank: index === 0 ? "best" : index === 1 ? "second-worst" : "worst" }));
}

function simplexCoordinates(point: TracePoint, spec: ObjectivePlotSpec): string {
  return `${mapX(point.coordinates[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right)},${mapY(point.coordinates[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom)}`;
}

function SimplexVertexMarker({ spec, vertex }: { spec: ObjectivePlotSpec; vertex: RankedSimplexVertex }) {
  const x = mapX(vertex.point.coordinates[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right);
  const y = mapY(vertex.point.coordinates[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom);
  const label = vertex.rank === "best" ? "B" : vertex.rank === "second-worst" ? "S" : "W";
  return <g className={`nm-vertex nm-vertex-${vertex.rank}`}>
    {vertex.rank === "best" ? <circle cx={x} cy={y} r="5" /> : vertex.rank === "second-worst" ? <rect x={x - 4.5} y={y - 4.5} width="9" height="9" /> : <polygon points={`${x},${y - 6} ${x - 6},${y + 5} ${x + 6},${y + 5}`} />}
    <text x={x + 7} y={y - 6}>{label}</text>
  </g>;
}

function SimplexCentroidMarker({ point, spec }: { point: TracePoint; spec: ObjectivePlotSpec }) {
  const x = mapX(point.coordinates[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right);
  const y = mapY(point.coordinates[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom);
  return <g className="nm-centroid"><line x1={x - 4} x2={x + 4} y1={y} y2={y} /><line x1={x} x2={x} y1={y - 4} y2={y + 4} /></g>;
}

function SimplexCandidateMarker({ accepted, point, spec }: { accepted: boolean; point: TracePoint; spec: ObjectivePlotSpec }) {
  const x = mapX(point.coordinates[0], spec.bounds, trajectoryPlot.left, trajectoryPlot.right);
  const y = mapY(point.coordinates[1], spec.bounds, trajectoryPlot.top, trajectoryPlot.bottom);
  return <g className={`nm-candidate ${accepted ? "candidate-accepted" : "candidate-rejected"}`}><polygon points={`${x},${y - 5} ${x + 5},${y} ${x},${y + 5} ${x - 5},${y}`} /></g>;
}

function simplexDiameter(vertices: readonly RankedSimplexVertex[]): number {
  return Math.max(0, ...vertices.flatMap((vertex, index) => vertices.slice(index + 1).map((other) => Math.hypot(
    vertex.point.coordinates[0] - other.point.coordinates[0],
    vertex.point.coordinates[1] - other.point.coordinates[1],
  ))));
}

function simplexSummary(frame: TraceFrame | undefined, vertices: readonly RankedSimplexVertex[], centroid: TracePoint | undefined, candidate: TracePoint | undefined): string {
  if (!frame) return "まだ評価されていません。";
  const best = vertices[0]?.point;
  return `${frame.event_label_ja ?? frame.event_type}。最良点 ${best ? `(${best.coordinates.map((value) => value.toFixed(3)).join(", ")})` : "未評価"}、simplexの直径 ${simplexDiameter(vertices).toFixed(3)}、重心 ${centroid ? `(${centroid.coordinates.map((value) => value.toFixed(3)).join(", ")})` : "なし"}、候補点 ${candidate ? `(${candidate.coordinates.map((value) => value.toFixed(3)).join(", ")})` : "なし"}。`;
}

function ScenarioComparison({ artifact, comparison, scenario }: { artifact: LearningSliceArtifact; comparison: ComparisonSet; scenario: VisualizationScenario }) {
  const paretoArtifact = artifact.renderer_family === "pareto_front" ? artifact : undefined;
  return (
    <section className="scenario-comparison" aria-labelledby="scenario-comparison-title">
      <header><h2 id="scenario-comparison-title">{scenario.lesson.learning_objective.ja}</h2><p>{scenario.lesson.text_alternative.ja}</p></header>
      <LearningSliceRenderer artifact={artifact} />
      <div className="comparison-scenario-members">
        {comparison.members.map((member) => {
          const selection = paretoArtifact ? paretoSelectionForMember(paretoArtifact, member) : undefined;
          return (
            <article aria-label={`${member.label_ja}の選択結果`} key={member.member_id}>
              <span>{member.role}</span><h3>{member.label_ja}</h3><p>{parameterText(member.parameters)}</p>
              {selection && (
                <dl className="comparison-pareto-selection">
                  <div><dt>Decision</dt><dd>({selection.decision.map(formatScalar).join(", ")})</dd></div>
                  <div><dt>f₁</dt><dd>{formatScalar(selection.objectives[0])}</dd></div>
                  <div><dt>f₂</dt><dd>{formatScalar(selection.objectives[1])}</dd></div>
                </dl>
              )}
            </article>
          );
        })}
      </div>
      <p className="atlas-note"><strong>Takeaway:</strong> {comparison.takeaway}</p>
      <ul className="comparison-limitations">{comparison.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
    </section>
  );
}

function MetricHistoryComparison({
  comparison,
  traces,
}: {
  comparison: ComparisonSet;
  traces: AlgorithmTrace[];
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
      event_label_ja: evaluation === 0 ? "比較を開始" : "指標の比較推移",
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
        <div><dt>評価回数</dt><dd>{frame?.oracle_evaluations ?? 0}</dd></div>
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
        TRF・LM・L-BFGS-Bは実行していません。この表示から到達解、収束速度、経過時間、一般的なsolver順位は比較できません。
      </p>
    </>
  );
}

function SurrogateComparison({
  comparison,
  payloads,
  scenarios,
}: {
  comparison: ComparisonSet;
  payloads: SurrogateUncertaintyPayload[];
  scenarios: VisualizationScenario[];
}) {
  const minimumEvaluation = scenarios[0].experiment.initial_condition.point.length;
  const [evaluation, setEvaluation] = useState(minimumEvaluation);
  const snapshots = comparison.members.map((member, index) => (
    surrogateSnapshot(member, payloads[index], evaluation)
  ));
  const referenceIndex = comparison.members.findIndex((member) => member.role === "reference_acquisition");
  const referencePayload = payloads[referenceIndex];
  const referenceFrame = referencePayload.frames.find((frame) => frame.oracle_evaluations === evaluation);
  const visibleLayers = new Set([
    "observations",
    "posterior_mean",
    "posterior_uncertainty",
    "expected_improvement",
    "selected_candidate",
  ]);
  return (
    <section className="surrogate-comparison" aria-labelledby="surrogate-comparison-title">
      <header>
        <h2 id="surrogate-comparison-title">同じ評価回数で観測と選択理由を読む</h2>
        <p>基準条件から1要因だけを変えた比較対象と、同じ初期設計を使うrandom baselineを同期します。</p>
      </header>
      <label className="surrogate-comparison-slider">
        <span>Oracle evaluations: {evaluation}/{comparison.budget.value}</span>
        <input
          aria-label="BO比較のevaluation"
          max={comparison.budget.value}
          min={minimumEvaluation}
          onChange={(event) => setEvaluation(Number(event.target.value))}
          type="range"
          value={evaluation}
        />
      </label>
      {referenceFrame && <SurrogatePlot frame={referenceFrame} visibleLayers={visibleLayers} />}
      <p className="atlas-note">上の図は基準条件だけです。下のカードで、同じ評価回数の各比較対象を読みます。</p>
      <div className="comparison-grid surrogate-comparison-members">
        {comparison.members.map((member, index) => {
          const snapshot = snapshots[index];
          return (
            <article className="comparison-card" key={member.member_id}>
              <header><div><h3>{member.label_ja}</h3><small>{member.label_en}</small></div><span>{member.role}</span></header>
              <p className="method-parameters">{parameterText(member.parameters)}</p>
              <dl className="comparison-metrics">
                <div><dt>observations</dt><dd>{snapshot.observations}</dd></div>
                <div><dt>best-so-far</dt><dd>{snapshot.bestSoFar.toFixed(4)}</dd></div>
                <div><dt>next x</dt><dd>{formatOptional(snapshot.nextPoint)}</dd></div>
                <div><dt>acquisition</dt><dd>{snapshot.historySource === "random_history" ? "not applicable" : formatOptional(snapshot.acquisition)}</dd></div>
                <div><dt>予測不確実性</dt><dd>{snapshot.historySource === "random_history" ? "該当なし" : formatOptional(snapshot.uncertainty)}</dd></div>
                <div><dt>noise σ</dt><dd>{payloads[index].noise_std.toFixed(2)}</dd></div>
              </dl>
            </article>
          );
        })}
      </div>
      <details className="text-alternative" open>
        <summary>同期値を文章で読む</summary>
        <ul>{comparison.members.map((member, index) => {
          const snapshot = snapshots[index];
          return <li key={member.member_id}><strong>{member.label_ja}</strong>: evaluation {evaluation}, observations {snapshot.observations}, best-so-far {snapshot.bestSoFar.toFixed(4)}, next x {formatOptional(snapshot.nextPoint)}。</li>;
        })}</ul>
      </details>
      <p className="atlas-note"><strong>Takeaway:</strong> {comparison.takeaway}</p>
      <ul className="comparison-limitations">{comparison.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
      <p className="atlas-note comparison-ranking-warning">この固定条件の比較から、手法、獲得関数、ノイズ処理、random baselineの一般的な優劣や因果効果は推論できません。</p>
    </section>
  );
}

type SurrogateSnapshot = {
  historySource: "bo_frames" | "random_history";
  observations: number;
  bestSoFar: number;
  nextPoint: number | null;
  acquisition: number | null;
  uncertainty: number | null;
};

function surrogateSnapshot(
  member: ComparisonMember,
  payload: SurrogateUncertaintyPayload,
  evaluation: number,
): SurrogateSnapshot {
  const historySource = member.parameters.history_source;
  if (historySource === "random_history") {
    const observations = payload.random_history.slice(0, evaluation);
    return {
      historySource,
      observations: observations.length,
      bestSoFar: Math.min(...observations.map((item) => item.observed_value)),
      nextPoint: payload.random_history[evaluation]?.x ?? null,
      acquisition: null,
      uncertainty: null,
    };
  }
  if (historySource !== "bo_frames") {
    throw new Error(`Unsupported surrogate history source for ${member.member_id}.`);
  }
  const frame = payload.frames.find((item) => item.oracle_evaluations === evaluation);
  if (!frame) throw new Error(`Surrogate payload has no frame at evaluation ${evaluation}.`);
  return {
    historySource,
    observations: frame.observations.length,
    bestSoFar: frame.incumbent_value,
    nextPoint: frame.selected_point,
    acquisition: frame.selected_acquisition,
    uncertainty: frame.selected_uncertainty,
  };
}

function formatOptional(value: number | null): string {
  return value === null ? "budget reached" : value.toFixed(4);
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
      {pointOutsideBounds && <p className="plot-boundary-note">表示範囲外（目的関数の表示範囲外。境界markerで表示）</p>}
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
      {traceEntity?.canonical_url && <JourneyLink className="text-link" journeyPatch={{ scenarioId: comparisonMember.scenario_id, memberId: comparisonMember.member_id, methodId: comparisonMember.method_id }} to={traceEntity.canonical_url}>この可視化を単独再生</JourneyLink>}
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
      <h2>目的値と評価回数の比較</h2>
      <svg viewBox="0 0 760 216" role="img" aria-label={`${traces.length}件のmemberの目的関数値を同じoracle evaluation軸で比較`}>
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
        <summary>同期値を文章で読む</summary>
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
  if (index.dataset_version !== manifest.dataset_version) {
    throw new Error("Comparison dataset version does not match the manifest.");
  }
  if (scenarioIndex.dataset_version !== manifest.dataset_version) {
    throw new Error("Visualization scenario dataset version does not match the manifest.");
  }
  const comparison = index.comparisons.find(
    (item) => item.comparison_id === comparisonId || item.aliases.includes(comparisonId),
  );
  if (!comparison) throw new EntityNotFoundError("比較ID", comparisonId);
  const families = new Set(comparison.members.map((member) => member.artifact.renderer_family));
  const isSimplexComparison = families.size === 1 && families.has("simplex_geometry");
  const isTraceComparison = [...families].every((family) => (
    family === "continuous_trajectory" || family === "generic_metric_history"
  ));
  if (isTraceComparison || isSimplexComparison) {
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
      renderer: isSimplexComparison ? "simplex" : families.has("generic_metric_history") ? "metric-history" : "trajectory",
      traces,
      scenarios,
    };
  }
  const family = comparison.members[0].artifact.renderer_family;
  if (families.size === 1 && family === "surrogate_uncertainty") {
    const loadedMembers = await Promise.all(comparison.members.map(async (member) => {
      const scenario = scenarioIndex.scenarios.find((candidate) => candidate.scenario_id === member.scenario_id);
      if (!scenario || !scenario.runs.some((run) => run.artifact_id === member.artifact.artifact_id)) {
        throw new Error(`Surrogate scenario is missing for ${member.artifact.artifact_id}.`);
      }
      if (
        scenario.artifact.renderer_family !== family
        || scenario.artifact.renderer_contract_version !== member.artifact.renderer_contract_version
        || scenario.artifact.payload_path !== member.artifact.payload_path
      ) {
        throw new Error(`Surrogate artifact contract differs from comparison member ${member.member_id}.`);
      }
      const artifactResponse = await fetch(`${siteBaseUrl()}data/${member.artifact.payload_path}`, { signal });
      if (!artifactResponse.ok) throw new Error(`Surrogate artifact request failed (${artifactResponse.status}).`);
      return { scenario, payload: parseSurrogateUncertaintyPayload(await artifactResponse.json()) };
    }));
    return {
      comparison,
      comparisons: index.comparisons,
      renderer: "surrogate",
      payloads: loadedMembers.map((item) => item.payload),
      scenarios: loadedMembers.map((item) => item.scenario),
    };
  }
  if (families.size === 1 && family === "search_tree") {
    if (comparison.synchronization_axis !== "oracle_evaluations") {
      throw new Error("Search-tree comparison must synchronize by oracle_evaluations.");
    }
    const searchTreeIndexResponse = await fetch(`${siteBaseUrl()}data/search-trees/index.json`, { signal });
    if (!searchTreeIndexResponse.ok) {
      throw new Error(`Search-tree index request failed (${searchTreeIndexResponse.status}).`);
    }
    const searchTreeIndex = parseSearchTreeIndex(await searchTreeIndexResponse.json());
    if (searchTreeIndex.dataset_version !== manifest.dataset_version) {
      throw new Error("Search-tree index dataset version does not match the manifest.");
    }
    const loadedMembers = await Promise.all(comparison.members.map(async (member) => {
      const scenario = scenarioIndex.scenarios.find((candidate) => candidate.scenario_id === member.scenario_id);
      const entry = searchTreeIndex.artifacts.find((candidate) => candidate.artifact_id === member.artifact.artifact_id);
      const run = scenario?.runs.find((candidate) => candidate.artifact_id === member.artifact.artifact_id);
      if (!scenario || !entry || !run) {
        throw new Error(`Search-tree scenario/index identity is missing for ${member.member_id}.`);
      }
      if (
        scenario.problem_definition_id !== comparison.problem_definition_id
        || scenario.problem_instance_id !== comparison.problem_instance_id
        || scenario.dataset_version !== manifest.dataset_version
        || run.method_id !== member.method_id
        || entry.scenario_id !== member.scenario_id
        || entry.artifact_id !== member.artifact.artifact_id
        || entry.path !== member.artifact.payload_path
        || entry.artifact_kind !== member.artifact.artifact_kind
        || entry.renderer_family !== member.artifact.renderer_family
        || entry.renderer_contract_version !== member.artifact.renderer_contract_version
        || scenario.artifact.artifact_kind !== member.artifact.artifact_kind
        || scenario.artifact.renderer_family !== member.artifact.renderer_family
        || scenario.artifact.renderer_contract_version !== member.artifact.renderer_contract_version
      ) {
        throw new Error(`Search-tree scenario/index contract differs from comparison member ${member.member_id}.`);
      }
      const artifactResponse = await fetch(`${siteBaseUrl()}data/${entry.path}`, { signal });
      if (!artifactResponse.ok) {
        throw new Error(`Search-tree artifact request failed (${artifactResponse.status}).`);
      }
      const artifact = parseSearchTreeArtifact(await artifactResponse.json());
      if (
        artifact.dataset_version !== manifest.dataset_version
        || artifact.artifact_id !== entry.artifact_id
        || artifact.artifact_kind !== entry.artifact_kind
        || artifact.renderer_family !== entry.renderer_family
        || artifact.renderer_contract_version !== entry.renderer_contract_version
        || artifact.scenario_id !== entry.scenario_id
        || artifact.trace.trace_id !== entry.trace_id
        || artifact.trace.method_id !== member.method_id
        || artifact.trace.objective_id !== comparison.problem_instance_id
      ) {
        throw new Error(`Search-tree artifact identity differs from comparison member ${member.member_id}.`);
      }
      const traceNodeStopLimit = artifact.trace.stopping.max_nodes;
      const scenarioNodeStopLimit = scenario.experiment.stopping.max_nodes;
      const memberNodeStopLimit = member.parameters.node_stop_limit;
      if (
        artifact.trace.profile_id !== run.profile_id
        || artifact.trace.implementation_mapping_status !== run.implementation_mapping_status
        || artifact.trace.implementation_id !== run.implementation_id
        || artifact.trace.evaluation_budget !== scenario.experiment.budget.value
        || artifact.trace.evaluation_budget !== member.budget.value
        || scenario.experiment.budget.value !== member.budget.value
        || !isPositiveInteger(traceNodeStopLimit)
        || !isPositiveInteger(scenarioNodeStopLimit)
        || !isPositiveInteger(memberNodeStopLimit)
        || traceNodeStopLimit !== scenarioNodeStopLimit
        || traceNodeStopLimit !== memberNodeStopLimit
      ) {
        throw new Error(`Search-tree execution contract differs from comparison member ${member.member_id}.`);
      }
      return { artifact, scenario };
    }));
    return {
      comparison,
      comparisons: index.comparisons,
      renderer: "search-tree",
      artifacts: loadedMembers.map((item) => item.artifact),
      scenarios: loadedMembers.map((item) => item.scenario),
    };
  }
  if (family !== "feasible_region" && family !== "pareto_front" && family !== "field_evolution") {
    throw new Error(`Comparison renderer is not implemented: ${family}.`);
  }
  const scenarioId = comparison.members[0].scenario_id;
  const scenario = scenarioIndex.scenarios.find((candidate) => candidate.scenario_id === scenarioId);
  if (!scenario || comparison.members.some((member) => member.scenario_id !== scenarioId)) {
    throw new Error("Scenario comparison members must share one canonical scenario.");
  }
  const artifactDescriptor = comparison.members[0].artifact;
  if (comparison.members.some((member) => (
    member.artifact.artifact_id !== artifactDescriptor.artifact_id
    || member.artifact.artifact_kind !== artifactDescriptor.artifact_kind
    || member.artifact.renderer_family !== artifactDescriptor.renderer_family
    || member.artifact.renderer_contract_version !== artifactDescriptor.renderer_contract_version
    || member.artifact.payload_path !== artifactDescriptor.payload_path
  ))) {
    throw new Error("Scenario comparison members must share one canonical artifact.");
  }
  const artifactResponse = await fetch(`${siteBaseUrl()}data/${artifactDescriptor.payload_path}`, { signal });
  if (!artifactResponse.ok) throw new Error(`Comparison artifact request failed (${artifactResponse.status}).`);
  const artifact = parseLearningSliceArtifact(await artifactResponse.json());
  if (
    artifact.dataset_version !== manifest.dataset_version
    || artifact.artifact_id !== artifactDescriptor.artifact_id
    || artifact.artifact_kind !== artifactDescriptor.artifact_kind
    || artifact.renderer_family !== family
    || artifact.contract_version !== artifactDescriptor.renderer_contract_version
    || scenario.dataset_version !== manifest.dataset_version
    || scenario.problem_definition_id !== comparison.problem_definition_id
    || scenario.problem_instance_id !== comparison.problem_instance_id
    || scenario.artifact.artifact_kind !== artifactDescriptor.artifact_kind
    || scenario.artifact.renderer_family !== family
    || scenario.artifact.renderer_contract_version !== artifactDescriptor.renderer_contract_version
    || scenario.artifact.payload_path !== artifactDescriptor.payload_path
    || scenario.experiment.budget.metric !== comparison.budget.metric
    || scenario.experiment.budget.value !== comparison.budget.value
  ) {
    throw new Error("Scenario comparison artifact contract differs from the comparison.");
  }
  const sharedArtifactRun = scenario.runs.find(
    (candidate) => candidate.artifact_id === artifactDescriptor.artifact_id,
  );
  for (const member of comparison.members) {
    const methodRun = scenario.runs.find((candidate) => (
      candidate.artifact_id === member.artifact.artifact_id
      && candidate.method_id === member.method_id
    ));
    const run = family === "pareto_front" && comparison.mode === "result_tradeoff"
      ? sharedArtifactRun
      : methodRun;
    if (
      !run
      || scenario.experiment.budget.metric !== member.budget.metric
      || scenario.experiment.budget.value !== member.budget.value
    ) {
      throw new Error(`Scenario comparison run differs from member ${member.member_id}.`);
    }
  }
  if (artifact.renderer_family === "pareto_front") {
    const weights = comparison.members.map((member) => paretoWeight(member));
    if (new Set(weights).size !== weights.length) {
      throw new Error("Pareto comparison preference weights must be unique.");
    }
    for (const member of comparison.members) paretoSelectionForMember(artifact, member);
  }
  return { comparison, comparisons: index.comparisons, renderer: "learning-slice", artifact, scenario };
}

function paretoWeight(member: ComparisonMember): number {
  const value = member.parameters.weight_f1;
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
    throw new Error(`Pareto member ${member.member_id} requires weight_f1 between zero and one.`);
  }
  return value;
}

function paretoSelectionForMember(
  artifact: ParetoFrontArtifact,
  member: ComparisonMember,
): ParetoFrontArtifact["preference_selections"][number] {
  const weight = paretoWeight(member);
  const selection = artifact.preference_selections.find((candidate) => candidate.weight_f1 === weight);
  if (!selection) {
    throw new Error(`Pareto artifact has no preference selection for member ${member.member_id}.`);
  }
  return selection;
}

function formatScalar(value: number): string {
  return Number(value.toFixed(3)).toString();
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

function searchTreeTerminalLabel(state: "ongoing" | "optimality_proven" | "budget_exhausted"): string {
  return {
    ongoing: "探索中",
    optimality_proven: "最適性証明済み",
    budget_exhausted: "予算停止・未証明",
  }[state];
}

function metricDirectionLabel(direction: string): string {
  return direction === "minimize" ? "小さいほど良い" : direction === "maximize" ? "大きいほど良い" : direction;
}

function metricUnitLabel(unit: string): string {
  return {
    "objective value": "目的関数値",
    status: "終了状態",
    "objective value / evaluation": "目的関数値 / 評価回数",
  }[unit] ?? unit;
}

function readableComparisonText(value: string): string {
  return value
    .replaceAll("failure signal", "失敗の兆候")
    .replaceAll("learning rate", "学習率")
    .replaceAll("parameter sensitivity", "条件感度")
    .replaceAll("initial simplex", "初期単体")
    .replaceAll("proposal policy", "候補選択方針")
    .replaceAll("observation noise", "観測ノイズ")
    .replaceAll("random baseline", "ランダム基準")
    .replaceAll("Expected Improvement", "期待改善量")
    .replaceAll("acquisition", "獲得関数")
    .replaceAll("budget", "評価予算")
    .replaceAll("solver", "ソルバー");
}

function identityStatusLabel(status: string): string {
  return status === "canonical" ? "登録済みの比較" : status === "derived" ? "派生した比較" : status;
}

function comparabilityLabel(status: string): string {
  return status === "comparable" ? "比較可能" : status === "comparable_with_caveat" ? "注意つきで比較可能" : status === "contrast_only" ? "対比として読む" : status;
}

function searchTreeFeasibilityLabel(payload: ReturnType<typeof parseSearchTreeFramePayload>): string {
  return payload.incumbent
    ? "実行可能解あり（feasible）"
    : "実行可能解は未発見（undetermined）";
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value > 0;
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
