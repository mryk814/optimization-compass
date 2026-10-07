import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseGalleryIndex, type GalleryCase } from "../../../contracts/gallery";
import { siteBaseUrl } from "../../../data/base-url";
import { EvidenceLinks } from "../../evidence/EvidenceLinks";
import { recommend } from "../../diagnose/recommend";
import { PlayerBar } from "../../explorable/controls";
import { useReplayOnChange, useTimeline } from "../../explorable/useTimeline";
import { NotFoundPage } from "../../navigation/NotFoundPage";
import {
  BudgetTicks,
  buildMethodLens,
  buildSignature,
  caseAnswers,
  DispositionMark,
  EvaluationMarks,
  MethodGlyph,
  ModelCurve,
  ProblemSignature,
  ProposalMarker,
  SpreadBracket,
  stageScale,
  StepArrow,
  TangentProbe,
  TerrainCurve,
  UncertaintyBand,
  UnseenField,
  useSiteData,
  type Disposition,
  type MethodLens,
  type MethodShape,
  type StageScale,
} from "../../../visual-system";
import "../../explorable/explorable.css";
import {
  GRADIENT_SETTINGS,
  LENS_BUDGET,
  LENS_DOMAIN,
  LENS_GRID,
  lensObjective,
  POPULATION_SETTINGS,
  runAllLenses,
  snapshotAt,
  SURROGATE_SETTINGS,
  type LensId,
  type LensRun,
  type LensSnapshot,
} from "./lensRuns";
import "./lens-theater.css";

const SUPPORTED_CASE = "hyperparameter-search";

interface LensSpec {
  id: LensId;
  shape: MethodShape;
  title: string;
  methodId: string;
  methodLabel: string;
  sees: string;
  decides: string;
  remembers: string;
  uncertainty: string;
}

/** What each instrument observes, decides, remembers, and whether it holds uncertainty. */
const LENSES: readonly LensSpec[] = [
  {
    id: "gradient",
    shape: "triangle",
    title: "傾きを測る",
    methodId: "M_GRADIENT_DESCENT",
    methodLabel: "前進差分つき勾配降下法",
    sees: "いまの点の値と、隣の点との差で測った傾き",
    decides: `傾きの逆向きへ η×傾き（η = ${GRADIENT_SETTINGS.step}）動く`,
    remembers: "直前の点だけ。過去の測点は使わない",
    uncertainty: "持たない",
  },
  {
    id: "population",
    shape: "diamond",
    title: "集団で試す",
    methodId: "M_CMA_ES",
    methodLabel: `(1, ${POPULATION_SETTINGS.lambda}) 進化戦略（CMA-ESなど集団型の最小形）`,
    sees: "今の世代の3点の値の順位",
    decides: "最良の1点を次の中心にし、改善すれば幅σを広げ、しなければ縮める",
    remembers: "中心と幅σだけ。世代が替わると点は捨てる",
    uncertainty: "探索の幅σとして持つ（予測の幅ではない）",
  },
  {
    id: "surrogate",
    shape: "circle",
    title: "地形を予測する",
    methodId: "M_BAYESIAN_OPT_GP",
    methodLabel: "ガウス過程によるベイズ最適化（EI）",
    sees: "すべての観測から作った予測平均と不確実性",
    decides: "期待改善量（EI）が最大の点を測る",
    remembers: "すべての観測",
    uncertainty: "予測の幅（±2σ）として持つ",
  },
];

const Y_DOMAIN: readonly [number, number] = [-0.9, 3.9];

