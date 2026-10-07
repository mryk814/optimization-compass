import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import type { GalleryCase } from "../../../contracts/gallery";
import { EvidenceLinks } from "../../evidence/EvidenceLinks";
import { recommend } from "../../diagnose/recommend";
import { PlayerBar } from "../../explorable/controls";
import { useReplayOnChange, useTimeline } from "../../explorable/useTimeline";
import {
  buildMethodLens,
  buildSignature,
  caseAnswers,
  ContourField,
  DispositionMark,
  EvaluationMarks,
  FeasibleCircle,
  loadGalleryCases,
  MethodGlyph,
  PathLine,
  ProblemSignature,
  stageScale,
  UnseenPlane,
  useSiteData,
  VectorArrow,
  type Disposition,
  type MethodShape,
  type StageScale,
} from "../../../visual-system";
import "../../explorable/explorable.css";
import {
  CONSTRAINED_BOUNDS,
  CONSTRAINED_ITERATIONS,
  CONSTRAINED_OPTIMUM,
  constrainedSnapshotAt,
  DISC_CENTER,
  DISC_RADIUS,
  OBJECTIVE_ONLY_STEP,
  PENALTY_SETTINGS,
  PROJECTION_STEP,
  runConstrainedLenses,
  type ConstrainedLensId,
  type ConstrainedRun,
  type ConstrainedSnapshot,
} from "./constrainedRuns";
import "./lens-theater.css";

export const CONSTRAINED_CASE = "constrained-design";

interface ConstrainedSpec {
  id: ConstrainedLensId;
  shape: MethodShape;
  title: string;
  methodId?: string;
  methodLabel: string;
  sees: string;
  constraint: string;
  decides: string;
}

const LENSES: readonly ConstrainedSpec[] = [
  {
    id: "objective-only",
    shape: "triangle",
    title: "目的の傾きだけを見る",
    methodId: "M_GRADIENT_DESCENT",
    methodLabel: `勾配降下法（η = ${OBJECTIVE_ONLY_STEP}）`,
    sees: "いまの点での目的 f の傾き",
    constraint: "読まない。円の外に出ても気づかない",
    decides: "傾きの逆向きへ η×傾き 動く",
  },
  {
    id: "penalty",
    shape: "diamond",
    title: "違反を罰として足す",
    methodLabel: `二次ペナルティ法（μ を毎回 ${PENALTY_SETTINGS.growth} 倍）`,
    sees: "f の傾きと、違反しているときだけ制約の値 g",
    constraint: "破ったときだけ、罰 μ·g² の傾きとして見える",
    decides: "f + 罰 の傾きの逆向きへ動き、μ を大きくする",
  },
  {
    id: "projection",
    shape: "circle",
    title: "境界へ射影する",
    methodId: "M_PROJECTED_GRADIENT",
    methodLabel: `射影勾配法（η = ${PROJECTION_STEP}）`,
    sees: "f の傾きと、実行可能な集合そのもの（円への射影）",
    constraint: "常に知っている。外へ出た試行点は円の上へ戻す",
    decides: "傾きの逆向きへ動き、円の外なら最も近い円上の点へ戻る",
  },
];

const LEVELS = [0.17, 0.5, 1, 2, 3, 4.5];

