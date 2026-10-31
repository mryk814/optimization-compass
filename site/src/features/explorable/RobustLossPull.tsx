import { useMemo, useState } from "react";

import { Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { LiveMath, mi, mn, mo, paren, row } from "./mathml";
import { articleClosedForm, compareFits, type ConstantFit } from "./math/robustConstant";
import { useStageViewport } from "./svg";

const ID = "robust-loss-pull";
const M_RANGE: readonly [number, number] = [0, 100];
const DELTA_RANGE: readonly [number, number] = [0.25, 10];
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
const NAMES = ["観測1", "観測2", "観測3", "観測4"] as const;

/** Smallest 1, 2, 5, 10 times a power of ten that is at least `value`. */
function niceCeil(value: number): number {
  const power = 10 ** Math.floor(Math.log10(value));
  return [1, 2, 5, 10].map((k) => k * power).find((candidate) => candidate >= value - 1e-12) ?? 10 * power;
}

export default function RobustLossPull() {
  const [m, setM] = useState(10);
  const [delta, setDelta] = useState(1);
  const fits = useMemo(() => compareFits(m, delta), [m, delta]);
  const { squared, huber } = fits;
  const same = Math.abs(squared.x - huber.x) < 1e-9;
  const summary = [
    `観測は0、0、0と最後の${fmt(m, 0)}。`,
    `二乗損失の当てはめは${fmt(squared.x, 3)}で、最後の観測の傾きは${fmt(squared.slopes[3], 2)}です。`,
    `Huber損失（尺度${fmt(delta, 2)}）の当てはめは${fmt(huber.x, 3)}で、最後の観測の傾きは${fmt(huber.slopes[3], 2)}です。`,
    same ? "すべての残差が二乗の領域に入り、二つは一致します。" : "Huberの方が最後の観測に引っ張られません。",
  ].join("");

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(m, 0)}
            label="最後の観測の値 m"
            max={M_RANGE[1]}
            min={M_RANGE[0]}
            onChange={setM}
            step={1}
            value={m}
          />
          <Slider
            display={fmt(delta, 2)}
            label="Huberの尺度 δ"
            max={DELTA_RANGE[1]}
            min={DELTA_RANGE[0]}
            onChange={setDelta}
            step={0.25}
            value={delta}
          />
        </>
      }
      id={ID}
      readout={<Readout delta={delta} huber={huber} m={m} same={same} squared={squared} />}
      stage={
        <div className="ex-twin">
          <FitPanel delta={delta} huber={huber} m={m} squared={squared} />
          <SlopePanel delta={delta} huber={huber} squared={squared} />
        </div>
      }
      summary={summary}
    />
  );
}

interface PanelProps {
  squared: ConstantFit;
  huber: ConstantFit;
  delta: number;
}

function FitPanel({ squared, huber, m }: PanelProps & { m: number }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.8);
  const width = viewport.width;
  const height = Math.max(240, viewport.height);
  const left = 40, right = width - 14, top = 18, bottom = height - 30;
  const yMax = Math.max(m, 4) * 1.1;
  const yMin = -0.1 * yMax;
  const px = (i: number) => left + 18 + (i / 3) * (right - left - 36);
  const py = (y: number) => bottom - ((y - yMin) / (yMax - yMin)) * (bottom - top);
  const step = niceCeil(yMax / 4);
  const ticks: number[] = [];
  for (let t = 0; t <= yMax; t += step) ticks.push(t);
  const ys = [0, 0, 0, m];
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">観測と当てはめ</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg
          aria-label={`観測0、0、0、${fmt(m, 0)}と、二乗の当てはめ${fmt(squared.x, 2)}、Huberの当てはめ${fmt(huber.x, 2)}`}
          className="ex-svg"
          role="img"
          viewBox={`0 0 ${width} ${height}`}
        >
          <rect className="ex-ground" height={height} width={width} />
          <g className="ex-axes">
            {ticks.map((t) => (
              <g key={t}>
                <line x1={left} x2={right} y1={py(t)} y2={py(t)} />
                <text textAnchor="end" x={left - 6} y={py(t) + 4}>{t}</text>
              </g>
            ))}
            {NAMES.map((name, i) => (
              <text key={name} textAnchor="middle" x={px(i)} y={height - 8}>{name}</text>
            ))}
          </g>
          <line className="rb-fit-squared" x1={left} x2={right} y1={py(squared.x)} y2={py(squared.x)} />
          <line className="rb-fit-huber" x1={left} x2={right} y1={py(huber.x)} y2={py(huber.x)} />
          {ys.map((y, i) => (
            <circle className="ex-observation" cx={px(i)} cy={py(y)} key={NAMES[i]} r={i === 3 ? 8 : 6} />
          ))}
          <text className="ex-label rb-label-squared" x={left + 4} y={py(squared.x) - 7}>二乗 {fmt(squared.x, 2)}</text>
          <text className="ex-label rb-label-huber" textAnchor="end" x={right - 2} y={py(huber.x) + 17}>Huber {fmt(huber.x, 2)}</text>
        </svg>
      </div>
      <p className="ex-hint">青緑の点が観測、紺の線が二乗損失、橙の線がHuber損失の当てはめです。</p>
    </figure>
  );
}

