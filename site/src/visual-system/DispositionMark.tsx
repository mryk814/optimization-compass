/**
 * Disposition Mark: one glyph per decision state, shared by every surface.
 * candidate ● (filled orange) / conditional ◐ (half) / excluded ⊘ (ink ring, slash) /
 * pending ◌ (dashed: not enough answers or evidence to decide).
 * Excluded is never red: red marks only the axis whose assumption broke.
 */
export type Disposition = "candidate" | "conditional" | "excluded" | "pending";

export const DISPOSITION_LABELS: Record<Disposition, string> = {
  candidate: "候補",
  conditional: "条件付き",
  excluded: "除外",
  pending: "判断保留",
};

/** label: visible text; false: screen-reader text only; "none": glyph only, when nearby text already names the state. */
export function DispositionMark({ kind, label = true, size = 14 }: { kind: Disposition; label?: boolean | "none"; size?: number }) {
  const r = size / 2 - 1.5;
  const c = size / 2;
  return (
    <span className={`vs-disposition is-${kind}`}>
      <svg aria-hidden="true" className="vs-disposition-glyph" height={size} viewBox={`0 0 ${size} ${size}`} width={size}>
        {kind === "candidate" && <circle className="vs-mark-fill" cx={c} cy={c} r={r} />}
        {kind === "conditional" && (
          <>
            <circle className="vs-mark-ring" cx={c} cy={c} r={r} />
            <path className="vs-mark-fill" d={`M ${c} ${c - r} A ${r} ${r} 0 0 0 ${c} ${c + r} Z`} />
          </>
        )}
        {kind === "excluded" && (
          <>
            <circle className="vs-mark-ring" cx={c} cy={c} r={r} />
            <line className="vs-mark-slash" x1={c - r * 0.7} x2={c + r * 0.7} y1={c + r * 0.7} y2={c - r * 0.7} />
          </>
        )}
        {kind === "pending" && <circle className="vs-mark-ring is-dashed" cx={c} cy={c} r={r} />}
      </svg>
      {label === true && <span>{DISPOSITION_LABELS[kind]}</span>}
      {label === false && <span className="vs-visually-hidden">{DISPOSITION_LABELS[kind]}</span>}
    </span>
  );
}

/** Method identity is a shape, never a colour: colour stays semantic. */
export type MethodShape = "triangle" | "diamond" | "circle" | "square";

export function shapePath(shape: MethodShape, x: number, y: number, r: number): string {
  switch (shape) {
    case "triangle":
      return `M ${x} ${y - r * 1.15} L ${x + r} ${y + r * 0.75} L ${x - r} ${y + r * 0.75} Z`;
    case "diamond":
      return `M ${x} ${y - r * 1.2} L ${x + r * 1.05} ${y} L ${x} ${y + r * 1.2} L ${x - r * 1.05} ${y} Z`;
    case "square":
      return `M ${x - r * 0.9} ${y - r * 0.9} h ${r * 1.8} v ${r * 1.8} h ${-r * 1.8} Z`;
    default:
      return `M ${x - r} ${y} a ${r} ${r} 0 1 0 ${r * 2} 0 a ${r} ${r} 0 1 0 ${-r * 2} 0`;
  }
}

export function MethodGlyph({ shape, size = 14 }: { shape: MethodShape; size?: number }) {
  return (
    <svg aria-hidden="true" className="vs-method-glyph" height={size} viewBox={`0 0 ${size} ${size}`} width={size}>
      <path d={shapePath(shape, size / 2, size / 2, size / 2 - 2.5)} />
    </svg>
  );
}
