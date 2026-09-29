import { memo, useMemo, useRef, useState, type KeyboardEvent } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import { contourSegments, type Bounds } from "./math/contours";
import {
  GRADIENT_TOLERANCE,
  axisRate,
  runDescent,
  stabilityLimit,
  valleyCurvatures,
  valleyValue,
  type AxisRate,
  type DescentMethod,
  type DescentPoint,
  type ValleyProblem,
} from "./math/descent";
import { LiveMath, addend, mi, mn, mo, paren, row, signed, sub } from "./mathml";
import {
  clamp,
  makeScale,
  polylinePath,
  segmentsPath,
  useDomainDrag,
  useStageViewport,
  type Scale,
  type Viewport,
} from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const MAX_STEPS = 100;
const CENTER = { cx: 1, cy: -2 } as const;
const DEFAULT_START: readonly [number, number] = [4, 3];
const BOUNDS: Bounds = { xMin: -4.5, xMax: 7, yMin: -5.5, yMax: 3.5 };
const ASPECT = (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin);
const LEVELS = [0.5, 2, 6, 15, 35, 80, 180, 400, 900];
const CHART = { height: 190, left: 58, right: 14, top: 12, bottom: 34 };

type Tone = "good" | "slow" | "swing" | "bad";

export default function GradientDescentValley() {
  const [eta, setEta] = useState(0.04);
  const [kappa, setKappa] = useState(20);
  const [method, setMethod] = useState<DescentMethod>("gd");
  const [beta, setBeta] = useState(0.5);
  const [start, setStart] = useState<readonly [number, number]>(DEFAULT_START);
  const svgRef = useRef<SVGSVGElement>(null);
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);

  const problem: ValleyProblem = useMemo(() => ({ ...CENTER, kappa }), [kappa]);
  const run = useMemo(
    () => runDescent(problem, start, { eta, method, beta, maxSteps: MAX_STEPS }),
    [problem, start, eta, method, beta],
  );
  const timeline = useTimeline(run.points.length - 1, 10);
  const limit = stabilityLimit(problem, method, beta);
  const { gentle, steep } = valleyCurvatures(problem);
  const gentleRate = axisRate(method, gentle, eta, beta);
  const steepRate = axisRate(method, steep, eta, beta);

  useReplayOnChange(timeline, [eta, kappa, method, beta, start[0], start[1]].join("|"));

  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const drag = useDomainDrag({
    svgRef,
    viewport,
    onDrag: (x, y) => setStart([clamp(x, BOUNDS.xMin + 0.3, BOUNDS.xMax - 0.3), clamp(y, BOUNDS.yMin + 0.3, BOUNDS.yMax - 0.3)]),
  });
  const nudgeStart = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 1 : 0.25;
    const move: Record<string, readonly [number, number]> = {
      ArrowLeft: [-amount, 0],
      ArrowRight: [amount, 0],
      ArrowUp: [0, amount],
      ArrowDown: [0, -amount],
    };
    const delta = move[event.key];
    if (!delta) return;
    event.preventDefault();
    setStart(([x, y]) => [
      clamp(x + delta[0], BOUNDS.xMin + 0.3, BOUNDS.xMax - 0.3),
      clamp(y + delta[1], BOUNDS.yMin + 0.3, BOUNDS.yMax - 0.3),
    ]);
  };

  const points = run.points;
  const step = Math.min(timeline.step, points.length - 1);
  const current = points[step];
  const previous = points[Math.max(0, step - 1)];
  const next = nextPoint(current, previous, { eta, method, beta });
  const travelled = points.slice(0, step + 1).map((p) => [p.x, p.y] as const);
  const fraction = timeline.position - step;
  const head: readonly [number, number] = step < points.length - 1
    ? [
        current.x + (points[step + 1].x - current.x) * fraction,
        current.y + (points[step + 1].y - current.y) * fraction,
      ]
    : [current.x, current.y];
  const trail = fraction > 0 && step < points.length - 1 ? [...travelled, head] : travelled;

  const verdict = describeRun(run.outcome, points, limit, eta);
  const summary = [
    `${method === "gd" ? "勾配降下法" : "Momentum"}、learning rate ${fmt(eta, 3)}、谷の細長さ κ=${kappa}、初期点${fmtPair(start[0], start[1])}。`,
    verdict.text,
    `x方向の倍率は${fmt(gentleRate.factor)}、y方向の倍率は${fmt(steepRate.factor)}です。`,
  ].join("");

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(eta, 3)}
            hint={<>安定限界は <strong>{fmt(limit, 3)}</strong>。この値を超えると誤差が増えます。</>}
            label="learning rate η"
            max={0.25}
            min={0.005}
            onChange={setEta}
            step={0.001}
            value={eta}
          />
          <Slider
            display={String(kappa)}
            hint="大きいほど、y方向だけが急な細長い谷になります。"
            label="谷の細長さ κ"
            max={40}
            min={1}
            onChange={setKappa}
            step={1}
            value={kappa}
          />
          <Choice<DescentMethod>
            legend="更新則"
            onChange={setMethod}
            options={[
              { value: "gd", label: "勾配降下法" },
              { value: "momentum", label: "Momentum" },
            ]}
            value={method}
          />
          {method === "momentum" && (
            <Slider
              display={fmt(beta, 2)}
              hint="直前の動きをどれだけ持ち越すか。"
              label="持ち越し β"
              max={0.95}
              min={0}
              onChange={setBeta}
              step={0.05}
              value={beta}
            />
          )}
        </>
      }
      id="gradient-descent-valley"
      player={
        <PlayerBar
          positionText={`k = ${step} / ${points.length - 1}`}
          stepLabel="反復 k"
          timeline={timeline}
        />
      }
      readout={
        <Readout
          current={current}
          eta={eta}
          gentleRate={gentleRate}
          method={method}
          beta={beta}
          next={next}
          previous={previous}
          curvatures={{ gentle, steep }}
          steepRate={steepRate}
          step={step}
          verdict={verdict}
        />
      }
      stage={
        <>
          <div className="ex-canvas" ref={stageRef}>
          <svg
            className="ex-svg"
            ref={svgRef}
            viewBox={`0 0 ${viewport.width} ${viewport.height}`}
          >
            <rect className="ex-ground" height={viewport.height} width={viewport.width} />
            <Axes scale={scale} viewport={viewport} />
            <ContourLayer kappa={kappa} scale={scale} startValue={valleyValue(problem, start[0], start[1])} />
            <path
              className="ex-ghost"
              d={polylinePath(points.map((p) => [p.x, p.y] as const), scale)}
            />
            <path className="ex-trail" d={polylinePath(trail, scale)} />
            {travelled.map(([x, y], index) => (
              <circle
                className="ex-iterate"
                cx={scale.px(x)}
                cy={scale.py(y)}
                key={index}
                r={index === step ? 0 : 3}
              />
            ))}
            <Minimum scale={scale} />
            <line
              className="ex-next-step"
              markerEnd="url(#ex-arrow)"
              x1={scale.px(current.x)}
              x2={scale.px(next[0])}
              y1={scale.py(current.y)}
              y2={scale.py(next[1])}
            />
            <circle className="ex-head" cx={scale.px(head[0])} cy={scale.py(head[1])} r={8} />
            <g
              aria-label={`初期点 ${fmtPair(start[0], start[1])}。ドラッグか矢印キーで動かせます。`}
              aria-roledescription="2次元のつまみ"
              className="ex-handle"
              onKeyDown={nudgeStart}
              role="group"
              tabIndex={0}
              {...drag}
            >
              <circle className="ex-handle-hit" cx={scale.px(start[0])} cy={scale.py(start[1])} r={20} />
              <circle className="ex-handle-ring" cx={scale.px(start[0])} cy={scale.py(start[1])} r={11} />
              <text className="ex-label" x={scale.px(start[0]) + 16} y={scale.py(start[1]) - 12}>初期点</text>
            </g>
            <defs>
              <marker id="ex-arrow" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="6" refY="4">
                <path className="ex-arrowhead" d="M0 0L8 4L0 8z" />
              </marker>
            </defs>
          </svg>
          </div>
          <LossChart points={points} position={timeline.position} width={viewport.width} />
        </>
      }
      summary={summary}
    />
  );
}

