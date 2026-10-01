import { useMemo, useRef, useState, type KeyboardEvent } from "react";

import { PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import type { Bounds } from "./math/contours";
import {
  ARTICLE_LP,
  feasibleVertices,
  greedyVertexWalk,
  levelLine,
  objectiveValue,
  optimalVertices,
  pathPoint,
  pullIntoPolygon,
  type Vec2,
} from "./math/lp2d";
import { LiveMath, mi, mn, mo, paren, row, signed } from "./mathml";
import { makeScale, polylinePath, useDomainDrag, useStageViewport } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const BOUNDS: Bounds = { xMin: -1.3, xMax: 6.26, yMin: -0.9, yMax: 4.6 };
const ASPECT = (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin);
/** On a phone the plot crops the empty right side so the polygon and its labels stay large. */
const COMPACT_BOUNDS: Bounds = { xMin: -1.0, xMax: 5.0, yMin: -0.9, yMax: 4.6 };
const COMPACT = {
  below: 520,
  bounds: COMPACT_BOUNDS,
  aspect: (COMPACT_BOUNDS.yMax - COMPACT_BOUNDS.yMin) / (COMPACT_BOUNDS.xMax - COMPACT_BOUNDS.xMin),
};
const VERTICES = feasibleVertices(ARTICLE_LP);
const START = VERTICES.findIndex((vertex) => vertex[0] === 0 && vertex[1] === 0);
const CENTROID: Vec2 = [
  VERTICES.reduce((sum, vertex) => sum + vertex[0], 0) / VERTICES.length,
  VERTICES.reduce((sum, vertex) => sum + vertex[1], 0) / VERTICES.length,
];
const DEFAULT_PROBE: Vec2 = [1.4, 1.1];


export default function LpVertexWalk() {
  const [c1, setC1] = useState(3);
  const [c2, setC2] = useState(2);
  const [probe, setProbe] = useState<Vec2>(DEFAULT_PROBE);
  const svgRef = useRef<SVGSVGElement>(null);
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT, COMPACT);
  const cost: Vec2 = [c1, c2];

  const path = useMemo(() => greedyVertexWalk(VERTICES, [c1, c2], START), [c1, c2]);
  const best = useMemo(() => optimalVertices(VERTICES, [c1, c2]), [c1, c2]);
  const bestValue = objectiveValue(cost, VERTICES[best[0]]);
  const timeline = useTimeline(path.length - 1, 1.2);

  useReplayOnChange(timeline, `${c1}|${c2}`);

  const scale = useMemo(() => makeScale(viewport), [viewport]);
  // The cost arrow sits in the empty upper-right of the plot, in pixels.
  const arrowOrigin: readonly [number, number] = [viewport.width - 64, Math.round(viewport.height * 0.2)];
  const drag = useDomainDrag({
    svgRef,
    viewport,
    onDrag: (x, y) => setProbe(pullIntoPolygon(ARTICLE_LP, CENTROID, [x, y])),
  });
  const nudgeProbe = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 0.5 : 0.1;
    const delta: Record<string, Vec2> = {
      ArrowLeft: [-amount, 0],
      ArrowRight: [amount, 0],
      ArrowUp: [0, amount],
      ArrowDown: [0, -amount],
    };
    const move = delta[event.key];
    if (!move) return;
    event.preventDefault();
    setProbe((point) => pullIntoPolygon(ARTICLE_LP, CENTROID, [point[0] + move[0], point[1] + move[1]]));
  };

  const walker = pathPoint(VERTICES, path, timeline.position);
  const walkerValue = objectiveValue(cost, walker);
  const probeValue = objectiveValue(cost, probe);
  const isZero = c1 === 0 && c2 === 0;
  const isEdge = best.length > 1 && !isZero;
  const polygon = polylinePath(VERTICES, scale) + "Z";
  const values = VERTICES.map((vertex) => objectiveValue(cost, vertex));
  const low = Math.min(...values);
  const high = Math.max(...values);
  const faintLevels = isZero
    ? []
    : Array.from({ length: 9 }, (_, index) => low - (high - low) * 0.5 + ((high - low) * 2 * index) / 8);
  const norm = Math.hypot(c1, c2);

  const verdictText = isZero
    ? "c=(0, 0) では、どの実行可能な点でも目的値が0で、動く理由がありません。"
    : isEdge
      ? `目的の向きが辺と直角なので、頂点 ${best.map((index) => fmtPair(VERTICES[index][0], VERTICES[index][1], 1)).join(" と ")} を結ぶ辺全体が最適です（z=${fmt(bestValue)}）。`
      : `最適解は頂点 ${fmtPair(VERTICES[best[0]][0], VERTICES[best[0]][1], 1)}、目的値は z=${fmt(bestValue)} です。原点から隣の頂点へ${path.length - 1}回移って到達します。`;
  const summary = `目的の係数は c=(${c1}, ${c2})。${verdictText}実行可能領域の内部の点は、最良の頂点より良くなりません。`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(c1, 1)}
            hint="x を増やすと目的値がどれだけ増えるか（最大化）。"
            label="係数 c₁（x の重み）"
            max={4}
            min={-4}
            onChange={setC1}
            step={0.5}
            value={c1}
          />
          <Slider
            display={fmt(c2, 1)}
            hint="y を増やすと目的値がどれだけ増えるか。"
            label="係数 c₂（y の重み）"
            max={4}
            min={-4}
            onChange={setC2}
            step={0.5}
            value={c2}
          />
        </>
      }
      id="lp-vertex-walk"
      player={
        <PlayerBar
          positionText={`${Math.min(timeline.step, path.length - 1)} / ${path.length - 1} 回移動`}
          stepLabel="頂点の移動"
          timeline={timeline}
        />
      }
      readout={
        <>
          <section aria-label="いまの位置での目的値" className="ex-equation">
            <p className="ex-eyebrow">目的値 z = c₁x + c₂y を、いまの位置（橙）と動かせる点（紺）で計算</p>
            <LiveMath
              block
              label={`橙の点 ${fmtPair(walker[0], walker[1])} での目的値は ${fmt(walkerValue)}`}
              markup={objectiveEquation(walker, c1, c2, walkerValue)}
            />
            <LiveMath
              block
              label={`紺の点 ${fmtPair(probe[0], probe[1])} での目的値は ${fmt(probeValue)}。最良の頂点の値は ${fmt(bestValue)}`}
              markup={objectiveEquation(probe, c1, c2, probeValue)}
            />
          </section>
          <section aria-label="頂点ごとの目的値">
            <p className="ex-eyebrow">頂点だけを比べれば十分です</p>
            <table className="ex-table">
              <thead>
                <tr><th scope="col">頂点</th><th scope="col">座標</th><th scope="col">目的値 z</th><th scope="col" /></tr>
              </thead>
              <tbody>
                {VERTICES.map((vertex, index) => (
                  <tr className={best.includes(index) && !isZero ? "ex-row-best" : undefined} key={index}>
                    <th scope="row">{String.fromCharCode(65 + index)}</th>
                    <td>{fmtPair(vertex[0], vertex[1], 1)}</td>
                    <td>{fmt(values[index])}</td>
                    <td>{best.includes(index) && !isZero ? "最良" : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="ex-hint">
              紺の点をどこへ動かしても、その目的値は最良の頂点 {fmt(bestValue)} を超えません。内部の点を動かすと目的値は一定の割合で変わるだけなので、改善の余地は境界の先にしかありません。
            </p>
          </section>
          <p className={`ex-verdict ${isZero ? "ex-tone-slow" : "ex-tone-good"}`}>{verdictText}</p>
        </>
      }
      stage={
        <div className="ex-canvas" ref={stageRef}>
        <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            <line x1={scale.px(0)} x2={scale.px(0)} y1={0} y2={viewport.height} />
            <line x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
            <text textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 6}>x</text>
            <text x={scale.px(0) + 6} y={16}>y</text>
          </g>
          {faintLevels.map((value) => {
            const line = levelLine(cost, value, viewport.bounds);
            return line && (
              <line
                className="ex-level"
                key={value}
                x1={scale.px(line[0][0])}
                x2={scale.px(line[1][0])}
                y1={scale.py(line[0][1])}
                y2={scale.py(line[1][1])}
              />
            );
          })}
          <path className="ex-feasible" d={polygon} />
          {ARTICLE_LP.map((constraint) => (
            <ConstraintLine bounds={viewport.bounds} constraint={constraint} key={constraint.label} scale={scale} />
          ))}
          <path className="ex-walk" d={polylinePath(path.map((index) => VERTICES[index]), scale)} />
          {!isZero && (
            <LevelThrough bounds={viewport.bounds} cost={cost} point={walker} scale={scale} />
          )}
          {VERTICES.map((vertex, index) => (
            <g key={index}>
              <circle
                className={best.includes(index) && !isZero ? "ex-vertex ex-vertex-best" : "ex-vertex"}
                cx={scale.px(vertex[0])}
                cy={scale.py(vertex[1])}
                r={best.includes(index) && !isZero ? 9 : 6}
              />
              <text
                className="ex-label"
                x={scale.px(vertex[0]) + (vertex[0] > 2 ? 12 : -12)}
                y={scale.py(vertex[1]) + (vertex[1] > 2 ? -10 : 20)}
                textAnchor={vertex[0] > 2 ? "start" : "end"}
              >
                {String.fromCharCode(65 + index)} z={fmt(values[index], 1)}
              </text>
            </g>
          ))}
          {!isZero && (
            <g>
              <line
                className="ex-cost-arrow"
                markerEnd="url(#ex-cost-head)"
                x1={arrowOrigin[0]}
                x2={arrowOrigin[0] + (c1 / norm) * 58}
                y1={arrowOrigin[1]}
                y2={arrowOrigin[1] - (c2 / norm) * 58}
              />
              <text className="ex-label" textAnchor="middle" x={arrowOrigin[0]} y={arrowOrigin[1] + 24}>
                改善する向き c
              </text>
              <defs>
                <marker id="ex-cost-head" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="6" refY="4">
                  <path className="ex-arrowhead" d="M0 0L8 4L0 8z" />
                </marker>
              </defs>
            </g>
          )}
          <circle className="ex-head" cx={scale.px(walker[0])} cy={scale.py(walker[1])} r={8} />
          <g
            aria-label={`動かせる点 ${fmtPair(probe[0], probe[1])}。ドラッグか矢印キーで実行可能領域の中を動かせます。`}
            aria-roledescription="2次元のつまみ"
            className="ex-handle"
            onKeyDown={nudgeProbe}
            role="group"
            tabIndex={0}
            {...drag}
          >
            <circle className="ex-handle-hit" cx={scale.px(probe[0])} cy={scale.py(probe[1])} r={20} />
            <rect
              className="ex-probe"
              height={14}
              transform={`rotate(45 ${scale.px(probe[0])} ${scale.py(probe[1])})`}
              width={14}
              x={scale.px(probe[0]) - 7}
              y={scale.py(probe[1]) - 7}
            />
            <text className="ex-label" x={scale.px(probe[0]) + 14} y={scale.py(probe[1]) - 12}>
              z={fmt(probeValue, 1)}
            </text>
          </g>
        </svg>
        </div>
      }
      summary={summary}
    />
  );
}

function objectiveEquation(point: Vec2, c1: number, c2: number, value: number): string {
  // Negative numbers are parenthesised so "3·(−1.20)" cannot be misread as a subtraction.
  const operand = (text: string) => (text.startsWith("−") ? paren(signed(text)) : mn(text));
  const term = (weight: number, coordinate: number) => row(
    operand(fmt(weight, 1)), mo("·"), operand(fmt(coordinate)),
  );
  return row(
    mi("z"), mo("="), term(c1, point[0]), mo("+"), term(c2, point[1]), mo("="), signed(fmt(value)),
  );
}

type Constraint = (typeof ARTICLE_LP)[number];

function ConstraintLine({
  constraint, scale, bounds,
}: { constraint: Constraint; scale: ReturnType<typeof makeScale>; bounds: Bounds }) {
  const line = levelLine(constraint.a, constraint.b, bounds);
  if (!line) return null;
  const [from, to] = line;
  // Label near the lower (or, for a horizontal line, right-hand) end so neighbouring lines
  // are far apart there, then nudge it toward the infeasible side, off the polygon.
  const end = from[1] < to[1] - 1e-9 || (Math.abs(from[1] - to[1]) <= 1e-9 && from[0] > to[0])
    ? from
    : to;
  const other = end === from ? to : from;
  const along = 0.95;
  const normal = Math.hypot(constraint.a[0], constraint.a[1]);
  const offset = 0.32;
  const lx = other[0] + (end[0] - other[0]) * along + (constraint.a[0] / normal) * offset;
  const ly = other[1] + (end[1] - other[1]) * along + (constraint.a[1] / normal) * offset;
  return (
    <g>
      <line
        className="ex-constraint"
        x1={scale.px(from[0])}
        x2={scale.px(to[0])}
        y1={scale.py(from[1])}
        y2={scale.py(to[1])}
      />
      <text className="ex-label" textAnchor="middle" x={scale.px(lx)} y={scale.py(ly)}>{constraint.label}</text>
    </g>
  );
}

function LevelThrough({
  cost, point, scale, bounds,
}: { cost: Vec2; point: Vec2; scale: ReturnType<typeof makeScale>; bounds: Bounds }) {
  const line = levelLine(cost, objectiveValue(cost, point), bounds);
  if (!line) return null;
  return (
    <line
      className="ex-level-now"
      x1={scale.px(line[0][0])}
      x2={scale.px(line[1][0])}
      y1={scale.py(line[0][1])}
      y2={scale.py(line[1][1])}
    />
  );
}
