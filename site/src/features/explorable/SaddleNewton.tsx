import { useMemo, useRef, useState, type KeyboardEvent } from "react";

import { Choice, PlayerBar } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import { contourSegments, type Bounds } from "./math/contours";
import {
  classify, curvatures, gradient, newtonRun, SADDLE, START_A, START_B, VALLEYS, value,
  type NewtonRun, type Point2,
} from "./math/saddleNewton";
import { makeScale, polylinePath, segmentsPath, useDomainDrag, useStageViewport } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const BOUNDS: Bounds = { xMin: -1.8, xMax: 1.8, yMin: -1.2, yMax: 1.2 };
const ASPECT = (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin);
/** Rings around the valleys, and the level of the saddle (f = 1) drawn darker. */
const LEVELS = [-0.1, 0.5, 2, 4];
const SADDLE_LEVEL = 1;

type Preset = "A" | "B" | "custom";

export default function SaddleNewton() {
  const [preset, setPreset] = useState<Preset>("A");
  const [start, setStart] = useState<Point2>(START_A);
  const svgRef = useRef<SVGSVGElement>(null);
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);

  const run = useMemo(() => newtonRun(start), [start]);
  const steps = run.points.length - 1;
  const timeline = useTimeline(steps, 1.1);
  useReplayOnChange(timeline, start.join("|"));
  const step = Math.min(timeline.step, steps);
  const current = interpolate(run, timeline.position);
  const finished = timeline.atEnd || steps === 0;

  const rings = useMemo(
    () => LEVELS.map((level) => segmentsPath(contourSegments(fn, BOUNDS, level, 144, 96), scale)),
    [scale],
  );
  const saddleRing = useMemo(
    () => segmentsPath(contourSegments(fn, BOUNDS, SADDLE_LEVEL, 144, 96), scale),
    [scale],
  );

  const place = (point: Point2) => {
    setPreset("custom");
    // Snap to 0.01 so keyboard steps land on the printed grid (0.9, not 0.9000000000000001).
    setStart([snap(clamp(point[0], BOUNDS.xMin, BOUNDS.xMax)), snap(clamp(point[1], BOUNDS.yMin, BOUNDS.yMax))]);
  };
  const choose = (next: Preset) => {
    if (next === "custom") return;
    setPreset(next);
    setStart(next === "A" ? START_A : START_B);
  };
  const drag = useDomainDrag({ svgRef, viewport, onDrag: (x, y) => place([x, y]) });
  const nudge = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 0.2 : 0.05;
    const delta: Record<string, Point2> = {
      ArrowLeft: [-amount, 0], ArrowRight: [amount, 0], ArrowUp: [0, amount], ArrowDown: [0, -amount],
    };
    const move = delta[event.key];
    if (!move) return;
    event.preventDefault();
    place([start[0] + move[0], start[1] + move[1]]);
  };

  const end = run.points[steps];
  const verdict = verdictText(run, start);
  const [low, high] = curvatures(current);
  const slope = Math.hypot(...gradient(current));
  const travelled = [...run.points.slice(0, step + 1), current];
  const summary = `誤差の指標 f=(x₁²−1)²+x₁x₂+2x₂² の等高線の上で、始点 ${fmtPair(start[0], start[1], 2)} から純粋なNewton法を繰り返します。${verdict}`;

  return (
    <ExplorableFrame
      controls={
        <Choice<Preset>
          legend="始点"
          onChange={choose}
          options={[
            { value: "A", label: "始点A (0.5, 1.0)" },
            { value: "B", label: "始点B (0.2, 0.1)" },
            ...(preset === "custom" ? [{ value: "custom" as const, label: `置いた点 ${fmtPair(start[0], start[1], 2)}` }] : []),
          ]}
          value={preset}
        />
      }
      id="saddle-newton"
      player={
        <PlayerBar
          positionText={`${step} / ${steps} 回`}
          stepLabel="Newton法の反復"
          timeline={timeline}
        />
      }
      readout={
        <>
          <section aria-label="いまの点の勾配と曲率">
            <p className="ex-eyebrow">いまの点を、勾配と曲率で調べる</p>
            <table className="ex-table">
              <tbody>
                <tr><th scope="row">位置 x</th><td>{pair(current)}</td></tr>
                <tr><th scope="row">誤差の指標 f(x)</th><td>{fmt(value(current), 3)}</td></tr>
                <tr><th scope="row">勾配の大きさ |∇f|</th><td>{magnitude(slope)}</td></tr>
                <tr>
                  <th scope="row">曲率（Hessianの固有値）</th>
                  <td>{fmt(low, 2)} と {fmt(high, 2)}</td>
                </tr>
              </tbody>
            </table>
            <p className="ex-hint">
              勾配が0の点で、曲率が二つとも正なら谷底、符号が混ざれば峠です。勾配がまだ0でない途中の点では、曲率だけで谷底かどうかは決まりません。
            </p>
          </section>
          <p className={`ex-verdict ${finished && classify(end) === "valley" ? "ex-tone-good" : "ex-tone-slow"}`}>
            {finished ? verdict : `${step} / ${steps} 回目。勾配はまだ0ではありません（|∇f|=${magnitude(slope)}）。`}
          </p>
        </>
      }
      stage={
        <figure className="ex-panel">
          <figcaption className="ex-panel-title">誤差の指標の等高線と、Newton法の道すじ</figcaption>
          <div className="ex-canvas" ref={stageRef}>
            <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
              <rect className="ex-ground" height={viewport.height} width={viewport.width} />
              <g className="ex-axes">
                {[-1, 0, 1].map((tick) => (
                  <g key={`x${tick}`}>
                    <line x1={scale.px(tick)} x2={scale.px(tick)} y1={0} y2={viewport.height} />
                    <text textAnchor="middle" x={scale.px(tick)} y={viewport.height - 6}>{tick}</text>
                  </g>
                ))}
                {[-1, 0, 1].map((tick) => (
                  <g key={`y${tick}`}>
                    <line x1={0} x2={viewport.width} y1={scale.py(tick)} y2={scale.py(tick)} />
                    <text x={6} y={scale.py(tick) + (tick > 0 ? 14 : -4)}>{tick}</text>
                  </g>
                ))}
              </g>
              {rings.map((d, index) => <path className="ex-contour" d={d} key={LEVELS[index]} />)}
              <path className="ex-contour-key" d={saddleRing} />
              <path className="ex-trail" d={polylinePath(travelled, scale)} />
              {run.points.slice(1, step + 1).map((point, index) => (
                <circle className="ex-iterate" cx={scale.px(point[0])} cy={scale.py(point[1])} key={index} r={3.5} />
              ))}
              {VALLEYS.map((valley, index) => (
                <g className="ex-minimum" key={index}>
                  <circle cx={scale.px(valley[0])} cy={scale.py(valley[1])} r={7} />
                  <text
                    textAnchor={valley[0] > 0 ? "end" : "start"}
                    x={scale.px(valley[0]) + (valley[0] > 0 ? -12 : 12)}
                    y={scale.py(valley[1]) + (valley[0] > 0 ? 22 : -12)}
                  >
                    谷底
                  </text>
                </g>
              ))}
              <g className="ex-saddle">
                <path d={cross(scale.px(SADDLE[0]), scale.py(SADDLE[1]))} />
                <text textAnchor="end" x={scale.px(SADDLE[0]) - 10} y={scale.py(SADDLE[1]) + 22}>峠</text>
              </g>
              <circle className="ex-head" cx={scale.px(current[0])} cy={scale.py(current[1])} r={7} />
              <g
                aria-label={`始点 ${fmtPair(start[0], start[1], 2)}。ドラッグか矢印キーで動かせます。`}
                aria-roledescription="2次元のつまみ"
                className="ex-handle"
                onKeyDown={nudge}
                role="group"
                tabIndex={0}
                {...drag}
              >
                <circle className="ex-handle-hit" cx={scale.px(start[0])} cy={scale.py(start[1])} r={20} />
                <circle className="ex-handle-ring" cx={scale.px(start[0])} cy={scale.py(start[1])} r={6} />
                {/* Near the top edge the label goes below the handle so it is never cut off. */}
                <text
                  className="ex-label"
                  textAnchor={scale.px(start[0]) > viewport.width - 48 ? "end" : "start"}
                  x={scale.px(start[0]) + (scale.px(start[0]) > viewport.width - 48 ? -12 : 12)}
                  y={scale.py(start[1]) + (scale.py(start[1]) < 28 ? 22 : -10)}
                >
                  始点
                </text>
              </g>
              <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 6}>x₁</text>
              <text className="ex-axis-name" x={scale.px(0) + 6} y={16}>x₂</text>
            </svg>
          </div>
        </figure>
      }
      summary={summary}
    />
  );
}