function nextPoint(
  current: DescentPoint,
  previous: DescentPoint,
  { eta, method, beta }: { eta: number; method: DescentMethod; beta: number },
): readonly [number, number] {
  const carryX = method === "momentum" ? beta * (current.x - previous.x) : 0;
  const carryY = method === "momentum" ? beta * (current.y - previous.y) : 0;
  return [current.x + carryX - eta * current.gx, current.y + carryY - eta * current.gy];
}

interface Verdict {
  tone: Tone;
  text: string;
}

function describeRun(
  outcome: "converged" | "diverged" | "unfinished",
  points: DescentPoint[],
  limit: number,
  eta: number,
): Verdict {
  const last = points[points.length - 1];
  if (outcome === "converged") {
    return { tone: "good", text: `収束しました（gradient norm が ${GRADIENT_TOLERANCE} を下回るまで ${last.k} 回）。` };
  }
  if (outcome === "diverged") {
    return {
      tone: "bad",
      text: `発散しました（${last.k} 回目で目的関数値が ${fmt(last.f, 0)} まで増加）。η=${fmt(eta, 3)} は安定限界 ${fmt(limit, 3)} を超えています。`,
    };
  }
  return {
    tone: "slow",
    text: `${MAX_STEPS} 回では収束していません（gradient norm ${fmt(last.gradNorm, 3)}、目的関数値 ${fmt(last.f, 3)}）。`,
  };
}

