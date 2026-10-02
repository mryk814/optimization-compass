import { useCallback, useContext, useId, useMemo, useState } from "react";

import "./bo-drilling.css";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import {
  BO_GRID,
  BO_INITIAL,
  BO_ITERATIONS,
  boObjective,
  gridMinimum,
  runBayesOpt,
  suggestBayesOpt,
  type Acquisition,
  type BoState,
} from "./math/bayesOpt";
import { LiveMath, mi, mn, mo, row, signed, tint } from "./mathml";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting, type BeatSettings } from "./scene";
import { useStageViewport } from "./svg";
import { SceneRecordingContext, useSceneTour } from "./useSceneTour";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const ID = "bayes-opt-acquisition";
const Y_MIN = -0.9;
const Y_MAX = 1.9;
const TOP = { height: 0, left: 40, right: 14, top: 12, bottom: 28 };
const ACQ_HEIGHT = 120;
/** Decisions per second while a guided beat plays. */
const TOUR_DECISIONS_PER_SECOND = 1.25;
const ACQUISITIONS = ["lcb", "ei"] as const;
const TRUTH = ["show", "hide"] as const;
type Truth = (typeof TRUTH)[number];
const MINIMUM = gridMinimum();
/** Table values keep three decimals so 0.0004 reads as 0.000, as in the article. */
const fixed3 = (value: number) => { const text = Math.abs(value).toFixed(3); return value < 0 && Number(text) !== 0 ? `−${text}` : text; };

interface Settings {
  acquisition: Acquisition;
  beta: number;
  lengthScale: number;
  truth: Truth;
}

const INITIAL: Settings = { acquisition: "lcb", beta: 2, lengthScale: 0.1, truth: "hide" };

function fromBeat(settings: BeatSettings, base: Settings): Settings {
  return {
    acquisition: stringSetting(settings, "acquisition", ACQUISITIONS, base.acquisition),
    beta: numberSetting(settings, "beta", base.beta),
    lengthScale: numberSetting(settings, "lengthScale", base.lengthScale),
    truth: stringSetting(settings, "truth", TRUTH, base.truth),
  };
}

