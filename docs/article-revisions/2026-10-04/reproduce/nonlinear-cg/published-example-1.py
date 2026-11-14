import numpy as np
import scipy
from scipy.optimize import minimize

H = np.diag([2.0, 40.0])
target = np.array([1.0, -2.0])
f = lambda x: (x[0] - 1)**2 + 20*(x[1] + 2)**2
grad = lambda x: H @ (x - target)

# 教材用 FR ＋厳密直線探索。SciPy CG の再実装ではない。
x = np.array([4.0, 3.0])
g = grad(x)
p = -g
for k in range(2):
    alpha = -(g @ p) / (p @ H @ p)
    xn = x + alpha*p
    gn = grad(xn)
    beta = (gn @ gn) / (g @ g)
    print(k, alpha, xn, f(xn))
    x, g, p = xn, gn, -gn + beta*p

# SciPy の PR+。停止ノルムと許容を明示する。
result = minimize(f, [4.0, 3.0], jac=grad, method="CG",
                  options={"gtol": 1e-5, "norm": np.inf,
                           "c1": 1e-4, "c2": 0.4, "maxiter": 400})
print(scipy.__version__, result.success, result.nit,
      result.nfev, result.njev, np.linalg.norm(grad(result.x), np.inf))
# SciPy 1.17.0: True, 2, 5, 5, 約 1.07e-13
