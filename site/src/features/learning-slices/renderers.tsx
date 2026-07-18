import { useMemo, useState } from "react";

import type { FeasibleRegionArtifact, ParetoFrontArtifact, TriObjectiveLens, TriObjectivePoint } from "../../contracts/learning-slices";
import type { FieldEvolutionPayload } from "../../contracts/field-evolution";

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
      <div className="learning-renderer-heading"><div><p className="eyebrow">実行可能領域 (feasible_region) · 1.0.0</p><h2 id="feasible-heading">目的値と実行可能性を同時に読む</h2></div><strong>{artifact.objective_direction} ↓</strong></div>
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
          <text className="plot-annotation" x={x(1)} y={y(1)}>実行可能</text><text className="plot-annotation" x={x(0.35) + 12} y={y(0.35) - 10}>既知の最適点</text>
        </svg>
        <div className="learning-plot-panel">
          <label htmlFor="feasible-step">現在の反復 <strong>{step} / {primary.steps.length - 1}</strong></label>
          <input id="feasible-step" max={primary.steps.length - 1} min="0" onChange={(event) => setStep(Number(event.target.value))} type="range" value={step} />
          <dl><div><dt>現在点 (Current)</dt><dd>({current.point.map(format).join(", ")})</dd></div><div><dt>目的値 (Objective)</dt><dd>{format(current.objective)}</dd></div><div><dt>違反量 (Violation)</dt><dd>{format(current.violation)}</dd></div><div><dt>状態 (Status)</dt><dd>{current.active_constraint ? "制約が有効" : current.feasible ? "実行可能" : "実行不可能"}</dd></div></dl>
          <p><strong>終了理由:</strong> {step === primary.steps.length - 1 ? primary.termination_reason_ja : "Traceを進めて確認します。"}</p>
        </div>
      </div>
      <ul className="plot-legend" aria-label="可視化の凡例"><li><span className="legend-swatch feasible" />実行可能領域 (feasible region)</li><li><span className="legend-swatch primary" />制約を考慮した経路 (constraint-aware)</li><li><span className="legend-swatch failure" />制約を無視した失敗経路 (unconstrained failure)</li><li><span className="legend-dot reference" />既知の最適点・最良の実行可能点</li></ul>
      <details><summary>制約付き手法の違い (SLSQP / projected / penalty / interior-point)</summary><ul>{artifact.method_distinctions_ja.map((item) => <li key={item}>{item}</li>)}</ul></details>
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
      <div className="learning-renderer-heading"><div><p className="eyebrow">パレート前線 (pareto_front) · 1.1.0</p><h2 id="pareto-heading">単一の最良解ではなく、トレードオフ集合を選ぶ</h2></div><strong>f₁ ↓ · f₂ ↓</strong></div>
      <p className="projection-disclosure"><strong>2Dでの確認:</strong> まず f₁ × f₂ の支配関係を読み、下の3Dとparallel coordinatesで第3目的を照合します。</p>
      <dl className="comparison-policy-grid pareto-coverage-summary" aria-label="パレート前線の集計">
        <div><dt>サンプル数</dt><dd>{artifact.points.length}</dd></div>
        <div><dt>支配された点</dt><dd>{dominatedCount}</dd></div>
        <div><dt>非支配のサンプル点</dt><dd>{nonDominatedCount}</dd></div>
        <div><dt>解析的な参照前線</dt><dd>{artifact.pareto_front.length} · {artifact.reference.status}</dd></div>
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
          <label htmlFor="preference-weight">f₁の重み (weight) <strong>{(weightPercent / 100).toFixed(2)}</strong></label>
          <input id="preference-weight" max="90" min="10" onChange={(event) => setWeightPercent(Number(event.target.value))} step="5" type="range" value={weightPercent} />
           <dl><div><dt>選択した f₁</dt><dd>{format(selected.objectives[0])}</dd></div><div><dt>選択した f₂</dt><dd>{format(selected.objectives[1])}</dd></div><div><dt>決定変数</dt><dd>({selected.decision.map(format).join(", ")})</dd></div><div><dt>参照</dt><dd>既知の正確な前線</dd></div></dl>
           <p><strong>単一の最良解ではありません。</strong>重みは前線上から意思決定を一つ選ぶための設定です。</p>
        </div>
      </div>
      <TriObjectiveLensView lens={artifact.triobjective_lens} selected={selectedTri} weightPercent={weightPercent} />
      <ul className="plot-legend" aria-label="可視化の凡例"><li><span className="legend-dot dominated" />支配された点 (dominated)</li><li><span className="legend-swatch pareto" />非支配点・パレート前線</li><li><span className="legend-dot selected" />重みで選択した点</li><li><span className="legend-dot ideal" />理想点・最悪点の参照</li></ul>
      <p className="weighted-sum-warning"><strong>重み付き和 (Weighted sum) の注意:</strong> {artifact.weighted_sum_limitation_ja}</p>
    </section>
  );
}

