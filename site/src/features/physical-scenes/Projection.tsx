import type { SceneDrawing, Vec3 } from "./types";

/** Orthographic projection of the exact same snapshot as the 3D viewport. */
export function Projection({ drawing, plane = "xz" }: { drawing: SceneDrawing; plane?: "xz" | "xy" }) {
  const axis = plane === "xz" ? 2 : 1;
  const r = drawing.radius;
  const px = (p: Vec3) => 170 + (p[0] - drawing.center[0]) * 140 / r;
  const py = (p: Vec3) => 120 - (p[axis] - drawing.center[axis]) * 105 / r;
  return <figure className="physical-projection">
    <figcaption>{plane === "xz" ? "横からの射影（x–z）" : "上からの射影（x–y）"}</figcaption>
    <svg viewBox="0 0 340 240" role="img" aria-label="3Dと同じ状態の2D射影">
      <line x1="18" x2="322" y1="222" y2="222" stroke="#c5d4d8" />
      <line x1="18" x2="18" y1="18" y2="222" stroke="#c5d4d8" />
      {(drawing.boxes ?? []).map((box, i) => <rect key={`b${i}`} x={px(box.center) - box.size[0] * 70 / r}
        y={py(box.center) - box.size[axis] * 52.5 / r} width={box.size[0] * 140 / r}
        height={box.size[axis] * 105 / r} fill={box.color} opacity={box.opacity ?? 1} />)}
      {(drawing.spheres ?? []).map((sphere, i) => <ellipse key={`s${i}`} cx={px(sphere.center)} cy={py(sphere.center)}
        rx={sphere.radius * 140 / r} ry={sphere.radius * 105 / r} fill={sphere.color} opacity={sphere.opacity ?? 1} />)}
      {(drawing.lines ?? []).map((line, i) => <polyline key={`l${i}`} points={line.points.map(p => `${px(p)},${py(p)}`).join(" ")}
        stroke={line.color} strokeWidth="2" fill="none" strokeDasharray={line.dashed ? "5 4" : undefined} />)}
      {(drawing.rods ?? []).map((rod, i) => <line key={`r${i}`} x1={px(rod.from)} y1={py(rod.from)} x2={px(rod.to)} y2={py(rod.to)}
        stroke={rod.color} strokeWidth={Math.max(3, rod.radius * 200 / r)} strokeLinecap="round" />)}
      {(drawing.arrows ?? []).map((arrow, i) => {
        const magnitude = Math.hypot(...arrow.direction);
        const end = arrow.from.map((v, axis) => v + arrow.direction[axis] / magnitude * arrow.length) as unknown as Vec3;
        const x = px(end); const y = py(end); const dx = x - px(arrow.from); const dy = y - py(arrow.from);
        const length = Math.hypot(dx, dy);
        if (length < 0.01) return null;
        const ux = dx / length; const uy = dy / length;
        return <g key={`a${i}`}>
          <line x1={px(arrow.from)} y1={py(arrow.from)} x2={x} y2={y} stroke={arrow.color} strokeWidth="2" />
          <polygon points={`${x},${y} ${x - ux * 7 + uy * 3},${y - uy * 7 - ux * 3} ${x - ux * 7 - uy * 3},${y - uy * 7 + ux * 3}`} fill={arrow.color} />
        </g>;
      })}
      {(drawing.voxels?.centers ?? []).map((p, i) => <rect key={`v${i}`} x={px(p) - drawing.voxels!.size[0] * 70 / r}
        y={py(p) - drawing.voxels!.size[axis] * 52.5 / r} width={drawing.voxels!.size[0] * 140 / r}
        height={drawing.voxels!.size[axis] * 105 / r} fill={drawing.voxels!.colors[i]} opacity="0.75" />)}
    </svg>
    <p>3D図と同じ時点を横から見ています。奥行き方向に重なる部分は、この図だけでは区別できません。</p>
  </figure>;
}
