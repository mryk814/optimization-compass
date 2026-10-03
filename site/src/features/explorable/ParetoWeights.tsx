import { useCallback, useMemo, useRef, useState, type KeyboardEvent } from "react";

import { Choice, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import type { Bounds } from "./math/contours";
import {
  deflectionDrop,
  epsilonChoice,
  isParetoOptimal,
  objectives,
  weightedSum,
  weightedSumChoice,
  type Design,
  type FrontShape,
} from "./math/pareto2d";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting, type BeatSettings } from "./scene";
import { clamp, makeScale, polylinePath, useDomainDrag, useStageViewport, type Scale, type Viewport } from "./svg";
import { useSceneTour } from "./useSceneTour";

const ID = "multiobjective-pareto-weights";
const DESIGN_BOUNDS: Bounds = { xMin: -0.12, xMax: 1.3, yMin: -0.15, yMax: 1.12 };
const OBJECTIVE_BOUNDS: Bounds = { xMin: -0.12, xMax: 1.35, yMin: -0.2, yMax: 2.15 };
const MODES = ["manual", "weighted", "epsilon"] as const;
const SHAPES = ["concave", "convex"] as const;
type Mode = (typeof MODES)[number];

interface Settings {
  mode: Mode;
  shape: FrontShape;
  design: Design;
  w: number;
  epsilon: number;
}

const INITIAL: Settings = { mode: "manual", shape: "concave", design: [0.5, 0.5], w: 0.5, epsilon: 0.5 };

function fromBeat(settings: BeatSettings, base: Settings): Settings {
  return {
    mode: stringSetting(settings, "mode", MODES, base.mode),
    shape: stringSetting(settings, "shape", SHAPES, base.shape),
    design: [numberSetting(settings, "x1", base.design[0]), numberSetting(settings, "x2", base.design[1])],
    w: numberSetting(settings, "w", base.w),
    epsilon: numberSetting(settings, "epsilon", base.epsilon),
  };
}

