import numpy as np

B = np.array([[3., 2.], [1., 3.]])
b = np.array([18., 13.])
c2 = np.array([-3., -4.])

def center(mu):
    u = np.array([2., 2.])
    def barrier(v):
        z = np.r_[v, b - B @ v]
        return c2 @ v - mu*np.log(z).sum() if np.all(z > 0) else np.inf
    for _ in range(100):
        slack = b - B @ u
        g = c2 - mu/u + mu*B.T @ (1/slack)
        H = np.diag(mu/u**2) + mu*B.T @ np.diag(1/slack**2) @ B
        if np.linalg.norm(g, np.inf) < 1e-10:
            break
        direction = np.linalg.solve(H, -g)
        alpha = 1.0
        while barrier(u + alpha*direction) > barrier(u) + .01*alpha*(g @ direction):
            alpha *= .5
            if alpha < 1e-14:
                raise RuntimeError("line search stalled")
        u += alpha*direction
    x = np.r_[u, b - B @ u]
    s = mu/x
    y = -s[2:]
    A = np.c_[B, np.eye(2)]
    c = np.r_[c2, 0., 0.]
    assert np.linalg.norm(A @ x - b) < 1e-10
    assert np.linalg.norm(A.T @ y + s - c) < 1e-8
    assert np.max(abs(x*s - mu)) < 1e-10
    return u, float(-c @ x), float(x @ s)

for mu in (10., 1., .1, .01):
    u, revenue, gap = center(mu)
    print(mu, np.round(u, 3), round(revenue, 2), round(gap, 4))
# 10.0 [2.638 1.855] 15.33 40.0
# 1.0 [3.752 2.727] 22.17 4.0
# 0.1 [3.974 2.97 ] 23.8 0.4
# 0.01 [3.997 2.997] 23.98 0.04


import numpy as np
from scipy.optimize import linprog

# 最小化 c^T x  s.t.  A x = b,  x >= 0（主スラック t1, t2 を含む標準形）
A = np.array([[3.0, 2.0, 1.0, 0.0], [1.0, 3.0, 0.0, 1.0]])
b = np.array([18.0, 13.0])
c = np.array([-3.0, -4.0, 0.0, 0.0])

x, y, s = np.ones(4), np.zeros(2), np.ones(4)  # 正値だが Ax=b と A.T@y+s=c は未充足
sigma = 0.3  # 現在の平均相補性から目標相補性を作る
history = []
for k in range(9):
    mu = x @ s / 4
    print(k, x[:2].round(3), round(-(c @ x), 3), round(x @ s, 4),
          round(float(np.linalg.norm(A @ x - b)), 4))
    r_primal = A @ x - b
    r_dual = A.T @ y + s - c
    history.append((float(np.linalg.norm(r_primal)),
                    float(np.linalg.norm(r_dual)), float(x @ s)))
    r_center = x * s - sigma * mu
    # Newton方程式を、dy についての小さな線形系に整理して解く
    d = x / s
    rhs = -r_primal - A @ ((-r_center + x * r_dual) / s)
    dy = np.linalg.solve(A @ (d[:, None] * A.T), rhs)
    ds = -r_dual - A.T @ dy
    dx = (-r_center - x * ds) / s
    # x と s が正のままでいられる最大の歩幅の 0.99 倍だけ進む
    step = 1.0
    for v, dv in ((x, dx), (s, ds)):
        if (dv < 0).any():
            step = min(step, 0.99 * float(np.min(-v[dv < 0] / dv[dv < 0])))
    x, y, s = x + step * dx, y + step * dy, s + step * ds

result = linprog(c[:2], A_ub=[[3, 2], [1, 3]], b_ub=[18, 13],
                 bounds=[(0, None)] * 2, method="highs-ipm")
print(result.x.round(3), round(-result.fun, 3), result.status)
