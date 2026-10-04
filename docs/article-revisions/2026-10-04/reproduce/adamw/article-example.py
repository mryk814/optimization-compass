import math

x, m, v = 2.0, 0.0, 0.0
for k in range(1, 4):
    g = 2.0 * (x - 1.0)
    m = 0.9 * m + 0.1 * g
    v = 0.999 * v + 0.001 * g * g
    gradient_step = 0.1 * (m / (1.0 - 0.9**k)) / (
        math.sqrt(v / (1.0 - 0.999**k)) + 1e-8
    )
    decay = 0.1 * 0.1 * x
    x -= gradient_step + decay
    print(k, round(gradient_step, 6), round(decay, 6),
          round(x, 6), round((x - 1.0)**2, 6))


import math

x0, eta, lam, eps = 2.0, 0.1, 0.1, 1e-8
g_data = 2.0 * (x0 - 1.0)
g_l2 = g_data + lam * x0
# 初回の補正後モーメントは g と g^2
adam_l2 = x0 - eta * g_l2 / (math.sqrt(g_l2*g_l2) + eps)
adamw = (1.0 - eta * lam) * x0 - eta * g_data / (abs(g_data) + eps)
print(round(adam_l2, 6), round(adamw, 6))
# 1.9 1.88
