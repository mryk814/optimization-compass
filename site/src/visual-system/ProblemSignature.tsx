import { useId } from "react";

import type { LensAxis, MethodLens } from "./method-lens";
import {
  axisValueText,
  MAX_SIGNATURE_SLOTS,
  shortValueLabel,
  SIGNATURE_GROUPS,
  SIGNATURE_SLOTS,
  signatureSummary,
  type SignatureAxis,
} from "./signature";

/**
 * Problem Signature as a punch card: one column per diagnosis axis, one slot per possible
 * value, a filled dot where the problem sits. A Method Lens overlays the same slots: an orange
 * ring where a rule or assumption supports the method, a red slash where it excludes it.
 * Unknown axes are hatched, unanswered axes are dashed, not-applicable axes are a short dash.
 */
export interface ProblemSignatureProps {
  axes: readonly SignatureAxis[];
  lens?: MethodLens;
  /** compact: a card glyph; medium: narrow panes (axis names alternate rows); full: wide panels. */
  size?: "compact" | "medium" | "full";
  /** Visible caption under the card (full size only). */
  showReading?: boolean;
  label?: string;
}

const GEOMETRY = {
  compact: { col: 7, row: 5, r: 1.7, pad: 3, groupGap: 6, header: 0 },
  medium: { col: 31, row: 13, r: 3.6, pad: 6, groupGap: 0, header: 34 },
  full: { col: 46, row: 15, r: 4.2, pad: 8, groupGap: 0, header: 22 },
} as const;

export function ProblemSignature({ axes, lens, size = "full", showReading = size !== "compact", label }: ProblemSignatureProps) {
  const summary = signatureSummary(axes);
  const lensByQuestion = new Map(lens?.axes.map((axis) => [axis.questionId, axis]));
  if (size === "compact") {
    return (
      <span className="vs-signature vs-signature-compact" role="img" aria-label={label ?? summary} title={summary}>
        <CompactCard axes={axes} lensByQuestion={lensByQuestion} />
      </span>
    );
  }
  return (
    <figure className={`vs-signature vs-signature-full is-${size}`} aria-label={label ?? "問題の署名"}>
      <div className="vs-signature-groups">
        {SIGNATURE_GROUPS.map((group) => (
          <div className="vs-signature-group" key={group.id}>
            <span className="vs-signature-group-label">{group.label}</span>
            <GroupCard
              axes={axes.filter((axis) => axis.group === group.id)}
              lensByQuestion={lensByQuestion}
              size={size}
            />
          </div>
        ))}
      </div>
      {showReading && (
        <figcaption className="vs-signature-reading">
          <span className="vs-visually-hidden">{summary}</span>
          <dl aria-hidden="true">
            {axes.filter((axis) => axis.state !== "missing").map((axis) => (
              <div className={`vs-reading is-${axis.state}`} key={axis.questionId}>
                <dt>{axis.name}</dt>
                <dd>{axisValueText(axis)}</dd>
              </div>
            ))}
            {axes.some((axis) => axis.state === "missing") && (
              <div className="vs-reading is-missing vs-reading-wide">
                <dt>未回答</dt>
                <dd>{axes.filter((axis) => axis.state === "missing").map((axis) => axis.name).join("・")}</dd>
              </div>
            )}
          </dl>
        </figcaption>
      )}
    </figure>
  );
}

function CompactCard({ axes, lensByQuestion }: { axes: readonly SignatureAxis[]; lensByQuestion: Map<string, LensAxis> }) {
  const g = GEOMETRY.compact;
  const width = axes.length * g.col + (SIGNATURE_GROUPS.length - 1) * g.groupGap + 2;
  const height = MAX_SIGNATURE_SLOTS * g.row + g.pad * 2;
  return (
    <svg aria-hidden="true" height={height} viewBox={`0 0 ${width} ${height}`} width={width}>
      {axes.map((axis, index) => {
        const groupIndex = SIGNATURE_GROUPS.findIndex((group) => group.id === axis.group);
        const x = 1 + index * g.col + groupIndex * g.groupGap + g.col / 2;
        return <Column axis={axis} g={g} key={axis.questionId} lensAxis={lensByQuestion.get(axis.questionId)} x={x} />;
      })}
    </svg>
  );
}

