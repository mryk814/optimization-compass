import numpy as np

def exact_objective(x):
    return float(np.sum((x - 1.0)**2))

x = np.zeros(2)
update_calls = diagnostic_calls = 0
for k, delta in enumerate(([1, 1], [1, -1], [1, 1]), start=1):
    delta = np.asarray(delta, dtype=float)
    y_plus = exact_objective(x + 0.1 * delta)
    y_minus = exact_objective(x - 0.1 * delta)
    update_calls += 2
    estimated_gradient = (y_plus - y_minus) / (0.2 * delta)
    x -= 0.1 * estimated_gradient
    value = exact_objective(x)
    diagnostic_calls += 1
    print(k, round(y_plus, 4), round(y_minus, 4),
          np.round(estimated_gradient, 4), np.round(x, 4), round(value, 4))
print(update_calls, diagnostic_calls)
# 1 1.62 2.42 [-4. -4.] [0.4 0.4] 0.72
# 2 0.74 0.74 [ 0. -0.] [0.4 0.4] 0.72
# 3 0.5 0.98 [-2.4 -2.4] [0.64 0.64] 0.2592
# 6 3


import numpy as np

rng = np.random.default_rng(7)


def objective(x: np.ndarray) -> float:
    noise = 0.01 * rng.normal()
    return float(np.sum((x - 1.0) ** 2) + noise)


x = np.zeros(20)
for iteration in range(1, 101):
    delta = rng.choice(np.array([-1.0, 1.0]), size=x.shape)
    a_k = 0.1 / (iteration ** 0.602)
    c_k = 0.1 / (iteration ** 0.101)
    y_plus = objective(x + c_k * delta)
    y_minus = objective(x - c_k * delta)
    gradient_estimate = (y_plus - y_minus) / (2.0 * c_k * delta)
    x = x - a_k * gradient_estimate

print(x[:3], objective(x))
