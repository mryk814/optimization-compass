import { memo, useEffect, useMemo, useRef, useState } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { contourSegments, type Bounds } from "./math/contours";
import {
  acceptedPath,
  alongStep,
  cost,
  costHistory,
  EXP_T,
  EXP_Y,
  MAX_TRIALS,
  modelAt,
  observationReadings,
  pointAfter,
  runTrials,
  type FitMode,
  type FitPoint,
  type Run,
  type Trial,
} from "./math/expFit";
import { EXPLORABLE_META } from "./meta";
import { clamp, makeScale, polylinePath, segmentsPath, useStageViewport, type Scale } from "./svg";
import { useTimeline } from "./useTimeline";
import "./gauss-newton-lm.css";

const ID = "gauss-newton-lm-steps";
const DATA_BOUNDS: Bounds = { xMin: -0.3, xMax: 4.4, yMin: -0.4, yMax: 7 };
const PARAM_BOUNDS: Bounds = { xMin: -0.4, xMax: 1.4, yMin: 0, yMax: 8 };
const LEVELS = [0.01, 0.05, 0.25, 1, 3, 8, 16, 32, 64];
const OPTIMUM: FitPoint = { a: 5.07867619, k: 0.50493273 };
const BAR_LIMIT = 4.5;
const S_MAX = 1.25;
const ALONG_BOUNDS: Bounds = { xMin: -0.1, xMax: S_MAX, yMin: 0, yMax: 1 };
const ALONG_FLOOR = -0.12;
const LOG_LOW = -6;
const LOG_HIGH = 3.6;
const STARTS = {
  far: { a: 1, k: 0.1 },
  near: { a: 5, k: 0.3 },
} as const;
type StartKey = keyof typeof STARTS;

/** A step arrow shorter than this many pixels is stretched to it, so the direction stays readable. */
const MIN_ARROW_PX = 14;

const lambdaOf = (logLambda: number) => 10 ** logLambda;
const lambdaText = (value: number) => (value === 0 ? "0" : value >= 100 ? value.toFixed(0) : value >= 1 ? value.toFixed(1) : value.toPrecision(2));
const modeName = (mode: FitMode) => (mode === "gn" ? "Gauss–Newton法" : "Levenberg–Marquardt法");
const startText = (key: StartKey) => `(a, k)=(${STARTS[key].a}, ${STARTS[key].k})`;

