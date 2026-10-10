import { useMemo, useState } from "react";

import { Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmtPair } from "./format";
import type { Bounds } from "./math/contours";
import { levelLine } from "./math/lp2d";
import {
  basisState, COLUMNS, edgeMove, fracText, improving, isBasic, pivot, POLYGON, RESOURCES, sign,
  START_BASIS, value, valuesAlong, VARIABLE_INFO, VARIABLES,
  type BasisState, type EdgeMove, type Fraction, type VariableIndex,
} from "./math/simplex";
import { frac as mfrac, LiveMath, mi, mn, mo, paren, row, signed, sub, tint } from "./mathml";
import { makeScale, polylinePath, useStageViewport, type Scale } from "./svg";

const ID = "simplex-pivot";
const BOUNDS: Bounds = { xMin: -0.9, xMax: 9.8, yMin: -1.35, yMax: 10.4 };
const ASPECT = (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin);
/** The bar range of the variable panel. Values past it are drawn at the end with their number. */
const BAR_MIN = -10;
const BAR_MAX = 20;
const CONSTRAINTS = [
  { a: [3, 2] as const, b: 18, label: "小麦粉 18" },
  { a: [1, 3] as const, b: 13, label: "バター 13" },
];

const symbol = (j: VariableIndex) => VARIABLE_INFO[j].symbol;
/** Two decimals without switching to exponents near 0, which the bars pass through often. */
const fixed = (v: number) => {
  const text = Math.abs(v).toFixed(2);
  return v < 0 && Number(text) !== 0 ? `−${text}` : text;
};
const named = (j: VariableIndex) => `${VARIABLE_INFO[j].symbol}（${VARIABLE_INFO[j].name}）`;
const basisText = (state: BasisState) => state.basis.map(symbol).join(", ");
const pointText = (state: BasisState) => `(${fracText(state.point[0])}, ${fracText(state.point[1])})`;
const signedFrac = (f: Fraction) => (sign(f) > 0 ? `+${fracText(f)}` : fracText(f));
/**
 * Slider range: at least half again past the minimum ratio, so the reader can step over the
 * boundary, and far enough to reach the other ratios that stay inside the plot (at most 9).
 */
const sliderMax = (move: EdgeMove) => {
  const ratios = move.rows.flatMap((r) => (r.ratio ? [value(r.ratio)] : [])).filter((r) => r <= 9);
  return Number(Math.max((move.theta ? value(move.theta) : 4) * 1.5, ...ratios).toFixed(2));
};

