import numpy as np

J = lambda m: 0.5 * (1.0 / m - 1.0)**2
m = 2.0
for iteration in range(3):
    u = 1.0 / m
    adjoint = (u - 1.0) / m
    gradient = -adjoint * u
    h = 1e-5
    fd = (J(m + h) - J(m - h)) / (2 * h)
    analytic = (m - 1.0) / m**3
    assert abs(m * u - 1.0) < 1e-12
    assert abs(m * adjoint - (u - 1.0)) < 1e-12
    assert abs(gradient - analytic) < 1e-12
    assert abs(gradient - fd) < 1e-9
    print(iteration, m, u, adjoint, gradient, J(m), abs(gradient-fd))
    m -= 0.5 * gradient  # This is a separate gradient-descent update.

m, gradient = 2.0, 0.125
previous = None
for h in (0.2, 0.1, 0.05, 0.025, 0.0125):
    remainder = abs(J(m + h) - J(m) - h * gradient)
    rate = np.log2(previous / remainder) if previous else None
    print('Taylor:', h, remainder, rate)
    previous = remainder
