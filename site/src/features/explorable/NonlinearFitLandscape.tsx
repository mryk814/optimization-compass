import { memo, useCallback, useMemo, useRef, useState, type KeyboardEvent } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { contourSegments, type Bounds } from "./math/contours";
import {
  bowlBottom,
  descend,
  GLOBAL_MINIMUM,
  linearizedSse,
  residuals,
  SPRING_T,
  SPRING_Y,
  sse,
  type Descent,
  type Iterate,
  type Method,
  type Params,
} from "./math/sineFit";
import type { Camera, SurfaceSpec } from "./math/surface3d";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting, type BeatSettings } from "./scene";
import { clamp, makeScale, polylinePath, segmentsPath, useDomainDrag, useStageViewport, type Scale, type Viewport } from "./svg";
import { Surface3D } from "./Surface3D";
import { useSceneTour } from "./useSceneTour";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const ID = "nonlinear-least-squares-landscape";
const DATA_BOUNDS: Bounds = { xMin: -0.2, xMax: 3.75, yMin: -3, yMax: 3 };
const PARAM_BOUNDS: Bounds = { xMin: 0.2, xMax: 5.8, yMin: -3, yMax: 3 };
const W_RANGE: readonly [number, number] = [0.2, 5.8];
const A_RANGE: readonly [number, number] = [-3, 3];
const LEVELS = [0.4, 1, 2, 4, 7, 10, 12.5, 13.65, 14, 15, 18, 22, 28];
const BOWL_OFFSETS = [0.4, 1.6, 4];
const METHODS = ["gn", "lm"] as const;
const VIEWS = ["contour", "surface"] as const;
type View = (typeof VIEWS)[number];
const SURFACE: SurfaceSpec = {
  bounds: PARAM_BOUNDS,
  fn: (w, a) => sse({ a, w }),
  zFloor: 0,
  zCeil: 20,
  resolution: 36,
  heightMode: "linear",
};
const ELEVATION = 34;

interface Settings {
  start: Params;
  method: Method;
  view: View;
  azimuth: number;
  /** False while the reader is choosing a start point; true once they asked to descend. */
  descending: boolean;
}

const INITIAL: Settings = { start: { a: 1, w: 1.8 }, method: "gn", view: "contour", azimuth: 35, descending: false };

function fromBeat(settings: BeatSettings, base: Settings): Settings {
  return {
    start: { a: numberSetting(settings, "a", base.start.a), w: numberSetting(settings, "w", base.start.w) },
    method: stringSetting(settings, "method", METHODS, base.method),
    view: stringSetting(settings, "view", VIEWS, base.view),
    azimuth: numberSetting(settings, "azimuth", base.azimuth),
    descending: numberSetting(settings, "descend", 1) === 1,
  };
}

/** Iterate shown at a fractional position: whole steps are exact, in between is interpolated. */
function iterateAt(run: Descent, position: number): Params {
  const last = run.path.length - 1;
  const k = Math.min(Math.floor(position), last);
  const next = run.path[Math.min(k + 1, last)];
  const f = Math.min(Math.max(position - k, 0), 1);
  const here = run.path[k];
  return { a: here.a + (next.a - here.a) * f, w: here.w + (next.w - here.w) * f };
}

