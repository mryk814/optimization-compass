import numpy as np
import scipy
from scipy.optimize import minimize

f = lambda x: (x[0]-1)**2 + 20*(x[1]+2)**2
grad = lambda x: np.array([2*(x[0]-1), 40*(x[1]+2)])

for inexact in [True, False]:
    calls = [0]
    def hessp(x, v):
        calls[0] += 1
        return np.array([2*v[0], 40*v[1]])

    r = minimize(f, [4.0, 3.0], jac=grad, hessp=hessp,
                 method="trust-krylov",
                 options={"gtol": 1e-8, "inexact": inexact,
                          "initial_trust_radius": 1.0,
                          "max_trust_radius": 1000.0,
                          "eta": 0.15, "maxiter": 300})
    print(inexact, r.nit, r.nhev, calls[0], np.linalg.norm(grad(r.x)))
# SciPy 1.17.0
# True  4 10 9 約8.88e-16
# False 3 10 9 約2.22e-13