export function LensTheaterPage() {
  const { caseId = SUPPORTED_CASE } = useParams();
  const [item, setItem] = useState<GalleryCase>();
  const [error, setError] = useState<Error>();
  const siteData = useSiteData();
  const [view, setView] = useState<"algorithm" | "human">("algorithm");
  const [layout, setLayout] = useState<"lanes" | "overlay">("lanes");
  const runs = useMemo(() => runAllLenses(), []);
  const timeline = useTimeline(LENS_BUDGET, 1.1);
  useReplayOnChange(timeline, "lens-theater");
  const t = timeline.step;

  useEffect(() => {
    if (caseId !== SUPPORTED_CASE) return;
    void fetch(`${siteBaseUrl()}data/gallery.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Gallery request failed (${response.status}).`);
        return response.json() as Promise<unknown>;
      })
      .then((raw) => setItem(parseGalleryIndex(raw).cases.find((entry) => entry.case_id === SUPPORTED_CASE)))
      .catch((caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught))));
  }, [caseId]);

  const answers = useMemo(() => (item ? caseAnswers(item.question_answers) : {}), [item]);
  const axes = useMemo(() => buildSignature(answers), [answers]);
  const dispositions = useMemo(() => {
    const result = new Map<string, { kind: Disposition; note: string }>();
    if (!item) return result;
    item.candidate_methods.forEach((entry) => result.set(entry.method_id, { kind: "candidate", note: "Caseで候補" }));
    item.conditional_methods.forEach((entry) => result.set(entry.method_id, { kind: "conditional", note: "Caseで条件付き" }));
    item.excluded_methods.forEach((entry) => result.set(entry.method_id, { kind: "excluded", note: "Caseで除外" }));
    if (siteData) {
      const rec = recommend(siteData, Object.fromEntries(Object.entries(item.question_answers).map(([key, value]) => [key, [value]])));
      const mark = (ids: string[], kind: Disposition) => ids.forEach((id) => {
        if (!result.has(id)) result.set(id, { kind, note: "診断規則で" + (kind === "candidate" ? "候補" : kind === "conditional" ? "条件付き" : "除外") });
      });
      mark(rec.first_choices.map((entry) => entry.entity_id), "candidate");
      mark(rec.conditional_choices.map((entry) => entry.entity_id), "conditional");
      mark(rec.excluded_methods.map((entry) => entry.entity_id), "excluded");
    }
    return result;
  }, [item, siteData]);

  if (caseId !== SUPPORTED_CASE) {
    return <NotFoundPage detail={`アルゴリズムの視点の舞台は、まだ ${SUPPORTED_CASE} だけに接続されています。`} />;
  }

  const excludedGradient = item?.excluded_methods.find((entry) => entry.method_id === "M_BFGS");

  return (
    <section className="atlas-page lens-theater">
      <header className="lens-theater-header">
        <p className="eyebrow">動きを見る · アルゴリズムの視点</p>
        <h1>同じ地形を、3つの計器で測る</h1>
        <p className="lens-theater-question">
          勾配・集団・代理モデルは、同じ{LENS_BUDGET}回の評価で<strong>何を見て</strong>、次に<strong>どこを測るか</strong>。動きの違いは、見えている世界の違いから生まれます。
        </p>
      </header>

      <section className="lens-theater-context" aria-label="この舞台の問題と条件">
        <div>
          <p className="eyebrow">問題 · <Link to={`/gallery/${SUPPORTED_CASE}`}>{item?.title_ja ?? "高価な実験の設定を探す"}</Link></p>
          {item ? <ProblemSignature axes={axes} size="compact" /> : null}
        </div>
        <dl className="vs-contract">
          <div><dt>固定</dt><dd>目的関数 f(x)（Caseの教材関数）、x ∈ [−3, 3]、評価予算 {LENS_BUDGET}回、x = 0 を必ず含む、ノイズなし</dd></div>
          <div><dt>変更</dt><dd>何を観測し、次の点をどう決めるか（計器）</dd></div>
          <div><dt>観察</dt><dd>各評価の時点で手法が持つ情報、次の一手、最良値の推移、切り替えの兆候</dd></div>
        </dl>
      </section>

      <div className="lens-theater-controls">
        <fieldset className="lens-toggle">
          <legend>視点</legend>
          <label><input checked={view === "algorithm"} name="lens-view" onChange={() => setView("algorithm")} type="radio" />アルゴリズムの視点</label>
          <label><input checked={view === "human"} name="lens-view" onChange={() => setView("human")} type="radio" />人間の視点（真の地形を重ねる）</label>
        </fieldset>
        <fieldset className="lens-toggle">
          <legend>並べ方</legend>
          <label><input checked={layout === "lanes"} name="lens-layout" onChange={() => setLayout("lanes")} type="radio" />計器ごとに並べる</label>
          <label><input checked={layout === "overlay"} name="lens-layout" onChange={() => setLayout("overlay")} type="radio" />1つの地形に重ねる</label>
        </fieldset>
      </div>

      <div className="explorable lens-theater-player">
        <PlayerBar positionText={`${t} / ${LENS_BUDGET} 回`} stepLabel="評価回数" timeline={timeline} />
      </div>

      {layout === "lanes" ? (
        <div className="lens-lanes">
          {LENSES.map((spec) => (
            <LensLane
              disposition={dispositions.get(spec.methodId)}
              key={spec.id}
              lensSignature={item && siteData ? (
                <ProblemSignature
                  axes={axes}
                  lens={buildMethodLens(spec.methodId, answers, siteData)}
                  size="compact"
                  label={`${spec.methodLabel}の目で見た署名`}
                />
              ) : null}
              lensNote={item && siteData ? lensNoteText(buildMethodLens(spec.methodId, answers, siteData)) : undefined}
              run={runs[spec.id]}
              spec={spec}
              t={t}
              view={view}
            />
          ))}
        </div>
      ) : (
        <OverlayStage runs={runs} t={t} view={view} />
      )}

      {excludedGradient && (
        <aside className="lens-theater-exclusion">
          <DispositionMark kind="excluded" />
          <p>
            このCaseでは、勾配を前提とする <Link to="/methods/M_BFGS">BFGS</Link> を除外しています。理由: {excludedGradient.reason}
            勾配の計器は、除外を覆すためではなく、<strong>除外の理由が観測でどう現れるか</strong>を見るために置いています（差分に予算を使い、近くの谷しか見えない）。
          </p>
        </aside>
      )}

      <details className="lens-theater-limits">
        <summary>この舞台の前提と、読み取れないこと</summary>
        <ul>
          <li>ブラウザ内で計算する教材用の実行で、正準Traceではありません。seed {POPULATION_SETTINGS.seed}・1次元・ノイズなしの1回だけです。</li>
          <li>最良値の大小は、この地形・この予算・この設定での記録です。手法の一般的な優劣や順位を示しません。seed・刻み・カーネルを変えれば結果は入れ替わり得ます。</li>
          <li>勾配の計器は刻み h = {GRADIENT_SETTINGS.h} の前進差分を使います。実験ノイズがあれば、差分の傾きはさらに不安定になります。</li>
          <li>代理モデルはRBFカーネル（長さの尺度 {SURROGATE_SETTINGS.lengthScale}）の仮定に依存します。ノイズなしのため、観測済みの点から {SURROGATE_SETTINGS.minSpacing} 以内は次の候補にしません。</li>
          <li>人間の視点の破線（真の地形）は答え合わせ用で、どの手法も参照していません。</li>
        </ul>
        <EvidenceLinks sourceIds={["S056", "S058", "S059"]} />
      </details>

      <nav className="lens-theater-next" aria-label="次に見る">
        <Link to={`/gallery/${SUPPORTED_CASE}`}>Caseに戻って候補と除外を見直す</Link>
        <Link to="/compare/COMPARE_BO_ACQUISITION_NOISE_BASELINE">正準の比較: 獲得関数・ノイズ・random baseline</Link>
        <Link to="/theater/bayesian-optimization">ベイズ最適化の1回の実行（正準Trace）</Link>
      </nav>
    </section>
  );
}