export function ConstrainedLensTheater() {
  const [item, setItem] = useState<GalleryCase>();
  const siteData = useSiteData();
  const [view, setView] = useState<"algorithm" | "human">("algorithm");
  const runs = useMemo(() => runConstrainedLenses(), []);
  const timeline = useTimeline(CONSTRAINED_ITERATIONS, 1.2);
  useReplayOnChange(timeline, "constrained-lens-theater");
  const k = timeline.step;

  useEffect(() => {
    let active = true;
    void loadGalleryCases().then((cases) => { if (active) setItem(cases.find((entry) => entry.case_id === CONSTRAINED_CASE)); }, () => undefined);
    return () => { active = false; };
  }, []);

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
      const mark = (ids: string[], kind: Disposition, label: string) => ids.forEach((id) => {
        if (!result.has(id)) result.set(id, { kind, note: `診断規則で${label}` });
      });
      mark(rec.first_choices.map((entry) => entry.entity_id), "candidate", "候補");
      mark(rec.conditional_choices.map((entry) => entry.entity_id), "conditional", "条件付き");
      mark(rec.excluded_methods.map((entry) => entry.entity_id), "excluded", "除外");
    }
    return result;
  }, [item, siteData]);
  const excluded = item?.excluded_methods[0];
  const candidate = item?.candidate_methods[0];

  return (
    <section className="atlas-page lens-theater">
      <header className="lens-theater-header">
        <p className="eyebrow">動きを見る · アルゴリズムの視点</p>
        <h1>同じ制約を、3つの計器で読む</h1>
        <p className="lens-theater-question">
          目的だけを見る計器、違反を罰として足す計器、境界へ射影する計器は、同じ{CONSTRAINED_ITERATIONS}回の反復で<strong>制約をどう見て</strong>、どこへ進むか。円の外は、目的が小さくても答えにできません。
        </p>
      </header>

      <section className="lens-theater-context" aria-label="この舞台の問題と条件">
        <div>
          <p className="eyebrow">問題 · <Link to={`/gallery/${CONSTRAINED_CASE}`}>{item?.title_ja ?? "強度制約を守りながら軽量設計を探す"}</Link></p>
          {item ? <ProblemSignature axes={axes} size="compact" /> : null}
        </div>
        <dl className="vs-contract">
          <div><dt>固定</dt><dd>f(x, y) = x² + y²、制約 (x − 1)² + (y − 1)² ≤ 1、開始点 (1.5, 1.7)（実行可能）、反復 {CONSTRAINED_ITERATIONS}回</dd></div>
          <div><dt>変更</dt><dd>制約をどう読み、次の点をどう決めるか（計器）</dd></div>
          <div><dt>観察</dt><dd>各反復で手法が持つ情報、違反量、次の一手、最後に立っている場所</dd></div>
        </dl>
      </section>

      <div className="lens-theater-controls">
        <fieldset className="lens-toggle">
          <legend>視点</legend>
          <label><input checked={view === "algorithm"} name="constrained-view" onChange={() => setView("algorithm")} type="radio" />アルゴリズムの視点</label>
          <label><input checked={view === "human"} name="constrained-view" onChange={() => setView("human")} type="radio" />人間の視点（等高線と実行可能領域を重ねる）</label>
        </fieldset>
      </div>

      <div className="explorable lens-theater-player">
        <PlayerBar positionText={`${k} / ${CONSTRAINED_ITERATIONS} 回`} stepLabel="反復" timeline={timeline} />
      </div>

      <div className="lens-lanes">
        {LENSES.map((spec) => {
          const disposition = spec.methodId ? dispositions.get(spec.methodId) : undefined;
          return (
            <ConstrainedLane
              disposition={disposition}
              k={k}
              key={spec.id}
              lensSignature={item && siteData && spec.methodId ? (
                <ProblemSignature axes={axes} label={`${spec.methodLabel}の目で見た署名`} lens={buildMethodLens(spec.methodId, answers, siteData)} size="compact" />
              ) : null}
              run={runs[spec.id]}
              spec={spec}
              view={view}
            />
          );
        })}
      </div>

      {excluded && (
        <aside className="lens-theater-exclusion">
          <DispositionMark kind="excluded" />
          <p>
            このCaseでは <Link to={`/methods/${excluded.method_id}`}>BFGS</Link> を除外しています。理由: {excluded.reason}
            「目的の傾きだけを見る」計器は、この理由が観測でどう現れるかを見るために置いています。候補の
            {candidate ? <> <Link to={`/methods/${candidate.method_id}`}>SLSQP</Link> は、制約を毎回線形化して部分問題を解きます。この舞台では、境界を明示的に使う最小形として射影を使っています。</> : null}
          </p>
        </aside>
      )}

      <details className="lens-theater-limits">
        <summary>この舞台の前提と、読み取れないこと</summary>
        <ul>
          <li>ブラウザ内で計算する教材用の実行で、正準Traceではありません。2変数・凸・滑らかな1つの問題だけです。</li>
          <li>最後の位置や違反量の差は、この問題・刻み・反復数での記録です。手法の一般的な優劣や順位を示しません。</li>
          <li>ペナルティ法は、μ を大きくするほど地形が急になり、刻みを小さくしないと発散します。ここでは曲率から刻みを決めています。罰は破った後にしか効かないので、点は境界の外側から近づき、ごく小さな違反が残ります。</li>
          <li>射影勾配法は、円への射影が閉じた式で書けるから使えます。一般の非線形制約では射影そのものが最適化問題になります。</li>
          <li>人間の視点の等高線と実行可能領域は答え合わせ用です。目的だけを見る計器は、円を一度も参照していません。</li>
        </ul>
        <EvidenceLinks sourceIds={["S056"]} />
      </details>

      <nav className="lens-theater-next" aria-label="次に見る">
        <Link to={`/gallery/${CONSTRAINED_CASE}`}>Caseに戻って候補と除外を見直す</Link>
        <Link to="/compare/COMPARE_CONSTRAINED_FAILURE">正準の比較: 制約を守る run と無視する run</Link>
        <Link to="/theater/lenses/hyperparameter-search">地形を3つの計器で測る（高価な実験）</Link>
      </nav>
    </section>
  );
}

