import numpy as np


def objective(p: np.ndarray) -> float:
    return float(abs(p[0] - 1.0) + 20.0 * abs(p[1] + 2.0))


def subgradient(p: np.ndarray) -> np.ndarray:
    # 折れ目では 0 を選ぶ。oracle が返す劣勾配の選び方も、再現条件に含める。
    return np.array([np.sign(p[0] - 1.0), 20.0 * np.sign(p[1] + 2.0)])


def run(step, iterations):
    p = np.array([4.0, 3.0])
    best_value = objective(p)
    rows = []
    for k in range(iterations):
        value = objective(p)
        best_value = min(best_value, value)
        rows.append((k, p.copy(), value, best_value))
        p = p - step(k) * subgradient(p)
    return rows


rows = run(lambda k: 1.0 / np.sqrt(k + 1), 1_000)
for k, p, value, best in rows[:7]:
    print(k, np.round(p, 3), round(value, 2), round(best, 2))
# 0 [4. 3.] 103.0 103.0
# 1 [  3. -17.] 302.0 103.0
# 2 [ 2.293 -2.858] 18.45 18.45
# 3 [1.716 8.689] 214.5 18.45
# 4 [ 1.216 -1.311] 14.0 14.0
# 5 [  0.768 -10.255] 165.33 14.0
# 6 [ 1.177 -2.09 ] 1.98 1.98
print("初期点を含む1000点の最良値", rows[-1][3])
# 初期点を含む1000点の最良値 1.6159782813662815e-05

rows = run(lambda k: 1.0, 1_000)
print("固定の歩幅係数 1 の最良値", rows[-1][3])
# 固定の歩幅係数 1 の最良値 100.0