function useMeasuredWidth(fallback = 360) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const element = ref.current;
    if (!element) return undefined;
    const measure = () => { if (element.clientWidth > 0) setWidth(Math.round(element.clientWidth)); };
    measure();
    if (typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return { ref, width };
}

function LensLane({
  spec,
  run,
  t,
  view,
  disposition,
  lensSignature,
  lensNote,
}: {
  spec: LensSpec;
  run: LensRun;
  t: number;
  view: "algorithm" | "human";
  disposition?: { kind: Disposition; note: string };
  lensSignature: React.ReactNode;
  lensNote?: string;
}) {
  const { ref, width } = useMeasuredWidth();
  const snapshot = snapshotAt(run, t);
  const height = spec.id === "surrogate" ? 250 : 210;
  const scale = stageScale(width, spec.id === "surrogate" ? height - 44 : height, LENS_DOMAIN, Y_DOMAIN);
  const events = run.events.filter((event) => event.at <= t);
  return (
    <article className="lens-lane" aria-labelledby={`lane-${spec.id}`}>
      <header className="lens-lane-header">
        <h2 id={`lane-${spec.id}`}><MethodGlyph shape={spec.shape} size={16} /> {spec.title}</h2>
        <p><Link to={`/methods/${spec.methodId}`}>{spec.methodLabel}</Link></p>
        <div className="lens-lane-disposition">
          <DispositionMark kind={disposition?.kind ?? "pending"} />
          <small>{disposition?.note ?? "Caseにも診断規則にも判断がない"}</small>
          {lensNote && <small className="lens-lane-lens-note">{lensNote}</small>}
        </div>
        <div className="lens-lane-signature">
          {lensSignature}
        </div>
      </header>
      <dl className="lens-lane-pov">
        <div><dt>見ているもの</dt><dd>{spec.sees}</dd></div>
        <div><dt>次の決め方</dt><dd>{spec.decides}</dd></div>
        <div><dt>覚えているもの</dt><dd>{spec.remembers}</dd></div>
        <div><dt>不確実性</dt><dd>{spec.uncertainty}</dd></div>
      </dl>
      <div className="lens-stage" ref={ref}>
        <svg aria-hidden="true" className="vs-stage" height={height} width={width}>
          <StageAxis scale={scale} />
          {view === "algorithm" && <UnseenField id={`unseen-${spec.id}`} known={knownRanges(snapshot)} scale={scale} />}
          {view === "human" && <TerrainCurve f={lensObjective} scale={scale} xs={LENS_GRID} />}
          <LensLayers scale={scale} snapshot={snapshot} spec={spec} />
          {spec.id === "surrogate" && snapshot.view.kind === "surrogate" && (
            <EiStrip ei={snapshot.view.ei} next={snapshot.view.next} top={height - 40} width={width} scale={scale} />
          )}
        </svg>
      </div>
      <p className="lens-lane-next" aria-live="polite">{nextActionText(spec.id, snapshot)}</p>
      <div className="lens-lane-budget">
        <BudgetTicks purposes={snapshot.evaluations.map((item) => item.purpose)} spent={snapshot.evaluations.length} total={LENS_BUDGET} />
        <span>{snapshot.best ? `最良 f = ${snapshot.best.y.toFixed(3)}（x = ${snapshot.best.x.toFixed(2)}）` : "まだ測っていない"}</span>
      </div>
      {spec.id === "gradient" && <p className="lens-lane-key"><span className="vs-budget-tick is-spent" /> 移動先の評価　<span className="vs-budget-tick is-spent is-probe" /> 傾きのための評価</p>}
      {events.map((event) => (
        <p className="vs-signal" key={event.kind}><span><strong>切り替えの兆候</strong>{event.text}</span></p>
      ))}
    </article>
  );
}