function GroupCard({ axes, lensByQuestion, size }: { axes: readonly SignatureAxis[]; lensByQuestion: Map<string, LensAxis>; size: "medium" | "full" }) {
  const g = GEOMETRY[size];
  const width = axes.length * g.col;
  const slots = Math.max(...axes.map((axis) => SIGNATURE_SLOTS[axis.questionId]?.length ?? 0));
  const height = g.header + slots * g.row + g.pad * 2 + 10;
  return (
    <svg aria-hidden="true" className="vs-signature-svg" height={height} viewBox={`0 0 ${width} ${height}`} width={width}>
      {axes.map((axis, index) => {
        const x = index * g.col + g.col / 2;
        return (
          <g key={axis.questionId}>
            <text className="vs-axis-name" textAnchor="middle" x={x} y={size === "medium" && index % 2 === 1 ? 28 : 13}>{axis.name}</text>
            {size === "medium" && index % 2 === 1 && <line className="vs-axis-leader" x1={x} x2={x} y1={30} y2={g.header + 2} />}
            <Column axis={axis} g={g} lensAxis={lensByQuestion.get(axis.questionId)} x={x} />
          </g>
        );
      })}
    </svg>
  );
}

type Geometry = (typeof GEOMETRY)[keyof typeof GEOMETRY];

function Column({ axis, g, lensAxis, x }: { axis: SignatureAxis; g: Geometry; lensAxis?: LensAxis; x: number }) {
  const hatchId = useId();
  const slots = SIGNATURE_SLOTS[axis.questionId] ?? [];
  const top = g.header + g.pad;
  const y = (index: number) => top + index * g.row + g.row / 2;
  const columnHeight = slots.length * g.row;
  const columnWidth = g.col - (g.header > 0 ? 10 : 2);
  const blocks = new Set(lensAxis?.blockValues ?? []);
  const supports = new Set(lensAxis?.flipValues ?? []);
  const lensClass = lensAxis ? ` lens-${lensAxis.status}` : "";
  return (
    <g className={`vs-column is-${axis.state}${lensClass}`}>
      {axis.state === "unknown" && (
        <>
          <defs>
            <pattern height="5" id={hatchId} patternTransform="rotate(45)" patternUnits="userSpaceOnUse" width="5">
              <rect className="vs-hatch-ground" height="5" width="5" />
              <line className="vs-hatch-line" x1="0" x2="0" y1="0" y2="5" />
            </pattern>
          </defs>
          <rect fill={`url(#${hatchId})`} height={columnHeight} rx={2} width={columnWidth} x={x - columnWidth / 2} y={top} />
        </>
      )}
      {axis.state === "missing" && (
        <rect className="vs-column-missing" height={columnHeight} rx={2} width={columnWidth} x={x - columnWidth / 2} y={top} />
      )}
      {lensAxis && lensAxis.status !== "unread" && g.header > 0 && !(axis.state === "known" && axis.values.length === 0) && (
        <rect className="vs-lens-base" height={4} rx={1} width={columnWidth} x={x - columnWidth / 2} y={top + columnHeight + 5} />
      )}
      <line className="vs-column-stem" x1={x} x2={x} y1={top + g.row / 2} y2={top + columnHeight - g.row / 2} />
      {slots.map((value, index) => {
        const chosen = axis.state === "known" && axis.values.includes(value);
        const cy = y(index);
        return (
          <g key={value}>
            {g.header > 0 && <title>{`${axis.name}: ${shortValueLabel(axis.questionId, value)}${chosen ? "（この問題）" : ""}${supports.has(value) ? "・支える値" : ""}${blocks.has(value) ? "・外れる値" : ""}`}</title>}
            {supports.has(value) && <circle className="vs-lens-ring" cx={x} cy={cy} r={g.r + (g.header > 0 ? 3.2 : 1.3)} />}
            <circle className={chosen ? "vs-slot is-chosen" : "vs-slot"} cx={x} cy={cy} r={chosen ? g.r + (g.header > 0 ? 0.8 : 0.5) : g.r * 0.62} />
            {blocks.has(value) && (
              <line className="vs-lens-slash" x1={x - g.r - 2} x2={x + g.r + 2} y1={cy + g.r + 2} y2={cy - g.r - 2} />
            )}
          </g>
        );
      })}
      {axis.state === "not_applicable" && (
        <line className="vs-column-na" x1={x - columnWidth / 3} x2={x + columnWidth / 3} y1={top + 2} y2={top + 2} />
      )}
    </g>
  );
}
