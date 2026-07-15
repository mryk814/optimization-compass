import { useMemo, useState } from "react";

import type { FeasibleRegionArtifact, ParetoFrontArtifact } from "../../contracts/learning-slices";

const SIZE = 360;
const LEFT = 70;
const TOP = 38;

export function FeasibleRegionRenderer({ artifact }: { artifact: FeasibleRegionArtifact }) {
  const primary = artifact.paths.find((path) => path.role === "constraint_aware")!;
  const failure = artifact.paths.find((path) => path.role === "unconstrained_failure")!;
  const [step, setStep] = useState(primary.steps.length - 1);
  const current = primary.steps[step];
  const x = (value: number) => LEFT + ((value - artifact.bounds.x[0]) / (artifact.bounds.x[1] - artifact.bounds.x[0])) * SIZE;
  const y = (value: number) => TOP + SIZE - ((value - artifact.bounds.y[0]) / (artifact.bounds.y[1] - artifact.bounds.y[0])) * SIZE;
  const scale = SIZE / (artifact.bounds.x[1] - artifact.bounds.x[0]);
  const path = (points: [number, number][]) => points.map((point, index) => `${index === 0 ? "M" : "L"}${x(point[0])},${y(point[1])}`).join(" ");
  const primaryPoints = primary.steps.slice(0, step + 1).map((item) => item.point);
  return (
    <section className="learning-renderer" aria-labelledby="feasible-heading">
      <div className="learning-renderer-heading"><div><p className="eyebrow">feasible_region · 1.0.0</p><h2 id="feasible-heading">目的値と実行可能性を同時に読む</h2></div><strong>{artifact.objective_direction} ↓</strong></div>
      <div className="learning-plot-layout">
        <svg aria-label={artifact.text_alternative_ja} className="learning-plot" role="img" viewBox="0 0 520 440">
          <defs><clipPath id="feasible-clip"><rect height={SIZE} width={SIZE} x={LEFT} y={TOP} /></clipPath></defs>
          <rect className="plot-background" height={SIZE} width={SIZE} x={LEFT} y={TOP} />
          <g clipPath="url(#feasible-clip)">
            {artifact.contour_values.map((value) => <circle className="objective-contour" cx={x(0)} cy={y(0)} key={value} r={Math.sqrt(value) * scale} />)}
            <circle className="feasible-region" cx={x(artifact.constraint.center[0])} cy={y(artifact.constraint.center[1])} r={artifact.constraint.radius * scale} />
            <circle className="active-boundary" cx={x(artifact.constraint.center[0])} cy={y(artifact.constraint.center[1])} r={artifact.constraint.radius * scale} />
            <path className="failure-path" d={path(failure.steps.map((item) => item.point))} />
            <path className="primary-path" d={path(primaryPoints)} />
            {failure.steps.map((item) => <circle className={item.feasible ? "failure-point" : "failure-point infeasible-point"} cx={x(item.point[0])} cy={y(item.point[1])} key={item.step} r="4" />)}
            <circle className="initial-marker" cx={x(artifact.initial_point[0])} cy={y(artifact.initial_point[1])} r="7" />
            <circle className="reference-marker" cx={x(artifact.known_reference.point[0])} cy={y(artifact.known_reference.point[1])} r="8" />
            <circle className={current.feasible ? "current-marker" : "current-marker infeasible-point"} cx={x(current.point[0])} cy={y(current.point[1])} r="6" />
          </g>
          <line className="plot-axis" x1={LEFT} x2={LEFT + SIZE} y1={TOP + SIZE} y2={TOP + SIZE} />
          <line className="plot-axis" x1={LEFT} x2={LEFT} y1={TOP} y2={TOP + SIZE} />
          <text className="plot-label" x={LEFT + SIZE - 8} y={TOP + SIZE + 28}>x →</text><text className="plot-label" x={LEFT - 38} y={TOP + 12}>y ↑</text>
          <text className="plot-annotation" x={x(1)} y={y(1)}>feasible</text><text className="plot-annotation" x={x(0.35) + 12} y={y(0.35) - 10}>known optimum</text>
        </svg>
        <div className="learning-plot-panel">
          <label htmlFor="feasible-step">現在の反復 <strong>{step} / {primary.steps.length - 1}</strong></label>
          <input id="feasible-step" max={primary.steps.length - 1} min="0" onChange={(event) => setStep(Number(event.target.value))} type="range" value={step} />
          <dl><div><dt>Current</dt><dd>({current.point.map(format).join(", ")})</dd></div><div><dt>Objective</dt><dd>{format(current.objective)}</dd></div><div><dt>Violation</dt><dd>{format(current.violation)}</dd></div><div><dt>Status</dt><dd>{current.active_constraint ? "active constraint" : current.feasible ? "feasible" : "infeasible"}</dd></div></dl>
          <p><strong>終了理由:</strong> {step === primary.steps.length - 1 ? primary.termination_reason_ja : "Traceを進めて確認します。"}</p>
        </div>
      </div>
      <ul className="plot-legend" aria-label="可視化の凡例"><li><span className="legend-swatch feasible" />feasible region</li><li><span className="legend-swatch primary" />constraint-aware</li><li><span className="legend-swatch failure" />unconstrained failure</li><li><span className="legend-dot reference" />known optimum / best feasible</li></ul>
      <details><summary>SLSQP / projected / penalty / interior-pointの違い</summary><ul>{artifact.method_distinctions_ja.map((item) => <li key={item}>{item}</li>)}</ul></details>
    </section>
  );
}

