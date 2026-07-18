import type { TopologyFieldArtifact, TopologyFieldStep } from "./learning-slices";

export type FieldObservableId =
  | "design_field"
  | "state_field"
  | "sensitivity_field"
  | "objective_value"
  | "mesh_quality";

export interface FieldEvolutionObservable {
  observable_id: FieldObservableId;
  kind: "field" | "scalar_series";
  label_ja: string;
  label_en: string;
  unit: string | null;
}

export interface FieldEvolutionEventMarker {
  marker_id: string;
  position: { axis: "optimizer_iterations"; value: number };
  event_type: "field_update" | "state_solve" | "sensitivity_update" | "checkerboard_risk";
  severity: "info" | "warning";
  decision: "not_applicable";
  observable_ids: FieldObservableId[];
  label_ja: string;
  label_en: string;
}

export interface FieldEvolutionFact {
  observable_id: FieldObservableId;
  value: string;
  status: "observed";
}

export interface FieldEvolutionStaticFallback {
  title_ja: string;
  title_en: string;
  artifact_kind: "executable_trace";
  execution_status: "executable_teaching_trace";
  facts: FieldEvolutionFact[];
  event_marker_ids: string[];
  limitations_ja: string;
  limitations_en: string;
}

export interface FieldEvolutionSnapshot {
  iteration: number;
  label_ja: string;
  fields: {
    design_field: number[];
    state_field: number[];
    sensitivity_field: number[];
  };
  metrics: {
    volume_fraction: number;
    compliance: number;
    gray_fraction: number;
    checkerboard_score: number;
    projection_beta: number;
  };
}

export interface FieldEvolutionPayload {
  payload_contract_version: "1.0.0";
  artifact_id: "topology-optimization-field-evolution";
  renderer_family: "field_evolution";
  renderer_contract_version: "1.0.0";
  artifact_kind: "executable_trace";
  execution_status: "executable_teaching_trace";
  progress_axis: { id: "optimizer_iterations"; unit: "iterations" };
  observables: FieldEvolutionObservable[];
  event_markers: FieldEvolutionEventMarker[];
  static_fallback: FieldEvolutionStaticFallback;
  family_payload: {
    mesh: {
      columns: number;
      rows: number;
      cell_order: "row_major";
      coordinate_system: "normalized_unit_square";
    };
    volume_fraction_target: number;
    objective_expression: string;
    state_equation: string;
    load_description: string;
    runs: {
      run_id: string;
      label_ja: string;
      role: TopologyFieldArtifact["runs"][number]["role"];
      snapshots: FieldEvolutionSnapshot[];
      termination_reason_ja: string;
    }[];
  };
}

const observables: FieldEvolutionObservable[] = [
  { observable_id: "design_field", kind: "field", label_ja: "設計密度 field", label_en: "design density field", unit: null },
  { observable_id: "state_field", kind: "field", label_ja: "状態 field", label_en: "state field", unit: null },
  { observable_id: "sensitivity_field", kind: "field", label_ja: "感度 field", label_en: "sensitivity field", unit: null },
  { observable_id: "objective_value", kind: "scalar_series", label_ja: "compliance", label_en: "compliance", unit: null },
  { observable_id: "mesh_quality", kind: "scalar_series", label_ja: "checkerboard score", label_en: "checkerboard score", unit: null },
];

