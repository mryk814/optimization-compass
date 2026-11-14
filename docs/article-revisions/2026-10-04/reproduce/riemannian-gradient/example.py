import numpy as np

A = np.diag([1.0, 2.0])
x = np.ones(2) / np.sqrt(2.0)
for k in range(31):
    f = float(x @ A @ x)
    g = 2.0 * (A @ x - f * x)
    assert abs(x @ g) < 1e-12
    assert abs(x @ x - 1.0) < 1e-12
    if k <= 3:
        print(k, x, f, np.linalg.norm(g))
    if k < 30:
        y = x - 0.25 * g
        x = y / np.linalg.norm(y)

# Independent oracle: smallest eigenvalue, with sign ambiguity.
w, V = np.linalg.eigh(A)
assert abs(x @ A @ x - w[0]) < 1e-12
assert min(np.linalg.norm(x - V[:, 0]),
           np.linalg.norm(x + V[:, 0])) < 1e-8

# Angular directional derivative at the same initial point.
theta, h = np.pi / 4, 1e-6
F = lambda t: np.cos(t)**2 + 2 * np.sin(t)**2
finite_difference = (F(theta + h) - F(theta - h)) / (2 * h)
x0 = np.array([np.cos(theta), np.sin(theta)])
tangent = np.array([-np.sin(theta), np.cos(theta)])
g0 = 2 * (A @ x0 - (x0 @ A @ x0) * x0)
assert abs(finite_difference - tangent @ g0) < 1e-8
print('final cost:', x @ A @ x)
