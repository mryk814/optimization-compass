import numpy as np
from scipy.linalg import null_space
from scipy.optimize import brentq

A = np.diag([1.0, 2.0, 4.0])

def subproblem(g, H, radius):
    # Spectral solution of a 2D Euclidean trust-region problem.
    d, V = np.linalg.eigh(H)
    c = V.T @ g
    if d[0] > 0:
        p = -c / d
        if np.linalg.norm(p) <= radius:
            return V @ p, 0.0
    lower = max(0.0, -d[0])
    denominator = d + lower
    singular = denominator < 1e-12
    p = np.zeros_like(c)
    p[~singular] = -c[~singular] / denominator[~singular]
    # Hard case: gradient is orthogonal to the lowest eigenspace.
    if np.all(np.abs(c[singular]) < 1e-12) and np.linalg.norm(p) <= radius:
        if lower > 0:
            j = np.flatnonzero(singular)[0]
            p[j] = np.sqrt(max(0.0, radius**2 - p @ p))
        return V @ p, lower
    norm_at = lambda lam: np.linalg.norm(c / (d + lam))
    lo, hi = lower + 1e-13, max(1.0, lower + 1.0)
    while norm_at(hi) > radius:
        hi = 2 * hi + 1
    lam = brentq(lambda z: norm_at(z) - radius, lo, hi, xtol=1e-14)
    return V @ (-c / (d + lam)), lam


def solve():
    x = np.ones(3) / np.sqrt(3.0)
    radius, history = 4.0, []
    for k in range(30):
        Q = null_space(x[None, :])  # 3 x 2 orthonormal tangent basis
        f = float(x @ A @ x)
        g = 2 * Q.T @ A @ x
        H = 2 * Q.T @ (A - f * np.eye(3)) @ Q
        if np.linalg.norm(g) < 1e-9:
            break
        p, lam = subproblem(g, H, radius)
        predicted = -g @ p - 0.5 * p @ H @ p
        if predicted <= 1e-15:
            break
        trial = x + Q @ p
        trial /= np.linalg.norm(trial)
        actual = f - trial @ A @ trial
        rho = actual / predicted
        accept = rho > 0.1
        history.append(dict(k=k, x=x.tolist(), f=f, radius=radius,
                            step=float(np.linalg.norm(p)), predicted=float(predicted),
                            actual=float(actual), rho=float(rho), accepted=bool(accept),
                            kkt=float(np.linalg.norm((H + lam * np.eye(2)) @ p + g))))
        old_radius = radius
        if rho < 0.25:
            radius *= 0.25
        elif rho > 0.75 and np.linalg.norm(p) > 0.99 * old_radius:
            radius = min(2 * radius, 4.0)
        if accept:
            x = trial
    return x, history

if __name__ == '__main__':
    x, history = solve()
    for r in history:
        print(r['k'], round(r['f'], 6), round(r['radius'], 4),
              round(r['rho'], 4), r['accepted'])
    print('cost:', x @ A @ x)
