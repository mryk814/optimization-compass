import numpy as np
from scipy.optimize import minimize


def solve(steps=20):
    h = 1.0 / steps
    n = 2 * steps + 1
    C = np.zeros((steps + 2, n))
    C[0, 0] = 1.0
    C[-1, steps] = 1.0
    for k in range(steps):
        C[k + 1, k] = -1.0
        C[k + 1, k + 1] = 1.0
        C[k + 1, steps + 1 + k] = -h
    rhs = np.zeros(steps + 2)
    rhs[-1] = 1.0

    def cost(z):
        return h * (z[steps + 1:] @ z[steps + 1:])

    def grad(z):
        return np.r_[np.zeros(steps + 1), 2 * h * z[steps + 1:]]

    initial = np.r_[np.linspace(0, 1, steps + 1), np.zeros(steps)]
    result = minimize(cost, initial, jac=grad, method='SLSQP',
                      constraints={'type': 'eq', 'fun': lambda z: C @ z - rhs,
                                   'jac': lambda z: C},
                      bounds=[(None, None)] * (steps + 1) + [(-2, 2)] * steps,
                      options={'ftol': 1e-12, 'maxiter': 200})
    assert result.success, result.message
    print(steps, 'initial:', cost(initial), np.linalg.norm(C @ initial - rhs))
    print(steps, 'solved:', cost(result.x), np.linalg.norm(C @ result.x - rhs))
    return result.x, initial, C, rhs

if __name__ == '__main__':
    solve(20)
