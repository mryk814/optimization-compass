import { memo, useCallback, useMemo, useState } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import { ADAM_DEFAULTS, runAdam, runPlainDescent, type AdamCoordinate } from "./math/adam";
import { contourSegments, type Bounds } from "./math/contours";
import { valleyValue, type ValleyProblem } from "./math/descent";
import { LiveMath, frac, hat, mi, mn, mo, row, signed, sub, tint } from "./mathml";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting, type BeatSettings } from "./scene";
import { makeScale, polylinePath, segmentsPath, useStageViewport, type Scale, type Viewport } from "./svg";
import { useSceneTour } from "./useSceneTour";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const ID = "adam-step-ratio";
const MAX_STEPS = 120;
const SEED = 7;
const PROBLEM: ValleyProblem = { cx: 1, cy: -2, kappa: 20 };
const START: readonly [number, number] = [4, 3];
const BOUNDS: Bounds = { xMin: -4.5, xMax: 7, yMin: -5.5, yMax: 3.5 };
const ASPECT = (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin);
const LEVELS = [0.5, 2, 6, 15, 35, 80, 180, 400, 900];
const CHART = { height: 214, left: 46, right: 14, top: 30, bottom: 34 };
const TOUR_STEPS_PER_SECOND = 16;
const COMPARE = ["none", "gd"] as const;
type Compare = (typeof COMPARE)[number];

interface Settings {
  eta: number;
  noise: number;
  beta1: number;
  compare: Compare;
}

const INITIAL: Settings = { eta: 0.1, noise: 0, beta1: 0.9, compare: "none" };

function fromBeat(settings: BeatSettings, base: Settings): Settings {
  return {
    eta: numberSetting(settings, "eta", base.eta),
    noise: numberSetting(settings, "noise", base.noise),
    beta1: numberSetting(settings, "beta1", base.beta1),
    compare: stringSetting(settings, "compare", COMPARE, base.compare),
  };
}

