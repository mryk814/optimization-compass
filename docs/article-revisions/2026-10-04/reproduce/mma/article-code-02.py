import numpy as np
from scipy.optimize import brentq

# Scalar worked example using MMA reciprocal coefficients and asymptote history.
# No slack variables, no GCMMA inner loop; not a general MMA implementation.
def values(x):
    return np.array([(x - 2)**2, x*x - 1.25**2])

def gradients(x):
    return np.array([2 * (x - 2), 2 * x])

def approximation(x, L, U):
    g = gradients(x)
    positive, negative = np.maximum(g, 0), np.maximum(-g, 0)
    p = (U - x)**2 * (1.001 * positive + .001 * negative + 1e-5 / 3)
    q = (x - L)**2 * (.001 * positive + 1.001 * negative + 1e-5 / 3)
    r = values(x) - p / (U - x) - q / (x - L)
    return p, q, r

def solve():
    x = 0.0
    points, history = [], []
    previous_L = previous_U = None
    for k in range(15):
        if k < 2:
            L, U, factor = x - 1.5, x + 1.5, 1.0
        else:
            last, older = points[-1], points[-2]
            product = (x - last) * (last - older)
            factor = 1.2 if product > 0 else .7 if product < 0 else 1.0
            L = x - np.clip(factor * (last - previous_L), .03, 30.)
            U = x + np.clip(factor * (previous_U - last), .03, 30.)
        alpha = max(0., .9 * L + .1 * x, x - .5)
        beta = min(3., .9 * U + .1 * x, x + .5)
        p, q, r = approximation(x, L, U)
        model = lambda z: r + p / (U - z) + q / (z - L)
        # Scalar convex constraint: find the feasible interval around current x.
        low = alpha if model(alpha)[1] <= 0 else brentq(lambda z:model(z)[1], alpha, x)
        high = beta if model(beta)[1] <= 0 else brentq(lambda z:model(z)[1], x, beta)
        stationary = (np.sqrt(q[0]) * U + np.sqrt(p[0]) * L) / (np.sqrt(p[0]) + np.sqrt(q[0]))
        candidate = float(np.clip(stationary, low, high))
        history.append(dict(k=k, x=x, L=float(L), U=float(U), factor=factor,
                            alpha=float(alpha), beta=float(beta), candidate=candidate,
                            f=float(values(candidate)[0]), original_constraint=float(values(candidate)[1]),
                            approximate_constraint=float(model(candidate)[1])))
        points.append(x)
        previous_L, previous_U = L, U
        # For this scalar problem, an active constraint with opposing gradients
        # satisfies the original KKT conditions (within numerical tolerance).
        if (abs(values(candidate)[1]) < 1e-10 and gradients(candidate)[0] < 0
                and gradients(candidate)[1] > 0) or abs(candidate - x) < 1e-10:
            break
        x = candidate
    return history

if __name__ == '__main__':
    for row in solve():
        print(row['k'], round(row['x'], 6), round(row['candidate'], 6),
              round(row['original_constraint'], 6), row['factor'])
