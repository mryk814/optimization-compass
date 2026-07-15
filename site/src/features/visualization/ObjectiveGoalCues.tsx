import type { JsonValue } from "../../contracts/trace";

interface ObjectiveGoalCuesProps {
  objective: Record<string, JsonValue>;
  initialPoint: readonly number[];
  currentPoint?: readonly number[];
  bestValue?: number | null;
  terminalReason: string;
}

export function ObjectiveGoalCues({
  objective,
  initialPoint,
  currentPoint,
  bestValue,
  terminalReason,
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
      <h2>目標と現在地 / Goal cues</h2>
      <dl>
        <div><dt>方向 / Direction</dt><dd>{direction} <small>({directionNote})</small></dd></div>
        <div><dt>初期点 / Initial</dt><dd>{formatPoint(initialPoint)}</dd></div>
        <div><dt>現在点 / Current</dt><dd>{currentPoint ? formatPoint(currentPoint) : "このframeでは未取得"}</dd></div>
        <div><dt>best-so-far</dt><dd>{bestValue === undefined || bestValue === null ? "未取得" : formatValue(bestValue)}</dd></div>
        <div><dt>既知の最適点 / Known optimum</dt><dd>{optimumPoint && optimumValue !== undefined ? `${formatPoint(optimumPoint)} · f=${formatValue(optimumValue)}` : "既知のreferenceなし"}</dd></div>
        <div><dt>終了理由 / Terminal</dt><dd>{terminalReason}</dd></div>
      </dl>
    </section>
  );
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
