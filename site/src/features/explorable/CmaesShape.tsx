import { memo, useCallback, useMemo, useState } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { contourSegments, type Bounds } from "./math/contours";
import { axisRatio, eigen2, runCmaes, valley, type Generation, type Mat, type Vec } from "./math/cmaes";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting, type BeatSettings } from "./scene";
import { makeScale, polylinePath, segmentsPath, useStageViewport, type Scale, type Viewport } from "./svg";
import { useSceneTour } from "./useSceneTour";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const ID = "cmaes-shape-learning";
const BOUNDS: Bounds = { xMin: -1.6, xMax: 4.4, yMin: -2, yMax: 3 };
const GENERATIONS = 70;
const START: Vec = [3, 1];
const UPDATES = ["cma", "iso"] as const;
const VALLEYS = ["narrow", "round"] as const;
type Update = (typeof UPDATES)[number];
type ValleyShape = (typeof VALLEYS)[number];
const RATIO: Record<ValleyShape, number> = { narrow: 10, round: 1 };
const LEVELS = [0.05, 0.3, 1, 3, 10, 30, 100, 300];

interface Settings {
  update: Update;
  valley: ValleyShape;
  seed: number;
}

const INITIAL: Settings = { update: "cma", valley: "narrow", seed: 1 };

function fromBeat(settings: BeatSettings, base: Settings): Settings {
  return {
    update: stringSetting(settings, "update", UPDATES, base.update),
    valley: stringSetting(settings, "valley", VALLEYS, base.valley),
    seed: numberSetting(settings, "seed", base.seed),
  };
}

export default function CmaesShape() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromBeat(settings, value)), []),
  );
  const shown = tour.beat ? fromBeat(tour.beat.settings, chosen) : chosen;
  const ratio = RATIO[shown.valley];
  const run = useMemo(
    () => runCmaes({ mean: START, sigma: 1, ratio, seed: shown.seed, adaptShape: shown.update === "cma", count: GENERATIONS + 1 }),
    [ratio, shown.seed, shown.update],
  );
  const timeline = useTimeline(GENERATIONS, 6);
  useReplayOnChange(timeline, `${shown.update}:${shown.valley}:${shown.seed}`);
  const beatStart = tour.beat ? numberSetting(tour.beat.settings, "from", 0) : 0;
  const beatEnd = tour.beat ? numberSetting(tour.beat.settings, "to", GENERATIONS) : GENERATIONS;
  const position = tour.beat
    ? beatStart + Math.min(1, tour.local / Math.max(tour.beat.durationS - 1.5, 1)) * (beatEnd - beatStart)
    : timeline.position;
  const g = Math.min(Math.floor(position + 1e-9), GENERATIONS);
  const current = run.generations[g];
  const next = run.generations[Math.min(g + 1, GENERATIONS)];
  const best = current.samples[0].f;
  const summary = `${shown.update === "cma" ? "CMA-ES" : "歩幅だけを調整する方法"}の${g}世代目。いちばん良い値は ${fmt(best, 3)}、楕円の縦横比は ${fmt(axisRatio(current.cov), 1)}（谷は ${ratio}）です。`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<Update>
            legend="分布の更新"
            onChange={(update) => setChosen((value) => ({ ...value, update }))}
            options={[
              { value: "cma", label: "形も学ぶ（CMA-ES）" },
              { value: "iso", label: "丸のまま、歩幅だけ調整" },
            ]}
            value={shown.update}
          />
          <Choice<ValleyShape>
            legend="谷の形"
            onChange={(valleyShape) => setChosen((value) => ({ ...value, valley: valleyShape }))}
            options={[
              { value: "narrow", label: "細く斜めの谷（10:1）" },
              { value: "round", label: "丸い谷" },
            ]}
            value={shown.valley}
          />
          <Slider
            display={String(shown.seed)}
            hint="乱数の種を変えると、同じ設定でも点の出方が変わります。"
            label="乱数の種"
            max={5}
            min={1}
            onChange={(seed) => setChosen((value) => ({ ...value, seed }))}
            step={1}
            value={shown.seed}
          />
        </>
      }
      id={ID}
      player={<PlayerBar positionText={`世代 ${g} / ${GENERATIONS}`} stepLabel="世代 g" timeline={timeline} />}
      readout={<Readout generation={current} next={next} ratio={ratio} weights={run.parameters.weights} />}
      stage={
        <div className="ex-twin">
          <ValleyPanel generation={current} next={next} path={run.generations.slice(0, g + 1).map((gen) => gen.mean)} ratio={ratio} />
          <ShapePanel generations={run.generations} index={g} ratio={ratio} />
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

/** SVG ellipse for σ²C scaled by `k` standard deviations, drawn with equal x and y scales. */
function covEllipse(center: Vec, sigma: number, cov: Mat, k: number, scale: Scale) {
  const { values, vectors: [axis] } = eigen2(cov);
  const unit = scale.px(1) - scale.px(0);
  const angle = (-Math.atan2(axis[1], axis[0]) * 180) / Math.PI;
  return {
    cx: scale.px(center[0]),
    cy: scale.py(center[1]),
    rx: k * sigma * Math.sqrt(values[0]) * unit,
    ry: k * sigma * Math.sqrt(Math.max(values[1], 0)) * unit,
    transform: `rotate(${angle.toFixed(2)} ${scale.px(center[0]).toFixed(1)} ${scale.py(center[1]).toFixed(1)})`,
  };
}

interface ValleyPanelProps {
  generation: Generation;
  next: Generation;
  path: Vec[];
  ratio: number;
}

function ValleyPanel({ generation, next, path, ratio }: ValleyPanelProps) {
  const { ref, viewport } = useStageViewport(BOUNDS, (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin));
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const { mean, sigma, cov, samples } = generation;
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">谷と分布</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <Axes scale={scale} viewport={viewport} />
          <ValleyContours ratio={ratio} scale={scale} />
          <path className="ex-trail" d={polylinePath(path, scale)} />
          <ellipse className="cma-ellipse-wide" {...covEllipse(mean, sigma, cov, 2, scale)} />
          <ellipse className="cma-ellipse" {...covEllipse(mean, sigma, cov, 1, scale)} />
          {samples.map((s, rank) => (
            <circle className={rank < 3 ? "cma-parent" : "cma-sample"} cx={scale.px(s.x[0])} cy={scale.py(s.x[1])} key={rank} r={rank < 3 ? 6 : 5} />
          ))}
          <line className="ex-next-step" markerEnd="url(#cma-arrow)" x1={scale.px(mean[0])} x2={scale.px(next.mean[0])} y1={scale.py(mean[1])} y2={scale.py(next.mean[1])} />
          <circle className="ex-head" cx={scale.px(mean[0])} cy={scale.py(mean[1])} r={6} />
          <g className="ex-minimum">
            <circle cx={scale.px(0)} cy={scale.py(0)} r={5} />
            <text x={scale.px(0) + 9} y={scale.py(0) + 20}>最小点</text>
          </g>
          <defs>
            <marker id="cma-arrow" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="6" refY="4">
              <path className="ex-arrowhead" d="M0 0L8 4L0 8z" />
            </marker>
          </defs>
        </svg>
      </div>
    </figure>
  );
}

