import { memo, useCallback, useMemo, useRef, useState, type KeyboardEvent, type RefObject } from "react";

import { Choice, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { contourSegments, type Bounds } from "./math/contours";
import { evaluateLine, fitLine, sseAt, type DataPoint, type Line } from "./math/leastSquares";
import { LiveMath, mn, mo, row, sup, tint } from "./mathml";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting, type BeatSettings } from "./scene";
import { clamp, makeScale, segmentsPath, useDomainDrag, useStageViewport, type Scale, type Viewport } from "./svg";
import { useSceneTour } from "./useSceneTour";

const ID = "least-squares-bowl";
const TS = [0, 1, 2, 3] as const;
const DEFAULT_YS: readonly number[] = [1, 2, 2, 4];
const Y_RANGE: readonly [number, number] = [-0.5, 8];
const DATA_BOUNDS: Bounds = { xMin: -0.6, xMax: 3.9, yMin: -1, yMax: 8.5 };
const PARAM_BOUNDS: Bounds = { xMin: -2.5, xMax: 4.5, yMin: -1.2, yMax: 3.2 };
const A_RANGE: readonly [number, number] = [-2, 4];
const B_RANGE: readonly [number, number] = [-1, 3];
const LEVEL_OFFSETS = [0.25, 1, 2.5, 5, 10, 20, 40, 80];
const MODES = ["fit", "manual"] as const;
type Mode = (typeof MODES)[number];

interface Settings {
  ys: readonly number[];
  mode: Mode;
  line: Line;
}

const INITIAL: Settings = { ys: DEFAULT_YS, mode: "manual", line: { a: 0.5, b: 1.3 } };

/** A beat may move the last point (`y3`), set the line (`a`, `b`), or snap it to the fit. */
function fromBeat(settings: BeatSettings, base: Settings): Settings {
  return {
    ys: DEFAULT_YS.map((y, index) => numberSetting(settings, `y${index}`, y)),
    mode: stringSetting(settings, "mode", MODES, base.mode),
    line: { a: numberSetting(settings, "a", base.line.a), b: numberSetting(settings, "b", base.line.b) },
  };
}