export default function NonlinearFitLandscape() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromBeat(settings, value)), []),
  );
  const shown = tour.beat ? fromBeat(tour.beat.settings, chosen) : chosen;
  const run = useMemo(() => descend(shown.method, shown.start), [shown.method, shown.start]);
  const length = run.path.length - 1;
  const timeline = useTimeline(length, 1.4);
  useReplayOnChange(timeline, `${shown.method}:${shown.start.a}:${shown.start.w}:${shown.descending}`);
  // A guided beat walks its descent at an even pace; otherwise the reader's player decides.
  const position = !shown.descending
    ? 0
    : tour.beat
      ? Math.min(length, (tour.local / Math.max(tour.beat.durationS - 1.5, 1)) * length)
      : timeline.position;
  const step = Math.min(Math.floor(position + 1e-9), length);
  const head = shown.descending ? iterateAt(run, position) : shown.start;
  const visibleRun: Descent = shown.descending ? { ...run, path: run.path.slice(0, step + 1) } : { ...run, path: [run.path[0]] };
  const finished = shown.descending && step === length;

  const setStart = (update: Partial<Params>) => setChosen((value) => ({
    ...value,
    descending: false,
    start: {
      a: clamp(update.a ?? value.start.a, A_RANGE[0], A_RANGE[1]),
      w: clamp(update.w ?? value.start.w, W_RANGE[0], W_RANGE[1]),
    },
  }));
  const camera: Camera = useMemo(() => ({ azimuthDeg: shown.azimuth, elevationDeg: ELEVATION }), [shown.azimuth]);
  const last = run.path[length];

  const summary = !shown.descending
    ? `始点は周波数 ω=${fmt(shown.start.w)}、振幅 a=${fmt(shown.start.a)}。残差の二乗和は ${fmt(sse(shown.start), 3)}。最良の当てはめの二乗和は ${fmt(GLOBAL_MINIMUM.sse, 3)} です。`
    : `${shown.method === "gn" ? "Gauss–Newton" : "Levenberg–Marquardt"}法で ${length} 回進み、${outcomeText(run, last)}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(shown.start.w)}
            label="周波数 ω（始点）"
            max={W_RANGE[1]}
            min={W_RANGE[0]}
            onChange={(w) => setStart({ w })}
            step={0.05}
            value={shown.start.w}
          />
          <Slider
            display={fmt(shown.start.a)}
            label="振幅 a（始点）"
            max={A_RANGE[1]}
            min={A_RANGE[0]}
            onChange={(a) => setStart({ a })}
            step={0.05}
            value={shown.start.a}
          />
          <Choice<Method>
            legend="下り方"
            onChange={(method) => setChosen((value) => ({ ...value, method }))}
            options={[
              { value: "gn", label: "Gauss–Newton" },
              { value: "lm", label: "Levenberg–Marquardt" },
            ]}
            value={shown.method}
          />
          <Choice<View>
            legend="地形の見方"
            onChange={(view) => setChosen((value) => ({ ...value, view }))}
            options={[
              { value: "contour", label: "等高線" },
              { value: "surface", label: "立体" },
            ]}
            value={shown.view}
          />
          {shown.view === "surface" && (
            <Slider
              display={`${shown.azimuth}°`}
              label="立体を回す"
              max={360}
              min={0}
              onChange={(azimuth) => setChosen((value) => ({ ...value, azimuth }))}
              step={5}
              value={shown.azimuth}
            />
          )}
          <div className="ex-button-row">
            <button
              className="ex-action"
              onClick={() => setChosen((value) => ({ ...value, descending: true }))}
              type="button"
            >
              この点から下る
            </button>
            <button className="ex-action" onClick={() => setChosen(INITIAL)} type="button">最初の点に戻す</button>
          </div>
        </>
      }
      id={ID}
      player={shown.descending ? <PlayerBar positionText={`k = ${step} / ${length}`} stepLabel="反復 k" timeline={timeline} /> : undefined}
      readout={<Readout descending={shown.descending} finished={finished} head={head} last={last} run={run} step={step} start={shown.start} />}
      stage={
        <div className="ex-twin">
          <DataPanel head={head} />
          {shown.view === "contour"
            ? (
              <ContourPanel
                descending={shown.descending}
                fixed={tour.active}
                head={head}
                onMove={(w, a) => setStart({ a, w })}
                run={visibleRun}
                start={shown.start}
              />
            )
            : <SurfacePanel camera={camera} head={head} run={visibleRun} />}
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

function outcomeText(run: Descent, last: Iterate): string {
  if (run.outcome === "stalled") return `近似の計算や更新が成立せず、二乗和 ${fmt(last.sse, 2)} で止まりました。局所最小に着いたとは判断できません。`;
  if (run.outcome === "budget") return `反復の上限で打ち切りました。二乗和は ${fmt(last.sse, 2)} で、まだ変化が止まったとは判断できません。`;
  if (run.outcome === "global") return `最良の当てはめ（二乗和 ${fmt(last.sse, 3)}）に着きました。`;
  if (run.outcome === "local") return `二乗和 ${fmt(last.sse, 2)} の谷で止まりました。最良の ${fmt(GLOBAL_MINIMUM.sse, 2)} とは別の谷です。`;
  return `一歩が地図の外（ω=${fmt(last.w, 1)}）へ飛びました。`;
}

function DataPanel({ head }: { head: Params }) {
  const { ref, viewport } = useStageViewport(DATA_BOUNDS, 0.8);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const r = residuals(head);
  const unit = scale.py(0) - scale.py(1);
  const curve: Array<readonly [number, number]> = [];
  for (let i = 0; i <= 160; i += 1) {
    const t = DATA_BOUNDS.xMin + ((DATA_BOUNDS.xMax - DATA_BOUNDS.xMin) * i) / 160;
    curve.push([t, head.a * Math.sin(head.w * t)]);
  }
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">観測点と曲線</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            {[0, 1, 2, 3].map((t) => (
              <g key={`t${t}`}>
                <line x1={scale.px(t)} x2={scale.px(t)} y1={0} y2={viewport.height} />
                <text textAnchor="middle" x={scale.px(t)} y={viewport.height - 6}>{t}</text>
              </g>
            ))}
            {[-2, 0, 2].map((y) => (
              <g key={`y${y}`}>
                <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
                <text x={6} y={scale.py(y) - 4}>{y}</text>
              </g>
            ))}
            <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={viewport.height - 22}>時刻 t（秒）</text>
          </g>
          {SPRING_T.map((t, index) => {
            const side = Math.abs(r[index]) * unit;
            const fitted = head.a * Math.sin(head.w * t);
            const left = index === SPRING_T.length - 1 ? scale.px(t) - side : scale.px(t);
            return <rect className="ex-square" height={side} key={`sq${index}`} width={side} x={left} y={Math.min(scale.py(SPRING_Y[index]), scale.py(fitted))} />;
          })}
          <path className="ex-fit-line" d={polylinePath(curve, scale)} fill="none" />
          {SPRING_T.map((t, index) => (
            <line className="ex-residual" key={`r${index}`} x1={scale.px(t)} x2={scale.px(t)} y1={scale.py(SPRING_Y[index])} y2={scale.py(head.a * Math.sin(head.w * t))} />
          ))}
          {SPRING_T.map((t, index) => (
            <circle className="ex-observation" cx={scale.px(t)} cy={scale.py(SPRING_Y[index])} key={`p${index}`} r={6} />
          ))}
        </svg>
      </div>
    </figure>
  );
}

interface ContourPanelProps {
  start: Params;
  head: Params;
  run: Descent;
  descending: boolean;
  fixed: boolean;
  onMove(w: number, a: number): void;
}

function ContourPanel({ start, head, run, descending, fixed, onMove }: ContourPanelProps) {
  const { ref, viewport } = useStageViewport(PARAM_BOUNDS, 0.8);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const svgRef = useRef<SVGSVGElement>(null);
  const snap = (value: number) => Math.round(value * 20) / 20;
  const drag = useDomainDrag({ svgRef, viewport, onDrag: (w, a) => onMove(snap(w), snap(a)) });
  const onKeyDown = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 0.5 : 0.05;
    const moves: Record<string, readonly [number, number]> = {
      ArrowLeft: [-amount, 0], ArrowRight: [amount, 0], ArrowUp: [0, amount], ArrowDown: [0, -amount],
    };
    const delta = moves[event.key];
    if (!delta) return;
    event.preventDefault();
    onMove(snap(start.w + delta[0]), snap(start.a + delta[1]));
  };
  const bottom = bowlBottom(head);
  const handleProps = fixed
    ? { className: "ex-handle is-fixed" }
    : {
        "aria-label": `始点（周波数 ω=${fmt(start.w)}、振幅 a=${fmt(start.a)}）。ドラッグか矢印キーで動かせます。`,
        "aria-roledescription": "2次元のつまみ",
        className: "ex-handle",
        onKeyDown,
        role: "group",
        tabIndex: 0,
        ...drag,
      };
  const inView = (p: Params) => p.w >= PARAM_BOUNDS.xMin && p.w <= PARAM_BOUNDS.xMax && p.a >= PARAM_BOUNDS.yMin && p.a <= PARAM_BOUNDS.yMax;
  const pathPoints: Array<readonly [number, number]> = [];
  for (const p of run.path) {
    pathPoints.push([clamp(p.w, PARAM_BOUNDS.xMin, PARAM_BOUNDS.xMax), clamp(p.a, PARAM_BOUNDS.yMin, PARAM_BOUNDS.yMax)]);
    if (!inView(p)) break;
  }
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">パラメータの地形 ↔↕ 始点を動かせます</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <ParamAxes scale={scale} viewport={viewport} />
          <LandscapeContours scale={scale} />
          <BowlContours head={head} scale={scale} />
          {bottom && inView(bottom) && (
            <g className="nls-bowl-bottom">
              <line x1={scale.px(head.w)} x2={scale.px(bottom.w)} y1={scale.py(head.a)} y2={scale.py(bottom.a)} />
              <circle cx={scale.px(bottom.w)} cy={scale.py(bottom.a)} r={5} />
            </g>
          )}
          <g className="ex-minimum">
            <circle cx={scale.px(GLOBAL_MINIMUM.w)} cy={scale.py(GLOBAL_MINIMUM.a)} r={6} />
            <text x={scale.px(GLOBAL_MINIMUM.w) + 10} y={scale.py(GLOBAL_MINIMUM.a) - 10}>最良</text>
          </g>
          {descending && pathPoints.length > 1 && (
            <path className="ex-trail" d={polylinePath(pathPoints, scale)} />
          )}
          {descending && pathPoints.map(([w, a], index) => (
            <circle className="ex-surface-dot" cx={scale.px(w)} cy={scale.py(a)} key={index} r={3.5} />
          ))}
          {descending && inView(head) && <circle className="ex-head" cx={scale.px(head.w)} cy={scale.py(head.a)} r={7} />}
          <g {...handleProps}>
            <circle className="ex-handle-hit" cx={scale.px(start.w)} cy={scale.py(start.a)} r={24} />
            <circle className="ex-handle-ring" cx={scale.px(start.w)} cy={scale.py(start.a)} r={10} />
            <circle className="ex-observation" cx={scale.px(start.w)} cy={scale.py(start.a)} r={5} />
          </g>
        </svg>
      </div>
    </figure>
  );
}

const LandscapeContours = memo(function LandscapeContours({ scale }: { scale: Scale }) {
  const paths = useMemo(() => {
    const fn = (w: number, a: number) => sse({ a, w });
    return LEVELS.map((level) => segmentsPath(contourSegments(fn, PARAM_BOUNDS, level, 180, 120), scale));
  }, [scale]);
  return <g>{paths.map((d, index) => <path className="ex-contour" d={d} key={LEVELS[index]} />)}</g>;
});

/** The quadratic bowl Gauss–Newton builds at the current point, drawn as dashed rings. */
function BowlContours({ head, scale }: { head: Params; scale: Scale }) {
  const bottom = bowlBottom(head);
  if (!bottom) return null;
  const floor = linearizedSse(head, bottom);
  const fn = (w: number, a: number) => linearizedSse(head, { a, w });
  return (
    <g className="nls-bowl">
      {BOWL_OFFSETS.map((offset) => (
        <path d={segmentsPath(contourSegments(fn, PARAM_BOUNDS, floor + offset, 120, 90), scale)} key={offset} />
      ))}
    </g>
  );
}

function ParamAxes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  return (
    <g className="ex-axes">
      {[1, 2, 3, 4, 5].map((w) => (
        <g key={`w${w}`}>
          <line x1={scale.px(w)} x2={scale.px(w)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(w)} y={viewport.height - 6}>{w}</text>
        </g>
      ))}
      {[-2, 0, 2].map((a) => (
        <g key={`a${a}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(a)} y2={scale.py(a)} />
          <text x={6} y={scale.py(a) - 4}>{a}</text>
        </g>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={viewport.height - 22}>周波数 ω</text>
      <text className="ex-axis-name" x={30} y={16}>振幅 a</text>
    </g>
  );
}

