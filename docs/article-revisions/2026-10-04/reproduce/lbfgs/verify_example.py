"""Original educational calculations for the L-BFGS article, not a solver benchmark."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

OUT = Path(__file__).resolve().parent
A = np.diag([2.0, 40.0])
CENTER = np.array([1.0, -2.0])
def f(x):
    d = x - CENTER
    return float(0.5 * d @ A @ d)
def grad(x):
    return A @ (x - CENTER)
def inverse_action(g, history, gamma=1.0):
    q = g.copy()
    saved = []
    for s, y in reversed(history):
        curvature = float(s @ y)
        if curvature <= 0:
            raise ValueError('positive curvature required')
        rho = 1.0 / curvature
        a = rho * float(s @ q)
        saved.append((s, y, rho, a))
        q -= a * y
    r = gamma * q
    for s, y, rho, a in reversed(saved):
        b = rho * float(y @ r)
        r += s * (a - b)
    return r

def dense_inverse(history, gamma=1.0):
    H = gamma * np.eye(2)
    for s, y in history:
        rho = 1.0 / float(s @ y)
        V = np.eye(2) - rho * np.outer(s, y)
        H = V @ H @ V.T + rho * np.outer(s, s)
    return H

def main():
    x0 = np.array([4.0, 3.0]); g0 = grad(x0); p0 = -g0
    t0 = -float(g0 @ p0) / float(p0 @ A @ p0)
    x1 = x0 + t0*p0; g1 = grad(x1)
    s0 = x1-x0; y0 = g1-g0; hist = [(s0,y0)]
    rho = 1.0/float(s0@y0)
    a = rho*float(s0@g1); q = g1-a*y0; b=rho*float(y0@q)
    p1 = -inverse_action(g1,hist)
    t1 = -float(g1@p1)/float(p1@A@p1);x2=x1+t1*p1
    np.testing.assert_allclose(x2,CENTER,atol=1e-12)
    np.testing.assert_allclose(inverse_action(g1,hist),dense_inverse(hist)@g1,atol=1e-12)
    frozen = [(np.array([1.,0.]),np.array([2.,0.])),(np.array([0.,1.]),np.array([0.,40.]))]
    x=np.array([3.,3.]);g=grad(x)
    directions={}
    for m in (0,1,2):
        h=frozen[-m:] if m else []
        p=-inverse_action(g,h)
        np.testing.assert_allclose(p,-dense_inverse(h)@g,atol=1e-12)
        directions[str(m)]={'p':p.tolist(),'unit_p':(p/np.linalg.norm(p)).tolist(),'H':dense_inverse(h).tolist()}
    np.testing.assert_allclose(directions['1']['p'],[-4.,-5.])
    np.testing.assert_allclose(directions['2']['p'],[-2.,-5.])
    scaled=-inverse_action(g,frozen[-1:],gamma=.025)
    np.testing.assert_allclose(scaled,[-.1,-5.])
    # General nonconjugate observations do not preserve every old secant condition.
    nonconj=[frozen[0],(np.array([1.,1.]),np.array([2.,40.]))]
    H=dense_inverse(nonconj)
    latest_res=np.linalg.norm(H@nonconj[-1][1]-nonconj[-1][0])
    old_res=np.linalg.norm(H@nonconj[0][1]-nonconj[0][0])
    assert latest_res < 1e-12 and old_res > .1
    rng=np.random.default_rng(814)
    max_error=0.
    for _ in range(100):
        pairs=[]
        for __ in range(4):
            s=rng.normal(size=2);pairs.append((s,A@s))
        v=rng.normal(size=2)
        for m in (1,2,3,4):
            for gamma in (.025,1.,3.):
                h=pairs[-m:]
                err=float(np.linalg.norm(inverse_action(v,h,gamma)-dense_inverse(h,gamma)@v))
                max_error=max(max_error,err)
                assert err < 1e-10
                assert np.linalg.eigvalsh(dense_inverse(h,gamma)).min()>0
    result=minimize(f,x0,jac=grad,method='L-BFGS-B',options={'maxcor':5,'gtol':1e-10,'ftol':1e-15})
    np.testing.assert_allclose(result.x,CENTER,atol=1e-8)
    info={'function':'(x-1)^2+20*(y+2)^2','initial':x0.tolist(),'first_step':{'g0':g0.tolist(),'p0':p0.tolist(),'step_size':t0,'x1':x1.tolist(),'g1':g1.tolist(),'s0':s0.tolist(),'y0':y0.tolist(),'rho':rho,'alpha':a,'beta':b,'p1':p1.tolist(),'next_step_size':t1,'x2':x2.tolist()},'frozen_history':{'current':x.tolist(),'g':g.tolist(),'directions':directions,'m1_scaled_direction':scaled.tolist()},'secant_counterexample':{'H':H.tolist(),'old_residual':float(old_res),'latest_residual':float(latest_res)},'tests':{'dense_equivalence_cases':1200,'max_error':max_error},'scipy':{'version':__import__('scipy').__version__,'success':bool(result.success),'nit':int(result.nit),'nfev':int(result.nfev),'x':result.x.tolist(),'f':float(result.fun),'gradient_infinity_norm':float(np.max(np.abs(result.jac))),'message':str(result.message)}}
    (OUT/'verified-numbers.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(info,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
