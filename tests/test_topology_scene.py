"""Independent mechanics checks for the offline topology generator."""

import numpy as np
import pytest

from optimization_compass.topology_scene import Cantilever, brick_stiffness


def test_brick_rigid_modes_and_affine_patch_energy() -> None:
    spacing = (2.0, 3.0, 4.0)
    stiffness = brick_stiffness(spacing)
    nodes = np.array([[x, y, z] for z in (0, 4) for y in (0, 3) for x in (0, 2)])
    assert np.allclose(stiffness, stiffness.T, atol=1e-14)
    eigenvalues = np.linalg.eigvalsh(stiffness)
    assert np.sum(np.abs(eigenvalues) < 1e-10) == 6
    assert eigenvalues[6] > 0
    for translation in np.eye(3):
        assert np.linalg.norm(stiffness @ np.tile(translation, 8)) < 1e-12
    for axis in np.eye(3):
        rotation = np.cross(np.tile(axis, (8, 1)), nodes).ravel()
        assert np.linalg.norm(stiffness @ rotation) < 1e-12
    # An affine strain is integrated exactly: u_x = alpha*x, all other u = 0.
    displacement = np.zeros((8, 3))
    displacement[:, 0] = 0.01 * nodes[:, 0]
    nu = 0.3
    c11 = (1 - nu) / ((1 + nu) * (1 - 2 * nu))
    expected = np.prod(spacing) * c11 * 0.01**2
    assert displacement.ravel() @ stiffness @ displacement.ravel() == pytest.approx(expected)


def test_equilibrium_energy_and_density_filter_chain_rule() -> None:
    mesh = Cantilever((4, 3, 2))
    design = np.linspace(0.3, 0.7, mesh.count)
    density = mesh.physical_density(design)
    state = mesh.solve(density)
    assert state.residual < 1e-9
    assert state.energy_error < 1e-10
    assert state.compliance > 0
    assert np.all(state.displacement.reshape(-1, 3)[mesh.coordinates[:, 0] == 0] == 0)
    analytic = mesh.gradient(density, state)
    for element in (0, 9, 23):
        perturbation = np.zeros(mesh.count)
        perturbation[element] = 1e-5
        plus = mesh.solve(mesh.physical_density(design + perturbation)).compliance
        minus = mesh.solve(mesh.physical_density(design - perturbation)).compliance
        assert analytic[element] == pytest.approx((plus - minus) / 2e-5, rel=2e-6)
        volume_difference = (
            mesh.physical_density(design + perturbation).mean()
            - mesh.physical_density(design - perturbation).mean()
        ) / 2e-5
        assert mesh.volume_gradient[element] == pytest.approx(volume_difference, rel=1e-8)


@pytest.mark.parametrize("fraction", [0.25, 0.4, 0.55])
def test_oc_respects_material_budget_and_improves_compliance(fraction: float) -> None:
    mesh = Cantilever((6, 4, 3))
    variant = mesh.optimize(fraction, iterations=35)
    frames = variant["frames"]
    assert frames[-1]["compliance"] < 0.8 * frames[0]["compliance"]
    for frame in frames:
        assert frame["volume"] <= fraction + 1e-7
        assert min(frame["density"]) >= 0.001
        assert max(frame["density"]) <= 1
        assert frame["residual"] < 1e-8
    assert variant["metrics"]["maxEnergyEqualityError"] < 1e-9
    assert len(frames[-1]["nodeDisplacements"]) == mesh.node_count
