import type { AlgorithmTrace, TraceMetric } from "../../contracts/trace";

const plot = { left: 48, right: 712, top: 24, bottom: 178 } as const;

export function GenericMetricHistory({
  traces,
  evaluation,
  budget,
  labels = {},
  metricIds,
}: {
  traces: AlgorithmTrace[];
  evaluation: number;
  budget: number;
  labels?: Record<string, string>;
  metricIds?: string[];
}) {
  const ids = metricIds ?? orderedMetricIds(traces);
  return (
    <section className="metric-history" aria-label="指標の履歴">
      <header>
        <h2>指標の履歴 (Metric history)</h2>
        <p>同じ評価回数 (oracle evaluation) で、目的・状態・制約診断を揃えて読みます。</p>
      </header>
      <div className="metric-history-grid">
        {ids.map((metricId) => (
          <MetricPanel
            budget={budget}
            evaluation={evaluation}
            key={metricId}
            labels={labels}
            metricId={metricId}
            traces={traces}
          />
        ))}
      </div>
    </section>
  );
}

function MetricPanel({
  traces,
  metricId,
  evaluation,
  budget,
  labels,
}: {
  traces: AlgorithmTrace[];
  metricId: string;
  evaluation: number;
  budget: number;
  labels: Record<string, string>;
}) {
  const series = traces.map((trace) => ({
    trace,
    values: trace.frames.flatMap((frame) => {
      const metric = frame.metrics.find((candidate) => candidate.metric_id === metricId);
      return metric ? [{ evaluation: frame.oracle_evaluations, metric }] : [];
    }),
  }));
  const sample = series.flatMap((item) => item.values)[0]?.metric;
  if (!sample) return null;
  const logScale = metricId !== "jacobian_rank" && series
    .flatMap((item) => item.values)
    .every((item) => item.metric.value >= 0);
  const transform = (value: number) => logScale ? Math.log10(Math.max(value, 1e-12)) : value;
  const transformed = series.flatMap((item) => item.values.map((value) => transform(value.metric.value)));
  const minimum = Math.min(...transformed);
  const maximum = Math.max(...transformed);
  const span = Math.max(maximum - minimum, 1e-9);
  const x = (value: number) => plot.left + (value / budget) * (plot.right - plot.left);
  const y = (value: number) => plot.bottom - ((transform(value) - minimum) / span) * (plot.bottom - plot.top);
  return (
    <figure className="metric-history-panel explanatory-figure">
      <h3>{sample.label_ja} <small>{sample.label_en}</small></h3>
      <svg viewBox="0 0 760 204" role="img" aria-label={`${sample.label_ja}を評価回数ごとに比較`}>
        <rect className="objective-background" height="204" rx="8" width="760" x="0" y="0" />
        <line className="plot-axis" x1={plot.left} x2={plot.right} y1={plot.bottom} y2={plot.bottom} />
        <line className="plot-axis" x1={plot.left} x2={plot.left} y1={plot.top} y2={plot.bottom} />
        <line className="history-cursor" x1={x(evaluation)} x2={x(evaluation)} y1={plot.top} y2={plot.bottom} />
        {series.map(({ trace, values }, index) => {
          const visible = values.filter((item) => item.evaluation <= evaluation);
          return (
            <g className={`history-series history-${index}`} key={trace.trace_id}>
              <polyline points={visible.map((item) => `${x(item.evaluation)},${y(item.metric.value)}`).join(" ")} />
              <text x={plot.right - 205} y={plot.top + 14 + index * 15}>
                {symbol(index)} {labels[trace.trace_id] ?? trace.method_id}
              </text>
            </g>
          );
        })}
        <text className="plot-axis-label" x={plot.right - 104} y={plot.bottom - 7}>評価回数</text>
        <text className="plot-axis-label" x={plot.left + 6} y={plot.top + 10}>{logScale ? "log₁₀スケール" : sample.unit ?? "値"}</text>
      </svg>
      <details className="text-alternative" open>
        <summary>評価 {evaluation}回時点の値</summary>
        <ul>
          {series.map(({ trace, values }) => {
            const latest = values.filter((item) => item.evaluation <= evaluation).at(-1);
            return (
              <li key={trace.trace_id}>
                <strong>{labels[trace.trace_id] ?? trace.method_id}</strong>: {formatMetric(latest?.metric)}
              </li>
            );
          })}
        </ul>
      </details>
    </figure>
  );
}

function orderedMetricIds(traces: AlgorithmTrace[]): string[] {
  const ids: string[] = [];
  for (const trace of traces) {
    for (const frame of trace.frames) {
      for (const metric of frame.metrics) {
        if (!ids.includes(metric.metric_id)) ids.push(metric.metric_id);
      }
    }
  }
  return ids;
}

function formatMetric(metric: TraceMetric | undefined): string {
  if (!metric) return "未評価";
  return `${metric.value.toPrecision(5)}${metric.unit ? ` ${metric.unit}` : ""}`;
}

function symbol(index: number): string {
  return index === 0 ? "●" : index === 1 ? "■" : index === 2 ? "▲" : "◆";
}
