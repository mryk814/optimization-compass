import numpy as np
from scipy.optimize import minimize


def solve(n):
    h = 1.0 / n

    def rollout(u, exact=False):
        position = velocity = 0.0
        positions = [position]
        for value in u:
            position += h * velocity + (0.5 * h**2 * value if exact else 0.0)
            velocity += h * value
            positions.append(position)
        return np.array(positions), velocity

    def terminal(u):
        positions, velocity = rollout(u)
        return np.array([positions[-1] - 1.0, velocity])

    result = minimize(
        lambda u: h * np.sum(u**2),
        np.zeros(n),
        jac=lambda u: 2.0 * h * u,
        method="SLSQP",
        constraints={"type": "eq", "fun": terminal},
        options={"ftol": 1e-12, "maxiter": 200},
    )
    nodes, _ = rollout(result.x)
    exact, _ = rollout(result.x, exact=True)
    error = float(np.max(np.abs(exact - nodes)))
    print(n, result.success, round(float(result.fun), 6), round(error, 6))


for n in (2, 4, 10):
    solve(n)