export default function AdamStepRatio() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromBeat(settings, value)), []),
  );
  const { eta, noise, beta1, compare } = tour.beat ? fromBeat(tour.beat.settings, chosen) : chosen;
  const set = <K extends keyof Settings>(key: K) => (value: Settings[K]) => setChosen((old) => ({ ...old, [key]: value }));
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);

  const run = useMemo(
    () => runAdam(PROBLEM, START, { ...ADAM_DEFAULTS, eta, beta1, noise, seed: SEED, maxSteps: MAX_STEPS }),
    [eta, beta1, noise],
  );
  const plain = useMemo(() => runPlainDescent(PROBLEM, START, eta, MAX_STEPS), [eta]);
  const timeline = useTimeline(MAX_STEPS, 12);
  useReplayOnChange(timeline, tour.active ? `guided${tour.index}` : [eta, noise, beta1].join("|"));
  const position = tour.active ? Math.min(MAX_STEPS, tour.local * TOUR_STEPS_PER_SECOND) : timeline.position;
  const step = Math.min(Math.floor(position + 1e-9), MAX_STEPS);
  const fraction = position - step;
  const path = run.path;
  const head: readonly [number, number] = step < MAX_STEPS
    ? [path[step][0] + (path[step + 1][0] - path[step][0]) * fraction, path[step][1] + (path[step + 1][1] - path[step][1]) * fraction]
    : path[step];
  const trail = [...path.slice(0, step + 1), ...(fraction > 0 ? [head] : [])];
  // The step about to be taken from the current point (the last one once the run has ended).
  const current = run.steps[Math.min(step, MAX_STEPS - 1)];
  const plainDrawable = drawable(plain.path);
  const plainShown = plain.path.slice(0, Math.min(step + 1, plainDrawable));

  const verdict = describe(current.cx, current.cy, step);
  const summary = [
    `Adam、η=${fmt(eta, 2)}、β1=${fmt(beta1, 2)}、勾配のノイズ σ=${fmt(noise, 0)}。`,
    `${step}歩目の位置は ${fmtPair(path[step][0], path[step][1])}、目的関数値 ${fmt(run.values[step], 3)}。`,
    `次の一歩は x が η の ${fmt(Math.abs(current.cx.ratio))} 倍、y が η の ${fmt(Math.abs(current.cy.ratio))} 倍です。`,
    compare === "gd"
      ? plain.diverged
        ? `同じ η の勾配降下法は発散します（安定限界は 0.05）。`
        : `同じ η の勾配降下法は、${MAX_STEPS}回で目的関数値 ${fmt(valleyValue(PROBLEM, plain.path[plain.path.length - 1][0], plain.path[plain.path.length - 1][1]), 3)} です。`
      : "",
  ].join("");

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(eta, 2)}
            hint="Adam では、各座標が1回に動く距離のおよその上限です。"
            label="learning rate η"
            max={0.4}
            min={0.02}
            onChange={set("eta")}
            step={0.01}
            value={eta}
          />
          <Slider
            display={fmt(noise, 0)}
            hint="勾配の各座標に、標準偏差 σ の乱数を足します（固定seed）。"
            label="勾配のノイズ σ"
            max={40}
            min={0}
            onChange={set("noise")}
            step={1}
            value={noise}
          />
          <Slider
            display={fmt(beta1, 2)}
            hint="一次モーメント m（勾配の平均）がどれだけ過去を覚えるか。"
            label="β1"
            max={0.99}
            min={0}
            onChange={set("beta1")}
            step={0.01}
            value={beta1}
          />
          <Choice<Compare>
            legend="重ねて比べる"
            onChange={set("compare")}
            options={[
              { value: "none", label: "なし" },
              { value: "gd", label: "同じηの勾配降下法" },
            ]}
            value={compare}
          />
        </>
      }
      id={ID}
      player={<PlayerBar positionText={`t = ${step} / ${MAX_STEPS}`} stepLabel="歩数 t" timeline={timeline} />}
      readout={<Readout current={current} eta={eta} step={step} verdict={verdict} />}
      stage={
        <>
          <div className="ex-canvas" ref={stageRef}>
            <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
              <rect className="ex-ground" height={viewport.height} width={viewport.width} />
              <ValleyAxes scale={scale} viewport={viewport} />
              <Contours scale={scale} />
              {compare === "gd" && (
                <>
                  <path className="ex-compare" d={polylinePath(plainShown, scale)} />
                  {plainShown.map(([x, y], index) => (
                    <circle className="ex-compare-dot" cx={scale.px(x)} cy={scale.py(y)} key={index} r={3} />
                  ))}
                </>
              )}
              <path className="ex-ghost" d={polylinePath(path, scale)} />
              <path className="ex-trail" d={polylinePath(trail, scale)} />
              <g className="ex-minimum">
                <circle cx={scale.px(PROBLEM.cx)} cy={scale.py(PROBLEM.cy)} r={6} />
                <text x={scale.px(PROBLEM.cx) + 10} y={scale.py(PROBLEM.cy) + 22}>最小点 (1, −2)</text>
              </g>
              <StepBox current={current} eta={eta} head={head} scale={scale} />
              <circle className="ex-head" cx={scale.px(head[0])} cy={scale.py(head[1])} r={7} />
              <text className="ex-label" x={scale.px(START[0]) + 12} y={scale.py(START[1]) - 10}>初期点 (4, 3)</text>
              {compare === "gd" && plain.diverged && (
                <text className="ex-label ex-label-strong" x={12} y={22}>灰色の破線：同じ η の勾配降下法（発散）</text>
              )}
            </svg>
          </div>
          <RatioChart position={position} steps={run.steps} width={viewport.width} />
        </>
      }
      summary={summary}
      tour={tour}
    />
  );
}

function drawable(path: ReadonlyArray<readonly [number, number]>): number {
  const outside = path.findIndex(([x, y]) => x < BOUNDS.xMin || x > BOUNDS.xMax || y < BOUNDS.yMin || y > BOUNDS.yMax);
  return outside === -1 ? path.length : outside + 1;
}

/**
 * The box each coordinate may move in one step is about ±η wide. Drawing it around the current
 * point shows that Adam's step is bounded per coordinate, unlike a gradient step.
 */
