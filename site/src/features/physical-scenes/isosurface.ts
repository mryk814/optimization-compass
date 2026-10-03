/** Display-only isosurface of cell-centred FEM densities, with zero-density padding.
 * Six conforming tetrahedra share each cube's 0→6 diagonal. No density or solve is changed.
 * Coordinates and outward triangle winding use engineering x,y,z (right-handed).
 */
type Vec3 = readonly [number, number, number]

const corners: readonly Vec3[] = [
  [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
  [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
]
const tetrahedra = [[0, 1, 2, 6], [0, 2, 3, 6], [0, 3, 7, 6],
  [0, 7, 4, 6], [0, 4, 5, 6], [0, 5, 1, 6]]

export function densitySurface(
  density: readonly number[],
  grid: Vec3,
  spacing: Vec3,
  threshold: number,
): { positions: number[]; normals: number[] } {
  if (grid.some(n => !Number.isInteger(n) || n < 1)
    || spacing.some(n => !Number.isFinite(n) || n <= 0)
    || density.length !== grid[0] * grid[1] * grid[2]
    || density.some(n => !Number.isFinite(n))
    || !Number.isFinite(threshold) || threshold <= 0) {
    throw new Error('Invalid cell-centred density grid, spacing, or positive threshold')
  }
  const positions: number[] = []
  const normals: number[] = []
  const [nx, ny, nz] = grid
  const sample = (x: number, y: number, z: number): number =>
    x < 0 || y < 0 || z < 0 || x >= nx || y >= ny || z >= nz
      ? 0 : density[x + nx * (y + ny * z)]

  const triangle = (a: Vec3, b: Vec3, c: Vec3, outward: Vec3) => {
    const u = b.map((v, i) => v - a[i])
    const v = c.map((value, i) => value - a[i])
    let normal = [u[1] * v[2] - u[2] * v[1],
      u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    const length = Math.hypot(...normal)
    // Equality at a vertex can collapse an intersection triangle to a point/edge.
    if (length <= Number.EPSILON * Math.max(...spacing) ** 2) return
    if (normal.reduce((sum, value, i) => sum + value * outward[i], 0) < 0) {
      const temporary = b
      b = c
      c = temporary
      normal = normal.map(n => -n)
    }
    positions.push(...a, ...b, ...c)
    for (let i = 0; i < 3; i++) normals.push(...normal.map(n => n / length))
  }

  for (let z = -1; z < nz; z++) {
    for (let y = -1; y < ny; y++) {
      for (let x = -1; x < nx; x++) {
        const values = corners.map(([dx, dy, dz]) => sample(x + dx, y + dy, z + dz))
        if (values.every(v => v <= threshold) || values.every(v => v > threshold)) continue
        const points: Vec3[] = corners.map(([dx, dy, dz]) => [
          (x + dx + 0.5) * spacing[0], (y + dy + 0.5) * spacing[1],
          (z + dz + 0.5) * spacing[2],
        ])
        const crossing = (a: number, b: number): Vec3 => {
          const fraction = (threshold - values[a]) / (values[b] - values[a])
          return [0, 1, 2].map(i => points[a][i]
            + fraction * (points[b][i] - points[a][i])) as [number, number, number]
        }
        for (const tet of tetrahedra) {
          const inside = tet.filter(i => values[i] > threshold)
          const outside = tet.filter(i => values[i] <= threshold)
          if (inside.length === 0 || outside.length === 0) continue
          const outward = [0, 1, 2].map(axis =>
            outside.reduce((sum, i) => sum + points[i][axis], 0) / outside.length
            - inside.reduce((sum, i) => sum + points[i][axis], 0) / inside.length,
          ) as [number, number, number]
          if (inside.length === 1) {
            triangle(crossing(inside[0], outside[0]), crossing(inside[0], outside[1]),
              crossing(inside[0], outside[2]), outward)
          } else if (inside.length === 3) {
            triangle(crossing(outside[0], inside[0]), crossing(outside[0], inside[1]),
              crossing(outside[0], inside[2]), outward)
          } else {
            const a = crossing(inside[0], outside[0])
            const b = crossing(inside[0], outside[1])
            const c = crossing(inside[1], outside[0])
            const d = crossing(inside[1], outside[1])
            triangle(a, b, c, outward)
            triangle(b, d, c, outward)
          }
        }
      }
    }
  }
  return { positions, normals }
}
