import { memo, useCallback, useMemo, useState } from "react";

import { PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import {
  barrier,
  centralPath,
  f,
  F_STAR,
  LAMBDA_STAR,
  MU_STEPS,
  muAt,
  slack,
  SOLUTION,
  type Center,
} from "./math/barrier2d";
import { contourSegments, type Bounds } from "./math/contours";
import type { Camera, SurfaceSpec } from "./math/surface3d";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, type BeatSettings } from "./scene";
import { makeScale, polylinePath, segmentsPath, useStageViewport, type Scale, type Viewport } from "./svg";
import { Surface3D } from "./Surface3D";
import { useSceneTour } from "./useSceneTour";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const ID = "interior-point-barrier-path";
const PLANE: Bounds = { xMin: -1.25, xMax: 2.35, yMin: -1.25, yMax: 1.55 };
const DISK: Bounds = { xMin: -1, xMax: 1, yMin: -1, yMax: 1 };
const F_LEVELS = [2.2, 3, 5, 8, 12, 17, 23];
const BARRIER_OFFSETS = [0.15, 0.6, 1.5];
const OUTSIDE = 1e3;
const ELEVATION = 58;

interface Settings {
  azimuth: number;
}

const INITIAL: Settings = { azimuth: 220 };

/** Barrier objective for drawing: very high outside the disk, where it is undefined. */
const barrierOrWall = (mu: number) => (x: number, y: number) => {
  const value = barrier([x, y], mu);
  return Number.isFinite(value) ? value : OUTSIDE;
};

export default function BarrierPath() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => ({ azimuth: numberSetting(settings, "azimuth", value.azimuth) })), []),
  );
  const azimuth = tour.beat ? numberSetting(tour.beat.settings, "azimuth", chosen.azimuth) : chosen.azimuth;
  const centers = useMemo(() => centralPath(Array.from({ length: MU_STEPS + 1 }, (_, index) => muAt(index))), []);
  const timeline = useTimeline(MU_STEPS, 5);
  useReplayOnChange(timeline, "barrier");
  const from = tour.beat ? numberSetting(tour.beat.settings, "from", 0) : 0;
  const to = tour.beat ? numberSetting(tour.beat.settings, "to", MU_STEPS) : MU_STEPS;
  const position = tour.beat
    ? from + Math.min(1, tour.local / Math.max(tour.beat.durationS - 1.5, 1)) * (to - from)
    : timeline.position;
  const index = Math.min(Math.round(position), MU_STEPS);
  const center = centers[index];
  const mu = center.mu;
  const s = slack(center.p);
  const camera: Camera = useMemo(() => ({ azimuthDeg: azimuth, elevationDeg: ELEVATION }), [azimuth]);
  const summary = `μ=${fmt(mu, 4)} の障壁つきの最小点は (${fmt(center.p[0], 3)}, ${fmt(center.p[1], 3)})、縁までの余裕 s=${fmt(s, 4)}、f の真の最小値との差は ${fmt(f(center.p) - F_STAR, 4)} です。`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={`μ = ${fmt(mu, mu < 0.01 ? 4 : 2)}`}
            label="障壁の強さ μ"
            max={MU_STEPS}
            min={0}
            onChange={(value) => timeline.seek(value)}
            step={1}
            value={index}
            valueText={`μ は ${fmt(mu, 4)}`}
          />
          <Slider
            display={`${azimuth}°`}
            label="立体を回す"
            max={360}
            min={0}
            onChange={(value) => setChosen({ azimuth: value })}
            step={5}
            value={azimuth}
          />
        </>
      }
      id={ID}
      player={<PlayerBar positionText={`μ = ${fmt(mu, mu < 0.01 ? 4 : 2)}`} stepLabel="μ を小さくする" timeline={timeline} />}
      readout={<Readout center={center} centers={centers} />}
      stage={
        <div className="ex-twin">
          <PlanePanel center={center} centers={centers} index={index} />
          <SurfacePanel camera={camera} center={center} mu={mu} />
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

function PlanePanel({ center, centers, index }: { center: Center; centers: Center[]; index: number }) {
  const { ref, viewport } = useStageViewport(PLANE, (PLANE.yMax - PLANE.yMin) / (PLANE.xMax - PLANE.xMin));
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const radius = scale.px(1) - scale.px(0);
  const path = centers.map((c) => c.p);
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">制約の円と中心パス</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <PlaneAxes scale={scale} viewport={viewport} />
          <circle className="ipm-feasible" cx={scale.px(0)} cy={scale.py(0)} r={radius} />
          <ObjectiveContours scale={scale} />
          <BarrierContours center={center} scale={scale} />
          <path className="ipm-path" d={polylinePath(path, scale)} />
          <path className="ex-trail" d={polylinePath(path.slice(0, index + 1), scale)} />
          <g className="ex-minimum">
            <circle cx={scale.px(SOLUTION[0])} cy={scale.py(SOLUTION[1])} r={5} />
            <text x={scale.px(SOLUTION[0]) + 8} y={scale.py(SOLUTION[1]) - 10}>答え</text>
          </g>
          <g className="ipm-free">
            <circle cx={scale.px(2)} cy={scale.py(1)} r={5} />
            <text textAnchor="end" x={scale.px(2) - 8} y={scale.py(1) - 10}>制約がなければ</text>
          </g>
          <circle className="ex-head" cx={scale.px(center.p[0])} cy={scale.py(center.p[1])} r={7} />
        </svg>
      </div>
    </figure>
  );
}

