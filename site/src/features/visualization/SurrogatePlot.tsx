import type { SurrogateFrame } from "../../contracts/surrogate-uncertainty";

export function SurrogatePlot({
  frame,
  visibleLayers,
}: {
  frame: SurrogateFrame;
  visibleLayers: ReadonlySet<string>;
}) {
  const points = frame.predictive_summary;
  const minY = Math.min(
    ...points.flatMap((point) => [point.lower, point.true_value]),
  );
  const maxY = Math.max(
    ...points.flatMap((point) => [point.upper, point.true_value]),
  );
  const x = (value: number) => 54 + ((value + 3) / 6) * 612;
  const y = (value: number) =>
    258 - ((value - minY) / (maxY - minY || 1)) * 212;
  const acquisitionMax = Math.max(
    ...points.map((point) => point.acquisition),
    1e-9,
  );
  const line = (values: (point: (typeof points)[number]) => number) =>
    points
      .map(
        (point, index) =>
          `${index ? "L" : "M"}${x(point.x).toFixed(1)},${y(values(point)).toFixed(1)}`,
      )
      .join(" ");
  const band = `${points.map((point, index) => `${index ? "L" : "M"}${x(point.x).toFixed(1)},${y(point.upper).toFixed(1)}`).join(" ")} ${[
    ...points,
  ]
    .reverse()
    .map((point) => `L${x(point.x).toFixed(1)},${y(point.lower).toFixed(1)}`)
    .join(" ")} Z`;
  return (
    <figure className="bo-figure">
      <svg
        viewBox="0 0 720 390"
        role="img"
        aria-labelledby="bo-plot-title bo-plot-desc"
      >
        <title id="bo-plot-title">
          surrogateの平均、不確実性、観測、Expected Improvement
        </title>
        <desc id="bo-plot-desc">
          上段は教材用の真の目的関数を破線、surrogateの予測を実線、不確実性を帯で示します。下段はacquisition値で、次候補は縦線です。
        </desc>
        <rect
          className="bo-chart-bg"
          x="38"
          y="24"
          width="644"
          height="338"
          rx="12"
        />
        {visibleLayers.has("posterior_uncertainty") && <path className="bo-band" d={band} />}
        <path className="bo-truth" d={line((point) => point.true_value)} />
        {visibleLayers.has("posterior_mean") && <path className="bo-mean" d={line((point) => point.mean)} />}
        {visibleLayers.has("observations") && frame.observations.map((point, index) => (
          <circle
            className="bo-observation"
            key={`${point.x}:${index}`}
            cx={x(point.x)}
            cy={y(point.observed_value)}
            r="5"
          />
        ))}
        {visibleLayers.has("selected_candidate") && frame.selected_point !== null && (
          <line
            className="bo-next"
            x1={x(frame.selected_point)}
            x2={x(frame.selected_point)}
            y1="24"
            y2="362"
          />
        )}
        {visibleLayers.has("expected_improvement") && points.map((point) => (
          <line
            className="bo-ei"
            key={point.x}
            x1={x(point.x)}
            x2={x(point.x)}
            y1="350"
            y2={350 - (point.acquisition / acquisitionMax) * 62}
          />
        ))}
        <text x="54" y="46">
          目的関数 / surrogate
        </text>
        <text x="54" y="286">
          Expected Improvement
        </text>
        <g className="bo-legend">
          <text x="430" y="46">
          ― surrogate平均
          </text>
          <text x="430" y="64">
            ┄ 真の目的関数 (教材のみ)
          </text>
          <text x="430" y="82">
            ● 観測値
          </text>
        </g>
      </svg>
      <figcaption>
         surrogateの予測（実線）と教材用の真の目的関数（破線）は別物です。
      </figcaption>
    </figure>
  );
}
