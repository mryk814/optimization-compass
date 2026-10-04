from math import sqrt

x = 0.0
for iteration in range(1, 4):
    lower, upper = x - 1.0, x + 1.0
    gradient = 2.0 * (x - 2.0)
    p = max(gradient, 0.0) + 0.01
    q = max(-gradient, 0.0) + 0.01
    stationary = (sqrt(q) * upper + sqrt(p) * lower) / (sqrt(p) + sqrt(q))
    candidate = max(x - 0.5, min(x + 0.5, stationary))
    print(iteration, lower, upper, candidate, (candidate - 2.0) ** 2)
    x = candidate