function StepBox({ current, eta, head, scale }: { current: { cx: AdamCoordinate; cy: AdamCoordinate }; eta: number; head: readonly [number, number]; scale: Scale }) {
  const left = scale.px(head[0] - eta);
  const right = scale.px(head[0] + eta);
  const top = scale.py(head[1] + eta);
  const bottom = scale.py(head[1] - eta);
  const tip = [head[0] + current.cx.move, head[1] + current.cy.move];
  return (
    <g>
      <rect className="ex-step-box" height={bottom - top} width={right - left} x={left} y={top} />
      <line
        className="ex-next-step"
        markerEnd="url(#ex-adam-arrow)"
        x1={scale.px(head[0])}
        x2={scale.px(tip[0])}
        y1={scale.py(head[1])}
        y2={scale.py(tip[1])}
      />
      <defs>
        <marker id="ex-adam-arrow" markerHeight="7" markerWidth="7" orient="auto-start-reverse" refX="5" refY="3.5">
          <path className="ex-arrowhead" d="M0 0L7 3.5L0 7z" />
        </marker>
      </defs>
    </g>
  );
}

function ValleyAxes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  return (
    <g className="ex-axes">
      {[-4, -2, 0, 2, 4, 6].map((x) => (
        <g key={`x${x}`}>
          <line x1={scale.px(x)} x2={scale.px(x)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(x)} y={viewport.height - 6}>{x}</text>
        </g>
      ))}
      {[-4, -2, 0, 2].map((y) => (
        <g key={`y${y}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
          <text x={6} y={scale.py(y) - 4}>{y}</text>
        </g>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 6}>x</text>
      <text className="ex-axis-name" x={scale.px(0) + 6} y={16}>y</text>
    </g>
  );
}

const Contours = memo(function Contours({ scale }: { scale: Scale }) {
  const paths = useMemo(() => {
    const fn = (x: number, y: number) => valleyValue(PROBLEM, x, y);
    return LEVELS.map((level) => segmentsPath(contourSegments(fn, BOUNDS, level, 230, 180), scale));
  }, [scale]);
  return <g>{paths.map((d, index) => <path className="ex-contour" d={d} key={LEVELS[index]} />)}</g>;
});

/** m̂/(√v̂+ε) per coordinate over time: the step in units of η. */
function RatioChart({ steps, position, width }: { steps: ReturnType<typeof runAdam>["steps"]; position: number; width: number }) {
  const { height, left, right, top, bottom } = CHART;
  const px = (t: number) => left + (t / MAX_STEPS) * (width - left - right);
  const py = (value: number) => top + ((1.05 - value) / 2.1) * (height - top - bottom);
  const line = (pick: (s: (typeof steps)[number]) => number) => steps
    .map((s, index) => `${index === 0 ? "M" : "L"}${px(index).toFixed(1)} ${py(pick(s)).toFixed(1)}`)
    .join("");
  const index = Math.min(Math.floor(position), MAX_STEPS - 1);
  const s = steps[index];
  return (
    <svg className="ex-svg ex-chart" viewBox={`0 0 ${width} ${height}`}>
      <rect className="ex-ground" height={height} width={width} />
      {[-1, -0.5, 0, 0.5, 1].map((value) => (
        <g className="ex-axes" key={value}>
          <line x1={left} x2={width - right} y1={py(value)} y2={py(value)} />
          <text textAnchor="end" x={left - 6} y={py(value) + 4}>{value === 0 ? "0" : fmt(value, 1)}</text>
        </g>
      ))}
      {[0, 20, 40, 60, 80, 100, 120].map((t) => (
        <text className="ex-axes-text" key={t} textAnchor="middle" x={px(t)} y={height - 14}>{t}</text>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={width - right} y={height - 1}>歩数 t</text>
      <text className="ex-axis-name" x={left + 4} y={16}>一歩 ÷ η（＝平均 ÷ 大きさ）</text>
      <path className="ex-ratio-x" d={line((item) => item.cx.ratio)} />
      <path className="ex-ratio-y" d={line((item) => item.cy.ratio)} />
      <circle className="ex-ratio-x-dot" cx={px(index)} cy={py(s.cx.ratio)} r={5} />
      <circle className="ex-ratio-y-dot" cx={px(index)} cy={py(s.cy.ratio)} r={5} />
      <text className="ex-label ex-ratio-x-label" textAnchor="end" x={width - right - 4} y={py(-0.62)}>━ x 座標（ゆるやか）</text>
      <text className="ex-label ex-ratio-y-label" textAnchor="end" x={width - right - 4} y={py(-0.85)}>━ y 座標（急）</text>
    </svg>
  );
}

interface Verdict {
  tone: "good" | "slow" | "swing";
  text: string;
}

function describe(cx: AdamCoordinate, cy: AdamCoordinate, step: number): Verdict {
  const rx = Math.abs(cx.ratio);
  const ry = Math.abs(cy.ratio);
  if (step <= 3) {
    return {
      tone: "swing",
      text: `勾配は x が ${fmt(Math.abs(cx.g), 1)}、y が ${fmt(Math.abs(cy.g), 1)} と大きく違うのに、比（勾配の平均÷勾配の大きさ）はどちらも約1です。両方の座標が同じ η だけ動くので、点は斜め45°に進みます。`,
    };
  }
  if (rx < 0.15 && ry < 0.15) {
    return {
      tone: "good",
      text: "どちらの座標でも比が小さくなりました。過去の大きな勾配を覚えている「勾配の大きさ」に比べて、最近の「勾配の平均」が小さいためです。一歩は自然に縮みます。",
    };
  }
  const [small, large, smallName, largeName] = rx < ry ? [rx, ry, "x", "y"] : [ry, rx, "y", "x"];
  if (small < 0.5 * large) {
    return {
      tone: "slow",
      text: `${smallName} の比（${fmt(small)}）が ${largeName} の比（${fmt(large)}）よりずっと小さくなっています。${smallName} では勾配の符号が揃わない（行き過ぎの往復やノイズ）か、過去より勾配が小さくなったので、Adam が ${smallName} の一歩を縮めています。`,
    };
  }
  return {
    tone: "good",
    text: `両方の座標で比が ${fmt(Math.min(rx, ry))}〜${fmt(Math.max(rx, ry))} です。勾配の向きがそろっている間は、勾配の大きさによらず η に近い距離を進みます。`,
  };
}

function Readout({ current, eta, step, verdict }: { current: { cx: AdamCoordinate; cy: AdamCoordinate }; eta: number; step: number; verdict: Verdict }) {
  const equation = (name: string, c: AdamCoordinate) => row(
    mo("Δ"), mi(name), mo("="), mo("−"), mn(fmt(eta, 2)), mo("×"),
    frac(tint("orange", signed(fmt(c.mHat, 2))), tint("teal", mn(fmt(c.rms, 2)))),
    mo("="), signed(fmt(c.move, 3)),
  );
  const symbolic = row(
    mo("Δ"), mi("x"), mo("="), mo("−"), mi("η"),
    frac(tint("orange", sub(hat("m"), mi("t"))), row(tint("teal", row(mo("√"), sub(hat("v"), mi("t")))), mo("+"), mi("ε"))),
  );
  const text = (name: string, c: AdamCoordinate) => `${name} の動き = −${fmt(eta, 2)} × ${fmt(c.mHat, 2)} ÷ ${fmt(c.rms, 2)} = ${fmt(c.move, 3)}`;
  return (
    <>
      <section aria-label="いまの一歩" className="ex-equation">
        <p className="ex-eyebrow">いまの一歩（t = {Math.min(step + 1, MAX_STEPS)}）：座標ごとに別々に計算する</p>
        <LiveMath block label="動き = マイナス η 掛ける、勾配の平均 m̂ を勾配の二乗平均の平方根で割った値" markup={symbolic} />
        <LiveMath block label={text("x", current.cx)} markup={equation("x", current.cx)} />
        <LiveMath block label={text("y", current.cy)} markup={equation("y", current.cy)} />
      </section>
      <table className="ex-table">
        <thead>
          <tr>
            <th scope="col">座標</th><th scope="col">いまの勾配 g</th><th scope="col">勾配の平均</th>
            <th scope="col">勾配の大きさ</th><th scope="col">比（平均÷大きさ）</th>
          </tr>
        </thead>
        <tbody>
          {([["x（ゆるやか）", current.cx], ["y（急）", current.cy]] as const).map(([name, c]) => (
            <tr key={name}>
              <th scope="row">{name}</th>
              <td>{fmt(c.g, 2)}</td>
              <td>{fmt(c.mHat, 2)}</td>
              <td>{fmt(c.rms, 2)}</td>
              <td>{fmt(c.ratio, 2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={`ex-verdict ex-tone-${verdict.tone}`}>{verdict.text}</p>
    </>
  );
}