function Axes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  const xs = [-4, -2, 0, 2, 4, 6];
  const ys = [-4, -2, 0, 2];
  return (
    <g className="ex-axes">
      {xs.map((x) => (
        <g key={`x${x}`}>
          <line x1={scale.px(x)} x2={scale.px(x)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(x)} y={viewport.height - 6}>{x}</text>
        </g>
      ))}
      {ys.map((y) => (
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

const ContourLayer = memo(function ContourLayer(
  { kappa, startValue, scale }: { kappa: number; startValue: number; scale: Scale },
) {
  const paths = useMemo(() => {
    const fn = (x: number, y: number) => valleyValue({ ...CENTER, kappa }, x, y);
    return LEVELS.map((level) => segmentsPath(contourSegments(fn, BOUNDS, level, 230, 180), scale));
  }, [kappa, scale]);
  const startPath = useMemo(() => {
    const fn = (x: number, y: number) => valleyValue({ ...CENTER, kappa }, x, y);
    return segmentsPath(contourSegments(fn, BOUNDS, startValue, 230, 180), scale);
  }, [kappa, scale, startValue]);
  return (
    <g>
      {paths.map((d, index) => <path className="ex-contour" d={d} key={LEVELS[index]} />)}
      <path className="ex-contour-start" d={startPath} />
    </g>
  );
});

function Minimum({ scale }: { scale: Scale }) {
  const x = scale.px(CENTER.cx);
  const y = scale.py(CENTER.cy);
  return (
    <g className="ex-minimum">
      <circle cx={x} cy={y} r={6} />
      <text x={x + 10} y={y + 22}>最小点 (1, −2)</text>
    </g>
  );
}

function LossChart({ points, position, width }: { points: DescentPoint[]; position: number; width: number }) {
  const { height, left, right, top, bottom } = CHART;
  const logs = points.map((p) => Math.log10(Math.max(p.f, 1e-6)));
  const high = Math.max(4, Math.ceil(Math.max(...logs)));
  const low = -6;
  const px = (k: number) => left + (k / MAX_STEPS) * (width - left - right);
  const py = (value: number) => top + ((high - value) / (high - low)) * (height - top - bottom);
  const decades: number[] = [];
  for (let d = low; d <= high; d += high - low > 10 ? 3 : 2) decades.push(d);
  const line = logs.map((value, k) => `${k === 0 ? "M" : "L"}${px(k).toFixed(1)} ${py(value).toFixed(1)}`).join("");
  const lower = Math.min(Math.floor(position), points.length - 1);
  const upper = Math.min(lower + 1, points.length - 1);
  const t = position - lower;
  const markerLog = logs[lower] + (logs[upper] - logs[lower]) * t;
  return (
    <svg className="ex-svg ex-chart" viewBox={`0 0 ${width} ${height}`}>
      <rect className="ex-ground" height={height} width={width} />
      {decades.map((d) => (
        <g className="ex-axes" key={d}>
          <line x1={left} x2={width - right} y1={py(d)} y2={py(d)} />
          <text textAnchor="end" x={left - 6} y={py(d) + 4}>
            {d === 0 ? "1" : (
              <>
                10<tspan dy={-6} fontSize="0.8em">{d}</tspan>
              </>
            )}
          </text>
        </g>
      ))}
      {[0, 20, 40, 60, 80, 100].map((k) => (
        <text className="ex-axes-text" key={k} textAnchor="middle" x={px(k)} y={height - 14}>{k}</text>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={width - right} y={height - 1}>反復 k</text>
      <text className="ex-axis-name" x={left} y={top + 10}>目的関数値 f（対数目盛）</text>
      <path className="ex-loss" d={line} />
      <circle className="ex-head" cx={px(lower + t)} cy={py(markerLog)} r={6} />
    </svg>
  );
}

interface ReadoutProps {
  current: DescentPoint;
  previous: DescentPoint;
  next: readonly [number, number];
  eta: number;
  beta: number;
  method: DescentMethod;
  gentleRate: AxisRate;
  steepRate: AxisRate;
  curvatures: { gentle: number; steep: number };
  step: number;
  verdict: Verdict;
}

function Readout({
  current, previous, next, eta, beta, method, gentleRate, steepRate, curvatures, step, verdict,
}: ReadoutProps) {
  const xk = sub(mi("𝐱"), mi("k"));
  const xk1 = sub(mi("𝐱"), row(mi("k"), mo("+"), mn("1")));
  const grad = row(mo("∇"), mi("f"), paren(xk));
  const symbolic = method === "gd"
    ? row(xk1, mo("="), xk, mo("−"), mi("η"), grad)
    : row(
        xk1, mo("="), xk, mo("+"), mi("β"),
        paren(xk, mo("−"), sub(mi("𝐱"), row(mi("k"), mo("−"), mn("1")))),
        mo("−"), mi("η"), grad,
      );
  const pair = (x: number, y: number) => paren(signed(fmt(x)), mo(","), signed(fmt(y)));
  // The substitution and its result sit on separate lines so a narrow column never scrolls.
  const numeric = method === "gd"
    ? row(
        mo("="), pair(current.x, current.y),
        mo("−"), mn(fmt(eta, 3)), mo("·"), pair(current.gx, current.gy),
      )
    : row(
        mo("="), pair(current.x, current.y),
        addend(fmt(beta)), mo("·"), pair(current.x - previous.x, current.y - previous.y),
        mo("−"), mn(fmt(eta, 3)), mo("·"), pair(current.gx, current.gy),
      );
  const result = row(mo("="), pair(next[0], next[1]));
  const plain = `k=${step} の一手: 次の点 ${fmtPair(next[0], next[1])} = 現在の点 ${fmtPair(current.x, current.y)} から、勾配 ${fmtPair(current.gx, current.gy)} に η=${fmt(eta, 3)} を掛けた分だけ動く`;
  return (
    <>
      <section className="ex-equation" aria-label="いまの一手">
        <p className="ex-eyebrow">いまの一手（k = {step}）</p>
        <LiveMath block label={method === "gd" ? "更新式 x の次の値は x から η 掛ける勾配を引いたもの" : "更新式 x の次の値は x に β 掛ける直前の動きを足し、η 掛ける勾配を引いたもの"} markup={symbolic} />
        <LiveMath block label={plain} markup={numeric} />
        <LiveMath block label={`結果は ${fmtPair(next[0], next[1])}`} markup={result} />
      </section>
      <section aria-label="方向ごとの誤差の縮み方">
        <p className="ex-eyebrow">方向ごとに、1回で誤差が何倍になるか</p>
        <table className="ex-table">
          <thead>
            <tr><th scope="col">方向</th><th scope="col">曲率</th><th scope="col">倍率</th><th scope="col">読み方</th></tr>
          </thead>
          <tbody>
            <RateRow curvature={fmt(curvatures.gentle, 0)} name="x（ゆるやか）" rate={gentleRate} />
            <RateRow curvature={fmt(curvatures.steep, 0)} name="y（急）" rate={steepRate} />
          </tbody>
        </table>
        <p className="ex-hint">
          倍率が1に近いほど遅く、負なら符号が反転し、絶対値が1を超えると発散します。谷が細長いほど、二つの方向の倍率を同時に良くできません。
        </p>
      </section>
      <p className={`ex-verdict ex-tone-${verdict.tone}`}>{verdict.text}</p>
    </>
  );
}

function RateRow({ name, curvature, rate }: { name: string; curvature: string; rate: AxisRate }) {
  const reading = readRate(rate);
  return (
    <tr>
      <th scope="row">{name}</th>
      <td>{curvature}</td>
      <td className={`ex-tone-${reading.tone}`}>{fmt(rate.factor, 2)}</td>
      <td>{reading.text}</td>
    </tr>
  );
}

function readRate(rate: AxisRate): { tone: Tone; text: string } {
  if (rate.rate >= 1) return { tone: "bad", text: "誤差が増える（発散）" };
  const perThousand = Math.ceil(Math.log(1e-3) / Math.log(Math.max(rate.rate, 1e-12)));
  const cost = `誤差を1/1000にするのに約${perThousand}回`;
  if (rate.oscillates) return { tone: "swing", text: `符号を変えながら縮む（振動）。${cost}` };
  if (perThousand > 50) return { tone: "slow", text: `ゆっくり縮む。${cost}` };
  if (perThousand > 15) return { tone: "good", text: `縮む。${cost}` };
  return { tone: "good", text: `速く縮む。${cost}` };
}
