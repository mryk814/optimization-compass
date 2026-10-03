"""Offline 3-D compliance minimization for the educational physical scene.

The numerical authority is this generator, not the rounded scene JSON. Eight-node
isoparametric bricks use 2 x 2 x 2 Gauss integration and engineering shear strains.
SIMP interpolates Young's modulus; a *density* filter precedes both the equilibrium
solve and volume evaluation, so its transpose belongs in the chain-rule gradient.
No stiffness tables or source-program implementation are copied.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import spsolve

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


def brick_stiffness(spacing: tuple[float, float, float], poisson: float = 0.3) -> FloatArray:
    """Unit-Young-modulus stiffness, local corners ordered by x + 2(y + 2z)."""
    if not -1 < poisson < 0.5 or min(spacing) <= 0:
        raise ValueError("Invalid isotropic elasticity parameters")
    lam = poisson / ((1 + poisson) * (1 - 2 * poisson))
    mu = 1 / (2 * (1 + poisson))
    elasticity = np.zeros((6, 6))
    elasticity[:3, :3] = lam
    elasticity[np.arange(3), np.arange(3)] += 2 * mu
    elasticity[3:, 3:] = np.eye(3) * mu
    signs = np.array(
        [[2 * x - 1, 2 * y - 1, 2 * z - 1] for z in range(2) for y in range(2) for x in range(2)]
    )
    matrix = np.zeros((24, 24))
    gauss = (-1 / np.sqrt(3), 1 / np.sqrt(3))
    for xi in gauss:
        for eta in gauss:
            for zeta in gauss:
                natural = np.array([xi, eta, zeta])
                derivatives = np.empty((8, 3))
                for axis in range(3):
                    others = [i for i in range(3) if i != axis]
                    derivatives[:, axis] = (
                        signs[:, axis]
                        / 8
                        * np.prod(1 + signs[:, others] * natural[others], axis=1)
                        * 2
                        / spacing[axis]
                    )
                strain = np.zeros((6, 24))
                for node, (dx, dy, dz) in enumerate(derivatives):
                    column = 3 * node
                    strain[0, column] = dx
                    strain[1, column + 1] = dy
                    strain[2, column + 2] = dz
                    strain[3, column : column + 2] = (dy, dx)
                    strain[4, column + 1 : column + 3] = (dz, dy)
                    strain[5, [column, column + 2]] = (dz, dx)
                matrix += strain.T @ elasticity @ strain * np.prod(spacing) / 8
    return matrix


@dataclass
class Equilibrium:
    displacement: FloatArray
    compliance: float
    element_energy: FloatArray
    residual: float
    energy_error: float


class Cantilever:
    """Regular solid mesh; x = 0 clamped, downward tip load spread across depth."""

    def __init__(self, grid: tuple[int, int, int] = (16, 8, 6), radius: float = 1.5):
        if min(grid) < 2 or radius <= 0:
            raise ValueError("At least two cells per axis and a positive filter radius required")
        self.grid = grid
        self.radius = radius
        self.spacing = (1.0, 1.0, 1.0)
        nx, ny, nz = grid
        self.count = nx * ny * nz
        self.node_count = (nx + 1) * (ny + 1) * (nz + 1)
        self.stiffness = brick_stiffness(self.spacing)
        self.penalty = 3.0
        self.minimum_modulus = 1e-6
        self.coordinates = np.array(
            [[x, y, z] for z in range(nz + 1) for y in range(ny + 1) for x in range(nx + 1)],
            dtype=float,
        )
        elements = []
        for z in range(nz):
            for y in range(ny):
                for x in range(nx):
                    nodes = [
                        self.node(x + dx, y + dy, z + dz)
                        for dz in range(2)
                        for dy in range(2)
                        for dx in range(2)
                    ]
                    elements.append([3 * node + axis for node in nodes for axis in range(3)])
        self.dofs: IntArray = np.array(elements, dtype=np.int64)
        self.rows = np.repeat(self.dofs, 24, axis=1).ravel()
        self.columns = np.tile(self.dofs, (1, 24)).ravel()
        fixed = np.flatnonzero(np.repeat(self.coordinates[:, 0] == 0, 3))
        self.free = np.setdiff1d(np.arange(3 * self.node_count), fixed)
        self.force = np.zeros(3 * self.node_count)
        self.loads: list[dict[str, Any]] = []
        for z in range(nz + 1):
            position = [nx, 0, z]
            force = [0.0, -1.0 / (nz + 1), 0.0]
            self.force[3 * self.node(*position) + 1] = force[1]
            self.loads.append({"position": position, "force": force})
        centers = np.array(
            [[x, y, z] for z in range(nz) for y in range(ny) for x in range(nx)], dtype=float
        )
        # This small offline mesh permits a direct pairwise construction. Assembly
        # and repeated equilibrium solves remain sparse.
        distance = np.linalg.norm(centers[:, None] - centers[None, :], axis=2)
        self.filter: csr_matrix = csr_matrix(np.maximum(0, radius - distance))
        self.filter_sum: FloatArray = np.asarray(self.filter.sum(axis=1)).ravel()
        self.volume_gradient: FloatArray = np.asarray(
            self.filter.T @ (np.ones(self.count) / self.filter_sum / self.count)
        ).ravel()

    def node(self, x: int, y: int, z: int) -> int:
        nx, ny, _ = self.grid
        return x + (nx + 1) * (y + (ny + 1) * z)

    def physical_density(self, design: FloatArray) -> FloatArray:
        return np.asarray(self.filter @ design).ravel() / self.filter_sum

    def solve(self, density: FloatArray) -> Equilibrium:
        modulus = self.minimum_modulus + (1 - self.minimum_modulus) * density**self.penalty
        values = (modulus[:, None, None] * self.stiffness[None]).ravel()
        matrix = coo_matrix(
            (values, (self.rows, self.columns)), shape=(3 * self.node_count, 3 * self.node_count)
        ).tocsr()
        displacement = np.zeros_like(self.force)
        displacement[self.free] = spsolve(matrix[self.free][:, self.free], self.force[self.free])
        local = displacement[self.dofs]
        element_energy = np.einsum("ei,ij,ej->e", local, self.stiffness, local)
        compliance = float(self.force @ displacement)
        energy = float(modulus @ element_energy)
        residual = float(
            np.linalg.norm((matrix @ displacement - self.force)[self.free])
            / np.linalg.norm(self.force[self.free])
        )
        return Equilibrium(
            displacement,
            compliance,
            element_energy,
            residual,
            abs(energy - compliance) / compliance,
        )

    def gradient(self, density: FloatArray, equilibrium: Equilibrium) -> FloatArray:
        physical = (
            -self.penalty
            * (1 - self.minimum_modulus)
            * density ** (self.penalty - 1)
            * equilibrium.element_energy
        )
        return np.asarray(self.filter.T @ (physical / self.filter_sum)).ravel()

    def update(self, design: FloatArray, gradient: FloatArray, fraction: float) -> FloatArray:
        low, high = 0.0, 1e10
        updated = design.copy()
        for _ in range(100):
            multiplier = (low + high) / 2
            candidate = design * np.sqrt(
                np.maximum(0, -gradient) / (self.volume_gradient * multiplier)
            )
            updated = np.clip(
                candidate, np.maximum(0.001, design - 0.15), np.minimum(1.0, design + 0.15)
            )
            if self.physical_density(updated).mean() > fraction:
                low = multiplier
            else:
                high = multiplier
            if (high - low) / (high + low) < 1e-9:
                break
        return updated

    def optimize(self, fraction: float, iterations: int = 100) -> dict[str, Any]:
        if not 0.01 < fraction < 1 or iterations < 1:
            raise ValueError("Invalid optimization budget or material fraction")
        design = np.full(self.count, fraction)
        frames: list[dict[str, Any]] = []
        worst_residual, worst_energy = 0.0, 0.0
        initial_compliance = 0.0
        change = 0.0
        for iteration in range(iterations + 1):
            density = self.physical_density(design)
            state = self.solve(density)
            if iteration == 0:
                initial_compliance = state.compliance
            worst_residual = max(worst_residual, state.residual)
            worst_energy = max(worst_energy, state.energy_error)
            if (
                not np.isfinite(state.compliance)
                or state.residual > 1e-6
                or state.energy_error > 1e-6
            ):
                raise RuntimeError("Equilibrium solve failed its residual contract")
            finished = iteration == iterations or (iteration >= 40 and change < 0.002)
            if iteration % 5 == 0 or finished:
                frame: dict[str, Any] = {
                    "iteration": iteration,
                    "density": np.round(density, 5).tolist(),
                    "compliance": round(state.compliance, 7),
                    "volume": round(float(density.mean()), 8),
                    "residual": state.residual,
                    "maxDisplacement": float(
                        np.linalg.norm(state.displacement.reshape(-1, 3), axis=1).max()
                    ),
                }
                # Complete nodal vectors in the final state enable a deformed mesh;
                # rounding is exclusively a display-size decision after validation.
                if finished:
                    frame["nodeDisplacements"] = np.round(
                        state.displacement.reshape(-1, 3), 5
                    ).tolist()
                frames.append(frame)
            if finished:
                break
            updated = self.update(design, self.gradient(density, state), fraction)
            change = float(np.max(np.abs(updated - design)))
            design = updated
        analytic = self.gradient(density, state)
        sensitivity_error = 0.0
        # Probe three strongly loaded elements: relative finite differences in
        # almost-void cells are dominated by subtraction roundoff, not mechanics.
        for element in np.argsort(np.abs(analytic))[-3:]:
            step = np.zeros(self.count)
            step[element] = 1e-4
            plus = self.solve(self.physical_density(design + step)).compliance
            minus = self.solve(self.physical_density(design - step)).compliance
            numerical = (plus - minus) / 2e-4
            sensitivity_error = max(
                sensitivity_error,
                abs(numerical - analytic[element]) / max(abs(analytic[element]), 1e-8),
            )
        if sensitivity_error > 1e-3:
            raise RuntimeError("Sensitivity failed its finite-difference contract")
        return {
            "id": f"volume-{int(fraction * 100)}",
            "label": f"材料量 {fraction:.0%}",
            "frames": frames,
            "metrics": {
                "volumeFraction": fraction,
                "initialCompliance": initial_compliance,
                "finalCompliance": state.compliance,
                "complianceReduction": 1 - state.compliance / initial_compliance,
                "maxEquilibriumResidual": worst_residual,
                "maxEnergyEqualityError": worst_energy,
                "maxSensitivityRelativeError": float(sensitivity_error),
                "finalDesignChange": change,
                "iterations": iteration,
                "stopReason": "design-change" if iteration < iterations else "iteration-budget",
                "youngModulus": 1.0,
                "poissonRatio": 0.3,
                "simpPenalty": self.penalty,
                "minimumModulus": self.minimum_modulus,
                "densityFilterRadius": self.radius,
            },
        }


def generate_topology_scene() -> dict[str, Any]:
    mesh = Cantilever()
    return {
        "grid": list(mesh.grid),
        "spacing": list(mesh.spacing),
        "supports": [{"axis": "x", "value": 0}],
        "loads": mesh.loads,
        "variants": [mesh.optimize(fraction) for fraction in (0.25, 0.4, 0.55)],
        "model": "3D linear elasticity / 8-node hexahedra / SIMP / density filter / OC",
        "sources": [
            {
                "title": "Liu & Tovar (2014), An efficient 3D topology optimization "
                "code written in Matlab",
                "url": "https://doi.org/10.1007/s00158-014-1107-x",
            }
        ],
        "limitations": [
            "無次元の教育用片持ち梁。16×8×6 要素の離散解であり、実製品の設計保証ではありません。",
            "微小変形・等方線形弾性を仮定。座屈、塑性、疲労、製造制約は扱いません。",
            "SIMP の非凸問題を OC 法で解きます。大域最適性を保証せず、"
            "反復予算で停止する場合があります。",
            "密度は連続値です。表示のしきい値で消した部分も有限要素計算では小さな剛性を持ちます。",
            "変形表示は拡大した模式図です。中間密度を含む計算値から"
            "最終形状だけの強度は推定できません。",
        ],
    }
