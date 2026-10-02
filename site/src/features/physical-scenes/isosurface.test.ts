import { describe, expect, it } from 'vitest'
import { densitySurface } from './isosurface'

function signedVolume(positions: number[]) {
  let volume = 0
  for (let i = 0; i < positions.length; i += 9) {
    const [ax, ay, az, bx, by, bz, cx, cy, cz] = positions.slice(i, i + 9)
    volume += (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz)
      + az * (bx * cy - by * cx)) / 6
  }
  return volume
}

function assertClosed(positions: number[]) {
  const edges = new Map<string, number>()
  const point = (offset: number) => positions.slice(offset, offset + 3)
    .map(n => n.toFixed(8)).join(',')
  for (let i = 0; i < positions.length; i += 9) {
    for (const [a, b] of [[0, 3], [3, 6], [6, 0]]) {
      const key = [point(i + a), point(i + b)].sort().join('|')
      edges.set(key, (edges.get(key) ?? 0) + 1)
    }
  }
  expect([...edges.values()].every(n => n === 2)).toBe(true)
}

describe('cell-centred marching tetrahedra surface', () => {
  it('returns no geometry for air and closes all exterior faces of uniform solid', () => {
    expect(densitySurface(Array(24).fill(0), [4, 3, 2], [1, 2, 3], 0.5).positions).toEqual([])
    const surface = densitySurface(Array(24).fill(1), [4, 3, 2], [1, 2, 3], 0.5)
    const axes = [0, 1, 2].map(axis => surface.positions.filter((_, i) => i % 3 === axis))
    expect(axes.map(a => Math.min(...a))).toEqual([0, 0, 0])
    expect(axes.map(a => Math.max(...a))).toEqual([4, 6, 6])
    assertClosed(surface.positions)
    expect(signedVolume(surface.positions)).toBeGreaterThan(0)
    expect(surface.normals.every(Number.isFinite)).toBe(true)
    for (let i = 0; i < surface.normals.length; i += 3) {
      expect(Math.hypot(...surface.normals.slice(i, i + 3))).toBeCloseTo(1)
    }
  })

  it('linearly places an interior plane crossing in x-fastest indexing', () => {
    const density = Array.from({ length: 64 }, (_, i) => (i % 4) / 3)
    const { positions, normals } = densitySurface(density, [4, 4, 4], [1, 1, 1], 0.5)
    let interiorTriangles = 0
    for (let i = 0; i < positions.length; i += 9) {
      const vertices = [0, 3, 6].map(j => positions.slice(i + j, i + j + 3))
      if (vertices.every(p => p[1] >= 1 && p[1] <= 3 && p[2] >= 1 && p[2] <= 3
        && p[0] < 3)) {
        interiorTriangles++
        for (const point of vertices) expect(point[0]).toBeCloseTo(2)
        expect(normals[i]).toBeCloseTo(-1)
      }
    }
    expect(interiorTriangles).toBeGreaterThan(0)
    assertClosed(positions)
  })

  it('has outward winding and approximately spherical volume on a sampled sphere', () => {
    const n = 18
    const spacing = 0.2
    const radius = 1.2
    const density = Array.from({ length: n ** 3 }, (_, i) => {
      const x = (i % n + 0.5) * spacing - n * spacing / 2
      const y = (Math.floor(i / n) % n + 0.5) * spacing - n * spacing / 2
      const z = (Math.floor(i / n ** 2) + 0.5) * spacing - n * spacing / 2
      return 0.5 + (radius - Math.hypot(x, y, z)) / 4
    })
    const { positions } = densitySurface(density, [n, n, n], [spacing, spacing, spacing], 0.5)
    assertClosed(positions)
    const expected = 4 / 3 * Math.PI * radius ** 3
    expect(Math.abs(signedVolume(positions) / expected - 1)).toBeLessThan(0.03)
  })

  it('skips collapsed equality triangles and rejects invalid inputs', () => {
    const surface = densitySurface([0, 0.5, 1], [3, 1, 1], [1, 1, 1], 0.5)
    expect(surface.positions.every(Number.isFinite)).toBe(true)
    expect(surface.normals.every(Number.isFinite)).toBe(true)
    expect(() => densitySurface([NaN], [1, 1, 1], [1, 1, 1], 0.5)).toThrow()
    expect(() => densitySurface([], [1, 1, 1], [1, 1, 1], 0.5)).toThrow()
    expect(() => densitySurface([1], [1, 1, 1], [1, 1, 1], 0)).toThrow()
  })
})