function lensNoteText(lens: MethodLens): string | undefined {
  const parts: string[] = [];
  if (lens.blockingAxes.length) parts.push(`前提が外れる軸: ${lens.blockingAxes.map((axis) => axis.name).join("・")}`);
  if (lens.supportingAxes.length) parts.push(`支える軸: ${lens.supportingAxes.map((axis) => axis.name).join("・")}`);
  return parts.join(" / ") || undefined;
}

/** x-ranges the method holds information about after this snapshot. */
function knownRanges(snapshot: LensSnapshot): Array<readonly [number, number]> {
  const { view, evaluations } = snapshot;
  if (view.kind === "surrogate" && view.mean.length > 0) return [LENS_DOMAIN];
  if (view.kind === "gradient") {
    return view.slope === null
      ? evaluations.filter((item) => item.x === view.at).map((item) => [item.x - 0.08, item.x + 0.08] as const)
      : [[view.at - 0.55, view.at + 0.55] as const];
  }
  const current = view.kind === "population" ? view.current : evaluations;
  return current.map((item) => [item.x - 0.08, item.x + 0.08] as const);
}

function StageAxis({ scale }: { scale: StageScale }) {
  const ticks = [-3, -2, -1, 0, 1, 2, 3];
  const base = scale.height - 18;
  return (
    <g>
      <line className="vs-stage-axis" x1={scale.px(-3)} x2={scale.px(3)} y1={base} y2={base} />
      {ticks.map((tick) => (
        <text className="vs-stage-tick" key={tick} textAnchor="middle" x={scale.px(tick)} y={scale.height - 4}>{tick}</text>
      ))}
    </g>
  );
}