/** Chases `target` at a fixed speed so a one-step press glides instead of jumping. */
function useChase(target: number, reduced: boolean, speed = 2.2): number {
  const [value, setValue] = useState(target);
  const current = useRef(target);
  useEffect(() => {
    if (reduced || current.current - target > 1.5) {
      current.current = target;
      setValue(target);
      return undefined;
    }
    let frame = 0;
    let last: number | undefined;
    const tick = (now: number) => {
      const dt = last === undefined ? 0 : Math.min(0.1, (now - last) / 1000);
      last = now;
      const diff = target - current.current;
      if (Math.abs(diff) < 1e-4) {
        current.current = target;
        setValue(target);
        return;
      }
      current.current += Math.sign(diff) * Math.min(Math.abs(diff), dt * speed);
      setValue(current.current);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, reduced, speed]);
  return reduced ? target : value;
}

export default function GaussNewtonLm() {
  const [mode, setMode] = useState<FitMode>("gn");
  const [startKey, setStartKey] = useState<StartKey>("far");
  const [logLambda, setLogLambda] = useState(-2);
  const [keepGn, setKeepGn] = useState(false);
  const start = STARTS[startKey];
  const lambda0 = lambdaOf(logLambda);
  const run = useMemo(() => runTrials(mode, start, lambda0), [mode, start, lambda0]);
  const gnRun = useMemo(() => runTrials("gn", start, 0), [start]);
  const ghost: Run | undefined = mode === "lm" && keepGn ? gnRun : undefined;
  const timeline = useTimeline(run.trials.length, 1.2);
  const position = useChase(timeline.position, timeline.reducedMotion);
  const step = timeline.step;
  const shown = run.trials.slice(0, step);
  const last: Trial | undefined = shown[shown.length - 1];

  // Displayed (animated) state: `done` whole trials plus `frac` of the trial in flight.
  const done = Math.min(run.trials.length, Math.floor(position + 1e-9));
  const frac = clamp(position - done, 0, 1);
  const flying: Trial | undefined = frac > 1e-3 ? run.trials[done] : undefined;
  const settled = done > 0 ? run.trials[done - 1] : undefined;
  const focus: Trial | undefined = flying ?? settled ?? run.trials[0];
  const progress = flying ? frac : settled ? 1 : 0;
  const base = pointAfter(run, start, done);
  const head: FitPoint = flying?.accepted
    ? { a: base.a + frac * flying.step.a, k: base.k + frac * flying.step.k }
    : base;
  const point = pointAfter(run, start, step);

  const change = (apply: () => void) => {
    apply();
    timeline.seek(0);
  };

  const summary = last === undefined
    ? `${modeName(mode)}、始点は ${startText(startKey)}、費用 ${fmt(cost(start), 3)}。まだ試していません。`
    : `${modeName(mode)}の試行${step}。λ=${lambdaText(last.lambda)}、予測した減少 ${fmt(last.predicted, 3)} に対して実際の減少は ${fmt(last.actual, 3)}、ρ=${fmt(last.rho, 2)}。${last.accepted ? "受け入れました" : "捨てました"}。現在点の費用は ${fmt(cost(point), 4)}。${ghost ? "Gauss–Newton法の軌跡を薄く重ねています。" : ""}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<FitMode>
            legend="一手の決め方"
            onChange={(value) => change(() => setMode(value))}
            options={[
              { value: "gn", label: "Gauss–Newton法" },
              { value: "lm", label: "Levenberg–Marquardt法" },
            ]}
            value={mode}
          />
          <Choice<StartKey>
            legend="始点"
            onChange={(value) => change(() => setStartKey(value))}
            options={[
              { value: "far", label: "遠い始点 (1, 0.1)" },
              { value: "near", label: "近い始点 (5, 0.3)" },
            ]}
            value={startKey}
          />
          <Slider
            disabled={mode === "gn"}
            display={mode === "gn" ? "0（使わない）" : lambdaText(lambda0)}
            hint={mode === "gn" ? "Gauss–Newton法は λ=0 の一手をそのまま受け入れます。" : "最初の試行の λ です。以降は受け入れで 1/3、捨てると 10 倍に動きます。"}
            label="減衰 λ（最初の試行）"
            max={3}
            min={-3}
            onChange={(value) => change(() => setLogLambda(value))}
            step={0.5}
            value={logLambda}
            valueText={`λ は ${lambdaText(lambda0)}`}
          />
          <div className="gl-ghost-control">
            <label className="gl-ghost-toggle">
              <input checked={keepGn} disabled={mode === "gn"} onChange={(event) => setKeepGn(event.target.checked)} type="checkbox" />
              GNの軌跡を残す
            </label>
            <p className="ex-hint">
              {mode === "gn"
                ? "Levenberg–Marquardt法のときに使えます。"
                : "同じ始点から Gauss–Newton法 が進む道を、薄い線で重ねます。"}
            </p>
          </div>
        </>
      }
      id={ID}
      player={<PlayerBar positionText={`試行 ${step} / ${run.trials.length}`} stepLabel="試行" timeline={timeline} />}
      readout={<Readout mode={mode} run={run} shown={shown} step={step} />}
      stage={
        <>
          <div className="ex-twin">
            <DataPanel flying={flying} frac={frac} head={head} landed={!flying && done > 0 ? settled : undefined} settled={settled} />
            <ParamPanel done={done} focus={focus} ghost={ghost} head={head} progress={progress} run={run} start={start} />
          </div>
          <div className="ex-twin">
            <AlongPanel focus={focus} progress={progress} trialNumber={flying ? done + 1 : done > 0 ? done : 1} />
            <GainPanel done={done} run={run} />
          </div>
          <div className="ex-twin">
            <HistoryPanel done={done} ghost={ghost} run={run} start={start} />
            <LambdaPanel done={done} mode={mode} run={run} />
          </div>
        </>
      }
      summary={summary}
    />
  );
}

function DataPanel({ head, flying, settled, frac, landed }: { head: FitPoint; flying: Trial | undefined; settled: Trial | undefined; frac: number; landed: Trial | undefined }) {
  const { ref, viewport } = useStageViewport(DATA_BOUNDS, 0.75);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const curve = (p: FitPoint) => {
    const points: Array<readonly [number, number]> = [];
    for (let i = 0; i <= 120; i += 1) {
      const t = DATA_BOUNDS.xMin + ((DATA_BOUNDS.xMax - DATA_BOUNDS.xMin) * i) / 120;
      points.push([t, clamp(modelAt(p, t), DATA_BOUNDS.yMin, DATA_BOUNDS.yMax)]);
    }
    return polylinePath(points, scale);
  };
  const ghost = flying && !flying.accepted ? flying : settled && !settled.accepted ? settled : undefined;
  const readings = landed ? observationReadings(landed) : [];
  const yAt = (value: number) => scale.py(clamp(value, DATA_BOUNDS.yMin, DATA_BOUNDS.yMax));
  const offset = 9;
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">観測点と曲線</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            {[0, 1, 2, 3, 4].map((t) => (
              <g key={`t${t}`}>
                <line x1={scale.px(t)} x2={scale.px(t)} y1={0} y2={viewport.height} />
                <text textAnchor="middle" x={scale.px(t)} y={viewport.height - 6}>{t}</text>
              </g>
            ))}
            {[2, 4, 6].map((y) => (
              <g key={`y${y}`}>
                <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
                <text x={6} y={scale.py(y) - 4}>{y}</text>
              </g>
            ))}
            <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={16}>時刻 t</text>
          </g>
          {ghost && (
            <path
              className="gl-reject-curve"
              d={curve(ghost.candidate)}
              fill="none"
              key={`ghost${ghost.candidate.a}`}
              style={flying ? { opacity: 0.25 + 0.75 * frac } : undefined}
            />
          )}
          <path className="ex-fit-line" d={curve(head)} fill="none" />
          {EXP_T.map((t, index) => (
            <line className="ex-residual" key={`r${index}`} x1={scale.px(t)} x2={scale.px(t)} y1={scale.py(EXP_Y[index])} y2={scale.py(clamp(modelAt(head, t), DATA_BOUNDS.yMin, DATA_BOUNDS.yMax))} />
          ))}
          {readings.map((reading, index) => (
            <g className="gl-mark" key={`m${index}`}>
              <line x1={scale.px(reading.t) - offset} x2={scale.px(reading.t) + offset} y1={yAt(reading.linearized)} y2={yAt(reading.actual)} />
              <rect className="gl-mark-lin" height={9} width={9} x={scale.px(reading.t) - offset - 4.5} y={yAt(reading.linearized) - 4.5} />
              <circle className="gl-mark-act" cx={scale.px(reading.t) + offset} cy={yAt(reading.actual)} r={5} />
            </g>
          ))}
          {EXP_T.map((t, index) => (
            <circle className="ex-observation" cx={scale.px(t)} cy={scale.py(EXP_Y[index])} key={`p${index}`} r={6} />
          ))}
        </svg>
      </div>
      <p className="ex-hint">
        実線が現在の曲線{ghost ? "、赤い破線が捨てる試行の曲線" : ""}です。
        {readings.length > 0 ? "試行の終わりでは、各観測の時刻に、一手の先で線形モデルが予想する値（青緑の四角）と、実際にその曲線が通る値（橙の丸）を並べます。二つが離れた時刻ほど、線形化が外れています。" : ""}
      </p>
    </figure>
  );
}

const Contours = memo(function Contours({ scale }: { scale: Scale }) {
  const paths = useMemo(() => {
    const fn = (k: number, a: number) => cost({ a, k });
    return LEVELS.map((level) => segmentsPath(contourSegments(fn, PARAM_BOUNDS, level, 160, 160), scale));
  }, [scale]);
  return <g>{paths.map((d, index) => <path className="ex-contour" d={d} key={LEVELS[index]} />)}</g>;
});

interface Arrow {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/** Stretches an arrow that would be a dot to MIN_ARROW_PX, keeping its direction. */
function stretched(arrow: Arrow): Arrow {
  const length = Math.hypot(arrow.x1 - arrow.x0, arrow.y1 - arrow.y0);
  if (length === 0 || length >= MIN_ARROW_PX) return arrow;
  const k = MIN_ARROW_PX / length;
  return { ...arrow, x1: arrow.x0 + (arrow.x1 - arrow.x0) * k, y1: arrow.y0 + (arrow.y1 - arrow.y0) * k };
}

function arrowHead(x0: number, y0: number, x1: number, y1: number): string {
  const angle = Math.atan2(y1 - y0, x1 - x0);
  const size = 9;
  const left = [x1 - size * Math.cos(angle - 0.45), y1 - size * Math.sin(angle - 0.45)];
  const right = [x1 - size * Math.cos(angle + 0.45), y1 - size * Math.sin(angle + 0.45)];
  return `M${x1} ${y1}L${left[0]} ${left[1]}L${right[0]} ${right[1]}Z`;
}

interface ParamProps {
  run: Run;
  start: FitPoint;
  done: number;
  head: FitPoint;
  focus: Trial | undefined;
  progress: number;
  /** Gauss–Newton run from the same start, drawn faintly behind the live one. */
  ghost: Run | undefined;
}

function ParamPanel({ run, start, done, head, focus, progress, ghost }: ParamProps) {
  const { ref, viewport } = useStageViewport(PARAM_BOUNDS, 0.75);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const at = (p: FitPoint): readonly [number, number] => [
    clamp(p.k, PARAM_BOUNDS.xMin, PARAM_BOUNDS.xMax),
    clamp(p.a, PARAM_BOUNDS.yMin, PARAM_BOUNDS.yMax),
  ];
  const finished = run.trials.slice(0, done);
  const trail: Array<readonly [number, number]> = [at(start)];
  for (const trial of finished) if (trial.accepted) trail.push(at(trial.candidate));
  const headAt = at(head);
  trail.push(headAt);
  let stepArrow: { x0: number; y0: number; x1: number; y1: number } | undefined;
  let gradArrow: { x0: number; y0: number; x1: number; y1: number } | undefined;
  let shortLabel = false;
  if (focus) {
    const [fx, fy] = at(focus.from);
    const tip = at({ a: focus.from.a + progress * focus.step.a, k: focus.from.k + progress * focus.step.k });
    stepArrow = stretched({ x0: scale.px(fx), y0: scale.py(fy), x1: scale.px(tip[0]), y1: scale.py(tip[1]) });
    const gradTip = at({ a: focus.from.a + focus.gradDir.a * focus.stepLength, k: focus.from.k + focus.gradDir.k * focus.stepLength });
    gradArrow = stretched({ x0: scale.px(fx), y0: scale.py(fy), x1: scale.px(gradTip[0]), y1: scale.py(gradTip[1]) });
    const [endX, endY] = at({ a: focus.from.a + focus.step.a, k: focus.from.k + focus.step.k });
    shortLabel = Math.hypot(scale.px(endX) - scale.px(fx), scale.py(endY) - scale.py(fy)) < MIN_ARROW_PX;
  }
  const ghostPoints: Array<readonly [number, number]> = ghost ? acceptedPath(ghost, start).map(at) : [];
  const rejectedFocus = focus !== undefined && !focus.accepted;
  const landed = progress >= 1 && focus !== undefined && done > 0;
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">パラメータ平面と一手の道すじ</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            {[0, 0.5, 1].map((k) => (
              <g key={`k${k}`}>
                <line x1={scale.px(k)} x2={scale.px(k)} y1={0} y2={viewport.height} />
                <text textAnchor="middle" x={scale.px(k)} y={viewport.height - 6}>{k}</text>
              </g>
            ))}
            {[2, 4, 6].map((a) => (
              <g key={`a${a}`}>
                <line x1={0} x2={viewport.width} y1={scale.py(a)} y2={scale.py(a)} />
                <text x={6} y={scale.py(a) - 4}>{a}</text>
              </g>
            ))}
            <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={16}>減衰率 k</text>
            <text className="ex-axis-name" x={30} y={16}>振幅 a</text>
          </g>
          <Contours scale={scale} />
          <g className="ex-minimum">
            <circle cx={scale.px(OPTIMUM.k)} cy={scale.py(OPTIMUM.a)} r={6} />
            <text x={scale.px(OPTIMUM.k) + 10} y={scale.py(OPTIMUM.a) - 10}>最良</text>
          </g>
          {ghostPoints.length > 1 && (
            <g className="gl-ghost">
              <path d={polylinePath(ghostPoints, scale)} fill="none" />
              {ghostPoints.slice(1).map(([x, y], index) => (
                <circle cx={scale.px(x)} cy={scale.py(y)} key={index} r={3.5} />
              ))}
              <text x={scale.px(ghostPoints[2]?.[0] ?? ghostPoints[1][0]) + 10} y={scale.py(ghostPoints[2]?.[1] ?? ghostPoints[1][1]) + 30}>GNの軌跡</text>
            </g>
          )}
          {finished.map((trial, index) => {
            if (trial.accepted) return null;
            const [x0, y0] = at(trial.from);
            const [x1, y1] = at(trial.candidate);
            const newest = index === done - 1;
            return (
              <g className={newest ? "gl-reject is-flash" : "gl-reject"} key={`x${index}`}>
                <line x1={scale.px(x0)} x2={scale.px(x1)} y1={scale.py(y0)} y2={scale.py(y1)} />
                <path d={`M${scale.px(x1) - 6} ${scale.py(y1) - 6}L${scale.px(x1) + 6} ${scale.py(y1) + 6}M${scale.px(x1) - 6} ${scale.py(y1) + 6}L${scale.px(x1) + 6} ${scale.py(y1) - 6}`} />
              </g>
            );
          })}
          {trail.length > 1 && <path className="ex-trail" d={polylinePath(trail, scale)} />}
          {trail.slice(0, -1).map(([x, y], index) => (
            <circle className="ex-surface-dot" cx={scale.px(x)} cy={scale.py(y)} key={index} r={3.5} />
          ))}
          {stepArrow && (stepArrow.x0 !== stepArrow.x1 || stepArrow.y0 !== stepArrow.y1) && (
            <g className={rejectedFocus ? "gl-step is-rejected" : "gl-step"}>
              <line x1={stepArrow.x0} x2={stepArrow.x1} y1={stepArrow.y0} y2={stepArrow.y1} />
              <path d={arrowHead(stepArrow.x0, stepArrow.y0, stepArrow.x1, stepArrow.y1)} />
            </g>
          )}
          {gradArrow && gradArrow.x0 !== gradArrow.x1 && (
            <g className="gl-grad">
              <line x1={gradArrow.x0} x2={gradArrow.x1} y1={gradArrow.y0} y2={gradArrow.y1} />
              <path d={arrowHead(gradArrow.x0, gradArrow.y0, gradArrow.x1, gradArrow.y1)} />
            </g>
          )}
          {shortLabel && stepArrow && focus && progress > 0.5 && (
            <text className="gl-short-label" x={stepArrow.x1 + 10} y={stepArrow.y1 + 20}>長さ {fmt(focus.stepLength, 4)}</text>
          )}
          {landed && rejectedFocus && stepArrow && (
            <text className="gl-verdict" textAnchor="middle" x={stepArrow.x1} y={stepArrow.y1 - 12}>捨てる</text>
          )}
          <circle className="ex-head" cx={scale.px(headAt[0])} cy={scale.py(headAt[1])} r={7} />
        </svg>
      </div>
      <p className="ex-hint">
        太い橙の矢印がこの試行の一手、細い破線の矢印が最急降下の向き（長さは同じ）です。一手が極端に短いときは、向きが読めるよう矢印を伸ばして描き、長さを文字で添えます。赤い ✕ は捨てた試行の行き先です。{ghost ? "灰色の細い線は、同じ始点から Gauss–Newton法 が進む道です。" : ""}
      </p>
    </figure>
  );
}

function AlongPanel({ focus, progress, trialNumber }: { focus: Trial | undefined; progress: number; trialNumber: number }) {
  const { ref, viewport } = useStageViewport(ALONG_BOUNDS, 0.72);
  const top = yTop(focus);
  const scale = useMemo(() => makeScale({ ...viewport, bounds: { ...ALONG_BOUNDS, yMin: ALONG_FLOOR * top, yMax: top } }), [viewport, top]);
  if (!focus) return null;
  const samples = Array.from({ length: 101 }, (_, i) => (i / 100) * S_MAX);
  const actualPoints = samples.map((s) => [s, Math.min(alongStep(focus, s).actual, top)] as const);
  const modelPoints = samples.map((s) => [s, Math.min(alongStep(focus, s).model, top)] as const);
  const here = alongStep(focus, progress);
  const end = alongStep(focus, 1);
  const clippedEnd = end.actual > top;
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">一手に沿った費用（試行{trialNumber}）</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            {[0, 0.5, 1].map((s) => (
              <g key={s}>
                <line x1={scale.px(s)} x2={scale.px(s)} y1={0} y2={viewport.height} />
                <text textAnchor="middle" x={scale.px(s)} y={viewport.height - 6}>{s}</text>
              </g>
            ))}
            <text className="ex-axis-name" x={8} y={viewport.height - 26}>一手の割合 s</text>
            <text className="ex-axis-name" x={6} y={16}>費用</text>
          </g>
          <line className="gl-start-line" x1={0} x2={viewport.width} y1={scale.py(focus.costBefore)} y2={scale.py(focus.costBefore)} />
          <text className="gl-start-label" x={viewport.width - 8} textAnchor="end" y={scale.py(focus.costBefore) - 6}>出発点の費用 {fmt(focus.costBefore, 3)}（これより上は悪化）</text>
          <path className="gl-model" d={polylinePath(modelPoints, scale)} fill="none" />
          <path className="gl-actual" d={polylinePath(actualPoints, scale)} fill="none" />
          <line className="gl-end" x1={scale.px(1)} x2={scale.px(1)} y1={0} y2={viewport.height - 30} />
          <circle className="gl-dot-model" cx={scale.px(progress)} cy={scale.py(Math.min(here.model, top))} r={6} />
          <circle className="gl-dot-actual" cx={scale.px(progress)} cy={scale.py(Math.min(here.actual, top))} r={6} />
          {progress >= 1 && (
            <g className="ex-axes">
              <text className="gl-label-model" textAnchor="end" x={scale.px(1) - 8} y={scale.py(Math.min(end.model, top)) + 16}>予測 {fmt(end.model, 2)}</text>
              <text className="gl-label-actual" textAnchor="end" x={scale.px(1) - 8} y={scale.py(Math.min(end.actual, top)) + (clippedEnd ? 32 : -8)}>
                {clippedEnd ? "▲ " : ""}実際 {fmt(end.actual, 2)}
              </text>
            </g>
          )}
        </svg>
      </div>
      <p className="ex-hint">
        青緑の放物線が、現在点で残差を直線にした線形モデルの予測です。橙が本当の費用です。s=1 が一手の先で、ここで二つが離れるほど、線形モデルは信じられません。横の破線は出発点の費用で、橙の曲線がこの線を超えた先は、出発点より悪化しています。
      </p>
    </figure>
  );
}

function yTop(focus: Trial | undefined): number {
  return focus ? Math.max(focus.costBefore * 1.4, 0.05) : 1;
}

function GainPanel({ run, done }: { run: Run; done: number }) {
  const total = run.trials.length;
  const bounds: Bounds = { xMin: -1.0, xMax: Math.max(total, 4) + 0.6, yMin: -BAR_LIMIT, yMax: BAR_LIMIT };
  const { ref, viewport } = useStageViewport(bounds, 0.62);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const slot = scale.px(1) - scale.px(0);
  const barWidth = Math.max(5, Math.min(18, slot * 0.34));
  const clipped = (value: number) => clamp(value, -BAR_LIMIT + 0.05, BAR_LIMIT - 0.05);
  const bar = (n: number, value: number, offset: number) => {
    const x = scale.px(n) + offset;
    const y0 = scale.py(0);
    const y1 = scale.py(clipped(value));
    return { x, y: Math.min(y0, y1), height: Math.abs(y1 - y0) };
  };
  const shown = run.trials.slice(0, done);
  return (
    <figure className="ex-panel gl-gain">
      <figcaption className="ex-panel-title">予測した減少と実際の減少</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            <line className="gl-zero" x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
            {Array.from({ length: total }, (_, index) => index + 1).map((n) => (
              <text key={n} textAnchor="middle" x={scale.px(n)} y={viewport.height - 6}>{n}</text>
            ))}
            <text x={6} y={scale.py(3) + 4}>減少↑</text>
            <text x={6} y={scale.py(-3) + 4}>増加↓</text>
            <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 6}>試行 n</text>
          </g>
          {shown.length === 0 && <text className="ex-axis-name" textAnchor="middle" x={viewport.width / 2} y={viewport.height / 2}>1つ進むと、ここに棒が出ます</text>}
          {shown.map((trial, index) => {
            const n = index + 1;
            const predicted = bar(n, trial.predicted, -barWidth);
            const actual = bar(n, trial.actual, 0);
            const cut = Math.abs(trial.actual) > BAR_LIMIT - 0.05;
            return (
              <g key={n}>
                <rect className="gl-bar-pred" height={predicted.height} width={barWidth} x={predicted.x} y={predicted.y} />
                <rect className={trial.accepted ? "gl-bar-act" : "gl-bar-act is-rejected"} height={actual.height} width={barWidth} x={actual.x} y={actual.y} />
                {cut && (
                  <text className="gl-clip" textAnchor="middle" x={actual.x + barWidth / 2} y={trial.actual < 0 ? viewport.height - 22 : 14}>
                    {trial.actual < 0 ? "▼" : "▲"}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
      <p className="ex-hint">
        青緑の棒が予測、橙の棒が実際の減少です。斜線の橙は捨てた試行です。±{BAR_LIMIT} を超える棒は端で切り、▼ を付けています。
      </p>
    </figure>
  );
}

function LambdaPanel({ run, done, mode }: { run: Run; done: number; mode: FitMode }) {
  const total = run.trials.length;
  const bounds: Bounds = { xMin: 0.4, xMax: Math.max(total, 4) + 0.6, yMin: LOG_LOW, yMax: LOG_HIGH };
  const { ref, viewport } = useStageViewport(bounds, 0.5);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const shown = run.trials.slice(0, done);
  const lambdaPoints = shown.map((t, i) => [i + 1, clamp(Math.log10(t.lambda), LOG_LOW, LOG_HIGH)] as const);
  const lengthPoints = shown.map((t, i) => [i + 1, clamp(Math.log10(Math.max(t.stepLength, 1e-12)), LOG_LOW, LOG_HIGH)] as const);
  const ticks: Array<[number, string]> = [[-4, "10⁻⁴"], [-2, "10⁻²"], [0, "1"], [2, "10²"]];
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">減衰 λ と一手の長さ（対数目盛り）</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            {ticks.map(([v, label]) => (
              <g key={v}>
                <line x1={0} x2={viewport.width} y1={scale.py(v)} y2={scale.py(v)} />
                <text x={6} y={scale.py(v) - 4}>{label}</text>
              </g>
            ))}
            {Array.from({ length: total }, (_, index) => index + 1).map((n) => (
              <text key={n} textAnchor="middle" x={scale.px(n)} y={viewport.height - 6}>{n}</text>
            ))}
            <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={16}>試行 n</text>
          </g>
          {shown.length === 0 && <text className="ex-axis-name" textAnchor="middle" x={viewport.width / 2} y={viewport.height / 2}>1つ進むと、ここに点が出ます</text>}
          {mode === "lm" && lambdaPoints.length > 1 && <path className="gl-lambda-line" d={polylinePath(lambdaPoints, scale)} fill="none" />}
          {mode === "lm" && shown.map((t, i) => (
            <circle className={t.accepted ? "gl-lambda-dot" : "gl-lambda-dot is-rejected"} cx={scale.px(i + 1)} cy={scale.py(lambdaPoints[i][1])} key={`l${i}`} r={5} />
          ))}
          {lengthPoints.length > 1 && <path className="gl-length-line" d={polylinePath(lengthPoints, scale)} fill="none" />}
          {shown.map((t, i) => (
            <rect className="gl-length-dot" height={8} key={`s${i}`} width={8} x={scale.px(i + 1) - 4} y={scale.py(lengthPoints[i][1]) - 4} />
          ))}
        </svg>
      </div>
      <p className="ex-hint">
        {mode === "lm" ? "橙の丸が λ（中が白い丸は捨てた試行）、" : "Gauss–Newton法は λ=0 なので丸はありません。"}紺の四角が一手の長さです。{mode === "lm" ? "捨てるたびに λ が10倍になり、λ が大きいほど一手は短くなります。" : ""}
      </p>
    </figure>
  );
}

const HIST_LOW = -2.6;
const HIST_HIGH = 1.7;

function HistoryPanel({ run, start, done, ghost }: { run: Run; start: FitPoint; done: number; ghost: Run | undefined }) {
  const total = Math.max(run.trials.length, ghost?.trials.length ?? 0, 4);
  const bounds: Bounds = { xMin: -0.5, xMax: total + 0.6, yMin: HIST_LOW, yMax: HIST_HIGH };
  const { ref, viewport } = useStageViewport(bounds, 0.5);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const level = (value: number) => clamp(Math.log10(Math.max(value, 1e-12)), HIST_LOW + 0.05, HIST_HIGH - 0.05);
  const history = costHistory(run, start, done);
  const linePoints = history.current.map((point) => [point.n, level(point.cost)] as const);
  const ghostPoints = ghost ? costHistory(ghost, start, ghost.trials.length).current.map((point) => [point.n, level(point.cost)] as const) : [];
  const peak = ghostPoints.reduce<readonly [number, number] | undefined>((best, point) => (best === undefined || point[1] > best[1] ? point : best), undefined);
  const ticks: Array<[number, string]> = [[-2, "0.01"], [-1, "0.1"], [0, "1"], [1, "10"]];
  const cross = (x: number, y: number) => `M${scale.px(x) - 6} ${scale.py(y) - 6}L${scale.px(x) + 6} ${scale.py(y) + 6}M${scale.px(x) - 6} ${scale.py(y) + 6}L${scale.px(x) + 6} ${scale.py(y) - 6}`;
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">費用の履歴（対数目盛り）</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            {ticks.map(([v, label]) => (
              <g key={v}>
                <line x1={0} x2={viewport.width} y1={scale.py(v)} y2={scale.py(v)} />
                <text x={6} y={scale.py(v) - 4}>{label}</text>
              </g>
            ))}
            {Array.from({ length: total + 1 }, (_, n) => n).map((n) => (
              <text key={n} textAnchor="middle" x={scale.px(n)} y={viewport.height - 6}>{n}</text>
            ))}
            <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={16}>試行 n</text>
          </g>
          {ghostPoints.length > 1 && (
            <g className="gl-ghost">
              <path d={polylinePath(ghostPoints, scale)} fill="none" />
              {peak && <text x={scale.px(peak[0]) + 10} y={scale.py(peak[1]) + 4}>GN</text>}
            </g>
          )}
          {linePoints.length > 1 && <path className="gl-hist-line" d={polylinePath(linePoints, scale)} fill="none" />}
          {history.rejected.map((point) => (
            <g className="gl-reject" key={`x${point.n}`}>
              <line x1={scale.px(point.n)} x2={scale.px(point.n)} y1={scale.py(level(history.current[point.n].cost))} y2={scale.py(level(point.cost))} />
              <path d={cross(point.n, level(point.cost))} />
            </g>
          ))}
          {linePoints.map(([n, y]) => (
            <circle className="gl-hist-dot" cx={scale.px(n)} cy={scale.py(y)} key={`c${n}`} r={4.5} />
          ))}
        </svg>
      </div>
      <p className="ex-hint">
        橙の線は、受け入れた点の費用です。捨てた試行の間は水平のままで、赤い ✕ がその試行の行き先の費用です。{ghost ? "灰色の線が Gauss–Newton法 の費用です。" : ""}
      </p>
    </figure>
  );
}

function Readout({ mode, run, shown, step }: { mode: FitMode; run: Run; shown: Trial[]; step: number }) {
  const last = shown[shown.length - 1];
  const finished = step === run.trials.length;
  let verdict: string;
  let tone = "ex-tone-swing";
  if (!last) {
    verdict = "「1つ進む」を押すと、いまの点で線形化した一手を1回試します。";
  } else {
    const gain = last.predicted > 1e-9 ? `ρ=${fmt(last.rho, 2)}` : "予測の減少がほぼ0";
    const move = `一手の長さは ${fmt(last.stepLength, last.stepLength < 0.1 ? 4 : 3)}、最急降下の向きから ${fmt(last.descentAngleDeg, last.descentAngleDeg < 10 ? 1 : 0)}° ずれています。`;
    if (mode === "gn") {
      tone = last.actual < 0 ? "ex-tone-bad" : "ex-tone-good";
      verdict = last.actual < 0
        ? `試行${step}: 線形モデルは費用が ${fmt(last.predicted, 2)} 減ると予測しましたが、実際は ${fmt(-last.actual, 2)} 増えました（${gain}）。Gauss–Newton法は結果を見ずに受け入れます。${move}`
        : `試行${step}: 予測 ${fmt(last.predicted, 4)} に対して実際の減少は ${fmt(last.actual, 4)}（${gain}）。${move}`;
    } else if (last.accepted) {
      tone = "ex-tone-good";
      verdict = `試行${step}: λ=${lambdaText(last.lambda)} の一手は予測 ${fmt(last.predicted, 4)} に対して実際 ${fmt(last.actual, 4)} 減り（${gain}）、受け入れました。次の λ は ${lambdaText(last.lambda / 3)} です。${move}`;
    } else {
      tone = "ex-tone-bad";
      verdict = `試行${step}: λ=${lambdaText(last.lambda)} の一手は費用を ${fmt(-last.actual, 2)} 増やしました（${gain}）。捨てて現在点に留まり、次は λ=${lambdaText(last.lambda * 10)} で試します。${move}`;
    }
  }
  if (finished && last) {
    const end = run.outcome === "converged"
      ? "予測した減少が 10⁻⁹ を下回り、これ以上進みません。"
      : run.outcome === "singular" ? "線形化した方程式が特異になり、止まりました。" : `試行の上限 ${MAX_TRIALS} 回で打ち切りました。まだ収束したとは言えません。`;
    verdict += ` ${end}`;
  }
  return (
    <>
      {shown.length > 0 && (
        <section aria-label="試行の記録" className="gl-table-wrap">
          <table className="ex-table">
            <thead>
              <tr>
                <th scope="col">n</th><th scope="col">λ</th><th scope="col">一手の長さ</th>
                <th scope="col">予測</th><th scope="col">実際</th><th scope="col">ρ</th><th scope="col">判定</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((trial, index) => (
                <tr className={index === shown.length - 1 ? "ex-row-best" : undefined} key={index}>
                  <th scope="row">{index + 1}</th>
                  <td>{lambdaText(trial.lambda)}</td>
                  <td>{fmt(trial.stepLength, trial.stepLength < 0.1 ? 4 : 3)}</td>
                  <td>{fmt(trial.predicted, 3)}</td>
                  <td>{fmt(trial.actual, 3)}</td>
                  <td>{Number.isFinite(trial.rho) ? fmt(trial.rho, 2) : "—"}</td>
                  <td>{trial.accepted ? "受け入れ" : "捨てる"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
      <p className={`ex-verdict ${tone}`}>{verdict}</p>
    </>
  );
}