function SurfacePanel({ camera, head, run }: { camera: Camera; head: Params; run: Descent }) {
  const { ref, viewport } = useStageViewport(PARAM_BOUNDS, 0.8);
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">パラメータの地形（立体）</figcaption>
      <div className="ex-canvas" ref={ref}>
        <Surface3D
          camera={camera}
          current={{ x: head.w, y: head.a }}
          height={viewport.height}
          axes={{ x: "ω", y: "a" }}
          marks={[{ x: GLOBAL_MINIMUM.w, y: GLOBAL_MINIMUM.a, label: "最良" }]}
          path={run.path.map((p) => ({ x: p.w, y: p.a }))}
          spec={SURFACE}
          width={viewport.width}
        />
      </div>
      <p className="ex-hint">床の二辺が周波数 ω と振幅 a、高さが二乗和です。高さは二乗和20で切っています。</p>
    </figure>
  );
}

interface ReadoutProps {
  run: Descent;
  start: Params;
  head: Params;
  last: Iterate;
  step: number;
  descending: boolean;
  finished: boolean;
}

function Readout({ run, start, head, last, step, descending, finished }: ReadoutProps) {
  if (!descending) {
    const bottom = bowlBottom(start);
    return (
      <>
        <p className="ex-verdict ex-tone-swing">
          始点の残差の二乗和は {fmt(sse(start), 3)} です。最良の当てはめ（ω={fmt(GLOBAL_MINIMUM.w)}、a={fmt(GLOBAL_MINIMUM.a)}）では {fmt(GLOBAL_MINIMUM.sse, 3)} です。
        </p>
        {bottom && (
          <p className="ex-hint">
            破線の輪は、この点で残差を直線で近似したときのお椀です。お椀の底（ω={fmt(bottom.w)}、a={fmt(bottom.a)}）では二乗和を {fmt(linearizedSse(start, bottom), 3)} と予測しますが、実際は {fmt(sse(bottom), 3)} です。
          </p>
        )}
      </>
    );
  }
  const rows = run.path.slice(0, step + 1);
  return (
    <>
      <section aria-label="反復の記録">
        <table className="ex-table">
          <thead>
            <tr>
              <th scope="col">k</th><th scope="col">ω</th><th scope="col">a</th>
              <th scope="col">二乗和</th><th scope="col">お椀の予測</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p, index) => (
              <tr className={index === step ? "ex-row-best" : undefined} key={index}>
                <th scope="row">{index}</th>
                <td>{fmt(p.w, 3)}</td>
                <td>{fmt(p.a, 3)}</td>
                <td>{fmt(p.sse, 3)}</td>
                <td>{p.predicted === undefined ? "—" : fmt(p.predicted, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className={`ex-verdict ${!finished ? "ex-tone-swing" : run.outcome === "global" ? "ex-tone-good" : "ex-tone-bad"}`}>
        {finished ? outcomeText(run, last) : `反復 ${step}：ω=${fmt(head.w)}、a=${fmt(head.a)}。`}
      </p>
    </>
  );
}