export default function ParetoWeights() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromBeat(settings, value)), []),
  );
  const base = tour.beat ? fromBeat(tour.beat.settings, chosen) : chosen;
  // A beat may sweep the weight or the cap from `from` to `to` over its duration.
  const sweep = (key: "w" | "epsilon") => {
    if (!tour.beat) return base[key];
    const from = numberSetting(tour.beat.settings, `${key}From`, base[key]);
    const to = numberSetting(tour.beat.settings, `${key}To`, from);
    return from + Math.min(1, tour.local / Math.max(tour.beat.durationS - 1.5, 1)) * (to - from);
  };
  const shown: Settings = { ...base, w: sweep("w"), epsilon: sweep("epsilon") };
  const choice: Design = shown.mode === "weighted"
    ? weightedSumChoice(shown.w, shown.shape)
    : shown.mode === "epsilon" ? epsilonChoice(shown.epsilon) : shown.design;
  const point = objectives(choice, shown.shape);
  const setDesign = (design: Design) => setChosen((value) => ({
    ...value,
    mode: "manual",
    design: [clamp(Math.round(design[0] * 100) / 100, 0, 1), clamp(Math.round(design[1] * 100) / 100, 0, 1)],
  }));
  const summary = `${shown.mode === "weighted" ? `重み w=${fmt(shown.w)} の重み付き和で選んだ` : shown.mode === "epsilon" ? `重さの上限 ε=${fmt(shown.epsilon)} で選んだ` : "選んだ"}設計は厚み ${fmt(choice[0])}、飾り ${fmt(choice[1])}。重さ ${fmt(point[0])}、たわみ ${fmt(point[1])} で、${isParetoOptimal(choice) ? "どちらかを良くするともう一方が悪くなる点です。" : "飾りを外せばたわみだけが小さくなる、改善できる点です。"}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<Mode>
            legend="選び方"
            onChange={(mode) => setChosen((value) => ({ ...value, mode }))}
            options={[
              { value: "manual", label: "自分で選ぶ" },
              { value: "weighted", label: "重み付き和" },
              { value: "epsilon", label: "重さの上限（ε制約）" },
            ]}
            value={shown.mode}
          />
          {shown.mode === "manual" && (
            <>
              <Slider display={fmt(shown.design[0])} label="厚み x₁" max={1} min={0} onChange={(x1) => setDesign([x1, shown.design[1]])} step={0.01} value={shown.design[0]} />
              <Slider display={fmt(shown.design[1])} label="飾り x₂" max={1} min={0} onChange={(x2) => setDesign([shown.design[0], x2])} step={0.01} value={shown.design[1]} />
            </>
          )}
          {shown.mode === "weighted" && (
            <Slider
              display={fmt(shown.w)}
              hint="重さに w、たわみに 1−w を掛けて足した値を最小にします。"
              label="重さの重み w"
              max={0.95}
              min={0.05}
              onChange={(w) => setChosen((value) => ({ ...value, w }))}
              step={0.01}
              value={shown.w}
            />
          )}
          {shown.mode === "epsilon" && (
            <Slider
              display={fmt(shown.epsilon)}
              hint="重さを ε 以下に抑えたうえで、たわみを最小にします。"
              label="重さの上限 ε"
              max={1}
              min={0}
              onChange={(epsilon) => setChosen((value) => ({ ...value, epsilon }))}
              step={0.01}
              value={shown.epsilon}
            />
          )}
          <Choice<FrontShape>
            legend="たわみの減り方"
            onChange={(shape) => setChosen((value) => ({ ...value, shape }))}
            options={[
              { value: "concave", label: "厚くするほど急に減る" },
              { value: "convex", label: "薄いうちに急に減る" },
            ]}
            value={shown.shape}
          />
        </>
      }
      id={ID}
      readout={<Readout choice={choice} mode={shown.mode} point={point} shape={shown.shape} w={shown.w} />}
      stage={
        <div className="ex-twin">
          <DesignPanel choice={choice} fixed={tour.active || shown.mode !== "manual"} onMove={setDesign} />
          <ObjectivePanel choice={choice} epsilon={shown.epsilon} mode={shown.mode} shape={shown.shape} w={shown.w} />
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

function DesignPanel({ choice, fixed, onMove }: { choice: Design; fixed: boolean; onMove(design: Design): void }) {
  const { ref, viewport } = useStageViewport(DESIGN_BOUNDS, 1);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const svgRef = useRef<SVGSVGElement>(null);
  const drag = useDomainDrag({ svgRef, viewport, onDrag: (x1, x2) => onMove([x1, x2]) });
  const onKeyDown = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 0.1 : 0.01;
    const moves: Record<string, Design> = {
      ArrowLeft: [-amount, 0], ArrowRight: [amount, 0], ArrowUp: [0, amount], ArrowDown: [0, -amount],
    };
    const delta = moves[event.key];
    if (!delta) return;
    event.preventDefault();
    onMove([choice[0] + delta[0], choice[1] + delta[1]]);
  };
  const handleProps = fixed
    ? { className: "ex-handle is-fixed" }
    : {
        "aria-label": `設計（厚み ${fmt(choice[0])}、飾り ${fmt(choice[1])}）。ドラッグか矢印キーで動かせます。`,
        "aria-roledescription": "2次元のつまみ",
        className: "ex-handle",
        onKeyDown,
        role: "group",
        tabIndex: 0,
        ...drag,
      };
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">設計の空間 ↔↕ 動かせます</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <Axes names={["厚み x₁", "飾り x₂"]} scale={scale} ticksX={[0, 0.5, 1]} ticksY={[0, 0.5, 1]} viewport={viewport} />
          <rect className="mo-feasible" height={scale.py(0) - scale.py(1)} width={scale.px(1) - scale.px(0)} x={scale.px(0)} y={scale.py(1)} />
          <line className="mo-pareto" x1={scale.px(0)} x2={scale.px(1)} y1={scale.py(0)} y2={scale.py(0)} />
          <text className="mo-label" x={scale.px(0.02)} y={scale.py(0) - 8}>飾りなし＝パレート最適</text>
          <g {...handleProps}>
            <circle className="ex-handle-hit" cx={scale.px(choice[0])} cy={scale.py(choice[1])} r={24} />
            <circle className="ex-handle-ring" cx={scale.px(choice[0])} cy={scale.py(choice[1])} r={11} />
            <circle className="ex-head" cx={scale.px(choice[0])} cy={scale.py(choice[1])} r={6} />
          </g>
        </svg>
      </div>
    </figure>
  );
}

interface ObjectivePanelProps {
  choice: Design;
  shape: FrontShape;
  mode: Mode;
  w: number;
  epsilon: number;
}

function ObjectivePanel({ choice, shape, mode, w, epsilon }: ObjectivePanelProps) {
  const { ref, viewport } = useStageViewport(OBJECTIVE_BOUNDS, 1);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const [f1, f2] = objectives(choice, shape);
  const front: Array<readonly [number, number]> = [];
  const top: Array<readonly [number, number]> = [];
  for (let i = 0; i <= 100; i += 1) {
    const x1 = i / 100;
    front.push([x1, deflectionDrop(x1, shape)]);
    top.push([x1, deflectionDrop(x1, shape) + 1]);
  }
  const region = `${polylinePath(front, scale)}${polylinePath([...top].reverse(), scale).replace(/^M/, "L")}Z`;
  const improving = !isParetoOptimal(choice) ? objectives([choice[0], 0], shape) : undefined;
  // Weighted sum: the line w f1 + (1 − w) f2 = c through the chosen point.
  const level = weightedSum([f1, f2], w);
  const lineAt = (x: number) => (level - w * x) / (1 - w);
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">目的の空間（重さとたわみ）</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <clipPath id="mo-plot"><rect height={viewport.height} width={viewport.width} /></clipPath>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <Axes names={["重さ f₁", "たわみ f₂"]} scale={scale} ticksX={[0, 0.5, 1]} ticksY={[0, 1, 2]} viewport={viewport} />
          <path className="mo-feasible" d={region} />
          <rect className="mo-better" height={Math.max(0, scale.py(OBJECTIVE_BOUNDS.yMin) - scale.py(f2))} width={Math.max(0, scale.px(f1) - scale.px(OBJECTIVE_BOUNDS.xMin))} x={scale.px(OBJECTIVE_BOUNDS.xMin)} y={scale.py(f2)} />
          <path className="mo-front" d={polylinePath(front, scale)} />
          <g clipPath="url(#mo-plot)">
            {mode === "weighted" && (
              <line className="mo-level" x1={scale.px(-0.2)} x2={scale.px(1.3)} y1={scale.py(lineAt(-0.2))} y2={scale.py(lineAt(1.3))} />
            )}
            {mode === "epsilon" && (
              <line className="mo-level" x1={scale.px(epsilon)} x2={scale.px(epsilon)} y1={0} y2={viewport.height} />
            )}
          </g>
          {improving && (
            <g className="mo-improve">
              <line markerEnd="url(#mo-arrow)" x1={scale.px(f1)} x2={scale.px(improving[0])} y1={scale.py(f2)} y2={scale.py(improving[1]) - 8} />
            </g>
          )}
          <circle className="ex-head" cx={scale.px(f1)} cy={scale.py(f2)} r={7} />
          <text className="mo-label" x={scale.px(0.04)} y={scale.py(1.75)}>前線より上はすべて作れる</text>
          <defs>
            <marker id="mo-arrow" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="6" refY="4">
              <path className="ex-arrowhead" d="M0 0L8 4L0 8z" />
            </marker>
          </defs>
        </svg>
      </div>
    </figure>
  );
}

interface AxesProps {
  scale: Scale;
  viewport: Viewport;
  ticksX: number[];
  ticksY: number[];
  names: readonly [string, string];
}

function Axes({ scale, viewport, ticksX, ticksY, names }: AxesProps) {
  return (
    <g className="ex-axes">
      {ticksX.map((x) => (
        <g key={`x${x}`}>
          <line x1={scale.px(x)} x2={scale.px(x)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(x)} y={viewport.height - 6}>{x}</text>
        </g>
      ))}
      {ticksY.map((y) => (
        <g key={`y${y}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
          <text x={6} y={scale.py(y) - 4}>{y}</text>
        </g>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={viewport.height - 22}>{names[0]}</text>
      <text className="ex-axis-name" x={30} y={16}>{names[1]}</text>
    </g>
  );
}