const ValleyContours = memo(function ValleyContours({ ratio, scale }: { ratio: number; scale: Scale }) {
  const paths = useMemo(
    () => LEVELS.map((level) => segmentsPath(contourSegments((x, y) => valley([x, y], ratio), BOUNDS, level, 150, 125), scale)),
    [ratio, scale],
  );
  return <g>{paths.map((d, index) => <path className="ex-contour" d={d} key={LEVELS[index]} />)}</g>;
});

function Axes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  return (
    <g className="ex-axes">
      {[-1, 0, 1, 2, 3, 4].map((x) => (
        <g key={`x${x}`}>
          <line x1={scale.px(x)} x2={scale.px(x)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(x)} y={viewport.height - 6}>{x}</text>
        </g>
      ))}
      {[-1, 0, 1, 2].map((y) => (
        <g key={`y${y}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
          <text x={6} y={scale.py(y) - 4}>{y}</text>
        </g>
      ))}
    </g>
  );
}

interface ShapePanelProps {
  generations: Generation[];
  index: number;
  ratio: number;
}

function ShapePanel({ generations, index, ratio }: ShapePanelProps) {
  const { ref, viewport } = useStageViewport({ xMin: 0, xMax: 1, yMin: 0, yMax: 1 }, (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin));
  const width = viewport.width;
  const shapeHeight = Math.round(viewport.height * 0.42);
  const chartTop = shapeHeight + 8;
  const chartHeight = (viewport.height - chartTop - 22) / 2;
  const { cov } = generations[index];
  const { values, vectors: [axis] } = eigen2(cov);
  // Rotated by about 45°, the ellipse spans 0.71 × 2 × major vertically; keep it inside the band.
  const major = Math.min(width * 0.3, (shapeHeight - 40) / 1.42);
  const learned = Math.sqrt(values[1] / values[0]);
  const angle = (-Math.atan2(axis[1], axis[0]) * 180) / Math.PI;
  const cx = width * 0.5;
  const cy = 26 + (shapeHeight - 40) / 2;
  const left = 40;
  const gx = (g: number) => left + ((width - left - 10) * g) / GENERATIONS;
  const bestLog = generations.map((gen) => Math.log10(Math.max(gen.samples[0].f, 1e-14)));
  const fy = (value: number) => chartTop + 4 + ((3 - Math.min(3, Math.max(-14, value))) / 17) * (chartHeight - 8);
  const ratios = generations.map((gen) => axisRatio(gen.cov));
  const ratioTop = chartTop + chartHeight + 6;
  const ry = (value: number) => ratioTop + chartHeight - 4 - (Math.min(value, 12) / 12) * (chartHeight - 8);
  const line = (ys: number[]) => ys.slice(0, index + 1).map((y, g) => `${g === 0 ? "M" : "L"}${gx(g).toFixed(1)} ${y.toFixed(1)}`).join("");
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">分布の形と記録</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={width} />
          <text className="ex-axis-name" x={8} y={18}>楕円の形（大きさをそろえて表示）</text>
          <ellipse className="cma-target" cx={cx} cy={cy} rx={major} ry={major / ratio} transform={`rotate(-45 ${cx} ${cy})`} />
          <ellipse className="cma-ellipse" cx={cx} cy={cy} rx={major} ry={major * learned} transform={`rotate(${angle.toFixed(2)} ${cx} ${cy})`} />
          <text className="cma-shape-label" textAnchor="end" x={width - 8} y={shapeHeight - 4}>縦横比 {fmt(axisRatio(cov), 1)}（破線の谷は {ratio}）</text>
          <g className="ex-axes">
            <line x1={left} x2={width} y1={fy(0)} y2={fy(0)} />
            <line x1={left} x2={width} y1={fy(-12)} y2={fy(-12)} />
            <text textAnchor="end" x={left - 4} y={fy(0) + 4}>1</text>
            <text textAnchor="end" x={left - 4} y={fy(-12) + 4}>10⁻¹²</text>
            <line x1={left} x2={width} y1={ry(1)} y2={ry(1)} />
            <line x1={left} x2={width} y1={ry(10)} y2={ry(10)} />
            <text textAnchor="end" x={left - 4} y={ry(1) + 4}>1</text>
            <text textAnchor="end" x={left - 4} y={ry(10) + 4}>10</text>
            <text textAnchor="middle" x={gx(index)} y={viewport.height - 4}>g={index}</text>
          </g>
          <text className="cma-chart-label" textAnchor="end" x={width - 8} y={chartTop + 14}>いちばん良い値</text>
          <text className="cma-chart-label" textAnchor="end" x={width - 8} y={ratioTop + 14}>楕円の縦横比</text>
          <path className="cma-line-f" d={line(bestLog.map(fy))} />
          <path className="cma-line-ratio" d={line(ratios.map(ry))} />
          <line className="cma-now" x1={gx(index)} x2={gx(index)} y1={chartTop} y2={viewport.height - 18} />
        </svg>
      </div>
    </figure>
  );
}

interface ReadoutProps {
  generation: Generation;
  next: Generation;
  ratio: number;
  weights: number[];
}

function Readout({ generation, next, ratio, weights }: ReadoutProps) {
  const { values, vectors: [axis] } = eigen2(generation.cov);
  const angle = ((Math.atan2(axis[1], axis[0]) * 180) / Math.PI + 180) % 180;
  const learned = Math.sqrt(values[0] / values[1]);
  return (
    <>
      <section aria-label="この世代のサンプル">
        <table className="ex-table">
          <thead>
            <tr><th scope="col">順位</th><th scope="col">点 x</th><th scope="col">f(x)</th><th scope="col">重み</th></tr>
          </thead>
          <tbody>
            {generation.samples.map((s, rank) => (
              <tr className={rank < weights.length ? "ex-row-best" : undefined} key={rank}>
                <th scope="row">{rank + 1}</th>
                <td>({fmt(s.x[0], 3)}, {fmt(s.x[1], 3)})</td>
                <td>{fmt(s.f, 3)}</td>
                <td>{rank < weights.length ? fmt(weights[rank], 3) : "0"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className="ex-hint">
        次の平均は、上位3点の重み付き平均で ({fmt(next.mean[0], 3)}, {fmt(next.mean[1], 3)}) です。歩幅 σ は {fmt(generation.sigma, 3)} から {fmt(next.sigma, 3)} になります。
      </p>
      <p className={`ex-verdict ${learned > 0.7 * ratio && ratio > 1 ? "ex-tone-good" : "ex-tone-swing"}`}>
        楕円の縦横比は {fmt(learned, 1)}、長い軸の向きは {fmt(angle, 0)}° です。{ratio > 1 ? `谷は縦横比 ${ratio}、向き45°です。` : "谷は丸いので、形を学ぶ必要はほとんどありません。"}
      </p>
    </>
  );
}
