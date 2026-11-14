import numpy as np
import scipy
from scipy.optimize import brentq, minimize

H = np.diag([2.0, 40.0])
g = np.array([6.0, 200.0])
x0 = np.array([4.0, 3.0])
f = lambda x: (x[0]-1)**2 + 20*(x[1]+2)**2
grad = lambda x: np.array([2*(x[0]-1), 40*(x[1]+2)])

# 主例専用の厳密部分問題。H が正定値であることを使う。
for delta in [1.0, 2.0, 4.0, np.sqrt(34.0)]:
    if delta >= np.sqrt(34.0):
        lam = 0.0
    else:
        def length_error(lam):
            return np.linalg.norm(-g/(np.diag(H)+lam))-delta
        lam = brentq(length_error, 0.0, 1000.0, xtol=1e-12)
    p = -g/(np.diag(H)+lam)
    print(delta, lam, p, f(x0+p))

# 別の実行。SciPy は固有値分解版の上記コードと同一ではない。
r = minimize(f, x0, jac=grad, hess=lambda x: H, method="trust-exact",
             options={"gtol": 1e-8, "initial_trust_radius": 1.0,
                      "max_trust_radius": 1000.0, "eta": 0.15,
                      "maxiter": 300, "subproblem_maxiter": 25})
print(scipy.__version__, r.success, r.nit, r.nfev, r.njev, r.nhev)
# 1.17.0 True 3 4 4 4
