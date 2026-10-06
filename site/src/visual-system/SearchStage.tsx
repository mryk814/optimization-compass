/**
 * Search Stage primitives: the landscape, what was measured on it, and what a method holds.
 * Theater lanes, the overlaid comparison, and Case previews draw with these same marks, so a
 * point, a band, or a proposal means the same thing wherever it appears.
 *
 *   TerrainCurve      the teaching objective — only the human view shows it
 *   UncertaintyBand   a model's spread (observed teal wash)
 *   ModelCurve        a model's mean (observed teal line)
 *   EvaluationMarks   measured points; the method's shape, teal fill, violations red
 *   ProposalMarker    where the method will measure next (orange)
 *   TangentProbe      a slope read at one point (orange)
 *   SpreadBracket     a population's sampling width (orange bracket)
 *   BudgetTicks       one tick per evaluation, filled when spent
 */
import { shapePath, type MethodShape } from "./DispositionMark";

export interface StageScale {
  px(x: number): number;
  py(y: number): number;
  width: number;
  height: number;
}

export function stageScale(
  width: number,
  height: number,
  xDomain: readonly [number, number],
  yDomain: readonly [number, number],
  pad = { left: 8, right: 8, top: 10, bottom: 18 },
): StageScale {
  const sx = (width - pad.left - pad.right) / (xDomain[1] - xDomain[0]);
  const sy = (height - pad.top - pad.bottom) / (yDomain[1] - yDomain[0]);
  return {
    px: (x) => pad.left + (x - xDomain[0]) * sx,
    py: (y) => height - pad.bottom - (y - yDomain[0]) * sy,
    width,
    height,
  };
}

function linePath(xs: readonly number[], ys: readonly number[], s: StageScale): string {
  return xs.map((x, i) => `${i === 0 ? "M" : "L"} ${s.px(x).toFixed(1)} ${s.py(ys[i]).toFixed(1)}`).join(" ");
}

export function TerrainCurve({ xs, f, scale }: { xs: readonly number[]; f: (x: number) => number; scale: StageScale }) {
  return <path className="vs-terrain" d={linePath(xs, xs.map(f), scale)} />;
}

export function UncertaintyBand({ xs, mean, sd, k = 2, scale }: { xs: readonly number[]; mean: readonly number[]; sd: readonly number[]; k?: number; scale: StageScale }) {
  if (mean.length === 0) return null;
  const upper = xs.map((x, i) => `${i === 0 ? "M" : "L"} ${scale.px(x).toFixed(1)} ${scale.py(mean[i] + k * sd[i]).toFixed(1)}`).join(" ");
  const lower = [...xs].reverse().map((x, j) => {
    const i = xs.length - 1 - j;
    return `L ${scale.px(x).toFixed(1)} ${scale.py(mean[i] - k * sd[i]).toFixed(1)}`;
  }).join(" ");
  return <path className="vs-band" d={`${upper} ${lower} Z`} />;
}

export function ModelCurve({ xs, ys, scale }: { xs: readonly number[]; ys: readonly number[]; scale: StageScale }) {
  if (ys.length === 0) return null;
  return <path className="vs-model" d={linePath(xs, ys, scale)} />;
}

export interface StagePoint {
  x: number;
  y: number;
  key: string | number;
  faded?: boolean;
  latest?: boolean;
  best?: boolean;
  violation?: boolean;
  label?: string;
}

export function EvaluationMarks({ points, shape, scale, r = 5 }: { points: readonly StagePoint[]; shape: MethodShape; scale: StageScale; r?: number }) {
  return (
    <g className="vs-evals">
      {points.map((point) => {
        const cx = scale.px(point.x);
        const cy = scale.py(point.y);
        const classes = ["vs-eval", point.faded && "is-faded", point.latest && "is-latest", point.best && "is-best", point.violation && "is-violation"]
          .filter(Boolean).join(" ");
        return (
          <g key={point.key}>
            {point.best && <circle className="vs-eval-best-ring" cx={cx} cy={cy} r={r + 4} />}
            <path className={classes} d={shapePath(shape, cx, cy, r)} />
            {point.label && <text className="vs-eval-label" x={cx + r + 3} y={cy - r}>{point.label}</text>}
          </g>
        );
      })}
    </g>
  );
}