export default function LeastSquaresBowl() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromBeat(settings, value)), []),
  );
  const shown = tour.beat ? fromBeat(tour.beat.settings, chosen) : chosen;
  const points: DataPoint[] = useMemo(() => TS.map((t, index) => ({ t, y: shown.ys[index] })), [shown.ys]);
  const best = useMemo(() => fitLine(points) ?? { a: 0, b: 0 }, [points]);
  const line = shown.mode === "fit" ? best : shown.line;
  const fit = evaluateLine(points, line);
  const optimum = evaluateLine(points, best);
  const atOptimum = Math.abs(fit.sse - optimum.sse) < 1e-6;

  const setLine = (update: (line: Line) => Line) => setChosen((value) => {
    const base = value.mode === "fit" ? fitLine(TS.map((t, i) => ({ t, y: value.ys[i] }))) ?? value.line : value.line;
    const next = update(base);
    return { ...value, mode: "manual", line: { a: clamp(next.a, A_RANGE[0], A_RANGE[1]), b: clamp(next.b, B_RANGE[0], B_RANGE[1]) } };
  });
  const setY = (index: number, y: number) => setChosen((value) => ({
    ...value,
    ys: value.ys.map((old, i) => (i === index ? clamp(y, Y_RANGE[0], Y_RANGE[1]) : old)),
  }));
  const setMode = (mode: Mode) => setChosen((value) => ({
    ...value,
    mode,
    line: mode === "manual" && value.mode === "fit"
      ? fitLine(TS.map((t, i) => ({ t, y: value.ys[i] }))) ?? value.line
      : value.line,
  }));
  const reset = () => setChosen(INITIAL);

  const summary = [
    `直線 y = ${fmt(line.a)} + ${fmt(line.b)} t（切片 x₁、傾き x₂）。残差の二乗和は ${fmt(fit.sse, 3)}。`,
    atOptimum
      ? "これが最小で、残差の合計と、残差に t を掛けた合計はどちらも0です。"
      : `最小の二乗和は ${fmt(optimum.sse, 3)}（直線 y = ${fmt(best.a)} + ${fmt(best.b)} t）です。`,
  ].join("");

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<Mode>
            legend="直線"
            onChange={setMode}
            options={[
              { value: "manual", label: "自分で動かす" },
              { value: "fit", label: "二乗和が最小の直線" },
            ]}
            value={shown.mode}
          />
          <Slider
            display={fmt(line.a)}
            label="切片 x₁"
            max={A_RANGE[1]}
            min={A_RANGE[0]}
            onChange={(a) => setLine((old) => ({ ...old, a }))}
            step={0.05}
            value={line.a}
          />
          <Slider
            display={fmt(line.b)}
            label="傾き x₂"
            max={B_RANGE[1]}
            min={B_RANGE[0]}
            onChange={(b) => setLine((old) => ({ ...old, b }))}
            step={0.05}
            value={line.b}
          />
          <details className="lsq-point-controls">
            <summary>観測点の値を調整する</summary>
            {shown.ys.map((y, index) => <Slider key={index} label={`観測点${index + 1}の高さ`} display={fmt(y)} min={Y_RANGE[0]} max={Y_RANGE[1]} step={0.1} value={y} onChange={(next) => setY(index, next)} />)}
          </details>
          <div className="ex-button-row">
            <button className="ex-action" onClick={reset} type="button">点と直線を最初に戻す</button>
          </div>
        </>
      }
      id={ID}
      readout={<Readout atOptimum={atOptimum} best={best} fit={fit} line={line} optimum={optimum.sse} points={points} />}
      stage={
        <div className="ex-twin">
          <DataPanel fit={fit} fixed={tour.active} line={line} onMoveY={setY} points={points} />
          <ParameterPanel
            best={best}
            fixed={tour.active}
            gradient={fit.gradient}
            line={line}
            onMove={(a, b) => setLine(() => ({ a, b }))}
            points={points}
          />
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

interface DataPanelProps {
  points: DataPoint[];
  line: Line;
  fit: ReturnType<typeof evaluateLine>;
  fixed: boolean;
  onMoveY(index: number, y: number): void;
}

function DataPanel({ points, line, fit, fixed, onMoveY }: DataPanelProps) {
  const { ref, viewport } = useStageViewport(DATA_BOUNDS, 0.95);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const svgRef = useRef<SVGSVGElement>(null);
  const unit = scale.py(0) - scale.py(1);
  const xEdge = [DATA_BOUNDS.xMin, DATA_BOUNDS.xMax];
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">観測点 ↕ 上下に動かせます</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <DataAxes scale={scale} viewport={viewport} />
          {points.map((p, index) => {
            const r = fit.residuals[index];
            const side = Math.abs(r) * unit;
            const predicted = line.a + line.b * p.t;
            // Squares open to the right, except the last point, whose square opens left to stay in view.
            const left = index === points.length - 1 ? scale.px(p.t) - side : scale.px(p.t);
            const top = Math.min(scale.py(p.y), scale.py(predicted));
            return <rect className="ex-square" height={side} key={`sq${index}`} width={side} x={left} y={top} />;
          })}
          <line
            className="ex-fit-line"
            x1={scale.px(xEdge[0])}
            x2={scale.px(xEdge[1])}
            y1={scale.py(line.a + line.b * xEdge[0])}
            y2={scale.py(line.a + line.b * xEdge[1])}
          />
          {points.map((p, index) => (
            <line
              className="ex-residual"
              key={`r${index}`}
              x1={scale.px(p.t)}
              x2={scale.px(p.t)}
              y1={scale.py(p.y)}
              y2={scale.py(line.a + line.b * p.t)}
            />
          ))}
          {points.map((p, index) => (
            <DataHandle
              fixed={fixed}
              index={index}
              key={`p${index}`}
              onMoveY={onMoveY}
              point={p}
              residual={fit.residuals[index]}
              scale={scale}
              svgRef={svgRef}
              viewport={viewport}
            />
          ))}
        </svg>
      </div>
    </figure>
  );
}

interface DataHandleProps {
  point: DataPoint;
  index: number;
  residual: number;
  scale: Scale;
  viewport: Viewport;
  svgRef: RefObject<SVGSVGElement | null>;
  fixed: boolean;
  onMoveY(index: number, y: number): void;
}

function DataHandle({ point, index, residual, scale, viewport, svgRef, fixed, onMoveY }: DataHandleProps) {
  const drag = useDomainDrag({ svgRef, viewport, onDrag: (_x, y) => onMoveY(index, Math.round(y * 20) / 20) });
  const onKeyDown = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 1 : 0.1;
    const delta = event.key === "ArrowUp" ? amount : event.key === "ArrowDown" ? -amount : 0;
    if (delta === 0) return;
    event.preventDefault();
    onMoveY(index, Math.round((point.y + delta) * 100) / 100);
  };
  const cx = scale.px(point.t);
  const cy = scale.py(point.y);
  const props = fixed
    ? { className: "ex-handle is-fixed" }
    : {
        "aria-label": `点${index + 1}（t=${point.t}、y=${fmt(point.y)}）。残差 ${fmt(residual)}。上下にドラッグするか、上下の矢印キーで動かせます。`,
        "aria-orientation": "vertical" as const,
        "aria-valuemax": Y_RANGE[1],
        "aria-valuemin": Y_RANGE[0],
        "aria-valuenow": point.y,
        className: "ex-handle",
        onKeyDown,
        role: "slider",
        tabIndex: 0,
        ...drag,
      };
  return (
    <g {...props}>
      <circle className="ex-handle-hit" cx={cx} cy={cy} r={24} />
      <circle className="ex-handle-ring" cx={cx} cy={cy} r={13} />
      <circle className="ex-observation" cx={cx} cy={cy} r={7} />
      <text className="lsq-drag-cue" aria-hidden="true" x={cx + 16} y={cy + 5}>↕</text>
    </g>
  );
}