export function buildFieldEvolutionPayload(artifact: TopologyFieldArtifact): FieldEvolutionPayload {
  const runs = artifact.runs.map((run) => ({
    run_id: run.run_id,
    label_ja: run.label_ja,
    role: run.role,
    snapshots: run.steps.map(toSnapshot),
    termination_reason_ja: run.termination_reason_ja,
  }));
  const eventMarkers = artifact.runs.flatMap((run) => run.steps.flatMap((step) => markersForStep(run, step)));
  const primary = runs.find((run) => run.role === "primary")!;
  const final = primary.snapshots[primary.snapshots.length - 1];
  const fallbackMarkerIds = [
    markerId(primary.run_id, final.iteration, "field-update"),
    markerId(primary.run_id, final.iteration, "state-solve"),
    markerId(primary.run_id, final.iteration, "sensitivity-update"),
    ...eventMarkers.filter((marker) => marker.event_type === "checkerboard_risk").map((marker) => marker.marker_id),
  ];
  return {
    payload_contract_version: "1.0.0",
    artifact_id: "topology-optimization-field-evolution",
    renderer_family: "field_evolution",
    renderer_contract_version: "1.0.0",
    artifact_kind: "executable_trace",
    execution_status: "executable_teaching_trace",
    progress_axis: { id: "optimizer_iterations", unit: "iterations" },
    observables: observables.map((observable) => ({ ...observable })),
    event_markers: eventMarkers,
    static_fallback: {
      title_ja: "静的な要点",
      title_en: "Static summary",
      artifact_kind: "executable_trace",
      execution_status: "executable_teaching_trace",
      facts: [
        { observable_id: "design_field", value: `${final.fields.design_field.length} cells · min ${format(minimum(final.fields.design_field))} · max ${format(maximum(final.fields.design_field))}`, status: "observed" },
        { observable_id: "state_field", value: `${final.fields.state_field.length} cells · min ${format(minimum(final.fields.state_field))} · max ${format(maximum(final.fields.state_field))}`, status: "observed" },
        { observable_id: "objective_value", value: format(final.metrics.compliance), status: "observed" },
        { observable_id: "mesh_quality", value: format(final.metrics.checkerboard_score), status: "observed" },
      ],
      event_marker_ids: fallbackMarkerIds,
      limitations_ja: artifact.limitations_ja,
      limitations_en: "This is a deterministic discretized teaching field; it does not establish continuous-domain feasibility or real-world performance.",
    },
    family_payload: {
      mesh: { columns: artifact.grid.columns, rows: artifact.grid.rows, cell_order: "row_major", coordinate_system: "normalized_unit_square" },
      volume_fraction_target: artifact.volume_fraction_target,
      objective_expression: artifact.objective_expression,
      state_equation: artifact.state_equation,
      load_description: artifact.load_description,
      runs,
    },
  };
}

function markersForStep(run: TopologyFieldArtifact["runs"][number], step: TopologyFieldStep): FieldEvolutionEventMarker[] {
  const common = { position: { axis: "optimizer_iterations" as const, value: step.iteration }, decision: "not_applicable" as const };
  const markers: FieldEvolutionEventMarker[] = [
    { ...common, marker_id: markerId(run.run_id, step.iteration, "field-update"), event_type: "field_update", severity: "info", observable_ids: ["design_field"], label_ja: `${step.label_ja}の密度更新`, label_en: `density update at ${step.label_ja}` },
    { ...common, marker_id: markerId(run.run_id, step.iteration, "state-solve"), event_type: "state_solve", severity: "info", observable_ids: ["state_field", "objective_value"], label_ja: `${step.label_ja}の状態方程式`, label_en: `state solve at ${step.label_ja}` },
    { ...common, marker_id: markerId(run.run_id, step.iteration, "sensitivity-update"), event_type: "sensitivity_update", severity: "info", observable_ids: ["sensitivity_field"], label_ja: `${step.label_ja}の感度更新`, label_en: `sensitivity update at ${step.label_ja}` },
  ];
  if (run.role === "failure_contrast" && step.checkerboard_score >= 0.6) {
    markers.push({ ...common, marker_id: markerId(run.run_id, step.iteration, "checkerboard-risk"), event_type: "checkerboard_risk", severity: "warning", observable_ids: ["design_field", "mesh_quality"], label_ja: `${step.label_ja}でcheckerboard risk`, label_en: `checkerboard risk at ${step.label_ja}` });
  }
  return markers;
}

function toSnapshot(step: TopologyFieldStep): FieldEvolutionSnapshot {
  return {
    iteration: step.iteration,
    label_ja: step.label_ja,
    fields: { design_field: [...step.density], state_field: [...step.displacement_field], sensitivity_field: [...step.sensitivity_filtered] },
    metrics: { volume_fraction: step.volume_fraction, compliance: step.compliance, gray_fraction: step.gray_fraction, checkerboard_score: step.checkerboard_score, projection_beta: step.projection_beta },
  };
}

function markerId(runId: string, iteration: number, event: string): string { return `${runId}-${iteration}-${event}`; }
function minimum(values: number[]): number { return Math.min(...values); }
function maximum(values: number[]): number { return Math.max(...values); }
function format(value: number): string { return Number(value.toFixed(3)).toString(); }
