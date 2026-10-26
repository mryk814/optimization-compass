import { useMemo, useState } from "react";

import { PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import type { Bounds } from "./math/contours";
import type { Vec2 } from "./math/lp2d";import {
  QP_ARTICLE_LIMIT, QP_ARTICLE_TARGET, QP_RANGE, balanceArrows, qpConstraints, relaxSumLimit, solveConvexQp, type QpSolution,
} from "./math/convexQp";
import { makeScale, polylinePath, useStageViewport } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const BOUNDS: Bounds = { xMin: -1.5, xMax: 5.6, yMin: -1.5, yMax: 5.6 };
const ASPECT = 1;
const STEPS = 24;
const LAMBDA_SCALE = 12;
const NAMES = ["合計の上限 x₁+x₂ ≤ b", "x₁ ≥ 0", "x₂ ≥ 0"] as const;

export default function ConvexQpProjection() {
  const [p1, setP1] = useState(QP_ARTICLE_TARGET[0]);
  const [p2, setP2] = useState(QP_ARTICLE_TARGET[1]);
  const [limit, setLimit] = useState(QP_ARTICLE_LIMIT);
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const timeline = useTimeline(STEPS, 6);
  useReplayOnChange(timeline, `${p1},${p2},${limit}`);
  // The target travels from the middle of the triangle to the reader's target; the nearest point follows it.
  const start: [number, number] = [limit / 4, limit / 4];
  const fraction = timeline.position / STEPS;
  const q: [number, number] = [start[0] + (p1 - start[0]) * fraction, start[1] + (p2 - start[1]) * fraction];
  const s = useMemo(() => solveConvexQp(q, limit), [q[0], q[1], limit]);
  const settled = useMemo(() => solveConvexQp([p1, p2], limit), [p1, p2, limit]);
  const relax = useMemo(() => relaxSumLimit(q, limit, 0.1), [q[0], q[1], limit]);
  const trail = useMemo(
    () => Array.from({ length: 49 }, (_, i) => {
      const f = i / 48;
      return solveConvexQp([start[0] + (p1 - start[0]) * f, start[1] + (p2 - start[1]) * f], limit).x;
    }),
    [p1, p2, limit],
  );

  const unit = viewport.width / (BOUNDS.xMax - BOUNDS.xMin);
  const polygon = polylinePath(s.vertices, scale) + "Z";
  const verdict = verdictText(s);
  const summary = `目標 ${fmtPair(p1, p2, 1)}、合計の上限 ${fmt(limit, 1)}。${verdictText(settled)}`;
  const cons = qpConstraints();
  const arrows = balanceArrows(s);
  const pushSum: [number, number] = [
    arrows.pushes.reduce((sum, push) => sum + push.vector[0], 0),
    arrows.pushes.reduce((sum, push) => sum + push.vector[1], 0),
  ];
  // One shared scale so arrow lengths compare directly, capped so a far target does not fill the plane.
  const longest = Math.max(Math.hypot(arrows.gradient[0], arrows.gradient[1]), ...arrows.pushes.map((p) => Math.hypot(p.vector[0], p.vector[1])), 1e-9);
  const forceK = Math.min(0.35, 2.4 / longest);

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(p1, 1)}
            hint="目標の x₁ 座標。記事の値は 3。"
            label="目標の x₁ 座標 p₁"
            max={QP_RANGE.target.max}
            min={QP_RANGE.target.min}
            onChange={setP1}
            step={QP_RANGE.target.step}
            value={p1}
          />
          <Slider
            display={fmt(p2, 1)}
            hint="目標の x₂ 座標。記事の値は 2。"
            label="目標の x₂ 座標 p₂"
            max={QP_RANGE.target.max}
            min={QP_RANGE.target.min}
            onChange={setP2}
            step={QP_RANGE.target.step}
            value={p2}
          />
          <Slider
            display={fmt(limit, 1)}
            hint="x₁ + x₂ の上限。記事の値は 3。"
            label="合計の上限 b"
            max={QP_RANGE.limit.max}
            min={QP_RANGE.limit.min}
            onChange={setLimit}
            step={QP_RANGE.limit.step}
            value={limit}
          />
        </>
      }
      id="convex-qp-projection"
      player={(
        <PlayerBar
          positionText={`目標 ${fmtPair(q[0], q[1], 1)}`}
          stepLabel="目標を動かす"
          timeline={timeline}
        />
      )}
      readout={
        <>
          <section aria-label="制約と乗数">
            <p className="ex-eyebrow">最適点で、制約はどう効いているか</p>
            <div aria-hidden="true" className="qp-bars">
              {NAMES.map((name, index) => (
                <div className="qp-bar-row" key={name}>
                  <span>{name}</span>
                  <div className="qp-bar-track">
                    <div
                      className={s.multipliers[index] > 1e-9 ? "qp-bar qp-bar-on" : "qp-bar"}
                      style={{ width: `${Math.min(100, (s.multipliers[index] / LAMBDA_SCALE) * 100)}%` }}
                    />
                  </div>
                  <span className="qp-bar-value">λ = {fmt(s.multipliers[index])}</span>
                </div>
              ))}
            </div>
            <table className="ex-table qp-table">
              <thead>
                <tr>
                  <th scope="col">制約</th>
                  <th scope="col">状態</th>
                  <th scope="col">乗数 λ</th>
                </tr>
              </thead>
              <tbody>
                {cons.map((_, index) => (
                  <tr className={s.multipliers[index] > 1e-9 ? "ex-row-best" : undefined} key={NAMES[index]}>
                    <th scope="row">{NAMES[index]}</th>
                    <td>{stateText(s, index)}</td>
                    <td>{fmt(s.multipliers[index])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="ex-hint">
              最適点 {fmtPair(s.x[0], s.x[1])}、目的値 {fmt(s.value)}。
              頂点の目的値は {s.vertices.map((v, i) => `${fmtPair(v[0], v[1], 1)} で ${fmt(s.vertexValues[i])}`).join("、")} で、
              頂点だけを比べると最小は {fmt(s.bestVertexValue)}、本当の最小値との差は {fmt(s.vertexGap)} です。
            </p>
            <p className="ex-hint">
              上限 b を 0.1 緩めたときの目的値の改善は、乗数からの予測が {fmt(relax.predicted, 3)}、解き直した値が {fmt(relax.actual, 3)} です。
            </p>
          </section>
          <p className={`ex-verdict ${s.targetInside ? "ex-tone-good" : "ex-tone-slow"}`}>{verdict}</p>
        </>
      }
      stage={
        <figure className="ex-panel">
          <figcaption className="ex-panel-title">可行領域と、目標に最も近い点</figcaption>
          <div className="ex-canvas" ref={stageRef}>
            <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
              <rect className="ex-ground" height={viewport.height} width={viewport.width} />
              <g className="ex-axes">
                <line x1={scale.px(0)} x2={scale.px(0)} y1={0} y2={viewport.height} />
                <line x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
                {[1, 2, 3, 4, 5].map((tick) => (
                  <text key={`x${tick}`} textAnchor="middle" x={scale.px(tick)} y={scale.py(0) + 18}>{tick}</text>
                ))}
                {[1, 2, 3, 4, 5].map((tick) => (
                  <text key={`y${tick}`} textAnchor="end" x={scale.px(0) - 7} y={scale.py(tick) + 4}>{tick}</text>
                ))}
                <text textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 8}>x₁</text>
                <text x={scale.px(0) + 8} y={16}>x₂</text>
              </g>
              <path className="ex-feasible" d={polygon} />
              {edges(limit).map((edge, index) => (
                <line
                  className={s.multipliers[index] > 1e-9 ? "qp-edge qp-edge-active" : s.tight.includes(index) ? "qp-edge qp-edge-tight" : "qp-edge"}
                  key={NAMES[index]}
                  x1={scale.px(edge[0][0])}
                  x2={scale.px(edge[1][0])}
                  y1={scale.py(edge[0][1])}
                  y2={scale.py(edge[1][1])}
                />
              ))}
              {edges(limit).map((edge, index) => {
                const label = edgeLabel(s, index);
                if (!label) return null;
                const mx = (edge[0][0] + edge[1][0]) / 2;
                const my = (edge[0][1] + edge[1][1]) / 2;
                const outward = index === 0 ? [10, -10] : index === 1 ? [-10, 0] : [0, -10];
                return (
                  <text
                    className="ex-label qp-edge-label"
                    key={`label${NAMES[index]}`}
                    textAnchor={index === 1 ? "end" : "start"}
                    x={scale.px(mx) + outward[0]}
                    y={scale.py(my) + outward[1]}
                  >
                    {label}
                  </text>
                );
              })}
              <path className="qp-trail" d={polylinePath(trail, scale)} />
              {s.radius > 1e-9 && (
                <circle
                  className="qp-level"
                  cx={scale.px(q[0])}
                  cy={scale.py(q[1])}
                  r={s.radius * unit}
                />
              )}
              <line
                className="qp-link"
                x1={scale.px(q[0])}
                x2={scale.px(s.x[0])}
                y1={scale.py(q[1])}
                y2={scale.py(s.x[1])}
              />
              {s.vertices.map((v) => (
                <circle
                  className={v === s.bestVertex ? "qp-vertex qp-vertex-best" : "qp-vertex"}
                  cx={scale.px(v[0])}
                  cy={scale.py(v[1])}
                  key={`${v[0]},${v[1]}`}
                  r={5}
                />
              ))}
              {s.vertices.map((v, i) => (
                <text
                  className={v === s.bestVertex ? "ex-label ex-label-strong qp-vlabel" : "ex-label qp-vlabel"}
                  key={`vl${v[0]},${v[1]}`}
                  textAnchor={i === 2 ? "start" : "end"}
                  x={scale.px(v[0]) + (i === 2 ? 10 : i === 1 ? 6 : -10)}
                  y={scale.py(v[1]) + (i === 2 ? -10 : i === 1 ? 38 : 20)}
                >
                  {fmt(s.vertexValues[i], 1)}
                </text>
              ))}
              {s.radius > 1e-9 && (
                <g className="qp-forces">
                  <path className="qp-arrow qp-arrow-grad" d={arrow(scale, s.x, forceEnd(s.x, arrows.gradient, forceK))} />
                  <text className="ex-label qp-arrow-label qp-arrow-label-grad" x={scale.px(s.x[0] + arrows.gradient[0] * forceK) + 8} y={scale.py(s.x[1] + arrows.gradient[1] * forceK) + 18}>
                    ∇f
                  </text>
                  {arrows.pushes.map((push) => (
                    <path
                      className="qp-arrow qp-arrow-push"
                      d={arrow(scale, s.x, forceEnd(s.x, push.vector, forceK))}
                      key={`push${NAMES[push.index]}`}
                    />
                  ))}
                  {arrows.pushes.length > 0 && (
                    <text className="ex-label qp-arrow-label qp-arrow-label-push" x={scale.px(s.x[0] + pushSum[0] * forceK) + 8} y={scale.py(s.x[1] + pushSum[1] * forceK) - 6}>
                      λ·法線
                    </text>
                  )}
                </g>
              )}
              <path className="qp-target" d={cross(scale.px(q[0]), scale.py(q[1]), 9)} />
              <path className="qp-best" d={star(scale.px(s.x[0]), scale.py(s.x[1]), 10)} />
              <text className="ex-label ex-label-strong" x={scale.px(s.x[0]) + 14} y={scale.py(s.x[1]) - 12}>
                最適 {fmt(s.value, 1)}
              </text>
            </svg>
          </div>
        </figure>
      }
      summary={summary}
    />
  );
}

function forceEnd(from: Vec2, force: Vec2, k: number): Vec2 {
  return [from[0] + force[0] * k, from[1] + force[1] * k];
}

/** A line from `from` to `to` with a filled head at `to`. */
function arrow(scale: { px(x: number): number; py(y: number): number }, from: Vec2, to: Vec2): string {
  const x1 = scale.px(from[0]);
  const y1 = scale.py(from[1]);
  const x2 = scale.px(to[0]);
  const y2 = scale.py(to[1]);
  const length = Math.hypot(x2 - x1, y2 - y1);
  if (length < 1) return "";
  const ux = (x2 - x1) / length;
  const uy = (y2 - y1) / length;
  const head = Math.min(11, length * 0.6);
  const bx = x2 - ux * head;
  const by = y2 - uy * head;
  return `M${x1} ${y1}L${bx} ${by}M${x2} ${y2}L${bx - uy * head * 0.45} ${by + ux * head * 0.45}L${bx + uy * head * 0.45} ${by - ux * head * 0.45}Z`;
}

function edges(limit: number): Array<[[number, number], [number, number]]> {
  return [[[limit, 0], [0, limit]], [[0, 0], [0, limit]], [[0, 0], [limit, 0]]];
}

function edgeLabel(s: QpSolution, index: number): string {
  if (s.multipliers[index] > 1e-9) return `λ = ${fmt(s.multipliers[index], 1)}`;
  if (s.tight.includes(index)) return "境界上・λ = 0";
  return "";
}

function stateText(s: QpSolution, index: number): string {
  if (s.multipliers[index] > 1e-9) return "効いている（λ > 0）";
  if (s.tight.includes(index)) return "境界上だが λ = 0";
  return "余裕あり（λ = 0）";
}

function verdictText(s: QpSolution): string {
  const point = `最も近い点は ${fmtPair(s.x[0], s.x[1])}、目的値は ${fmt(s.value)} です。`;
  if (s.targetInside) {
    return `目標が領域の内部にあるので、目標そのものが答えで、どの制約も効かず乗数はすべて 0 です。`;
  }
  const active = s.activeSet.map((index) => NAMES[index]);
  if (s.activeSet.length === 0) {
    return `${point}目標が境界上にあり、勾配が 0 なので乗数は 0 です。`;
  }
  if (s.atVertex) {
    const lambdas = s.activeSet.map((index) => `${NAMES[index]} の λ は ${fmt(s.multipliers[index])}`).join("、");
    return `${point}2本の制約（${active.join("、")}）が同時に効く頂点が答えで、${lambdas}です。`;
  }
  const gap = s.vertexGap > 1e-9
    ? `辺の途中が答えで、頂点だけを比べると最小が ${fmt(s.bestVertexValue)} になり ${fmt(s.vertexGap)} だけ取り逃がします。`
    : `答えは辺の上にあります。`;
  return `${point}${active[0]} が効いていて λ は ${fmt(s.multipliers[s.activeSet[0]])} です。${gap}`;
}

function cross(x: number, y: number, r: number): string {
  return `M${x - r} ${y - r}L${x + r} ${y + r}M${x - r} ${y + r}L${x + r} ${y - r}`;
}

function star(x: number, y: number, r: number): string {
  const points = Array.from({ length: 10 }, (_, index) => {
    const radius = index % 2 === 0 ? r : r * 0.45;
    const angle = -Math.PI / 2 + (index * Math.PI) / 5;
    return `${x + radius * Math.cos(angle)} ${y + radius * Math.sin(angle)}`;
  });
  return `M${points.join("L")}Z`;
}