const ObjectiveContours = memo(function ObjectiveContours({ scale }: { scale: Scale }) {
  const paths = useMemo(
    () => F_LEVELS.map((level) => segmentsPath(contourSegments((x, y) => f([x, y]), PLANE, level, 150, 120), scale)),
    [scale],
  );
  return <g>{paths.map((d, index) => <path className="ex-contour" d={d} key={F_LEVELS[index]} />)}</g>;
});

/** Level sets of φ_μ just above its minimum: the barrier's own bowl inside the disk. */
function BarrierContours({ center, scale }: { center: Center; scale: Scale }) {
  const { mu, p } = center;
  const paths = useMemo(() => {
    const fn = barrierOrWall(mu);
    const centerValue = barrier(p, mu);
    return BARRIER_OFFSETS.map((offset) => segmentsPath(contourSegments(fn, DISK, centerValue + offset, 110, 110), scale));
  }, [mu, p, scale]);
  return <g className="ipm-barrier-contour">{paths.map((d, index) => <path d={d} key={BARRIER_OFFSETS[index]} />)}</g>;
}

function PlaneAxes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  return (
    <g className="ex-axes">
      {[-1, 0, 1, 2].map((x) => (
        <g key={`x${x}`}>
          <line x1={scale.px(x)} x2={scale.px(x)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(x)} y={viewport.height - 6}>{x}</text>
        </g>
      ))}
      {[-1, 0, 1].map((y) => (
        <g key={`y${y}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
          <text x={6} y={scale.py(y) - 4}>{y}</text>
        </g>
      ))}
    </g>
  );
}

function SurfacePanel({ camera, center, mu }: { camera: Camera; center: Center; mu: number }) {
  const { ref, viewport } = useStageViewport(PLANE, (PLANE.yMax - PLANE.yMin) / (PLANE.xMax - PLANE.xMin));
  const spec: SurfaceSpec = useMemo(
    () => ({
      bounds: DISK,
      fn: barrierOrWall(mu),
      zFloor: 1.5,
      zCeil: 14,
      resolution: 56,
      heightMode: "linear",
      domain: (x: number, y: number) => x * x + y * y < 1,
    }),
    [mu],
  );
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">障壁つきの地形（立体）</figcaption>
      <div className="ex-canvas" ref={ref}>
        <Surface3D
          axes={{ x: "x", y: "y" }}
          camera={camera}
          current={{ x: center.p[0], y: center.p[1] }}
          height={viewport.height}
          marks={[{ x: SOLUTION[0], y: SOLUTION[1], label: "答え" }]}
          spec={spec}
          width={viewport.width}
        />
      </div>
      <p className="ex-hint">円の内側だけを描いています。縁では値が無限に高くなるので、高さは14で切っています。</p>
    </figure>
  );
}

function Readout({ center, centers }: { center: Center; centers: Center[] }) {
  const s = slack(center.p);
  const lambda = center.mu / s;
  const decades = [0, 10, 20, 30, 40, 50].map((index) => centers[index]);
  return (
    <>
      <section aria-label="μごとの記録">
        <table className="ex-table">
          <thead>
            <tr>
              <th scope="col">μ</th><th scope="col">点</th><th scope="col">余裕 s</th>
              <th scope="col">λ=μ/s</th><th scope="col">f − f*</th>
            </tr>
          </thead>
          <tbody>
            {decades.map((c) => (
              <tr className={c === center ? "ex-row-best" : undefined} key={c.mu}>
                <th scope="row">{fmt(c.mu, c.mu < 0.01 ? 4 : 2)}</th>
                <td>({fmt(c.p[0], 3)}, {fmt(c.p[1], 3)})</td>
                <td>{fmt(slack(c.p), 4)}</td>
                <td>{fmt(c.mu / slack(c.p), 3)}</td>
                <td>{fmt(f(c.p) - F_STAR, 4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="ex-verdict ex-tone-good">
        μ={fmt(center.mu, center.mu < 0.01 ? 4 : 2)} では、縁までの余裕 s={fmt(s, 4)} と乗数の推定 λ={fmt(lambda, 3)} の積がちょうど μ です。f の差 {fmt(f(center.p) - F_STAR, 4)} もほぼ μ で、λ は最適な乗数 {fmt(LAMBDA_STAR, 3)} に近づいていきます。
      </p>
    </>
  );
}