function DataAxes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  return (
    <g className="ex-axes">
      {[0, 1, 2, 3].map((t) => (
        <g key={`t${t}`}>
          <line x1={scale.px(t)} x2={scale.px(t)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(t)} y={viewport.height - 6}>{t}</text>
        </g>
      ))}
      {[0, 2, 4, 6, 8].map((y) => (
        <g key={`y${y}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
          <text x={6} y={scale.py(y) - 4}>{y}</text>
        </g>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={viewport.height - 22}>t</text>
      <text className="ex-axis-name" x={scale.px(0) + 8} y={16}>y</text>
    </g>
  );
}

interface ParameterPanelProps {
  points: DataPoint[];
  line: Line;
  best: Line;
  gradient: readonly [number, number];
  fixed: boolean;
  onMove(a: number, b: number): void;
}

function ParameterPanel({ points, line, best, gradient, fixed, onMove }: ParameterPanelProps) {
  const { ref, viewport } = useStageViewport(PARAM_BOUNDS, 0.95);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const svgRef = useRef<SVGSVGElement>(null);
  const snap = (value: number) => Math.round(value * 20) / 20;
  const drag = useDomainDrag({ svgRef, viewport, onDrag: (a, b) => onMove(snap(a), snap(b)) });
  const onKeyDown = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 0.5 : 0.05;
    const moves: Record<string, readonly [number, number]> = {
      ArrowLeft: [-amount, 0], ArrowRight: [amount, 0], ArrowUp: [0, amount], ArrowDown: [0, -amount],
    };
    const delta = moves[event.key];
    if (!delta) return;
    event.preventDefault();
    onMove(snap(line.a + delta[0]), snap(line.b + delta[1]));
  };
  // The arrow shows the direction that lowers the sum fastest, at a fixed drawn length.
  const norm = Math.hypot(gradient[0], gradient[1]);
  const arrowLength = 0.8;
  const tip: readonly [number, number] = norm > 1e-6
    ? [line.a - (gradient[0] / norm) * arrowLength, line.b - (gradient[1] / norm) * arrowLength]
    : [line.a, line.b];
  const handleProps = fixed
    ? { className: "ex-handle is-fixed" }
    : {
        "aria-label": `直線を表す点（x₁=${fmt(line.a)}、x₂=${fmt(line.b)}）。ドラッグか矢印キーで直線を動かせます。`,
        "aria-roledescription": "2次元のつまみ",
        className: "ex-handle",
        onKeyDown,
        role: "group",
        tabIndex: 0,
        ...drag,
      };
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">直線を表す点 ↔↕ 動かせます</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <ParamAxes scale={scale} viewport={viewport} />
          <BowlContours best={best} points={points} scale={scale} />
          {norm > 1e-6 && (
            <line
              className="ex-next-step"
              markerEnd="url(#ex-ls-arrow)"
              x1={scale.px(line.a)}
              x2={scale.px(tip[0])}
              y1={scale.py(line.b)}
              y2={scale.py(tip[1])}
            />
          )}
          <g className="ex-minimum">
            <circle cx={scale.px(best.a)} cy={scale.py(best.b)} r={6} />
            <text x={scale.px(best.a) + 10} y={scale.py(best.b) + 20}>底 ({fmt(best.a)}, {fmt(best.b)})</text>
          </g>
          <g {...handleProps}>
            <circle className="ex-handle-hit" cx={scale.px(line.a)} cy={scale.py(line.b)} r={24} />
            <circle className="ex-handle-ring" cx={scale.px(line.a)} cy={scale.py(line.b)} r={10} />
            <circle className="ex-head" cx={scale.px(line.a)} cy={scale.py(line.b)} r={5} />
            <text className="lsq-drag-cue" aria-hidden="true" x={scale.px(line.a) + 15} y={scale.py(line.b) - 14}>↔↕</text>
          </g>
          <defs>
            <marker id="ex-ls-arrow" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="6" refY="4">
              <path className="ex-arrowhead" d="M0 0L8 4L0 8z" />
            </marker>
          </defs>
        </svg>
      </div>
    </figure>
  );
}

const BowlContours = memo(function BowlContours(
  { points, best, scale }: { points: DataPoint[]; best: Line; scale: Scale },
) {
  const paths = useMemo(() => {
    const floor = sseAt(points, best.a, best.b);
    const fn = (a: number, b: number) => sseAt(points, a, b);
    return LEVEL_OFFSETS.map((offset) => segmentsPath(contourSegments(fn, PARAM_BOUNDS, floor + offset, 160, 110), scale));
  }, [points, best, scale]);
  return <g>{paths.map((d, index) => <path className="ex-contour" d={d} key={LEVEL_OFFSETS[index]} />)}</g>;
});

function ParamAxes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  return (
    <g className="ex-axes">
      {[-2, 0, 2, 4].map((a) => (
        <g key={`a${a}`}>
          <line x1={scale.px(a)} x2={scale.px(a)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(a)} y={viewport.height - 6}>{a}</text>
        </g>
      ))}
      {[-1, 0, 1, 2, 3].map((b) => (
        <g key={`b${b}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(b)} y2={scale.py(b)} />
          <text x={6} y={scale.py(b) - 4}>{b}</text>
        </g>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={viewport.height - 22}>切片 x₁</text>
      <text className="ex-axis-name" x={scale.px(0) + 8} y={16}>傾き x₂</text>
    </g>
  );
}

interface ReadoutProps {
  points: DataPoint[];
  line: Line;
  best: Line;
  fit: ReturnType<typeof evaluateLine>;
  optimum: number;
  atOptimum: boolean;
}

function Readout({ points, line, best, fit, optimum, atOptimum }: ReadoutProps) {
  const squares = fit.residuals.map((r) => sup(mn(`(${fmt(r)})`), mn("2")));
  const terms: string[] = [];
  squares.forEach((square, index) => {
    if (index > 0) terms.push(mo("+"));
    terms.push(square);
  });
  const sum = row(...terms);
  const total = row(mo("="), tint(atOptimum ? "teal" : "orange", mn(fmt(fit.sse, 3))));
  const near = (value: number) => Math.abs(value) < 5e-3;
  return (
    <>
      <section aria-label="残差の二乗和" className="ex-equation">
        <p className="ex-eyebrow">残差の二乗和（四角の面積の合計）</p>
        <LiveMath block label={`残差の二乗を4つ足す`} markup={sum} />
        <LiveMath block label={`二乗和は ${fmt(fit.sse, 3)}`} markup={total} />
        <p className="ex-hint">最小値は {fmt(optimum, 3)}。そのときの直線は y = {fmt(best.a)} + {fmt(best.b)} t です。</p>
      </section>
      <section aria-label="点ごとの残差">
        <table className="ex-table">
          <thead>
            <tr>
              <th scope="col">点</th><th scope="col">t</th><th scope="col">y</th><th scope="col">予測 x₁+x₂t</th>
              <th scope="col">残差 r</th><th scope="col">t·r</th>
            </tr>
          </thead>
          <tbody>
            {points.map((p, index) => (
              <tr key={index}>
                <th scope="row">{index + 1}</th>
                <td>{p.t}</td>
                <td>{fmt(p.y)}</td>
                <td>{fmt(line.a + line.b * p.t)}</td>
                <td>{fmt(fit.residuals[index])}</td>
                <td>{fmt(p.t * fit.residuals[index])}</td>
              </tr>
            ))}
            <tr className={near(fit.residualSum) && near(fit.residualMoment) ? "ex-row-best" : undefined}>
              <th scope="row" colSpan={4}>合計</th>
              <td>{fmt(fit.residualSum)}</td>
              <td>{fmt(fit.residualMoment)}</td>
            </tr>
          </tbody>
        </table>
      </section>
      <p className={`ex-verdict ${atOptimum ? "ex-tone-good" : "ex-tone-swing"}`}>
        {atOptimum
          ? "お椀の底です。残差の合計 Σr も、t を掛けた合計 Σt·r も0なので、切片を動かしても傾きを動かしても二乗和は増えます。"
          : `まだ底ではありません。Σr = ${fmt(fit.residualSum)}、Σt·r = ${fmt(fit.residualMoment)} が0でない分だけ、右の矢印の向きへ直線を動かすと二乗和が減ります。`}
      </p>
      <p className="ex-hint">四角の面積が残差の二乗です。観測点の高さを動かすと、最小の直線とお椀の底の位置が変わります。</p>
    </>
  );
}
