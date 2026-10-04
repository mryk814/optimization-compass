x, velocity = 2.0, 0.0
eta, beta = 0.1, 0.5
for k in range(1, 9):
    gradient = 2.0 * (x - 1.0)  # 必ず更新前の点で計算する
    carry = beta * velocity
    velocity = carry + gradient
    x -= eta * velocity
    print(k, round(gradient, 6), round(carry, 6),
          round(velocity, 6), round(x, 6), round((x - 1.0)**2, 8))
# 1 2.0 0.0 2.0 1.8 0.64
# 2 1.6 1.0 2.6 1.54 0.2916
# 3 1.08 1.3 2.38 1.302 0.091204
# 6 0.01676 0.5711 0.58786 0.949594 0.00254076


import numpy as np


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 40.0 * (x[1] + 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 80.0 * (x[1] + 2.0)])


x = np.array([4.0, 3.0])
velocity = np.zeros_like(x)
learning_rate = 0.02
momentum = 0.85

for _ in range(2_000):
    g = gradient(x)
    velocity = momentum * velocity + g
    candidate = x - learning_rate * velocity
    if not np.isfinite(objective(candidate)):
        raise FloatingPointError("non-finite objective")
    x = candidate
    if np.linalg.norm(gradient(x)) < 1e-8 and np.linalg.norm(velocity) < 1e-8:
        break

print(x, objective(x), np.linalg.norm(gradient(x)))