export default function SimplexPivot() {
  const [history, setHistory] = useState<BasisState[]>(() => [basisState(START_BASIS)]);
  const [entering, setEntering] = useState<VariableIndex>();
  const [amount, setAmount] = useState(0);
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);

  const state = history.at(-1)!;
  const move = entering === undefined ? undefined : edgeMove(state, entering);
  const values = move ? valuesAlong(state, move, amount) : state.values.map(value);
  const probe: readonly [number, number] = [values[0], values[1]];
  const sales = 3 * values[0] + 4 * values[1];
  const negative = VARIABLES.filter((j) => values[j] < -1e-9);
  const atOptimum = improving(state).length === 0;
  const nonbasic = VARIABLES.filter((j) => !isBasic(state, j));

  const choose = (j: VariableIndex) => { setEntering(j); setAmount(0); };
  const doPivot = () => {
    if (!move || move.leaving === undefined) return;
    setHistory([...history, pivot(state, move)]);
    setEntering(undefined);
    setAmount(0);
  };
  const undo = () => { setHistory(history.slice(0, -1)); setEntering(undefined); setAmount(0); };
  const reset = () => { setHistory([basisState(START_BASIS)]); setEntering(undefined); setAmount(0); };

  const verdict = verdictText(state, move, amount, negative, atOptimum);
  const tone = negative.length ? "ex-tone-bad" : atOptimum && !move ? "ex-tone-good" : move && sign(move.salesRate) <= 0 ? "ex-tone-swing" : "ex-tone-slow";
  const summary = `いまの頂点は ${pointText(state)}、基底は ${basisText(state)}、売上は ${fracText(state.sales)}。${verdict}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <fieldset className="ex-choice spx-enter">
            <legend>増やす変数を選ぶ（いまは0の変数）</legend>
            <div>
              {nonbasic.map((j) => (
                <button
                  aria-pressed={entering === j}
                  className={entering === j ? "is-selected" : undefined}
                  key={j}
                  onClick={() => choose(j)}
                  type="button"
                >
                  {named(j)}を増やす
                  <span className="spx-rate">1増やすと売上 {signedFrac(edgeMove(state, j).salesRate)}</span>
                </button>
              ))}
            </div>
          </fieldset>
          {move && (
            <Slider
              display={fixed(amount)}
              hint={`${symbol(move.entering)} を0からどれだけ増やすか。ほかの基底変数は辺に沿って変わります。`}
              label={`増やす量 θ（${symbol(move.entering)} の値）`}
              max={sliderMax(move)}
              min={0}
              onChange={setAmount}
              step={0.01}
              value={amount}
            />
          )}
          <div className="ex-button-row spx-actions">
            <button className="ex-action" disabled={!move || move.leaving === undefined} onClick={doPivot} type="button">
              {move?.leaving !== undefined
                ? `比の最小値 θ=${fracText(move.theta!)} まで進めて ${symbol(move.leaving)} と入れ替える`
                : "比の最小値まで進めて入れ替える"}
            </button>
            <button className="ex-action" disabled={history.length <= 1} onClick={undo} type="button">一手戻す</button>
            <button className="ex-action" disabled={history.length <= 1 && entering === undefined} onClick={reset} type="button">原点に戻す</button>
          </div>
        </>
      }
      id={ID}
      readout={<Readout history={history} move={move} state={state} tone={tone} verdict={verdict} />}
      stage={
        <div className="ex-twin">
          <figure className="ex-panel">
            <figcaption className="ex-panel-title">頂点と辺</figcaption>
            <div className="ex-canvas" ref={stageRef}>
              <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
                <rect className="ex-ground" height={viewport.height} width={viewport.width} />
                <Axes scale={scale} viewport={viewport} />
                <path className="ex-feasible" d={polylinePath(POLYGON, scale) + "Z"} />
                {CONSTRAINTS.map((constraint) => (
                  <ConstraintLine constraint={constraint} key={constraint.label} scale={scale} viewport={viewport} />
                ))}
                <path className="ex-walk" d={polylinePath(history.map((s) => s.point.map(value) as [number, number]), scale)} />
                {POLYGON.map(([x, y]) => (
                  <circle className="ex-vertex" cx={scale.px(x)} cy={scale.py(y)} key={`${x},${y}`} r={6} />
                ))}
                <VertexLabels scale={scale} />
                {move && <EdgePreview bounds={viewport.bounds} move={move} scale={scale} state={state} />}
                <circle
                  className={negative.length ? "spx-probe is-infeasible" : "ex-head"}
                  cx={scale.px(clampTo(probe[0], viewport.bounds.xMin, viewport.bounds.xMax))}
                  cy={scale.py(clampTo(probe[1], viewport.bounds.yMin, viewport.bounds.yMax))}
                  r={8}
                />
                {outside(probe, viewport.bounds) && (
                  <text className="ex-label ex-label-strong" x={12} y={22}>いまは {fmtPair(probe[0], probe[1], 1)}（図の外）</text>
                )}
              </svg>
            </div>
          </figure>
          <figure className="ex-panel">
            <figcaption className="ex-panel-title">4つの変数の値</figcaption>
            <VariableBars move={move} state={state} values={values} />
            <p className="spx-sales">売上 3x₁+4x₂ = <strong>{fixed(sales)}</strong></p>
          </figure>
        </div>
      }
      summary={summary}
    />
  );
}

function verdictText(
  state: BasisState, move: EdgeMove | undefined, amount: number, negative: VariableIndex[], atOptimum: boolean,
): string {
  if (!move) {
    return atOptimum
      ? `どの変数を増やしても売上は増えません。頂点 ${pointText(state)} が最適で、売上は ${fracText(state.sales)} です。`
      : `増やすと売上が上がる変数は ${improving(state).map(named).join("と")}です。一つ選んでください。`;
  }
  if (negative.length) {
    return `${negative.map((j) => VARIABLE_INFO[j].name).join("と")}が負になりました。θ=${fixed(amount)} は実行可能領域の外です。`;
  }
  if (move.leaving === undefined) return "どの基底変数も減らないので、いくらでも増やせます（非有界）。";
  const rising = sign(move.salesRate) > 0;
  const head = rising ? "" : `${symbol(move.entering)} を増やすと売上が${sign(move.salesRate) < 0 ? "下がります" : "変わりません"}。`;
  if (Math.abs(amount - value(move.theta!)) < 0.005) {
    return `${head}θ=${fracText(move.theta!)} で ${named(move.leaving)}がちょうど0になりました。ここが隣の頂点です。`;
  }
  return `${head}θ を ${fracText(move.theta!)} まで増やせます。そこで ${named(move.leaving)}が先に0になります。`;
}

function Readout({
  state, move, history, verdict, tone,
}: { state: BasisState; move?: EdgeMove; history: BasisState[]; verdict: string; tone: string }) {
  return (
    <>
      {move ? (
        <section aria-label="入る変数と出る変数の計算" className="ex-equation">
          <p className="ex-eyebrow">{symbol(move.entering)} を1増やしたときの売上の変化：直接の売上 − 使う資源の値段</p>
          <ReducedCostMath move={move} state={state} />
          <p className="ex-eyebrow">増やせる量：各基底変数の「いまの値 ÷ 1あたりの減り方」の最小</p>
          <RatioMath move={move} state={state} />
        </section>
      ) : (
        <section aria-label="資源の値段" className="ex-equation">
          <p className="ex-eyebrow">いまの基底での資源1単位の値段（双対値）</p>
          <p>小麦粉 {fracText(state.prices[0])}、バター {fracText(state.prices[1])}。被約費用は、この値段で使う資源を差し引いた売上の増え方です。</p>
        </section>
      )}
      <table className="ex-table">
        <thead>
          <tr><th scope="col">反復</th><th scope="col">基底</th><th scope="col">頂点 (x₁, x₂)</th><th scope="col">売上</th></tr>
        </thead>
        <tbody>
          {history.map((s, index) => (
            <tr className={index === history.length - 1 && improving(s).length === 0 ? "ex-row-best" : undefined} key={index}>
              <th scope="row">{index}</th>
              <td>{basisText(s)}</td>
              <td>{pointText(s)}</td>
              <td>{fracText(s.sales)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={`ex-verdict ${tone}`}>{verdict}</p>
    </>
  );
}

/** Text for a fraction in MathML: a stacked fraction when it is not an integer. */
function num(f: Fraction): string {
  const body = f.d === 1 ? mn(String(Math.abs(f.n))) : mfrac(mn(String(Math.abs(f.n))), mn(String(f.d)));
  return f.n < 0 ? paren(row(mo("−"), body)) : body;
}

function ReducedCostMath({ state, move }: { state: BasisState; move: EdgeMove }) {
  const j = move.entering;
  const direct = [3, 4, 0, 0][j];
  const [flour, butter] = COLUMNS[j];
  const markup = row(
    tint("orange", mn(String(direct))),
    mo("−"),
    paren(num(state.prices[0]), mo("×"), mn(String(flour)), mo("+"), num(state.prices[1]), mo("×"), mn(String(butter))),
    mo("="),
    signed(fracText(move.salesRate)),
  );
  const label = `直接の売上 ${direct} から、小麦粉の値段 ${fracText(state.prices[0])} × ${flour} とバターの値段 ${fracText(state.prices[1])} × ${butter} を引くと ${fracText(move.salesRate)}`;
  return (
    <>
      <LiveMath block label={label} markup={markup} />
      <p className="ex-hint">
        最小化の形 −3x₁−4x₂ では、{symbol(j)} の被約費用はこの符号を逆にした {fracText({ n: -move.salesRate.n, d: move.salesRate.d })} です。
        {RESOURCES[0]} {flour}、{RESOURCES[1]} {butter} は、{symbol(j)} を1増やすときに使う量です。
      </p>
    </>
  );
}

function RatioMath({ state, move }: { state: BasisState; move: EdgeMove }) {
  const finite = move.rows.filter((r) => r.ratio);
  if (!finite.length) {
    return <p>どの基底変数も減らないので、比が取れません。この向きには境界がありません。</p>;
  }
  const parts = finite.flatMap((r, index) => [
    ...(index ? [mo(",")] : []),
    row(varMath(r.variable), mo(":"), mfrac(num(state.values[r.variable]), num(r.rate))),
  ]);
  const markup = row(mi("θ"), mo("="), mi("min"), row(mo("{"), ...parts, mo("}")), mo("="), tint("orange", num(move.theta!)));
  const label = `θ は ${finite.map((r) => `${symbol(r.variable)} の ${fracText(state.values[r.variable])} ÷ ${fracText(r.rate)}`).join("、")} の最小で ${fracText(move.theta!)}`;
  const skipped = move.rows.filter((r) => !r.ratio);
  return (
    <>
      <LiveMath block label={label} markup={markup} />
      {skipped.length > 0 && (
        <p className="ex-hint">{skipped.map((r) => symbol(r.variable)).join("、")} は増えるか変わらないので、比の候補に入りません。</p>
      )}
    </>
  );
}

/** x₁, x₂, s₁, s₂ as MathML. */
const varMath = (j: VariableIndex) => sub(mi(j < 2 ? "x" : "s"), mn(String((j % 2) + 1)));

function VariableBars({ state, move, values }: { state: BasisState; move?: EdgeMove; values: number[] }) {
  const span = BAR_MAX - BAR_MIN;
  const zero = ((0 - BAR_MIN) / span) * 100;
  return (
    <ul className="spx-bars">
      {VARIABLES.map((j) => {
        const v = values[j];
        const clipped = clampTo(v, BAR_MIN, BAR_MAX);
        const left = Math.min(zero, ((clipped - BAR_MIN) / span) * 100);
        const width = Math.abs(((clipped - BAR_MIN) / span) * 100 - zero);
        const role = move?.entering === j ? "増やす" : isBasic(state, j) ? "基底" : "0に固定";
        const rate = move ? value(move.direction[j]) : 0;
        const leaving = move?.leaving === j;
        return (
          <li className={v < -1e-9 ? "is-negative" : undefined} key={j}>
            <span className="spx-bar-name"><strong>{VARIABLE_INFO[j].symbol}</strong> {VARIABLE_INFO[j].name}</span>
            <span className="spx-bar-role">
              {role}
              {move && rate !== 0 && `・θ 1あたり ${rate > 0 ? "+" : ""}${fracText(move.direction[j])}`}
              {leaving && "・先に0になる"}
            </span>
            <span aria-hidden="true" className="spx-bar-track">
              <span className="spx-bar-zero" style={{ left: `${zero}%` }} />
              <span className={`spx-bar-fill${move?.entering === j ? " is-entering" : ""}`} style={{ left: `${left}%`, width: `${width}%` }} />
            </span>
            <span className="spx-bar-value">{fixed(v)}</span>
          </li>
        );
      })}
    </ul>
  );
}

function EdgePreview({
  state, move, scale, bounds,
}: { state: BasisState; move: EdgeMove; scale: Scale; bounds: Bounds }) {
  const start = state.point.map(value);
  const far = valuesAlong(state, move, sliderMax(move));
  // A stop outside the plot (x1 = 13 on the x1 axis) is listed in the readout, not drawn.
  const stops = move.rows
    .filter((r) => r.ratio)
    .map((r) => ({ variable: r.variable, at: valuesAlong(state, move, value(r.ratio!)) }))
    .filter(({ at }) => !outside([at[0], at[1]], bounds));
  return (
    <g>
      <line className="spx-ray" x1={scale.px(start[0])} x2={scale.px(far[0])} y1={scale.py(start[1])} y2={scale.py(far[1])} />
      {stops.map(({ variable, at }) => (
        <g className={variable === move.leaving ? "spx-stop is-first" : "spx-stop"} key={variable}>
          <circle cx={scale.px(at[0])} cy={scale.py(at[1])} r={5} />
          <StopLabel at={[at[0], at[1]]} scale={scale} text={`${symbol(variable)}=0`} />
        </g>
      ))}
    </g>
  );
}

/**
 * The vertex labels sit right of (0, y), below-left of (6, 0) and right of (4, 3), so a stop label
 * goes right on the x2 axis, below-right on the x1 axis, and below elsewhere.
 */
function StopLabel({ at, text, scale }: { at: readonly [number, number]; text: string; scale: Scale }) {
  const [x, y] = at;
  const place = x < 0.5
    ? { anchor: "start" as const, dx: 12, dy: 5 }
    : y < 0.5
      ? { anchor: "start" as const, dx: 8, dy: 30 }
      : { anchor: "middle" as const, dx: 0, dy: 26 };
  return (
    <text className="ex-label" textAnchor={place.anchor} x={scale.px(x) + place.dx} y={scale.py(y) + place.dy}>
      {text}
    </text>
  );
}

function Axes({ scale, viewport }: { scale: Scale; viewport: { width: number; height: number } }) {
  return (
    <g className="ex-axes">
      <line x1={scale.px(0)} x2={scale.px(0)} y1={0} y2={viewport.height} />
      <line x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
      <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 8}>x₁ 食パン</text>
      <text className="ex-axis-name" x={scale.px(0) + 8} y={18}>x₂ クロワッサン</text>
    </g>
  );
}

function ConstraintLine({
  constraint, scale, viewport,
}: { constraint: (typeof CONSTRAINTS)[number]; scale: Scale; viewport: { bounds: Bounds } }) {
  const line = levelLine(constraint.a, constraint.b, viewport.bounds);
  if (!line) return null;
  const [from, to] = line;
  // Short labels placed outside the polygon, away from the vertex and stop labels.
  const flour = constraint.a[0] > constraint.a[1];
  const anchor = flour ? [1.75, 7.4] : [6.9, 2.45];
  return (
    <g>
      <line className="ex-constraint" x1={scale.px(from[0])} x2={scale.px(to[0])} y1={scale.py(from[1])} y2={scale.py(to[1])} />
      <text className="ex-label" x={scale.px(anchor[0])} y={scale.py(anchor[1])}>{constraint.label}</text>
    </g>
  );
}

function VertexLabels({ scale }: { scale: Scale }) {
  const labels: { at: readonly [number, number]; text: string; dx: number; dy: number; anchor: "start" | "end" }[] = [
    { at: [0, 0], text: "売上 0", dx: 10, dy: 30, anchor: "start" },
    { at: [6, 0], text: "売上 18", dx: -8, dy: 30, anchor: "end" },
    { at: [4, 3], text: "売上 24", dx: 12, dy: -6, anchor: "start" },
    { at: [0, 13 / 3], text: "売上 52/3", dx: 12, dy: 30, anchor: "start" },
  ];
  return (
    <g>
      {labels.map(({ at, text, dx, dy, anchor }) => (
        <text className="ex-label" key={text} textAnchor={anchor} x={scale.px(at[0]) + dx} y={scale.py(at[1]) + dy}>{text}</text>
      ))}
    </g>
  );
}

const clampTo = (v: number, low: number, high: number) => Math.min(high, Math.max(low, v));
const outside = (p: readonly [number, number], b: Bounds) => p[0] < b.xMin || p[0] > b.xMax || p[1] < b.yMin || p[1] > b.yMax;