function useMeasuredWidth(fallback = 320) {
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

function ConstrainedLane({
  spec,
  run,
  k,
  view,
  disposition,
  lensSignature,
}: {
  spec: ConstrainedSpec;
  run: ConstrainedRun;
  k: number;
  view: "algorithm" | "human";
  disposition?: { kind: Disposition; note: string };
  lensSignature: ReactNode;
}) {
  const { ref, width } = useMeasuredWidth();
  const size = Math.min(width, 380);
  const scale = stageScale(size, size, [CONSTRAINED_BOUNDS.xMin, CONSTRAINED_BOUNDS.xMax], [CONSTRAINED_BOUNDS.yMin, CONSTRAINED_BOUNDS.yMax], { left: 8, right: 8, top: 8, bottom: 8 });
  const snapshot = constrainedSnapshotAt(run, k);
  const current = snapshot.steps.at(-1)!;
  const knowsFeasibleSet = spec.id === "projection";
  return (
    <article className="lens-lane" aria-labelledby={`lane-${spec.id}`}>
      <header className="lens-lane-header">
        <h2 id={`lane-${spec.id}`}><MethodGlyph shape={spec.shape} size={16} /> {spec.title}</h2>
        <p>{spec.methodId ? <Link to={`/methods/${spec.methodId}`}>{spec.methodLabel}</Link> : spec.methodLabel}</p>
        <div className="lens-lane-disposition">
          <DispositionMark kind={disposition?.kind ?? "pending"} />
          <small>{disposition?.note ?? (spec.methodId ? "Caseにも診断規則にも判断がない" : "Atlasに手法として未登録")}</small>
        </div>
        <div className="lens-lane-signature">{lensSignature}</div>
      </header>
      <dl className="lens-lane-pov">
        <div><dt>見ているもの</dt><dd>{spec.sees}</dd></div>
        <div><dt>制約の見え方</dt><dd>{spec.constraint}</dd></div>
        <div><dt>次の決め方</dt><dd>{spec.decides}</dd></div>
      </dl>
      <div className="lens-stage" ref={ref}>
        <svg aria-hidden="true" className="vs-stage" height={size} width={size}>
          {view === "algorithm" && (
            <UnseenPlane id={`unseen-${spec.id}`} knownCircle={knowsFeasibleSet ? { center: DISC_CENTER, radius: DISC_RADIUS } : undefined} scale={scale} />
          )}
          {(view === "human" || knowsFeasibleSet) && <FeasibleCircle center={DISC_CENTER} radius={DISC_RADIUS} scale={scale} />}
          {view === "human" && <ContourField bounds={CONSTRAINED_BOUNDS} f={(x, y) => x * x + y * y} levels={LEVELS} scale={scale} />}
          {view === "human" && <OptimumMark scale={scale} />}
          <PathLine points={snapshot.steps.map((s) => s.point)} scale={scale} />
          <EvaluationMarks
            points={snapshot.steps.map((s) => ({
              key: s.k,
              x: s.point[0],
              y: s.point[1],
              faded: s.k !== current.k && spec.id !== "projection",
              latest: s.k === current.k,
              violation: s.violation > 1e-9,
            }))}
            r={4.5}
            scale={scale}
            shape={spec.shape}
          />
          <LaneVectors scale={scale} snapshot={snapshot} />
        </svg>
      </div>
      <p className="lens-lane-next" aria-live="polite">{nextText(spec.id, snapshot)}</p>
      <div className="lens-lane-budget">
        <span>f = {current.value.toFixed(3)}</span>
        <span className={current.violation > 1e-9 ? "lens-violation" : undefined}>違反量 {formatViolation(current.violation)}</span>
      </div>
      {spec.id === "objective-only" && current.violation > 1e-9 && (
        <p className="vs-signal"><span><strong>切り替えの兆候</strong>目的は下がり続けているが、点は円の外にある。この計器は違反を読まないので、自分では止まれない。</span></p>
      )}
      {spec.id === "penalty" && snapshot.steps.some((s) => s.violation > 1e-9) && (
        <p className="vs-signal"><span><strong>切り替えの兆候</strong>罰が効くのは破った後なので、一度は外へはみ出す。違反量が0へ戻るかを毎回確かめる。</span></p>
      )}
    </article>
  );
}

function OptimumMark({ scale }: { scale: StageScale }) {
  const x = scale.px(CONSTRAINED_OPTIMUM[0]);
  const y = scale.py(CONSTRAINED_OPTIMUM[1]);
  return (
    <g className="vs-optimum">
      <circle cx={x} cy={y} r={7} />
      <text textAnchor="end" x={x - 10} y={y + 18}>制約付きの最適点</text>
    </g>
  );
}

function LaneVectors({ snapshot, scale }: { snapshot: ConstrainedSnapshot; scale: StageScale }) {
  const view = snapshot.view;
  if (!view) return null;
  const at = snapshot.steps.at(-1)!.point;
  if (view.kind === "penalty") {
    return (
      <>
        {Math.hypot(view.penaltyPull[0], view.penaltyPull[1]) > 1e-9 && <VectorArrow from={at} kind="read" scale={scale} vector={view.penaltyPull} />}
        <VectorArrow from={at} kind="next" scale={scale} vector={view.direction} />
      </>
    );
  }
  if (view.kind === "projection") {
    return (
      <>
        <VectorArrow from={at} kind="next" maxLength={2} scale={scale} vector={[view.trial[0] - at[0], view.trial[1] - at[1]]} />
        {view.projected && <circle className="vs-trial" cx={scale.px(view.trial[0])} cy={scale.py(view.trial[1])} r={4} />}
      </>
    );
  }
  return <VectorArrow from={at} kind="next" scale={scale} vector={view.direction} />;
}

function nextText(id: ConstrainedLensId, snapshot: ConstrainedSnapshot): string {
  const current = snapshot.steps.at(-1)!;
  const where = `(${current.point[0].toFixed(2)}, ${current.point[1].toFixed(2)})`;
  const view = snapshot.view;
  if (!view) return `${CONSTRAINED_ITERATIONS}回の反復を終えた。最後の点は ${where}、違反量 ${formatViolation(current.violation)}。`;
  if (view.kind === "objective-only") {
    return current.violation > 1e-9
      ? `${where} は円の外。それでも f の傾きだけを読んで、原点の方向へ進む。`
      : `${where} で f の傾きを読み、原点の方向へ進む。円は見えていない。`;
  }
  if (view.kind === "penalty") {
    return current.violation > 1e-9
      ? `${where} は円の外なので、罰の傾き（青緑）が円の方へ引き戻す。μ = ${view.mu.toFixed(1)}。`
      : `${where} は円の中なので罰はゼロ。f の傾きだけで進む（μ = ${view.mu.toFixed(1)}）。`;
  }
  return view.projected
    ? `${where} から動いた試行点は円の外。円の上の最も近い点へ戻す。`
    : `${where} から傾きの逆向きへ動く。試行点が円の中なので、そのまま進む。`;
}

/** Small violations stay visible: 0 means feasible, anything else keeps its magnitude. */
function formatViolation(value: number): string {
  if (value <= 1e-9) return "0";
  return value < 0.001 ? value.toExponential(1) : value.toFixed(3);
}