function SlopePanel({ squared, huber, delta }: PanelProps) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.8);
  const width = viewport.width;
  const height = Math.max(240, viewport.height);
  const left = 44, right = width - 14, top = 18, bottom = height - 30;
  const extent = niceCeil(Math.max(...squared.slopes.map(Math.abs), ...huber.slopes.map(Math.abs), delta) * 1.05);
  const py = (v: number) => bottom - ((v + extent) / (2 * extent)) * (bottom - top);
  const group = (right - left) / 4;
  const barWidth = Math.min(22, group * 0.36);
  const centre = (i: number) => left + group * (i + 0.5);
  const ticks = [-extent, 0, extent];
  const bar = (value: number, x: number, className: string) => (
    <rect
      className={className}
      height={Math.max(Math.abs(py(value) - py(0)), 1)}
      width={barWidth}
      x={x}
      y={Math.min(py(value), py(0))}
    />
  );
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">損失の傾き（影響）</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg
          aria-label={`各観測が当てはめを引く力。二乗の最後の観測は${fmt(squared.slopes[3], 2)}、Huberは${fmt(huber.slopes[3], 2)}`}
          className="ex-svg"
          role="img"
          viewBox={`0 0 ${width} ${height}`}
        >
          <rect className="ex-ground" height={height} width={width} />
          <g className="ex-axes">
            {ticks.map((t) => (
              <g key={t}>
                <line x1={left} x2={right} y1={py(t)} y2={py(t)} />
                <text textAnchor="end" x={left - 6} y={py(t) + 4}>{t}</text>
              </g>
            ))}
            {NAMES.map((name, i) => (
              <text key={name} textAnchor="middle" x={centre(i)} y={height - 8}>{name}</text>
            ))}
          </g>
          <line className="rb-cap" x1={left} x2={right} y1={py(delta)} y2={py(delta)} />
          <line className="rb-cap" x1={left} x2={right} y1={py(-delta)} y2={py(-delta)} />
          <text className="ex-label rb-label-huber" x={left + 4} y={top + 12}>破線：Huberの上限 ±δ = {fmt(delta, 2)}</text>
          {squared.slopes.map((value, i) => (
            <g key={NAMES[i]}>
              {bar(value, centre(i) - barWidth - 1, "rb-bar-squared")}
              {bar(huber.slopes[i], centre(i) + 1, "rb-bar-huber")}
            </g>
          ))}
        </svg>
      </div>
      <p className="ex-hint">
        棒の高さは、その観測が当てはめを動かす力（損失の傾き）です。
        <span className="rb-key rb-key-squared">紺は二乗</span>
        <span className="rb-key rb-key-huber">橙はHuber</span>
        です。
      </p>
    </figure>
  );
}

interface ReadoutProps extends PanelProps {
  m: number;
  same: boolean;
}

function Readout({ squared, huber, delta, m, same }: ReadoutProps) {
  const closed = articleClosedForm(m, delta);
  const rows: Array<[string, ConstantFit]> = [["二乗", squared], [`Huber（δ=${fmt(delta, 2)}）`, huber]];
  return (
    <>
      <section aria-label="Huberの推定値の式" className="ex-equation">
        <p className="ex-eyebrow">この配置の推定値（三つの0と一つの m）</p>
        <LiveMath
          block
          label={`推定値は m割る4と、δ割る3の小さい方。${fmt(closed, 3)}`}
          markup={row(
            mi("x"), mo("="), mi("min"),
            paren(mn(fmt(m / 4, 3)), mo(","), mn(fmt(delta / 3, 3))),
            mo("="), mn(fmt(closed, 3)),
          )}
        />
      </section>
      <section aria-label="損失ごとの結果" className="rb-scroll">
        <table className="ex-table rb-table">
          <thead>
            <tr>
              <th scope="col">損失</th>
              <th scope="col">推定 x</th>
              <th scope="col">0への残差</th>
              <th scope="col">mへの残差</th>
              <th scope="col">mの傾き</th>
              <th scope="col">目的値</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([name, fit]) => (
              <tr key={name}>
                <th scope="row">{name}</th>
                <td>{fmt(fit.x, 3)}</td>
                <td>{fmt(fit.residuals[0], 3)}</td>
                <td>{fmt(fit.residuals[3], 3)}</td>
                <td>{fmt(fit.slopes[3], 3)}</td>
                <td>{fmt(fit.objective, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className={`ex-verdict ${same ? "ex-tone-good" : "ex-tone-swing"}`}>
        {same
          ? `すべての残差が尺度 δ=${fmt(delta, 2)} 以内で、Huberは二乗と同じ ${fmt(squared.x, 3)} になります。`
          : `最後の観測を除けば推定値は0です。二乗は ${fmt(squared.x, 3)}、Huberは ${fmt(huber.x, 3)} まで引っ張られ、Huberでは最後の観測の傾きが ${fmt(huber.slopes[3], 2)} にとどまります。`}
      </p>
      <p className="ex-hint">目的値の大小で損失を比べることはできません。傾きの合計は二乗・Huberとも0です。</p>
    </>
  );
}
