import { useMemo, useState } from "react";

import { Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import type { Bounds } from "./math/contours";
import { levelLine, type Vec2 } from "./math/lp2d";
import {
  LATTICE_MAX, MILP_ARTICLE_LIMITS, MILP_LIMIT_RANGE, MILP_PROFIT, solveMilp, type MilpSolution,
} from "./math/milpLattice";
import { makeScale, polylinePath, useStageViewport } from "./svg";

const BOUNDS: Bounds = { xMin: -0.7, xMax: LATTICE_MAX + 0.4, yMin: -0.7, yMax: LATTICE_MAX - 0.1 };
const ASPECT = (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin);

export default function MilpLattice() {
  const [b1, setB1] = useState(MILP_ARTICLE_LIMITS[0]);
  const [b2, setB2] = useState(MILP_ARTICLE_LIMITS[1]);
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const s = useMemo(() => solveMilp(b1, b2), [b1, b2]);

  const polygon = polylinePath(s.vertices, scale) + "Z";
  const integerLevel = levelLine(MILP_PROFIT, s.integerValue, viewport.bounds);
  const boundLevel = levelLine(MILP_PROFIT, s.lpValue, viewport.bounds);
  const verdict = verdictText(s);
  const summary = `資源1の上限 ${b1}、資源2の上限 ${b2} の生産計画。${verdict}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={String(b1)}
            hint="製品A 1個が6、製品B 1個が4使う資源の上限。記事の値は 24。"
            label="資源1の上限 b₁"
            max={MILP_LIMIT_RANGE.b1.max}
            min={MILP_LIMIT_RANGE.b1.min}
            onChange={setB1}
            step={MILP_LIMIT_RANGE.b1.step}
            value={b1}
          />
          <Slider
            display={String(b2)}
            hint="製品A 1個が1、製品B 1個が2使う資源の上限。記事の値は 6。"
            label="資源2の上限 b₂"
            max={MILP_LIMIT_RANGE.b2.max}
            min={MILP_LIMIT_RANGE.b2.min}
            onChange={setB2}
            step={MILP_LIMIT_RANGE.b2.step}
            value={b2}
          />
        </>
      }
      id="milp-integer-lattice"
      readout={
        <>
          <section aria-label="三つの点の比較">
            <p className="ex-eyebrow">利益 z = 5x₁ + 4x₂ を、三つの点で比べる</p>
            <table className="ex-table milp-table">
              <thead>
                <tr>
                  <th scope="col">点</th>
                  <th scope="col">座標</th>
                  <th scope="col">利益 z</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">
                    <Glyph kind="lp" />LP緩和の最適解（上界）
                    <span className="milp-state">{s.lpIsInteger ? "整数なので実行できる" : "整数でない"}</span>
                  </th>
                  <td>{fmtPair(s.lpPoint[0], s.lpPoint[1])}</td>
                  <td>{fmt(s.lpValue)}</td>
                </tr>
                <tr>
                  <th scope="row">
                    <Glyph kind={s.roundedFeasible ? "round-ok" : "round-bad"} />LP解を丸めた点
                    <span className="milp-state">{s.roundedFeasible ? "実行できる" : excessText(s)}</span>
                  </th>
                  <td>{fmtPair(s.rounded[0], s.rounded[1], 0)}</td>
                  <td>{fmt(s.roundedValue, 0)}</td>
                </tr>
                <tr className="ex-row-best">
                  <th scope="row">
                    <Glyph kind="best" />整数の最適解
                    <span className="milp-state">実行できる</span>
                  </th>
                  <td>{fmtPair(s.integerBest[0], s.integerBest[1], 0)}</td>
                  <td>{fmt(s.integerValue, 0)}</td>
                </tr>
              </tbody>
            </table>
            <p className="ex-hint">
              上界と整数最適値の差は {fmt(s.gap)}。実行できる整数点は {s.insideCount} 個です。
              {s.integerTies > 1 ? `最良の利益は ${s.integerTies} 点で同じ値になり、表にはその一つを載せています。` : ""}
            </p>
          </section>
          <p className={`ex-verdict ${s.gap === 0 ? "ex-tone-good" : "ex-tone-slow"}`}>{verdict}</p>
        </>
      }
      stage={
        <figure className="ex-panel">
          <figcaption className="ex-panel-title">LP緩和の領域と整数の格子点</figcaption>
          <div className="ex-canvas" ref={stageRef}>
            <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
              <rect className="ex-ground" height={viewport.height} width={viewport.width} />
              <g className="ex-axes">
                <line x1={scale.px(0)} x2={scale.px(0)} y1={0} y2={viewport.height} />
                <line x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
                {Array.from({ length: LATTICE_MAX + 1 }, (_, tick) => (
                  <text key={`x${tick}`} textAnchor="middle" x={scale.px(tick)} y={scale.py(0) + 18}>{tick}</text>
                ))}
                {Array.from({ length: LATTICE_MAX - 1 }, (_, index) => index + 1).map((tick) => (
                  <text key={`y${tick}`} textAnchor="end" x={scale.px(0) - 7} y={scale.py(tick) + 4}>{tick}</text>
                ))}
                <text textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 8}>x₁ A</text>
                <text x={scale.px(0) + 8} y={16}>x₂ B</text>
              </g>
              {boundLevel && <LevelLine className="ex-level" line={boundLevel} scale={scale} />}
              <path className="ex-feasible" d={polygon} />
              {integerLevel && <LevelLine className="ex-level-now" line={integerLevel} scale={scale} />}
              {s.lattice.map((point) => (
                <circle
                  className={point.inside ? "milp-dot-in" : "milp-dot-out"}
                  cx={scale.px(point.x)}
                  cy={scale.py(point.y)}
                  key={`${point.x},${point.y}`}
                  r={point.inside ? 4.5 : 2.5}
                />
              ))}
              <circle
                className={s.roundedFeasible ? "milp-round-ok" : "milp-round-bad"}
                cx={scale.px(s.rounded[0])}
                cy={scale.py(s.rounded[1])}
                r={9}
              />
              <path className="milp-lp" d={diamond(scale.px(s.lpPoint[0]), scale.py(s.lpPoint[1]), 9)} />
              <path className="milp-best" d={star(scale.px(s.integerBest[0]), scale.py(s.integerBest[1]), 9)} />
            </svg>
          </div>
        </figure>
      }
      summary={summary}
    />
  );
}

function LevelLine({
  line, scale, className,
}: { line: [Vec2, Vec2]; scale: ReturnType<typeof makeScale>; className: string }) {
  return (
    <line
      className={className}
      x1={scale.px(line[0][0])}
      x2={scale.px(line[1][0])}
      y1={scale.py(line[0][1])}
      y2={scale.py(line[1][1])}
    />
  );
}

function diamond(x: number, y: number, r: number): string {
  return `M${x} ${y - r}L${x + r} ${y}L${x} ${y + r}L${x - r} ${y}Z`;
}

function star(x: number, y: number, r: number): string {
  const points = Array.from({ length: 10 }, (_, index) => {
    const radius = index % 2 === 0 ? r : r * 0.45;
    const angle = -Math.PI / 2 + (index * Math.PI) / 5;
    return `${x + radius * Math.cos(angle)} ${y + radius * Math.sin(angle)}`;
  });
  return `M${points.join("L")}Z`;
}

type GlyphKind = "lp" | "round-ok" | "round-bad" | "best";

/** The same marker as in the plot, so the table rows can be matched to the points by shape. */
function Glyph({ kind }: { kind: GlyphKind }) {
  return (
    <svg aria-hidden="true" className="milp-glyph" height={22} viewBox="0 0 22 22" width={22}>
      {kind === "lp" && <path className="milp-lp" d={diamond(11, 11, 8)} />}
      {kind === "best" && <path className="milp-best" d={star(11, 11, 9)} />}
      {(kind === "round-ok" || kind === "round-bad") && (
        <circle className={kind === "round-ok" ? "milp-round-ok" : "milp-round-bad"} cx={11} cy={11} r={8} />
      )}
    </svg>
  );
}

function excessText(s: MilpSolution): string {
  const parts: string[] = [];
  if (s.roundedExcess[0] > 0) parts.push(`資源1が${fmt(s.roundedExcess[0], 0)}超過`);
  if (s.roundedExcess[1] > 0) parts.push(`資源2が${fmt(s.roundedExcess[1], 0)}超過`);
  return `実行できない（${parts.join("、")}）`;
}

function verdictText(s: MilpSolution): string {
  const lp = `LP緩和の最適解は ${fmtPair(s.lpPoint[0], s.lpPoint[1])}、利益 ${fmt(s.lpValue)} が上界です。`;
  const best = `整数の最適解は ${fmtPair(s.integerBest[0], s.integerBest[1], 0)}で利益 ${fmt(s.integerValue, 0)}、上界との差は ${fmt(s.gap)} です。`;
  if (s.lpIsInteger) {
    return `LP緩和の最適解 ${fmtPair(s.lpPoint[0], s.lpPoint[1], 0)} がもともと整数で、そのまま実行できます。利益は ${fmt(s.lpValue, 0)}、上界との差は 0 です。`;
  }
  if (!s.roundedFeasible) {
    return `${lp}丸めた点 ${fmtPair(s.rounded[0], s.rounded[1], 0)} は${excessText(s).replace("実行できない", "実行できません")}。${best}`;
  }
  if (s.roundedValue === s.integerValue) {
    // Profit coefficients are integers, so every integer plan earns at most ⌊upper bound⌋.
    const ceiling = Math.floor(s.lpValue + 1e-9);
    const proof = s.roundedValue === ceiling
      ? `利益の係数が整数なので、整数解の利益は上界を切り捨てた ${ceiling} 以下です。この比較から最適だと言えます。根拠は上界との比較で、丸めたこと自体ではありません。`
      : `上界を切り捨てた ${ceiling} との差が残るので、この上界だけでは最適だと言い切れません。`;
    return `${lp}丸めた点 ${fmtPair(s.rounded[0], s.rounded[1], 0)} は実行できて利益 ${fmt(s.roundedValue, 0)}、整数の最適解と一致しました。${proof}`;
  }
  return `${lp}丸めた点 ${fmtPair(s.rounded[0], s.rounded[1], 0)} は実行できますが利益 ${fmt(s.roundedValue, 0)} で、${best}`;
}