function fn(x1: number, x2: number): number {
  return value([x1, x2]);
}

function clamp(x: number, low: number, high: number): number {
  return Math.min(Math.max(x, low), high);
}

function interpolate(run: NewtonRun, position: number): Point2 {
  const last = run.points.length - 1;
  const at = clamp(position, 0, last);
  const index = Math.min(Math.floor(at), Math.max(last - 1, 0));
  if (last === 0) return run.points[0];
  const t = at - index;
  const [a, b] = [run.points[index], run.points[index + 1]];
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
}

function cross(x: number, y: number): string {
  const r = 7;
  return `M${x - r} ${y - r}L${x + r} ${y + r}M${x - r} ${y + r}L${x + r} ${y - r}`;
}

function magnitude(x: number): string {
  if (x === 0) return "0";
  return Math.abs(x) < 0.001 ? x.toExponential(1) : fmt(x, 3);
}

function verdictText(run: NewtonRun, start: Point2): string {
  const steps = run.points.length - 1;
  const end = run.points[steps];
  const from = `始点 ${fmtPair(start[0], start[1], 2)} から`;
  if (run.stop === "singular") {
    return `${from}${steps}回進んだ点で、Hessianが特異（x₁≈±0.595 の線の上）になり、Newton法の一手が決まりません。`;
  }
  if (run.stop === "escaped") return `${from}${steps + 1}回目の一手が大きすぎて、図の外へ出ました。`;
  if (run.stop === "budget") return `${from}${steps}回繰り返しても、勾配が0になりませんでした。`;
  const [low, high] = curvatures(end);
  const curvature = `曲率は ${fmt(low, 2)} と ${fmt(high, 2)}`;
  const kind = classify(end);
  if (kind === "valley") {
    return `${from}${steps}回で谷底 ${pair(end)}（f=${fmt(value(end), 3)}）に着きました。勾配は0で、${curvature}と二つとも正です。`;
  }
  if (kind === "saddle") {
    return `${from}${steps}回で峠 ${pair(end)}（f=${fmt(value(end), 3)}）に着き、そこで止まりました。勾配は0ですが、${curvature}と符号が混ざるので、谷底ではありません。`;
  }
  return `${from}${steps}回で勾配が0の点 ${pair(end)} に着きました。${curvature}です。`;
}

function snap(x: number): number {
  return Math.round(x * 100) / 100;
}

/** Iterates converge to 1e-17 rather than 0; print those as 0 instead of in exponent form. */
function pair(point: Point2): string {
  const clean = (x: number) => (Math.abs(x) < 1e-9 ? 0 : x);
  return fmtPair(clean(point[0]), clean(point[1]), 3);
}
