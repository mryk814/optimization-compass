import numpy as np

target = np.array([0.65, 0.25, 0.10])


def loss(p: np.ndarray) -> float:
    return float(0.5 * np.sum((p - target) ** 2))


def loss_gradient(p: np.ndarray) -> np.ndarray:
    return p - target


def exponentiated_gradient_step(p: np.ndarray, g: np.ndarray, eta: float) -> np.ndarray:
    """負のエントロピーを mirror map に使った更新: p_i ∝ p_i exp(-eta g_i)。"""
    if np.any(p <= 0) or not np.all(np.isfinite(p)):
        raise ValueError("p must be strictly positive and finite")
    log_weight = np.log(p) - eta * g
    log_weight -= np.max(log_weight)          # overflow を避ける
    weight = np.exp(log_weight)
    result = weight / weight.sum()
    if np.any(result == 0):
        raise FloatingPointError("underflow: consider storing log probabilities")
    return result


def euclidean_step_with_projection(p: np.ndarray, g: np.ndarray, eta: float) -> np.ndarray:
    """比較用: ユークリッドの一手を、単体へ射影する。"""
    v = p - eta * g
    u = np.sort(v)[::-1]
    cumulative = np.cumsum(u) - 1.0
    k = np.nonzero(u * np.arange(1, v.size + 1) > cumulative)[0][-1]
    return np.maximum(v - cumulative[k] / (k + 1), 0.0)


p = np.full(3, 1.0 / 3.0)
for k in range(4):
    print(k, np.round(p, 4), round(loss(p), 4))
    p = exponentiated_gradient_step(p, loss_gradient(p), eta=0.8)
# 0 [0.3333 0.3333 0.3333] 0.0808
# 1 [0.4219 0.3064 0.2717] 0.0423
# 2 [0.4887 0.2827 0.2286] 0.0218
# 3 [0.5359 0.2654 0.1988] 0.0115

start = np.full(3, 1.0 / 3.0)
g = loss_gradient(start)
print(np.round(start - 3.0 * g, 3))                                  # ユークリッドの一手そのもの
# [ 1.283  0.083 -0.367]
print(np.round(euclidean_step_with_projection(start, g, 3.0), 3))   # 射影後
# [1. 0. 0.]
print(np.round(exponentiated_gradient_step(start, g, 3.0), 3))      # 指数化勾配の一手
# [0.67  0.202 0.129]

p = np.full(3, 1.0 / 3.0)
for k in range(1, 501):
    g = loss_gradient(p)
    if np.linalg.norm(g) < 1e-9:
        break
    p = exponentiated_gradient_step(p, g, 0.8)
print(k, p, p.sum())
# 167 [0.65 0.25 0.1 ] 1.0
