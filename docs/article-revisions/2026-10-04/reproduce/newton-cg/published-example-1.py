import numpy as np
import scipy
from scipy.optimize import minimize

f = lambda x: (x[0]-1)**2 + 20*(x[1]+2)**2
grad = lambda x: np.array([2*(x[0]-1), 40*(x[1]+2)])
hvp_calls = 0

def hessp(x, v):
    global hvp_calls
    hvp_calls += 1
    return np.array([2*v[0], 40*v[1]])

path = [np.array([4.0, 3.0])]
result = minimize(f, path[0], jac=grad, hessp=hessp,
                  method="Newton-CG",
                  callback=lambda xk: path.append(xk.copy()),
                  options={"xtol": 1e-5, "maxiter": 400,
                           "c1": 1e-4, "c2": 0.9})
print(scipy.__version__, result.success, result.nit, result.nhev)
print(hvp_calls, np.linalg.norm(grad(result.x), np.inf))
# SciPy 1.17.0: True, 3, 4
# 4, 約 8.88e-16