export function ProposalMarker({ x, scale, label = "次" }: { x: number; scale: StageScale; label?: string }) {
  const px = scale.px(x);
  return (
    <g className="vs-proposal">
      <line x1={px} x2={px} y1={10} y2={scale.height - 18} />
      <path d={`M ${px} ${scale.height - 16} l -5 9 h 10 Z`} />
      <text textAnchor="middle" x={px} y={scale.height - 1}>{label}</text>
    </g>
  );
}

export function TangentProbe({ x, y, slope, halfWidth = 0.55, scale }: { x: number; y: number; slope: number; halfWidth?: number; scale: StageScale }) {
  const x0 = x - halfWidth;
  const x1 = x + halfWidth;
  return (
    <g className="vs-tangent">
      <line x1={scale.px(x0)} x2={scale.px(x1)} y1={scale.py(y - slope * halfWidth)} y2={scale.py(y + slope * halfWidth)} />
    </g>
  );
}

export function StepArrow({ from, to, y, scale }: { from: number; to: number; y: number; scale: StageScale }) {
  const a = scale.px(from);
  const b = scale.px(to);
  const py = scale.py(y);
  if (Math.abs(b - a) < 2) return null;
  const dir = Math.sign(b - a);
  return (
    <g className="vs-step-arrow">
      <line x1={a} x2={b - dir * 6} y1={py} y2={py} />
      <path d={`M ${b} ${py} l ${-dir * 8} -4.5 v 9 Z`} />
    </g>
  );
}

export function SpreadBracket({ mean, sigma, scale, xDomain }: { mean: number; sigma: number; scale: StageScale; xDomain: readonly [number, number] }) {
  const lo = Math.max(xDomain[0], mean - 2 * sigma);
  const hi = Math.min(xDomain[1], mean + 2 * sigma);
  const y = scale.height - 30;
  return (
    <g className="vs-spread">
      <rect height={6} width={scale.px(hi) - scale.px(lo)} x={scale.px(lo)} y={y - 3} />
      <line x1={scale.px(mean)} x2={scale.px(mean)} y1={y - 8} y2={y + 8} />
    </g>
  );
}

export function BudgetTicks({ total, spent, purposes }: { total: number; spent: number; purposes?: readonly string[] }) {
  return (
    <span className="vs-budget" role="img" aria-label={`評価予算 ${total}回のうち ${spent}回を使用`}>
      {Array.from({ length: total }, (_, index) => (
        <span
          className={index < spent ? `vs-budget-tick is-spent${purposes?.[index] ? ` is-${purposes[index]}` : ""}` : "vs-budget-tick"}
          key={index}
        />
      ))}
    </span>
  );
}

/**
 * Unknown is data: in the algorithm's view the stage starts hatched, and only the x-ranges the
 * method holds information about are cleared. A slope knows a sliver; a surrogate models the
 * whole domain (with its uncertainty band); a population knows only where it sampled.
 */
export function UnseenField({ scale, known, id }: { scale: StageScale; known: ReadonlyArray<readonly [number, number]>; id: string }) {
  const top = 4;
  const bottom = scale.height - 18;
  return (
    <g className="vs-unseen-field">
      <defs>
        <pattern height="7" id={id} patternTransform="rotate(45)" patternUnits="userSpaceOnUse" width="7">
          <rect className="vs-hatch-ground" height="7" width="7" />
          <line className="vs-hatch-line" x1="0" x2="0" y1="0" y2="7" />
        </pattern>
        <mask id={`${id}-mask`}>
          <rect fill="white" height={bottom - top} width={scale.width} x={0} y={top} />
          {known.map(([a, b]) => (
            <rect fill="black" height={bottom - top} key={`${a}:${b}`} width={Math.max(0, scale.px(b) - scale.px(a))} x={scale.px(a)} y={top} />
          ))}
        </mask>
      </defs>
      <rect fill={`url(#${id})`} height={bottom - top} mask={`url(#${id}-mask)`} opacity={0.55} width={scale.width} x={0} y={top} />
    </g>
  );
}
