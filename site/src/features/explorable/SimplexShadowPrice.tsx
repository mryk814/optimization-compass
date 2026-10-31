import { useMemo, useState } from "react";

import { Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import type { Bounds } from "./math/contours";
import { levelLine } from "./math/lp2d";
import {
  BASE, BASE_FLOUR, BASE_PRICE, BASE_RANGE, BUTTER, estimateAt, flourAt, FLOUR_MAX, FLOUR_MIN, inRange,
  optimumAt, polygonAt, readingAt, SLIDER_MAX, SLIDER_MIN, sliderIndex, sortedBasis,
  type FlourReading,
} from "./math/shadowPrice";
import { frac, fracText, less, value, VARIABLE_INFO, type Fraction } from "./math/simplex";
import { frac as mfrac, LiveMath, mn, mo, row, tint } from "./mathml";
import { makeScale, polylinePath, useStageViewport, type Scale } from "./svg";

const ID = "simplex-shadow-price";

/** Left panel: the (x1, x2) plane. The flour line can leave the frame; the polygon never does. */
const PLANE: Bounds = { xMin: -1.2, xMax: 15.6, yMin: -1.7, yMax: 6.4 };
const PLANE_ASPECT = (PLANE.yMax - PLANE.yMin) / (PLANE.xMax - PLANE.xMin);
/** Right panel: flour stock b against the best sales. */
const CHART: Bounds = { xMin: -2.5, xMax: 47, yMin: -14, yMax: 54 };
const CHART_ASPECT = 0.8;

/** The special stocks the reader can jump to; every one is a multiple of 1/3. */
const PRESETS: readonly Fraction[] = [frac(26, 3), frac(18), frac(19), frac(39), frac(40)];

const symbol = (j: number) => VARIABLE_INFO[j].symbol;
const basisText = (reading: FlourReading) => `{${sortedBasis(reading.state).map(symbol).join(", ")}}`;
const pointText = (reading: FlourReading) => `(${reading.state.point.map(fracText).join(", ")})`;
/** "26/3 ≈ 8.67": the exact fraction first, the decimal only as a reading aid. */
const approx = (f: Fraction) => (f.d === 1 ? fracText(f) : `${fracText(f)} ≈ ${value(f).toFixed(2)}`);
const same = (a: Fraction, b: Fraction) => a.n === b.n && a.d === b.d;

const RANGE_LOW = BASE_RANGE.low!;
const RANGE_HIGH = BASE_RANGE.high!;
const RANGE_TEXT = `${fracText(RANGE_LOW)} ≤ b ≤ ${fracText(RANGE_HIGH)}`;

/** The optimum for every slider step, solved once with the exact solver and only drawn here. */
const CURVE = (() => {
  const points: [number, number][] = [];
  for (let k = SLIDER_MIN; k <= SLIDER_MAX; k += 1) {
    const flour = flourAt(k);
    points.push([value(flour), value(optimumAt(flour).sales)]);
  }
  return points;
})();

/** Where the optimal vertex goes as b grows: it turns at the two ends of the valid range. */
const VERTEX_PATH: [number, number][] = [FLOUR_MIN, RANGE_LOW, RANGE_HIGH].map((flour) => {
  const point = optimumAt(flour).point;
  return [value(point[0]), value(point[1])];
});

function verdictText(reading: FlourReading): string {
  const b = fracText(reading.flour);
  const actual = approx(reading.state.sales);
  const estimate = approx(reading.estimate);
  if (reading.sameBasis) {
    const edge = same(reading.flour, RANGE_LOW) || same(reading.flour, RANGE_HIGH) ? "（範囲の端）" : "";
    return `b=${b}${edge}では最適な基底が ${basisText(reading)} のままで、実際の最適値 ${actual} と 5/7 の見積もり ${estimate} が一致します。`;
  }
  const side = less(reading.flour, RANGE_LOW) ? "下" : "上";
  const why = side === "上"
    ? "小麦粉が余り、売上はバターで決まります"
    : "食パンを焼かない頂点で、小麦粉の値段は 5/7 より高くなります";
  return `b=${b} は範囲 ${RANGE_TEXT} の${side}の外です。最適な基底は ${basisText(reading)} に変わり（${why}）、実際の最適値は ${actual}、頂点は ${pointText(reading)} です。5/7 の見積もり ${estimate} は ${approx(reading.gap)} だけ大きすぎます。`;
}

export default function SimplexShadowPrice() {
  const [index, setIndex] = useState(sliderIndex(BASE_FLOUR));
  const flour = flourAt(index);
  const reading = useMemo(() => readingAt(flour), [flour]);
  const inside = inRange(BASE_RANGE, flour);
  const verdict = verdictText(reading);
  const tone = inside ? "ex-tone-good" : "ex-tone-swing";
  const summary = `小麦粉の在庫 b は ${approx(flour)}。${verdict}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={approx(flour)}
            hint={`6 から 45 まで 1/3 刻みです。矢印キーで 1/3 ずつ動きます。値段 5/7 を使ってよい範囲は ${RANGE_TEXT} です。`}
            label="小麦粉の在庫 b"
            max={SLIDER_MAX}
            min={SLIDER_MIN}
            onChange={setIndex}
            step={1}
            value={index}
            valueText={`小麦粉の在庫 ${approx(flour)}`}
          />
          <fieldset className="ex-choice sps-presets">
            <legend>特別な在庫へ移る</legend>
            <div>
              {PRESETS.map((preset) => (
                <button
                  aria-pressed={same(preset, flour)}
                  className={same(preset, flour) ? "is-selected" : undefined}
                  key={fracText(preset)}
                  onClick={() => setIndex(sliderIndex(preset))}
                  type="button"
                >
                  b = {fracText(preset)}
                </button>
              ))}
            </div>
          </fieldset>
        </>
      }
      id={ID}
      readout={<Readout inside={inside} reading={reading} tone={tone} verdict={verdict} />}
      stage={
        <div className="ex-twin">
          <figure className="ex-panel">
            <figcaption className="ex-panel-title">頂点と辺</figcaption>
            <PlanePanel reading={reading} />
          </figure>
          <figure className="ex-panel">
            <figcaption className="ex-panel-title">見積もりと実際</figcaption>
            <ChartPanel reading={reading} />
          </figure>
        </div>
      }
      summary={summary}
    />
  );
}

function PlanePanel({ reading }: { reading: FlourReading }) {
  const { ref, viewport } = useStageViewport(PLANE, PLANE_ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const polygon = polygonAt(reading.flour);
  // The flour line stops at the x₁ axis so that it never crosses the axis name below it.
  const flourLine = levelLine([3, 2], value(reading.flour), { ...viewport.bounds, yMin: 0 });
  const butterLine = levelLine([1, 3], value(BUTTER), { ...viewport.bounds, yMin: 0 });
  const [x, y] = reading.state.point.map(value);
  const [baseX, baseY] = BASE.point.map(value);
  return (
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
        <rect className="ex-ground" height={viewport.height} width={viewport.width} />
        <g className="ex-axes">
          <line x1={scale.px(0)} x2={scale.px(0)} y1={0} y2={viewport.height} />
          <line x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
          <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={scale.py(0) + 24}>x₁ 食パン</text>
          <text className="ex-axis-name" x={scale.px(0) + 8} y={20}>x₂ クロワッサン</text>
        </g>
        <path className="ex-feasible" d={polylinePath(polygon, scale) + "Z"} />
        {butterLine && (
          <line className="ex-constraint" x1={scale.px(butterLine[0][0])} x2={scale.px(butterLine[1][0])} y1={scale.py(butterLine[0][1])} y2={scale.py(butterLine[1][1])} />
        )}
        <text className="ex-label" x={scale.px(8)} y={scale.py(2.9)}>バター 13</text>
        {flourLine && (
          <line className="sps-flour" x1={scale.px(flourLine[0][0])} x2={scale.px(flourLine[1][0])} y1={scale.py(flourLine[0][1])} y2={scale.py(flourLine[1][1])} />
        )}
        <text className="ex-label sps-flour-label" textAnchor="end" x={viewport.width - 8} y={42}>
          橙：小麦粉 b={fracText(reading.flour)}
        </text>
        <path className="sps-path" d={polylinePath(VERTEX_PATH, scale)} />
        <circle className="sps-base" cx={scale.px(baseX)} cy={scale.py(baseY)} r={7} />
        <text className="ex-label" textAnchor="end" x={scale.px(baseX) - 10} y={scale.py(baseY) + 22}>b=18: (4, 3)</text>
        <circle className="ex-head" cx={scale.px(x)} cy={scale.py(y)} r={8} />
        <text
          className="ex-label ex-label-strong"
          textAnchor={x < 3 ? "start" : x > 10 ? "end" : "middle"}
          x={scale.px(x) + (x < 3 ? 14 : x > 10 ? 8 : 0)}
          y={scale.py(y) + (x < 3 && y > 3.5 ? 5 : -16)}
        >
          {x < 3 && y > 3.5 ? "" : "最適 "}({fracText(reading.state.point[0])}, {fracText(reading.state.point[1])})
        </text>
      </svg>
    </div>
  );
}

function ChartPanel({ reading }: { reading: FlourReading }) {
  const { ref, viewport } = useStageViewport(CHART, CHART_ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const b = value(reading.flour);
  const actual = value(reading.state.sales);
  const estimate = value(reading.estimate);
  const left = scale.px(value(RANGE_LOW));
  const right = scale.px(value(RANGE_HIGH));
  const estimateLine: [number, number][] = [FLOUR_MIN, FLOUR_MAX].map((f) => [value(f), value(estimateAt(f))]);
  return (
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
        <rect className="ex-ground" height={viewport.height} width={viewport.width} />
        <rect className="sps-range" height={scale.py(0) - scale.py(CHART.yMax)} width={right - left} x={left} y={scale.py(CHART.yMax)} />
        <text className="ex-label sps-range-label" textAnchor="start" x={left + 8} y={scale.py(0) - 10}>見積もれる範囲</text>
        <g className="ex-axes">
          <line x1={scale.px(CHART.xMin)} x2={scale.px(CHART.xMax)} y1={scale.py(0)} y2={scale.py(0)} />
          <line x1={scale.px(CHART.xMin)} x2={scale.px(CHART.xMin)} y1={0} y2={scale.py(0)} />
          {[0, 10, 20, 30, 40].map((tick) => (
            <text key={tick} textAnchor="end" x={scale.px(CHART.xMin) - 4} y={scale.py(tick) + 5}>{tick}</text>
          ))}
          {[[value(RANGE_LOW), fracText(RANGE_LOW)], [18, "18"], [value(RANGE_HIGH), fracText(RANGE_HIGH)]].map(([at, text]) => (
            <text key={text} textAnchor="middle" x={scale.px(at as number)} y={scale.py(0) + 20}>{text}</text>
          ))}
          <text className="ex-axis-name" textAnchor="end" x={viewport.width - 6} y={scale.py(0) + 40}>小麦粉の在庫 b</text>
        </g>
        <path className="sps-estimate" d={polylinePath(estimateLine, scale)} />
        <text className="ex-label sps-estimate-label" textAnchor="end" x={scale.px(value(FLOUR_MAX)) - 2} y={scale.py(value(estimateAt(FLOUR_MAX))) - 10}>
          5/7 の見積もり
        </text>
        <path className="sps-true" d={polylinePath(CURVE, scale)} />
        <text className="ex-label sps-true-label" textAnchor="end" x={scale.px(value(FLOUR_MAX)) - 2} y={scale.py(39) + 24}>実際の最適値</text>
        <line className="sps-now" x1={scale.px(b)} x2={scale.px(b)} y1={scale.py(0)} y2={scale.py(CHART.yMax - 6)} />
        {value(reading.gap) > 0 && (
          <line className="sps-gap" x1={scale.px(b)} x2={scale.px(b)} y1={scale.py(actual)} y2={scale.py(estimate)} />
        )}
        <circle className="sps-estimate-dot" cx={scale.px(b)} cy={scale.py(estimate)} r={7} />
        <circle className="sps-true-dot" cx={scale.px(b)} cy={scale.py(actual)} r={6} />
      </svg>
    </div>
  );
}

/** A fraction as MathML: stacked when it is not an integer. */
function num(f: Fraction): string {
  const body = f.d === 1 ? mn(String(Math.abs(f.n))) : mfrac(mn(String(Math.abs(f.n))), mn(String(f.d)));
  return f.n < 0 ? row(mo("−"), body) : body;
}

function Readout({
  reading, verdict, tone, inside,
}: { reading: FlourReading; verdict: string; tone: string; inside: boolean }) {
  const [u, v] = reading.state.prices;
  const markup = row(
    num(u), mo("×"), num(reading.flour), mo("+"), num(v), mo("×"), mn(String(BUTTER.n)), mo("="),
    tint("teal", num(reading.certificate)),
  );
  const label = `${fracText(u)} かける ${fracText(reading.flour)} たす ${fracText(v)} かける 13 は ${fracText(reading.certificate)}`;
  return (
    <>
      <table className="ex-table">
        <thead>
          <tr>
            <th scope="col">小麦粉 b</th>
            <th scope="col">最適な基底</th>
            <th scope="col">最適な頂点 (x₁, x₂)</th>
            <th scope="col">実際の最適値</th>
            <th scope="col">5/7 の見積もり</th>
          </tr>
        </thead>
        <tbody>
          <tr className={inside ? "ex-row-best" : undefined}>
            <th scope="row">{fracText(reading.flour)}</th>
            <td>{basisText(reading)}</td>
            <td>{pointText(reading)}</td>
            <td>{fracText(reading.state.sales)}</td>
            <td>{fracText(reading.estimate)}</td>
          </tr>
        </tbody>
      </table>
      <section aria-label="この在庫での証明書" className="ex-equation">
        <p className="ex-eyebrow">
          いまの最適な基底の双対値（小麦粉 {fracText(u)}、バター {fracText(v)}）で在庫を評価した値が、実際の最適値と一致する
        </p>
        <LiveMath block label={label} markup={markup} />
        <p className="ex-hint">
          {fracText(u)} は、ソルバーが出したいまの基底の小麦粉の値段です。{fracText(BASE_PRICE)} は b=18 の基底の値段で、見積もりはこれを使い続けた直線です。
        </p>
      </section>
      <p className={`ex-verdict ${tone}`}>{verdict}</p>
    </>
  );
}