export function AlgorithmReplay() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromBeat(settings, value)), []),
  );
  const { acquisition, beta, lengthScale, truth } = tour.beat ? fromBeat(tour.beat.settings, chosen) : chosen;
  const set = <K extends keyof Settings>(key: K) => (value: Settings[K]) => setChosen((old) => ({ ...old, [key]: value }));
  const states = useMemo(() => runBayesOpt({ acquisition, beta, lengthScale }), [acquisition, beta, lengthScale]);
  const timeline = useTimeline(BO_ITERATIONS, 1.5);
  useReplayOnChange(timeline, tour.active ? `guided${tour.index}` : [acquisition, beta, lengthScale].join("|"));
  const n = tour.active
    ? Math.min(BO_ITERATIONS, Math.floor(tour.local * TOUR_DECISIONS_PER_SECOND))
    : Math.min(timeline.step, BO_ITERATIONS);
  const state = states[n];
  const { ref, viewport } = useStageViewport({ xMin: 0, xMax: 1, yMin: Y_MIN, yMax: Y_MAX }, 0.5);
  const width = viewport.width;
  const topHeight = Math.max(220, Math.round(width * 0.48));

  const repeated = state.xs.some((x) => Math.abs(x - state.nextX) < 1e-9);
  const reason = describeChoice(state, acquisition, beta, repeated);
  const found = state.best <= MINIMUM.value + 0.01;
  const summary = [
    `${acquisition === "lcb" ? `下側信頼限界 μ−βσ（β=${fmt(beta, 1)}）` : "Expected Improvement"}、長さの尺度 ℓ=${fmt(lengthScale, 2)}。`,
    `${state.xs.length}回評価した時点の最良値は ${fmt(state.best, 3)}（x=${fmt(state.bestX, 3)}）。`,
    `次に評価する点は x=${fmt(state.nextX, 3)}。${reason.text}`,
    truth === "show" && found ? "深い谷の底に着いています。" : "",
  ].join("");

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<Acquisition>
            legend="獲得関数"
            onChange={set("acquisition")}
            options={[
              { value: "lcb", label: "下側信頼限界 μ−βσ" },
              { value: "ei", label: "Expected Improvement" },
            ]}
            value={acquisition}
          />
          {acquisition === "lcb" && (
            <Slider
              display={fmt(beta, 1)}
              hint="大きいほど、不確実な場所を調べる（探索）方へ寄ります。"
              label="探索の重み β"
              max={8}
              min={0}
              onChange={set("beta")}
              step={0.5}
              value={beta}
            />
          )}
          <Slider
            display={fmt(lengthScale, 2)}
            hint="代理モデルが「この距離までは値が似ている」と仮定する幅。"
            label="長さの尺度 ℓ"
            max={0.3}
            min={0.04}
            onChange={set("lengthScale")}
            step={0.01}
            value={lengthScale}
          />
          <Choice<Truth>
            legend="真の目的関数"
            onChange={set("truth")}
            options={[
              { value: "show", label: "答え合わせに表示" },
              { value: "hide", label: "隠す（実務の見え方）" },
            ]}
            value={truth}
          />
        </>
      }
      id={ID}
      player={(
        <PlayerBar
          positionText={`評価 ${state.xs.length} 回（初期 ${BO_INITIAL.length} + 選択 ${n}）`}
          stepLabel="選んだ回数"
          timeline={timeline}
        />
      )}
      readout={<Readout acquisition={acquisition} beta={beta} found={found} reason={reason} showTruth={truth === "show"} state={state} />}
      stage={
        <div className="ex-canvas" ref={ref}>
          <SurrogatePanel height={topHeight} showTruth={truth === "show"} state={state} width={width} />
          <AcquisitionPanel acquisition={acquisition} state={state} width={width} />
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

function xScale(width: number) {
  return (x: number) => TOP.left + x * (width - TOP.left - TOP.right);
}

function SurrogatePanel({ state, width, height, showTruth }: { state: BoState; width: number; height: number; showTruth: boolean }) {
  const clipId = useId().replaceAll(":", "");
  const px = xScale(width);
  const py = (y: number) => TOP.top + ((Y_MAX - y) / (Y_MAX - Y_MIN)) * (height - TOP.top - TOP.bottom);
  const mean = BO_GRID.map((x, i) => `${i === 0 ? "M" : "L"}${px(x).toFixed(1)} ${py(state.post.mean[i]).toFixed(1)}`).join("");
  const upper = BO_GRID.map((x, i) => `${px(x).toFixed(1)} ${py(state.post.mean[i] + 2 * state.post.sd[i]).toFixed(1)}`);
  const lower = BO_GRID.map((x, i) => `${px(x).toFixed(1)} ${py(state.post.mean[i] - 2 * state.post.sd[i]).toFixed(1)}`).reverse();
  const band = `M${upper.join("L")}L${lower.join("L")}Z`;
  const truth = BO_GRID.map((x, i) => `${i === 0 ? "M" : "L"}${px(x).toFixed(1)} ${py(boObjective(x)).toFixed(1)}`).join("");
  const latest = state.xs.length - 1;
  return (
    <svg className="ex-svg" viewBox={`0 0 ${width} ${height}`}>
      <rect className="ex-ground" height={height} width={width} />
      <defs>
        <clipPath id={clipId}>
          <rect height={height - TOP.top - TOP.bottom} width={width - TOP.left - TOP.right} x={TOP.left} y={TOP.top} />
        </clipPath>
      </defs>
      <g className="ex-axes">
        {[-0.5, 0, 0.5, 1, 1.5].map((y) => (
          <g key={y}>
            <line x1={TOP.left} x2={width - TOP.right} y1={py(y)} y2={py(y)} />
            <text textAnchor="end" x={TOP.left - 6} y={py(y) + 4}>{fmt(y, 1)}</text>
          </g>
        ))}
        {[0, 0.2, 0.4, 0.6, 0.8, 1].map((x) => (
          <text key={x} textAnchor="middle" x={px(x)} y={height - 8}>{fmt(x, 1)}</text>
        ))}
      </g>
      <g clipPath={`url(#${clipId})`}>
        <path className="ex-band" d={band} />
        {showTruth && <path className="ex-truth" d={truth} />}
        <path className="ex-mean" d={mean} />
        <line className="ex-next-line" x1={px(state.nextX)} x2={px(state.nextX)} y1={TOP.top} y2={height - TOP.bottom} />
      </g>
      {state.xs.map((x, i) => (
        <circle
          className={i < BO_INITIAL.length ? "ex-observation is-initial" : i === latest ? "ex-observation is-latest" : "ex-observation"}
          cx={px(x)}
          cy={py(state.ys[i])}
          key={i}
          r={i === latest && i >= BO_INITIAL.length ? 7 : 5.5}
        />
      ))}
      <circle className="ex-incumbent" cx={px(state.bestX)} cy={py(state.best)} r={11} />
      <text className="ex-label ex-label-strong" textAnchor={state.nextX > 0.75 ? "end" : "start"} x={px(state.nextX) + (state.nextX > 0.75 ? -6 : 6)} y={TOP.top + 14}>
        次に評価 x={fmt(state.nextX, 3)}
      </text>
      <g className="ex-legend">
        <text className="ex-label" x={TOP.left + 6} y={height - TOP.bottom - 26}>━ 予測平均 μ　▒ μ±2σ</text>
        {showTruth && <text className="ex-label" x={TOP.left + 6} y={height - TOP.bottom - 8}>┄ 真の関数（実務では見えない）</text>}
      </g>
    </svg>
  );
}

function AcquisitionPanel({ state, width, acquisition }: { state: BoState; width: number; acquisition: Acquisition }) {
  const px = xScale(width);
  const lo = Math.min(...state.scores);
  const hi = Math.max(...state.scores);
  const span = hi - lo > 1e-12 ? hi - lo : 1;
  const inner = { top: 22, bottom: 10 };
  const py = (score: number) => inner.top + (1 - (score - lo) / span) * (ACQ_HEIGHT - inner.top - inner.bottom);
  // Drawn upside down: the chosen point (the minimum score) is the peak, so "highest = next".
  const flip = (score: number) => ACQ_HEIGHT - inner.bottom - (py(score) - inner.top);
  const path = BO_GRID.map((x, i) => `${i === 0 ? "M" : "L"}${px(x).toFixed(1)} ${flip(state.scores[i]).toFixed(1)}`).join("");
  const fill = `${path}L${px(1).toFixed(1)} ${ACQ_HEIGHT - inner.bottom}L${px(0).toFixed(1)} ${ACQ_HEIGHT - inner.bottom}Z`;
  return (
    <svg className="ex-svg ex-chart" viewBox={`0 0 ${width} ${ACQ_HEIGHT}`}>
      <rect className="ex-ground" height={ACQ_HEIGHT} width={width} />
      <path className="ex-acq-fill" d={fill} />
      <path className="ex-acq" d={path} />
      <line className="ex-next-line" x1={px(state.nextX)} x2={px(state.nextX)} y1={inner.top - 4} y2={ACQ_HEIGHT - inner.bottom} />
      <circle className="ex-head" cx={px(state.nextX)} cy={flip(state.scores[state.nextIndex])} r={6} />
      <text className="ex-axis-name" x={TOP.left + 4} y={15}>
        {acquisition === "lcb" ? "評価する価値（−(μ−βσ)、相対値）" : "Expected Improvement（相対値）"}：山の頂上を次に評価する
      </text>
    </svg>
  );
}

interface Reason {
  tone: "good" | "slow" | "swing";
  text: string;
}

function describeChoice(state: BoState, acquisition: Acquisition, beta: number, repeated: boolean): Reason {
  const i = state.nextIndex;
  const mean = state.post.mean[i];
  const sd = state.post.sd[i];
  const maxSd = Math.max(...state.post.sd);
  if (repeated) {
    return {
      tone: "slow",
      text: "すでに測った点をもう一度選んでいます。ノイズのない関数では新しい情報が得られないので、これは「このモデルと獲得関数ではもう選ぶ場所がない」という停止の合図です。",
    };
  }
  const exploring = sd > 0.5 * maxSd;
  const exploiting = mean < state.best + 0.05;
  if (exploring && exploiting) {
    return { tone: "good", text: "予測平均が最良値に近く、不確実性も大きい点です。活用と探索の両方の理由で選ばれました。" };
  }
  if (exploring) {
    return {
      tone: "swing",
      text: acquisition === "lcb"
        ? `予測平均は最良値より高い（${fmt(mean, 2)}）ものの、不確実性 σ=${fmt(sd, 2)} が大きく、βσ=${fmt(beta * sd, 2)} だけ割り引かれて選ばれました（探索）。`
        : `予測平均は最良値より高い（${fmt(mean, 2)}）ものの、σ=${fmt(sd, 2)} が大きく、最良値を下回る見込みが残っています（探索）。`,
    };
  }
  return {
    tone: "good",
    text: `不確実性は小さい（σ=${fmt(sd, 2)}）が、予測平均 ${fmt(mean, 2)} が最良値 ${fmt(state.best, 2)} の近くにある点です。分かっている良い場所を詰めています（活用）。`,
  };
}

function Readout({ state, acquisition, beta, reason, found, showTruth }: { state: BoState; acquisition: Acquisition; beta: number; reason: Reason; found: boolean; showTruth: boolean }) {
  const i = state.nextIndex;
  const mean = state.post.mean[i];
  const sd = state.post.sd[i];
  const markup = acquisition === "lcb"
    ? row(
        mi("a"), mo("("), mi("x"), mo(")"), mo("="), tint("navy", mi("μ")), mo("−"), mi("β"), tint("teal", mi("σ")),
        mo("="), signed(fmt(mean, 3)), mo("−"), mn(fmt(beta, 1)), mo("×"), mn(fmt(sd, 3)), mo("="), tint("orange", signed(fmt(mean - beta * sd, 3))),
      )
    : row(
        mi("EI"), mo("("), mi("x"), mo(")"), mo("="), tint("orange", mn(fmt(-state.scores[i], 4))),
        mo("（"), tint("navy", mi("μ")), mo("="), signed(fmt(mean, 3)), mo("、"), tint("teal", mi("σ")), mo("="), mn(fmt(sd, 3)), mo("）"),
      );
  const label = acquisition === "lcb"
    ? `獲得関数 a = μ − βσ = ${fmt(mean, 3)} − ${fmt(beta, 1)} × ${fmt(sd, 3)} = ${fmt(mean - beta * sd, 3)}`
    : `Expected Improvement は ${fmt(-state.scores[i], 4)}。予測平均 ${fmt(mean, 3)}、標準偏差 ${fmt(sd, 3)}`;
  const chosen = state.xs.slice(BO_INITIAL.length);
  return (
    <>
      <section aria-label="次の点を選んだ計算" className="ex-equation" tabIndex={0}>
        <p className="ex-eyebrow">次の点 x = {fmt(state.nextX, 3)} を選んだ計算</p>
        <LiveMath block label={label} markup={markup} />
      </section>
      <p className={`ex-verdict ex-tone-${reason.tone}`}>{reason.text}</p>
      <table className="ex-table">
        <thead>
          <tr><th scope="col">評価</th><th scope="col">x</th><th scope="col">f(x)</th><th scope="col">それまでの最良値</th></tr>
        </thead>
        <tbody>
          {state.xs.map((x, index) => {
            const bestSoFar = Math.min(...state.ys.slice(0, index + 1));
            return (
              <tr className={index === state.ys.indexOf(state.best) ? "ex-row-best" : undefined} key={index}>
                <th scope="row">{index < BO_INITIAL.length ? `初期 ${index + 1}` : `${index - BO_INITIAL.length + 1} 回目`}</th>
                <td>{fmt(x, 3)}</td>
                <td>{fixed3(state.ys[index])}</td>
                <td>{fixed3(bestSoFar)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="ex-hint">
        {chosen.length === 0
          ? "まだ初期の3点だけです。再生すると、1回ごとに代理モデルを作り直して次の点を選びます。"
          : !showTruth
            ? "真の関数を隠しているので、深い谷に着いたかどうかは、観測とモデルからしか判断できません。"
            : found
            ? `深い谷（x≈${fmt(MINIMUM.x, 2)}、f≈${fmt(MINIMUM.value, 2)}）に着いています。`
            : `深い谷（x≈${fmt(MINIMUM.x, 2)}）にはまだ着いていません。`}
      </p>
    </>
  );
}

const DRILL_BUDGET = 5;
type Reflection = "near" | "unknown" | "both" | "skip";

/** The learner's observations remain fixed when model assumptions change. */
export default function BayesOptAcquisition() {
  const [replay, setReplay] = useState(false);
  const recording = useContext(SceneRecordingContext);
  // Recording keeps the existing deterministic guided scenes.
  if (recording) return <AlgorithmReplay />;
  return <>
    <OilDrilling />
    <details className="bo-replay" onToggle={(event) => setReplay(event.currentTarget.open)}>
      <summary>BOの自動選択を再生する</summary>
      {replay && <AlgorithmReplay />}
    </details>
  </>;
}

function OilDrilling() {
  const [drilled, setDrilled] = useState<number[]>([]);
  const [point, setPoint] = useState(0.75);
  const [phase, setPhase] = useState<"choose" | "reflect" | "compare">("choose");
  const [reflection, setReflection] = useState<Reflection>("skip");
  const [settings, setSettings] = useState({ acquisition: "lcb" as Acquisition, beta: 2, lengthScale: 0.1 });
  const [answer, setAnswer] = useState(false);
  const xs = useMemo(() => [...BO_INITIAL, ...drilled], [drilled]);
  const ys = useMemo(() => xs.map(boObjective), [xs]);
  const state = useMemo(() => suggestBayesOpt(xs, ys, settings), [xs, ys, settings]);
  const { ref, viewport } = useStageViewport({ xMin: 0, xMax: 1, yMin: 0, yMax: 3 }, 0.5);
  const width = viewport.width;
  const compare = phase === "compare";
  const repeated = xs.some((x) => Math.abs(x - point) < 0.00001);
  const full = drilled.length >= DRILL_BUDGET;
  const dig = (x: number) => {
    if (full) return;
    setPoint(x);
    setDrilled((old) => [...old, x]);
    setReflection("skip");
    setPhase("reflect");
    setAnswer(false);
  };
  const reset = () => {
    setDrilled([]); setPoint(0.75); setPhase("choose"); setReflection("skip");
    setSettings({ acquisition: "lcb", beta: 2, lengthScale: 0.1 }); setAnswer(false);
  };
  const back = () => {
    const last = drilled.at(-1);
    if (last === undefined) return;
    setPoint(last); setDrilled((old) => old.slice(0, -1));
    setPhase("choose"); setReflection("skip"); setAnswer(false);
  };
  return <section aria-label="自分で油田を探す" className="ex-frame bo-drilling">
    <p className="ex-question"><span>まず一手</span>次は、どこを掘りますか？</p>
    <p>分かっているのは3本の井戸の結果だけ。あと{DRILL_BUDGET}本まで試せます。</p>
    <div className="bo-observations" ref={ref}>
      <OilObservations point={point} state={state} width={width} />
    </div>
    <p aria-live="polite" className="bo-result">
      {drilled.length ? `いま掘った x=${fmt(drilled.at(-1)!, 3)} の油の多さは ${fmt(2 - ys.at(-1)!, 3)}。` : "点が高いほど、油が多い場所です。"}
      {` 自分で掘った本数 ${drilled.length} / ${DRILL_BUDGET}。`}
    </p>
    {phase === "reflect" ? <>
      <Choice<Reflection> legend="なぜ、そこを選びましたか？（任意）" value={reflection} onChange={setReflection}
        options={[{ value: "near", label: "良かった井戸の近く" }, { value: "unknown", label: "まだ分からない土地" },
          { value: "both", label: "両方を考えた" }, { value: "skip", label: "今は言葉にしない" }]} />
      <div className="bo-actions">
        <button className="ex-action" onClick={() => setPhase("compare")} type="button">同じ観測でBOと比べる</button>
        {!full && <button className="ex-action" onClick={() => setPhase("choose")} type="button">もう一本、自分で選ぶ</button>}
      </div>
    </> : <>
      {!full && <>
        <Slider label="掘る場所 x" min={0} max={1} step={0.005} value={point} display={fmt(point, 3)} onChange={setPoint} />
        <div className="bo-actions"><button className="ex-action" onClick={() => dig(point)} type="button">ここを掘る</button></div>
        {repeated && <p className="ex-hint">同じ場所は同じ結果になります。この例には測定ノイズがありません。</p>}
      </>}
      {!compare && drilled.length > 0 && <button className="ex-action" onClick={() => setPhase("compare")} type="button">同じ観測でBOと比べる</button>}
    </>}
    {compare && <section aria-label="自分の観測とBOの提案" className="bo-model">
      <h3>あなたの観測から、BOは何を期待する？</h3>
      <p>{reflection === "near" ? "良かった近くを狙う気持ちは「活用」。予測平均を見てみましょう。"
        : reflection === "unknown" ? "未知の土地を試す気持ちは「探索」。不確実性の帯を見てみましょう。"
        : reflection === "both" ? "期待できる良さと、まだ分からない広がり。両方を一つの基準で比べます。"
        : "自分の選択を思い出しながら、期待できる良さと、まだ分からない広がりを比べてみましょう。"}</p>
      <p>ここからは油の多さ q を f=2−q に読み替えます。予測図は下ほど良い値。紺の線が予測、帯はモデルの不確実性です。</p>
      <div className="ex-controls">
        <Choice<Acquisition> legend="次の点の選び方（一例）" value={settings.acquisition}
          onChange={(acquisition) => setSettings((old) => ({ ...old, acquisition }))}
          options={[{ value: "lcb", label: "下側信頼限界 μ−βσ" }, { value: "ei", label: "Expected Improvement" }]} />
        {settings.acquisition === "lcb" && <Slider label="探索の重み β" min={0} max={8} step={0.5} value={settings.beta}
          display={fmt(settings.beta, 1)} onChange={(beta) => setSettings((old) => ({ ...old, beta }))}
          hint="同じ観測のまま、未知の場所をどれだけ試したいかを変えます。" />}
        <Slider label="長さの尺度 ℓ" min={0.04} max={0.3} step={0.01} value={settings.lengthScale}
          display={fmt(settings.lengthScale, 2)} onChange={(lengthScale) => setSettings((old) => ({ ...old, lengthScale }))}
          hint="近くの井戸の結果を、どこまで信用するかという仮定です。" />
      </div>
      <SurrogatePanel height={260} showTruth={answer} state={state} width={width} />
      <AcquisitionPanel acquisition={settings.acquisition} state={state} width={width} />
      <p aria-live="polite">BOの提案は x={fmt(state.nextX, 3)}。つまみを変えても、すでに掘った結果は変わりません。</p>
      <p>予測平均だけで選ぶならβ=0。不確実な場所にも期待するならβを上げます。帯は未知の正解や測定のばらつきではなく、このモデルの仮定から計算したものです。</p>
      <Readout acquisition={settings.acquisition} beta={settings.beta} found={answer && state.best <= MINIMUM.value + 0.01}
        reason={describeChoice(state, settings.acquisition, settings.beta, xs.some((x) => Math.abs(x - state.nextX) < 1e-9))}
        showTruth={answer} state={state} />
      {!full && <button className="ex-action" onClick={() => dig(state.nextX)} type="button">BOの提案する場所を掘る</button>}
      {full && <label className="bo-answer"><input type="checkbox" checked={answer} onChange={(event) => setAnswer(event.target.checked)} />答え合わせの曲線を見る</label>}
    </section>}
    {full && <p>5本の結果がそろいました。どの結果で期待が変わりましたか？採れた量の勝負ではなく、選び方を振り返るための例です。</p>}
    <div className="bo-actions">
      <button className="ex-action" disabled={!drilled.length} onClick={back} type="button">一手戻す</button>
      <button className="ex-action" onClick={reset} type="button">同じ土地でやり直す</button>
    </div>
    <details className="ex-limits"><summary>この体験の前提</summary>
      <p>固定の1次元関数・初期3点・追加5本・測定ノイズなし。油の多さは教材用の指標です。GPは観測値を標準化し、RBFカーネルと数値安定化の小さい対角項を使います。実際の地質、採油量、BOの一般性能を示しません。</p>
    </details>
  </section>;
}

function OilObservations({ state, point, width }: { state: BoState; point: number; width: number }) {
  const px = xScale(width);
  const py = (q: number) => 25 + (1 - q / 3) * 145;
  return <svg aria-label="掘った場所の油の多さ。未観測の場所の値は表示しません。" role="img" className="ex-svg" viewBox={`0 0 ${width} 205`}>
    <rect className="ex-ground" width={width} height={205} />
    {[0, 1, 2, 3].map((q) => <g className="ex-axes" key={q}><line x1={TOP.left} x2={width - TOP.right} y1={py(q)} y2={py(q)} />
      <text x={TOP.left - 6} y={py(q) + 4} textAnchor="end">{q}</text></g>)}
    <text className="ex-axis-name" x={TOP.left} y={16}>油の多さ（上ほど良い）</text>
    {[0, 0.25, 0.5, 0.75, 1].map((x) => <text className="ex-label" key={x} x={px(x)} y={195} textAnchor="middle">{fmt(x, 2)}</text>)}
    <line className="ex-next-line" x1={px(point)} x2={px(point)} y1={25} y2={170} />
    {state.xs.map((x, i) => <circle className={i < BO_INITIAL.length ? "ex-observation is-initial" : "ex-observation is-latest"}
      key={i} cx={px(x)} cy={py(2 - state.ys[i])} r={6}><title>{`x=${fmt(x, 3)}、油の多さ ${fmt(2 - state.ys[i], 3)}`}</title></circle>)}
  </svg>;
}
