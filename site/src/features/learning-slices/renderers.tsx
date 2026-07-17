import { useMemo, useState } from "react";

import type { FeasibleRegionArtifact, ParetoFrontArtifact, TriObjectiveLens, TriObjectivePoint } from "../../contracts/learning-slices";

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
  const dominatedCount = artifact.points.filter((point) => point.dominated).length;
  const nonDominatedCount = artifact.points.length - dominatedCount;
  const selectedTri = useMemo(() => selectTriObjectivePoint(artifact.triobjective_lens, weightPercent), [artifact.triobjective_lens, weightPercent]);
  return (
    <section className="learning-renderer" aria-labelledby="pareto-heading">
      <div className="learning-renderer-heading"><div><p className="eyebrow">pareto_front · 1.1.0</p><h2 id="pareto-heading">単一bestではなくtrade-off集合を選ぶ</h2></div><strong>f₁ ↓ · f₂ ↓</strong></div>
      <p className="projection-disclosure"><strong>2D precision fallback:</strong> まず f₁ × f₂ の支配関係を読み、下の3Dとparallel coordinatesで第3目的を照合します。</p>
      <dl className="comparison-policy-grid pareto-coverage-summary" aria-label="Pareto coverage集計">
        <div><dt>Sampled</dt><dd>{artifact.points.length}</dd></div>
        <div><dt>Dominated</dt><dd>{dominatedCount}</dd></div>
        <div><dt>Non-dominated sampled</dt><dd>{nonDominatedCount}</dd></div>
        <div><dt>Analytic reference</dt><dd>{artifact.pareto_front.length} · {artifact.reference.status}</dd></div>
      </dl>
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
      <TriObjectiveLensView lens={artifact.triobjective_lens} selected={selectedTri} weightPercent={weightPercent} />
      <ul className="plot-legend" aria-label="可視化の凡例"><li><span className="legend-dot dominated" />dominated</li><li><span className="legend-swatch pareto" />non-dominated / Pareto front</li><li><span className="legend-dot selected" />selected by preference</li><li><span className="legend-dot ideal" />ideal / nadir reference</li></ul>
      <p className="weighted-sum-warning"><strong>Weighted sumの注意:</strong> {artifact.weighted_sum_limitation_ja}</p>
    </section>
  );
}

function TriObjectiveLensView({
  lens,
  selected,
  weightPercent,
}: {
  lens: TriObjectiveLens;
  selected: TriObjectivePoint;
  weightPercent: number;
}) {
  const [azimuth, setAzimuth] = useState(315);
  const projected = lens.points.map((point) => ({
    point,
    position: projectTriObjective(point.objectives, lens.reference.nadir, azimuth),
  }));
  const selectedPosition = projectTriObjective(selected.objectives, lens.reference.nadir, azimuth);
  const parallelX = [72, 260, 448] as const;
  const parallelY = (value: number, axis: number) => 34 + (value / lens.reference.nadir[axis]) * 190;
  const parallelPoints = lens.pareto_front.filter((_, index) => index % Math.max(1, Math.floor(lens.pareto_front.length / 16)) === 0);
  const selectedParallel = selected.objectives.map((value, axis) => `${parallelX[axis]},${parallelY(value, axis)}`).join(" ");
  return (
    <section className="triobjective-lens" aria-labelledby="triobjective-heading">
      <header>
        <div>
          <p className="eyebrow">3-objective lens · sampled_grid</p>
          <h3 id="triobjective-heading">3目的のtrade-offを同じ選択で読む</h3>
          <p>f₁ weight {weightPercent / 100} の選択点を、3D・2D fallback・parallel coordinatesで共有します。</p>
        </div>
        <label className="surface-camera-control">
          <span>Camera azimuth <output>{azimuth}°</output></span>
          <input aria-label="3目的表示のカメラ方位" max="405" min="225" onChange={(event) => setAzimuth(Number(event.target.value))} step="5" type="range" value={azimuth} />
        </label>
      </header>
      <div className="triobjective-grid">
        <figure>
          <svg aria-label={lens.text_alternative_ja} className="triobjective-scatter" data-testid="triobjective-scatter" role="img" viewBox="0 0 520 300">
            <rect className="surface-background" height="300" rx="10" width="520" />
            <g className="triobjective-points">
              {projected.map(({ point, position }) => <circle className={point.dominated ? "is-dominated" : "is-front"} cx={position.x} cy={position.y} key={point.point_id} r={point.dominated ? 2.2 : 3.4} />)}
              <circle className="is-selected" cx={selectedPosition.x} cy={selectedPosition.y} r="7" />
            </g>
            <g className="surface-axis-labels" aria-hidden="true"><text x="462" y="258">f₁</text><text x="58" y="258">f₂</text><text x="260" y="24">f₃</text></g>
          </svg>
          <figcaption>Projection: orthographic · axis values normalized by sampled nadir · exact values remain in the panels below.</figcaption>
        </figure>
        <figure>
          <svg aria-label="3目的のparallel coordinates fallback" className="parallel-objectives" role="img" viewBox="0 0 520 260">
            {parallelX.map((x, axis) => <g key={x}><line x1={x} x2={x} y1="34" y2="224" /><text x={x} y="20">f{axis + 1} ↓</text><text x={x} y="244">{format(lens.reference.nadir[axis])}</text></g>)}
            <g className="parallel-front">{parallelPoints.map((point) => <polyline key={point.point_id} points={point.objectives.map((value, axis) => `${parallelX[axis]},${parallelY(value, axis)}`).join(" ")} />)}</g>
            <polyline className="parallel-selected" points={selectedParallel} />
          </svg>
          <figcaption>Parallel coordinates fallback: 上ほど各目的が小さい。橙線が現在のpreference選択です。</figcaption>
        </figure>
      </div>
      <dl className="triobjective-values">
        {selected.objectives.map((value, axis) => <div key={lens.axis_labels[axis]}><dt>{lens.axis_labels[axis]}</dt><dd>{format(value)}</dd></div>)}
      </dl>
      <p className="atlas-note">{lens.limitations_ja}</p>
      <details><summary>3目的lensの数式定義</summary><ul>{lens.objective_expressions.map((expression) => <li key={expression}>{expression}</li>)}</ul></details>
    </section>
  );
}

export function selectTriObjectivePoint(lens: TriObjectiveLens, weightPercent: number): TriObjectivePoint {
  const firstWeight = weightPercent / 100;
  const otherWeight = (1 - firstWeight) / 2;
  const weights = [firstWeight, otherWeight, otherWeight];
  return lens.pareto_front.reduce((best, point) => {
    const score = point.objectives.reduce((sum, value, axis) => sum + weights[axis] * value / lens.reference.nadir[axis], 0);
    const bestScore = best.objectives.reduce((sum, value, axis) => sum + weights[axis] * value / lens.reference.nadir[axis], 0);
    return score < bestScore ? point : best;
  });
}

export function projectTriObjective(
  objectives: [number, number, number],
  nadir: [number, number, number],
  azimuth: number,
): { x: number; y: number } {
  const normalized = objectives.map((value, axis) => value / nadir[axis] - 0.5);
  const radians = azimuth * Math.PI / 180;
  const horizontal = normalized[0] * Math.cos(radians) - normalized[1] * Math.sin(radians);
  const depth = normalized[0] * Math.sin(radians) + normalized[1] * Math.cos(radians);
  return { x: 260 + horizontal * 176, y: 232 + depth * 72 - (normalized[2] + 0.5) * 176 };
}

function format(value: number): string { return Number(value.toFixed(3)).toString(); }