export function FieldEvolutionRenderer({ payload }: { payload: FieldEvolutionPayload }) {
  const [selectedRunId, setSelectedRunId] = useState(payload.family_payload.runs[0].run_id);
  const [selectedStep, setSelectedStep] = useState(payload.family_payload.runs[0].snapshots.length - 1);
  const selectedRun = payload.family_payload.runs.find((run) => run.run_id === selectedRunId) ?? payload.family_payload.runs[0];
  const stepIndex = Math.min(selectedStep, selectedRun.snapshots.length - 1);
  const current = selectedRun.snapshots[stepIndex];
  const changeRun = (runId: string) => {
    const next = payload.family_payload.runs.find((run) => run.run_id === runId) ?? payload.family_payload.runs[0];
    setSelectedRunId(next.run_id);
    setSelectedStep(Math.min(next.snapshots.length - 1, stepIndex));
  };
  const currentMarkers = payload.event_markers.filter((marker) => marker.position.value === current.iteration && marker.marker_id.startsWith(`${selectedRun.run_id}-`));
  return (
    <section className="learning-renderer topology-renderer" aria-labelledby="topology-heading">
      <div className="learning-renderer-heading"><div><p className="eyebrow">設計fieldの進化 (field_evolution) · {payload.renderer_contract_version}</p><h2 id="topology-heading">密度、状態、感度を同じ反復で読む</h2></div><strong>volume {format(payload.family_payload.volume_fraction_target)}</strong></div>
      <p className="projection-disclosure"><strong>見る順番:</strong> 密度fieldで荷重経路を見て、状態と感度を重ね、最後にcomplianceとcheckerboardを確認します。</p>
      <div className="topology-controls">
        <label htmlFor="topology-run">経路 <select id="topology-run" onChange={(event) => changeRun(event.target.value)} value={selectedRun.run_id}>{payload.family_payload.runs.map((run) => <option key={run.run_id} value={run.run_id}>{run.label_ja}</option>)}</select></label>
        <label htmlFor="topology-step">反復 <strong>{current.iteration} / {selectedRun.snapshots[selectedRun.snapshots.length - 1].iteration}</strong><input id="topology-step" max={selectedRun.snapshots.length - 1} min="0" onChange={(event) => setSelectedStep(Number(event.target.value))} type="range" value={stepIndex} /></label>
      </div>
      <div className="topology-field-grid">
        <FieldGrid label="設計密度 density" values={current.fields.design_field} columns={payload.family_payload.mesh.columns} rows={payload.family_payload.mesh.rows} mode="density" />
        <FieldGrid label="状態 state" values={current.fields.state_field} columns={payload.family_payload.mesh.columns} rows={payload.family_payload.mesh.rows} mode="state" />
        <FieldGrid label="filter後の感度" values={current.fields.sensitivity_field} columns={payload.family_payload.mesh.columns} rows={payload.family_payload.mesh.rows} mode="sensitivity" />
      </div>
      <dl className="comparison-policy-grid topology-metrics" aria-label="トポロジー最適化の現在値">
        <div><dt>体積率</dt><dd>{format(current.metrics.volume_fraction)} / {format(payload.family_payload.volume_fraction_target)}</dd></div>
        <div><dt>compliance</dt><dd>{format(current.metrics.compliance)}</dd></div>
        <div><dt>gray fraction</dt><dd>{format(current.metrics.gray_fraction)}</dd></div>
        <div><dt>checkerboard score</dt><dd>{format(current.metrics.checkerboard_score)}</dd></div>
        <div><dt>projection beta</dt><dd>{format(current.metrics.projection_beta)}</dd></div>
      </dl>
      <ul className="plot-legend topology-legend" aria-label="設計fieldの凡例"><li><span className="legend-swatch density-low" />低密度</li><li><span className="legend-swatch density-high" />高密度</li><li><span className="legend-swatch sensitivity" />感度の大きいセル</li></ul>
      <p><strong>{current.label_ja}</strong>。{stepIndex === selectedRun.snapshots.length - 1 ? selectedRun.termination_reason_ja : "反復を進めて密度fieldと指標の対応を確認します。"}</p>
      <section className="field-event-markers" aria-labelledby="field-event-markers-title"><h3 id="field-event-markers-title">イベントマーカー</h3><ol>{currentMarkers.map((marker) => <li key={marker.marker_id}><strong>{marker.label_ja}</strong> · {marker.position.axis}={marker.position.value} · {marker.severity === "warning" ? "warning" : "info"} · {marker.observable_ids.join(", ")}</li>)}</ol></section>
      <aside className="field-static-fallback" aria-labelledby="field-static-fallback-title"><h3 id="field-static-fallback-title">{payload.static_fallback.title_ja}</h3><p>アニメーションなしでも、同じ field と指標の要点を確認できます。{payload.static_fallback.artifact_kind} · {payload.static_fallback.execution_status}</p><dl>{payload.static_fallback.facts.map((fact) => <div key={fact.observable_id}><dt>{payload.observables.find((observable) => observable.observable_id === fact.observable_id)?.label_ja ?? fact.observable_id}</dt><dd>{fact.value}</dd></div>)}</dl><p className="atlas-note">{payload.static_fallback.limitations_ja}</p></aside>
    </section>
  );
}