interface ReadoutProps {
  choice: Design;
  point: readonly [number, number];
  mode: Mode;
  shape: FrontShape;
  w: number;
}

function Readout({ choice, point, mode, shape, w }: ReadoutProps) {
  const pareto = isParetoOptimal(choice);
  const atEnd = choice[0] === 0 || choice[0] === 1;
  const message = mode === "weighted" && shape === "concave"
    ? `重み w=${fmt(w)} では、${atEnd ? (choice[0] === 1 ? "いちばん厚い端（重さ1、たわみ0）" : "いちばん薄い端（重さ0、たわみ1）") : "前線の途中"}が選ばれます。前線が凹んでいるので、どの重みでも途中の点は選ばれず、w=0.5 を境に端から端へ飛びます。`
    : mode === "weighted"
      ? `重み w=${fmt(w)} では、前線の途中の点（重さ ${fmt(point[0])}、たわみ ${fmt(point[1])}）が選ばれます。前線が凸なので、重みを変えると選ばれる点が前線に沿って動きます。`
      : mode === "epsilon"
        ? `重さを ${fmt(point[0])} 以下に抑えた中で、たわみが最も小さい点です。上限を動かせば、前線のどの点も選べます。`
        : pareto
          ? "飾りがない設計なので、厚みを変えると重さとたわみのどちらかが悪くなります。この点はパレート最適です。"
          : `飾りを外すと、重さはそのままでたわみが ${fmt(point[1])} から ${fmt(point[1] - choice[1])} に下がります。この点は改善できる（支配される）点です。`;
  return (
    <>
      <section aria-label="選んだ設計">
        <table className="ex-table">
          <thead>
            <tr><th scope="col">厚み x₁</th><th scope="col">飾り x₂</th><th scope="col">重さ f₁</th><th scope="col">たわみ f₂</th></tr>
          </thead>
          <tbody>
            <tr className="ex-row-best">
              <td>{fmt(choice[0])}</td><td>{fmt(choice[1])}</td><td>{fmt(point[0])}</td><td>{fmt(point[1])}</td>
            </tr>
          </tbody>
        </table>
      </section>
      <p className={`ex-verdict ${pareto ? (mode === "weighted" && shape === "concave" ? "ex-tone-swing" : "ex-tone-good") : "ex-tone-bad"}`}>{message}</p>
    </>
  );
}