export function ParetoFrontRenderer({ artifact }: { artifact: ParetoFrontArtifact }) {
  const [weightPercent, setWeightPercent] = useState(50);
  const selected = useMemo(() => {
    const weight = weightPercent / 100;
    const t = 2 * (1 - weight);
    return { decision: [t, t] as [number, number], objectives: [2 * t * t, 2 * (t - 2) ** 2] as [number, number] };
  }, [weightPercent]);
  const x = (value: number) => LEFT + (value / 8) * SIZE;
  const y = (value: number) => TOP + (value / 8) * SIZE;
  const frontPath = artifact.pareto_front.map((point, index) => `${index === 0 ? "M" : "L"}${x(point.objectives[0])},${y(point.objectives[1])}`).join(" ");
  return (
    <section className="learning-renderer" aria-labelledby="pareto-heading">
      <div className="learning-renderer-heading"><div><p className="eyebrow">pareto_front · 1.0.0</p><h2 id="pareto-heading">単一bestではなくtrade-off集合を選ぶ</h2></div><strong>f₁ ↓ · f₂ ↓</strong></div>
      <div className="learning-plot-layout">
        <svg aria-label={artifact.text_alternative_ja} className="learning-plot" role="img" viewBox="0 0 520 440">
          <rect className="plot-background" height={SIZE} width={SIZE} x={LEFT} y={TOP} />
          {artifact.points.filter((point) => point.dominated).map((point) => <circle className="dominated-point" cx={x(point.objectives[0])} cy={y(point.objectives[1])} key={point.point_id} r="3" />)}
          <path className="pareto-front" d={frontPath} />
          {artifact.pareto_front.filter((_, index) => index % 2 === 0).map((point) => <circle className="pareto-point" cx={x(point.objectives[0])} cy={y(point.objectives[1])} key={point.point_id} r="4" />)}
          <path className="minimize-cue" d={`M${LEFT + 72},${TOP + 72} L${LEFT + 18},${TOP + 18}`} markerEnd="url(#none)" />
          <rect className="ideal-marker" height="10" width="10" x={x(artifact.reference.ideal[0]) - 5} y={y(artifact.reference.ideal[1]) - 5} />
          <path className="selected-marker" d={`M${x(selected.objectives[0])},${y(selected.objectives[1]) - 9} l8,16 h-16 z`} />
          <line className="plot-axis" x1={LEFT} x2={LEFT + SIZE} y1={TOP + SIZE} y2={TOP + SIZE} /><line className="plot-axis" x1={LEFT} x2={LEFT} y1={TOP} y2={TOP + SIZE} />
          <text className="plot-label" x={LEFT + SIZE - 55} y={TOP + SIZE + 28}>f₁ minimize →</text><text className="plot-label" x={LEFT - 48} y={TOP + 12}>f₂ ↓</text>
          <text className="plot-annotation" x={LEFT + 12} y={TOP + 20}>ideal (not feasible)</text><text className="plot-annotation" x={LEFT + SIZE - 78} y={TOP + SIZE - 10}>nadir ref.</text>
        </svg>
        <div className="learning-plot-panel">
          <label htmlFor="preference-weight">f₁のweight <strong>{(weightPercent / 100).toFixed(2)}</strong></label>
          <input id="preference-weight" max="90" min="10" onChange={(event) => setWeightPercent(Number(event.target.value))} step="5" type="range" value={weightPercent} />
          <dl><div><dt>Selected f₁</dt><dd>{format(selected.objectives[0])}</dd></div><div><dt>Selected f₂</dt><dd>{format(selected.objectives[1])}</dd></div><div><dt>Decision</dt><dd>({selected.decision.map(format).join(", ")})</dd></div><div><dt>Reference</dt><dd>known exact front</dd></div></dl>
          <p><strong>単一bestではありません。</strong> weightはfront上の意思決定を一つ選ぶpreferenceです。</p>
        </div>
      </div>
      <ul className="plot-legend" aria-label="可視化の凡例"><li><span className="legend-dot dominated" />dominated</li><li><span className="legend-swatch pareto" />non-dominated / Pareto front</li><li><span className="legend-dot selected" />selected by preference</li><li><span className="legend-dot ideal" />ideal / nadir reference</li></ul>
      <p className="weighted-sum-warning"><strong>Weighted sumの注意:</strong> {artifact.weighted_sum_limitation_ja}</p>
    </section>
  );
}

function format(value: number): string { return Number(value.toFixed(3)).toString(); }
