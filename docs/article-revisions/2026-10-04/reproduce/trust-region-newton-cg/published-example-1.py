import numpy as np
import scipy
from scipy.optimize import minimize

f = lambda x: (1-x[0])**2 + 20*(x[1]-x[0]**2)**2

def grad(x):
    return np.array([2*(x[0]-1)-80*x[0]*(x[1]-x[0]**2),
                     40*(x[1]-x[0]**2)])

hvp_calls = 0
def hessp(x, v):
    global hvp_calls
    hvp_calls += 1
    return np.array([(2-80*x[1]+240*x[0]**2)*v[0]-80*x[0]*v[1],
                     -80*x[0]*v[0]+40*v[1]])

path = [np.array([-1.2, 1.0])]
r = minimize(f, path[0], jac=grad, hessp=hessp, method="trust-ncg",
             callback=lambda xk: path.append(xk.copy()),
             options={"gtol": 1e-8, "maxiter": 300,
                      "initial_trust_radius": 1.0,
                      "max_trust_radius": 1000.0, "eta": 0.15})
print(scipy.__version__, r.success, r.nit, r.nfev, r.njev, r.nhev)
print(hvp_calls, np.linalg.norm(grad(r.x)))
# 1.17.0 True 23 24 23 61
# 60 0.0