function FieldGrid({ label, values, columns, rows, mode }: { label: string; values: number[]; columns: number; rows: number; mode: "density" | "state" | "sensitivity" }) {
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const range = maximum - minimum || 1;
  const color = (value: number) => {
    const normalized = (value - minimum) / range;
    if (mode === "density") return `hsl(${210 - normalized * 150} 80% ${92 - normalized * 55}%)`;
    if (mode === "state") return `hsl(198 72% ${95 - normalized * 45}%)`;
    return `hsl(28 85% ${94 - normalized * 46}%)`;
  };
  return (
    <figure className="topology-field-card">
      <figcaption>{label}</figcaption>
      <svg aria-label={label} className="topology-field" role="img" viewBox={`0 0 ${columns * 32} ${rows * 32}`}>
        {values.map((value, index) => <rect fill={color(value)} height="30" key={index} rx="2" width="30" x={(index % columns) * 32} y={Math.floor(index / columns) * 32} />)}
      </svg>
    </figure>
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
          <p className="eyebrow">3目的の表示 · sampled_grid</p>
          <h3 id="triobjective-heading">3目的のトレードオフを同じ選択で読む</h3>
          <p>f₁の重み {weightPercent / 100} で選んだ点を、3D・2D・parallel coordinatesで共有します。</p>
        </div>
        <label className="surface-camera-control">
          <span>カメラ方位 <output>{azimuth}°</output></span>
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
          <figcaption>直交投影 (orthographic) · 軸の値はサンプルの最悪点で正規化 · 正確な値は下のパネルに示します。</figcaption>
        </figure>
        <figure>
          <svg aria-label="3目的のparallel coordinates表示" className="parallel-objectives" role="img" viewBox="0 0 520 260">
            {parallelX.map((x, axis) => <g key={x}><line x1={x} x2={x} y1="34" y2="224" /><text x={x} y="20">f{axis + 1} ↓</text><text x={x} y="244">{format(lens.reference.nadir[axis])}</text></g>)}
            <g className="parallel-front">{parallelPoints.map((point) => <polyline key={point.point_id} points={point.objectives.map((value, axis) => `${parallelX[axis]},${parallelY(value, axis)}`).join(" ")} />)}</g>
            <polyline className="parallel-selected" points={selectedParallel} />
          </svg>
          <figcaption>Parallel coordinates: 上ほど各目的が小さく、橙線が現在の重みで選んだ点です。</figcaption>
        </figure>
      </div>
      <dl className="triobjective-values">
        {selected.objectives.map((value, axis) => <div key={lens.axis_labels[axis]}><dt>{lens.axis_labels[axis]}</dt><dd>{format(value)}</dd></div>)}
      </dl>
      <p className="atlas-note">{lens.limitations_ja}</p>
      <details><summary>3目的表示の数式定義</summary><ul>{lens.objective_expressions.map((expression) => <li key={expression}>{expression}</li>)}</ul></details>
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