function LensLayers({ spec, snapshot, scale }: { spec: LensSpec; snapshot: LensSnapshot; scale: StageScale }) {
  const { view, evaluations } = snapshot;
  const latest = evaluations.at(-1);
  if (view.kind === "gradient") {
    // The gradient instrument holds only the current point and one slope: older points fade.
    const points = evaluations.map((item) => ({
      key: item.index,
      x: item.x,
      y: item.y,
      faded: item.x !== view.at && item.index !== latest?.index,
      latest: item.index === latest?.index,
    }));
    return (
      <>
        <EvaluationMarks points={points} scale={scale} shape={spec.shape} />
        {view.slope !== null && <TangentProbe scale={scale} slope={view.slope} x={view.at} y={view.atValue} />}
        {view.slope !== null && view.next !== null && <StepArrow from={view.at} scale={scale} to={view.next} y={view.atValue} />}
        {view.next !== null && <ProposalMarker scale={scale} x={view.next} />}
      </>
    );
  }
  if (view.kind === "population") {
    const currentIds = new Set(view.current.map((item) => item.index));
    const points = evaluations.map((item) => ({
      key: item.index,
      x: item.x,
      y: item.y,
      faded: !currentIds.has(item.index),
      latest: item.index === latest?.index,
    }));
    return (
      <>
        <SpreadBracket mean={view.mean} scale={scale} sigma={view.sigma} xDomain={LENS_DOMAIN} />
        <EvaluationMarks points={points} scale={scale} shape={spec.shape} />
        {view.next !== null && <ProposalMarker label="中心" scale={scale} x={view.mean} />}
      </>
    );
  }
  const points = evaluations.map((item) => ({ key: item.index, x: item.x, y: item.y, latest: item.index === latest?.index }));
  return (
    <>
      <UncertaintyBand mean={view.mean} scale={scale} sd={view.sd} xs={LENS_GRID} />
      <ModelCurve scale={scale} xs={LENS_GRID} ys={view.mean} />
      <EvaluationMarks points={points} scale={scale} shape={spec.shape} />
      {view.next !== null && <ProposalMarker scale={scale} x={view.next} />}
    </>
  );
}

function EiStrip({ ei, next, top, width, scale }: { ei: readonly number[]; next: number | null; top: number; width: number; scale: StageScale }) {
  if (ei.length === 0) return null;
  const max = Math.max(...ei, 1e-12);
  const h = 30;
  const d = LENS_GRID.map((x, i) => `${i === 0 ? "M" : "L"} ${scale.px(x).toFixed(1)} ${(top + h - (ei[i] / max) * h).toFixed(1)}`).join(" ");
  return (
    <g>
      <text className="vs-stage-tick" x={4} y={top + 8}>EI</text>
      <path className="vs-ei" d={`${d} L ${scale.px(LENS_DOMAIN[1])} ${top + h} L ${scale.px(LENS_DOMAIN[0])} ${top + h} Z`} />
      {next !== null && <line className="vs-stage-axis" x1={scale.px(next)} x2={scale.px(next)} y1={top} y2={top + h} />}
      <line className="vs-stage-axis" x1={0} x2={width} y1={top + h} y2={top + h} />
    </g>
  );
}

function nextActionText(id: LensId, snapshot: LensSnapshot): string {
  const { view, evaluations } = snapshot;
  const n = evaluations.length;
  if (view.kind === "gradient") {
    if (n === 0) return "出発点 x = 0 を測る。";
    if (view.slope === null) return `x = ${view.at.toFixed(2)} の値だけでは向きが分からない。傾きを測るため、隣の x = ${(view.at + GRADIENT_SETTINGS.h).toFixed(2)} を測る。`;
    if (view.next === null) return `傾き ${view.slope.toFixed(2)} を測ったが、予算を使い切った。移動先は評価できない。`;
    return `傾き ${view.slope.toFixed(2)} を読み、逆向きへ ${(view.next - view.at).toFixed(2)} 動いて x = ${view.next.toFixed(2)} を測る。測っていない場所の形は分からない。`;
  }
  if (view.kind === "population") {
    if (n === 0) return "中心 x = 0 を測る。";
    if (view.next === null) return `第${view.generation}世代で予算を使い切った。中心 ${view.mean.toFixed(2)}、幅 σ = ${view.sigma.toFixed(2)}。`;
    return `中心 ${view.mean.toFixed(2)}、幅 σ = ${view.sigma.toFixed(2)} の分布から次の点を引く。順位しか使わないので、値の大きさの差は見ていない。`;
  }
  if (view.mean.length === 0) {
    return n < SURROGATE_SETTINGS.design.length
      ? `初期設計の点 x = ${view.next?.toFixed(2)} を測る。まだ予測モデルはない。`
      : "初期設計を測り終えた。";
  }
  if (view.next === null) return "予算を使い切った。予測と不確実性は、最後の観測までで固定される。";
  const index = LENS_GRID.indexOf(view.next);
  return `期待改善量が最大の x = ${view.next.toFixed(2)} を測る（予測 ${view.mean[index].toFixed(2)}、不確実性 ±${(2 * view.sd[index]).toFixed(2)}）。予測が低いか、不確実性が大きい所が選ばれる。`;
}

