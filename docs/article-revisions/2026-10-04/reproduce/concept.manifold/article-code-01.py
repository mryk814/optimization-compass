import numpy as np

x = np.array([1.0, 0.0])
g = np.array([0.2, -1.0])
grad = g - x * (x @ g)
xi = -0.5 * grad

def retract(x, xi):
    if not np.isclose(x @ x, 1.0) or not np.isclose(x @ xi, 0.0):
        raise ValueError("unit point and tangent step required")
    y = x + xi
    return y / np.linalg.norm(y)

next_x = retract(x, xi)
assert abs(x @ grad) < 1e-12
assert abs(np.linalg.norm(next_x) - 1.0) < 1e-12
print(next_x, g @ next_x)
for h in (1e-2, 1e-3, 1e-4):
    error = np.linalg.norm((retract(x, h * xi) - x) / h - xi)
    print(h, error)
