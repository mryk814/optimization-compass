import type { JsonValue } from "../../contracts/trace";
import type { VisualizationScenario } from "../../contracts/visualization-scenarios";

interface ObjectiveGoalCuesProps {
  objective: Record<string, JsonValue>;
  initialPoint: readonly number[];
  currentPoint?: readonly number[];
  bestValue?: number | null;
  terminalReason: string;
  knownReferenceDisplay: VisualizationScenario["lesson"]["known_reference_display"];
}

export function ObjectiveGoalCues({
  objective,
  initialPoint,
  currentPoint,
  bestValue,
  terminalReason,
  knownReferenceDisplay,
}: ObjectiveGoalCuesProps) {
  const optimum = objectiveRecord(objective.optimum);
  const optimumPoint = numberList(optimum?.point);
  const optimumValue = finiteNumber(optimum?.value);
  const direction = objective.direction === "maximize" ? "maximize" : "minimize";
  const directionNote = objective.direction === "maximize" || objective.direction === "minimize"
    ? "objective metadata"
    : "canonical objective default";
  return (
    <section aria-label="最適化の目標と現在値" className="visualization-goal-cues">
      <h2>目標と現在地 (Goal cues)</h2>
      <dl>
        <div><dt>方向 (Direction)</dt><dd>{direction} <small>({directionNote})</small></dd></div>
        <div><dt>初期点 (Initial)</dt><dd>{formatPoint(initialPoint)}</dd></div>
        <div><dt>現在点 (Current)</dt><dd>{currentPoint ? formatPoint(currentPoint) : "このフレームでは未取得"}</dd></div>
        <div><dt>現在までの最良値 (best-so-far)</dt><dd>{bestValue === undefined || bestValue === null ? "未取得" : formatValue(bestValue)}</dd></div>
        <div>
          <dt>既知の最適点 (Known optimum)</dt>
          <dd>{knownReferenceText(knownReferenceDisplay, optimumPoint, optimumValue)}</dd>
        </div>
        <div><dt>終了理由 (Terminal)</dt><dd>{terminalReason}</dd></div>
      </dl>
    </section>
  );
}

function knownReferenceText(
  display: VisualizationScenario["lesson"]["known_reference_display"],
  optimumPoint: number[] | undefined,
  optimumValue: number | undefined,
): string {
  if (display.policy === "not_shown") return display.note_ja;
  if (optimumPoint && optimumValue !== undefined) {
    return `${formatPoint(optimumPoint)} · f=${formatValue(optimumValue)}`;
  }
  return display.note_ja;
}

function objectiveRecord(value: JsonValue | undefined): Record<string, JsonValue> | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value : undefined;
}

function numberList(value: JsonValue | undefined): number[] | undefined {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "number" || !Number.isFinite(item))) return undefined;
  return value as number[];
}

function finiteNumber(value: JsonValue | undefined): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function formatPoint(point: readonly number[]): string {
  return `[${point.map((value) => value.toFixed(3)).join(", ")}]`;
}

function formatValue(value: number): string {
  return value.toPrecision(5);
}