const OVERLAY_ORDER: readonly LensId[] = ["gradient", "population", "surrogate"];

function OverlayStage({ runs, t, view }: { runs: Record<LensId, LensRun>; t: number; view: "algorithm" | "human" }) {
  const { ref, width } = useMeasuredWidth(640);
  const height = 260;
  const scale = stageScale(width, height, LENS_DOMAIN, Y_DOMAIN);
  const chartHeight = 170;
  const chart = stageScale(width, chartHeight, [0.5, LENS_BUDGET + 0.5], [-0.65, 3.2], { left: 34, right: 12, top: 10, bottom: 22 });
  return (
    <section className="lens-overlay" aria-label="3つの計器を1つの地形に重ねる">
      <p className="lens-overlay-note">形が計器を表します（▲ 傾き・◆ 集団・● 予測）。色は「観測した点」の意味だけを持ちます。</p>
      <div className="lens-stage" ref={ref}>
        <svg aria-hidden="true" className="vs-stage" height={height} width={width}>
          <StageAxis scale={scale} />
          {view === "human" && <TerrainCurve f={lensObjective} scale={scale} xs={LENS_GRID} />}
          {OVERLAY_ORDER.map((id) => {
            const spec = LENSES.find((lens) => lens.id === id)!;
            const snapshot = snapshotAt(runs[id], t);
            return (
              <EvaluationMarks
                key={id}
                points={snapshot.evaluations.map((item) => ({ key: `${id}-${item.index}`, x: item.x, y: item.y, best: snapshot.best?.index === item.index }))}
                scale={scale}
                shape={spec.shape}
              />
            );
          })}
        </svg>
        <h3 className="lens-overlay-chart-title">評価回数ごとの最良値（best-so-far）</h3>
        <svg aria-hidden="true" className="vs-stage" height={chartHeight} width={width}>
          <line className="vs-stage-axis" x1={chart.px(0.5)} x2={chart.px(LENS_BUDGET + 0.5)} y1={chartHeight - 22} y2={chartHeight - 22} />
          {Array.from({ length: LENS_BUDGET }, (_, i) => i + 1).map((n) => (
            <text className="vs-stage-tick" key={n} textAnchor="middle" x={chart.px(n)} y={chartHeight - 6}>{n}</text>
          ))}
          {[0, 1, 2, 3].map((v) => (
            <text className="vs-stage-tick" key={v} textAnchor="end" x={28} y={chart.py(v) + 4}>{v}</text>
          ))}
          {OVERLAY_ORDER.map((id) => {
            const spec = LENSES.find((lens) => lens.id === id)!;
            const evaluations = snapshotAt(runs[id], t).evaluations;
            let best = Infinity;
            const pts = evaluations.map((item) => { best = Math.min(best, item.y); return { key: `${id}-b-${item.index}`, x: item.index, y: best }; });
            const d = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${chart.px(p.x)} ${chart.py(Math.min(p.y, 3.2))}`).join(" ");
            return (
              <g className={`lens-best is-${id}`} key={id}>
                <path d={d} />
                <EvaluationMarks points={pts.map((p) => ({ ...p, y: Math.min(p.y, 3.2) }))} r={3.5} scale={chart} shape={spec.shape} />
              </g>
            );
          })}
        </svg>
      </div>
      <p className="lens-overlay-note">
        最良値の差は、この1つの地形・seed・予算での記録です。読むべきは順位ではなく、各計器が<strong>どの評価で何を知ったか</strong>です。
        勾配は差分に評価を使い、集団は世代ごとに点を捨て、予測は全観測を使って遠くの谷を測りに行きます。
      </p>
    </section>
  );
}
