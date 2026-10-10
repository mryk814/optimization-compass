---
content_id: concept.vehicle-routing
kind: concept
canonical_entity_type: problem
canonical_entity_id: PA031
title_ja: 配送経路問題（VRP）
title_en: Vehicle Routing Problem
summary: 配送経路問題（VRP）は、depotを出る複数の車両が、各顧客をちょうど1回ずつ回って戻る経路を選び、総移動時間を最小にする定式化です。どの車がどの顧客を、どの順に回るかを同時に決め、容量や時間窓を制約として足せます。顧客が少なければ全探索やMILPで最適を確かめられますが、近似の結果がどれだけ最適に近いかは、最適値を知らなければ言えません。
prerequisites: [concept.mixed-integer-linear-program]
related_ids: [cp-sat, cp-search, branch-and-cut, local-search-combinatorial, simulated-annealing, dynamic-programming, concept.knapsack-set-cover]
source_ids: [S023, S024, S005, S054, S079, S022]
status: published
last_reviewed: 2026-10-10
---

配送経路問題（VRP）は、depotを出る複数の車両が、各顧客をちょうど1回ずつ回って戻る経路を選び、総移動時間を最小にする定式化です。どの車がどの顧客を、どの順に回るかを同時に決め、容量や時間窓を制約として足せます。顧客が少なければ全探索やMILPで最適を確かめられますが、近似の結果がどれだけ最適に近いかは、最適値を知らなければ言えません。

## 30秒でつかむ

倉庫（depot）から、2台のトラックで7軒の顧客へ荷物を届けます。移動時間は、地図上の直線距離と同じ数値（1単位を1分）とします。顧客ごとに荷物の量（需要）が決まっていて、トラックは1台あたり9まで積めます。

7軒を1周する最短の順番なら、1台で31.805分です。ところが荷物の合計は16で、1台には積みきれません。2台に分ける必要があるので、「誰がどの顧客を回るか」と「回る順番」を一緒に決めることになります。順番だけを考える問題より、決めることが一つ増えます。

- **決めるもの**: 各車がどの顧客をどの順に回るか（どの2点の間を車が通るかの0か1）
- **良くしたいもの**: 全車の総移動時間
- **守ること**: 各顧客をちょうど1回訪れる、各車の積載を9以下にする、各車はdepotを出てdepotへ戻る（時間窓があれば、その時刻までに着く）

次の図は、同じ7軒を、最近傍法と2-optで組んだ経路（橙）と、全探索で確かめた最適な経路（緑）で並べたものです。

![depotと顧客1から7の地図を2枚並べた図。最近傍法と2-optの経路（橙）は、顧客1,3,2と顧客4,5,7,6の2本で合計38.508。全探索の最適（緑）は、顧客3,1,4,6と顧客2,7,5の2本で合計35.527。](./figures/vrp-routes.svg "depot 1個・顧客7人・容量9の2台：近似と最適の比較。距離は直線距離で、実際の道路や交通は表さない教材用の1例")

1. 橙は、顧客1,3,2を回る1本（24.718分）と、顧客4,5,7,6を回る1本（13.79分）で、合計は38.508分です。
2. 緑は、顧客3,1,4,6を回る1本（15.798分）と、顧客2,7,5を回る1本（19.729分）で、合計は35.527分です。
3. 2枚の違いは、経路の中の順番ではなく、顧客の分け方です。橙は{1,2,3}と{4,5,6,7}、緑は{1,3,4,6}と{2,5,7}に分けています。

経路の中の順番を直す手法で、この分け方の違いまで直せるのでしょうか。小さな例で確かめます。

## 標準形を読む

次の式が表すのは「各顧客をちょうど1回通る経路をK本選び、車が積む荷物の量が容量を超えないようにして、辺の長さの合計を最小にする」です。$x_{ij}=1$ は、車が点 $i$ から点 $j$ へ直接進むことを表します。

$$
\min_{x,u}\ \sum_{i\ne j} d_{ij}\,x_{ij}
\quad\text{s.t.}\quad
\sum_{j\ne i} x_{ij}=1,\ \ \sum_{j\ne i} x_{ji}=1\ \ (i\in C),\quad
\sum_{j\in C} x_{0j}=K,\ \ \sum_{i\in C} x_{i0}=K
$$

$$
u_j\ \ge\ u_i+q_j-Q\,(1-x_{ij})\ \ (i\ne j\in C),\qquad q_i\le u_i\le Q,\qquad x_{ij}\in\{0,1\}
$$

記号は次の意味です。

| 記号 | 意味 | 7顧客の例では |
|---|---|---|
| $0$、$C$ | depotと、顧客の集合 | $0$ がdepot、$C=\{1,\dots,7\}$ |
| $d_{ij}$ | 点 $i$ から $j$ への移動時間 | 直線距離（例：$d_{0,1}=6$） |
| $x_{ij}$ | 辺 $(i,j)$ を車が通るなら1 | 56個（$8\times7$）の0-1変数 |
| $K$ | 車両の数 | $2$ |
| $q_i$、$Q$ | 顧客 $i$ の需要、車の容量 | $q=(2,3,2,1,3,2,3)$、$Q=9$ |
| $u_i$ | 顧客 $i$ を訪れた直後の積載量 | 7個の連続変数 |

1行目の式は、どの顧客にも入る辺と出る辺が1本ずつあり、depotから出る辺と戻る辺がK本ずつあることを表します。この式だけだと、depotにつながらない輪（部分巡回路）が解に残ります。2行目の式は、辺 $(i,j)$ を通るなら、$j$ での積載は $i$ での積載より $q_j$ 以上大きいことを表します。積載は顧客を進むごとに必ず増えるので、顧客だけを一周する輪は作れません。

### 積載の式は、容量と輪の禁止を兼ねる

2行目の式が持つ役目は二つあります。一つ目は、$u_i\le Q$ によって、1本の経路の積載が容量を超えないようにすることです。二つ目は、輪の禁止です。もし顧客だけの輪があれば、輪を一周して元の顧客に戻るとき、$u$ が $q$ の合計だけ増えて元の値より大きくなり、矛盾します。この形はMTZ（Miller–Tucker–Zemlin）の式と呼ばれる書き方です。輪を禁じる式は他にも書けます。

### 車ごとに添字を持つ形との違い

アトラスの標準形は、車 $k$ ごとに $x_{ijk}$ を持つ形です。車の種類（容量、費用、使える時間）が違うときは、この形が自然です。この記事の車は同じものなので、車の添字を持たない形で足ります。形が違っても、決めるものと守ることは同じです。

## 小さな例

### 7顧客の例・設定

以下の表と数値は、depot 1個、顧客7人、車2台、容量9の例に対応します。座標は整数で、$d_{ij}$ は直線距離です。需要の合計は16で、1台では運べません。

| 点 | 0（depot） | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 座標 $(x,y)$ | $(0,0)$ | $(0,6)$ | $(0,-6)$ | $(-2,2)$ | $(1,0)$ | $(6,-2)$ | $(1,-1)$ | $(3,-3)$ |
| 需要 $q$ | 0 | 2 | 3 | 2 | 1 | 3 | 2 | 3 |

### 7顧客の例・全探索で最適を知る

顧客7人の訪問順は $7!=5040$ 通りです。2台に分ける場合は、顧客を2組に分け（容量を守る分け方は22通り）、各組の最短の順番を全探索します。

```python
import itertools
import math

xy = [(0, 0), (0, 6), (0, -6), (-2, 2), (1, 0), (6, -2), (1, -1), (3, -3)]  # 0 が depot
q = [0, 2, 3, 2, 1, 3, 2, 3]  # 需要
Q, K = 9, 2  # 容量、車両数
n = len(xy)
d = [[math.dist(a, b) for b in xy] for a in xy]  # 移動時間 = 距離（速さ1）


def length(route):
    p = [0, *route, 0]
    return sum(d[a][b] for a, b in zip(p, p[1:]))


tsp = min(itertools.permutations(range(1, n)), key=length)
print(sum(q), tsp, round(length(tsp), 3))
# 16 (3, 1, 5, 7, 2, 6, 4) 31.805
print(math.factorial(7), math.factorial(15))
# 5040 1307674368000

splits = []  # 顧客を2組に分け、各組の最短の順番を全探索する
for mask in range(1, 2 ** (n - 1) - 1):
    A = tuple(i for i in range(1, n) if mask >> (i - 1) & 1)
    B = tuple(i for i in range(1, n) if not mask >> (i - 1) & 1)
    if A < B and sum(q[i] for i in A) <= Q and sum(q[i] for i in B) <= Q:
        ra = min(itertools.permutations(A), key=length)
        rb = min(itertools.permutations(B), key=length)
        splits.append((length(ra) + length(rb), ra, rb))
splits.sort()
print(len(splits))
# 22
for v, ra, rb in splits[:3]:
    print(round(v, 3), ra, rb)
# 35.527 (3, 1, 4, 6) (2, 7, 5)
# 38.171 (3, 1, 5, 4) (2, 7, 6)
# 38.508 (1, 3, 2) (4, 5, 7, 6)
print([round(length(r), 3) for r in splits[0][1:]], round(splits[-1][0], 3))
# [15.798, 19.729] 44.541
```

`splits` は、容量を守る22通りの分け方に対する、2本の経路の合計の短い順です。最適は、顧客3,1,4,6と顧客2,7,5の2本で、合計35.527分です。2本の積載は7と9で、2本目は容量にちょうど達します。容量を守る22通りのうち、最も長い分け方は44.541分です。

手で確かめられる量が二つあります。一つ目は、1本目の長さです。$d_{0,3}=\sqrt{8}=2.828$、$d_{3,1}=\sqrt{20}=4.472$、$d_{1,4}=\sqrt{37}=6.083$、$d_{4,6}=1$、$d_{6,0}=\sqrt2=1.414$ の合計が15.798です。二つ目は、1台で回る場合です。顧客7人を1周する最短の31.805分は、容量を無視した値です。距離が三角不等式を満たすので、2本の経路をdepotで切らずにつなぎ直しても長さは増えません。したがって、31.805分は2台の最適35.527分の下界でもあります。

### 7顧客の例・最近傍法と2-optで近似する

最近傍法は、今いる点から最も近く、積んでも容量を超えない顧客を次に選んで進み、選べる顧客がなくなったら新しい経路を始めます。2-optは、1本の経路の中の2辺を選んで、その間の順番を逆にして、短くなるあいだ繰り返します。

```python
def nearest_neighbour():
    left, routes = set(range(1, n)), []
    while left:
        route, load, here = [], 0, 0
        while True:
            fits = [j for j in left if load + q[j] <= Q]
            if not fits:
                break
            j = min(fits, key=lambda j: d[here][j])
            route.append(j)
            left.remove(j)
            load, here = load + q[j], j
        routes.append(route)
    return routes


def two_opt(route):
    route, improved = list(route), True
    while improved:
        improved = False
        for i in range(len(route) - 1):
            for j in range(i + 1, len(route)):
                trial = route[:i] + route[i : j + 1][::-1] + route[j + 1 :]
                if length(trial) < length(route) - 1e-12:
                    route, improved = trial, True
    return route


nn = nearest_neighbour()
print(nn, [sum(q[i] for i in r) for r in nn], round(sum(map(length, nn)), 3))
# [[4, 6, 7, 5], [3, 1, 2]] [9, 7] 39.616
opt2 = [two_opt(r) for r in nn]
best = splits[0][0]
total = sum(map(length, opt2))
print(opt2, round(total, 3), f"{total / best - 1:.1%}")
# [[4, 5, 7, 6], [1, 3, 2]] 38.508 8.4%
print([round(length(r), 3) for r in opt2])
# [13.79, 24.718]
print(f"{sum(map(length, nn)) / best - 1:.1%}")
# 11.5%
```

最近傍法は、顧客4,6,7,5を回る1本（積載9）と、顧客3,1,2を回る1本（積載7）に分け、合計は39.616分です。2-optで各経路の中の順番を直すと38.508分になり、最適35.527分より8.4%長い結果です。最近傍法だけでは11.5%長い結果でした。

2-optが直せるのは、1本の経路の中の順番だけで、顧客をどの経路に入れるかは変わりません。そこで、顧客を別の経路へ1人移す、または2本の経路の顧客を1人ずつ入れ替える、という近傍も試します。

```python
def moves(routes):
    """1人を別の経路へ移す（relocate）か、2つの経路の顧客を1人ずつ入れ替える（swap）。"""
    for a, b in ((0, 1), (1, 0)):
        for i in routes[a]:
            for pos in range(len(routes[b]) + 1):
                new = [list(r) for r in routes]
                new[a].remove(i)
                new[b].insert(pos, i)
                yield new
    for i in routes[0]:
        for j in routes[1]:
            new = [list(r) for r in routes]
            new[0][new[0].index(i)], new[1][new[1].index(j)] = j, i
            yield new


cands = [r for r in moves(opt2) if all(r) and all(sum(q[i] for i in x) <= Q for x in r)]
after = sorted((sum(map(length, map(two_opt, r))), r) for r in cands)
print(len(cands), round(after[0][0], 3), after[0][1])
# 16 38.987 [[4, 2, 7, 6], [1, 3, 5]]
```

容量を守る近傍は16通りで、どれも2-optを当てた後の合計は38.987分以上です。38.508分より短くなる動きは1つもありません。この橙の結果は、2-optの近傍でも、移動と入れ替えの近傍でも、これ以上改善できません。最適に届くには、橙の分け方{1,2,3}と{4,5,6,7}から、顧客2を{5,7}の側へ、顧客4と6を{1,3}の側へ、合わせて3人を動かす必要があります。1回の移動や入れ替えでは届きません。

この比較は、この7顧客の1例での結果です。最近傍法や2-optが、一般に8.4%ほど最適より長くなるという意味ではありません。顧客を増やしたときの近似の質は、この例からは言えません。

### 7顧客の例・MILPで解く

上の標準形を、そのままMILPにして解きます。ソルバーは、SciPy 1.18.1の `scipy.optimize.milp`（HiGHS、S005）で、許容誤差は既定のままです（`mip_rel_gap` は $10^{-4}$、整数性の許容は $10^{-6}$）。辺は、変数の値が0.5を超えるかどうかで選ばれたかどうかを読みます。許容誤差は、この例のための記録で、推奨値ではありません。

```python
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
col = {a: k for k, a in enumerate(arcs)}  # x_ij の列番号。その後ろに積載 u_1..u_7 が並ぶ
nx, nv = len(arcs), len(arcs) + n - 1


def solve(mtz=True, deadline=None, relax=False):
    """deadline = {顧客: 最も遅い到着時刻}。到着時刻 t_0..t_7 を変数に加える。"""
    nt = n if deadline is not None else 0
    rows, lo, hi = [], [], []

    def add(coef, low, high):
        row = np.zeros(nv + nt)
        for k, v in coef:
            row[k] = v
        rows.append(row), lo.append(low), hi.append(high)

    for i in range(1, n):  # 各顧客に入る弧と出る弧が1本ずつ
        add([(col[(i, j)], 1) for j in range(n) if j != i], 1, 1)
        add([(col[(j, i)], 1) for j in range(n) if j != i], 1, 1)
    add([(col[(0, j)], 1) for j in range(1, n)], K, K)  # depot を出る弧は K 本
    add([(col[(j, 0)], 1) for j in range(1, n)], K, K)
    if mtz:  # x_ij = 1 なら u_j >= u_i + q_j（積載が増えるので、顧客だけの輪は作れない）
        for i in range(1, n):
            for j in range(1, n):
                if i != j:
                    add([(nx + j - 1, 1), (nx + i - 1, -1), (col[(i, j)], -Q)], q[j] - Q, np.inf)
    ub = np.r_[np.ones(nx), np.full(n - 1, Q)]
    if nt:  # x_ij = 1 なら t_j >= t_i + d_ij（big-M = 100）
        for i, j in arcs:
            if j:
                add([(nv + j, 1), (nv + i, -1), (col[(i, j)], -100)], d[i][j] - 100, np.inf)
        ub = np.r_[ub, 0, [deadline.get(i, 1e3) for i in range(1, n)]]
    c = np.r_[[d[i][j] for i, j in arcs], np.zeros(n - 1 + nt)]
    lb = np.r_[np.zeros(nx), q[1:], np.zeros(nt)]
    integrality = np.r_[np.full(nx, 0 if relax else 1), np.zeros(n - 1 + nt)]
    return milp(c, constraints=LinearConstraint(np.array(rows), lo, hi),
                bounds=Bounds(lb, ub), integrality=integrality)


def read(res):
    """選ばれた弧から、depot を出る経路と、depot につながらない輪（部分巡回路）を取り出す。"""
    nxt = {i: j for (i, j), k in col.items() if res.x[k] > 0.5 and i}
    starts = [j for (i, j), k in col.items() if res.x[k] > 0.5 and i == 0]
    routes, seen = [], set()
    for s in starts:
        r = [s]
        while nxt[r[-1]]:
            r.append(nxt[r[-1]])
        routes.append(r), seen.update(r)
    loops = []
    for s in range(1, n):
        if s not in seen:
            r = [s]
            while nxt[r[-1]] != s:
                r.append(nxt[r[-1]])
            loops.append(r), seen.update(r)
    return routes, loops


res = solve()
print(res.status, round(res.fun, 3), res.mip_gap, read(res))
# 0 35.527 0.0 ([[2, 7, 5], [3, 1, 4, 6]], [])
print(res.x[nx:].round(1))
# [4. 3. 2. 5. 9. 7. 6.]
print(round(solve(relax=True).fun, 3), round(solve(mtz=False, relax=True).fun, 3))
# 29.696 28.389
```

`res.status` が0で `res.mip_gap` が0.0なので、HiGHSは最適性を示して止まりました。目的値は35.527分で、全探索と同じです。経路は、顧客2,7,5と顧客3,1,4,6の2本です。`res.x[nx:]` は積載 $u_1,\dots,u_7$ で、顧客2,7,5の順に、3、6、9と増えています。顧客3,1,4,6の順には、2、4、5、7と増えます。最後の行は、整数条件を外したLP緩和の値です。積載の式を入れたモデルは29.696分、次数の式だけのモデルは28.389分でした。29.696分は、最適35.527分より下にあります。HiGHSは、この差を分枝で詰めて最適性を示します。

### 7顧客の例・輪を禁じないと現れる解

2行目の式（積載の式）を外し、次数の式だけにしてみます。

```python
bad = solve(mtz=False)
routes, loops = read(bad)
print(round(bad.fun, 3), routes, loops, [sum(q[i] for i in r) for r in loops + routes])
# 28.389 [[4], [6]] [[1, 3], [2, 7, 5]] [4, 9, 1, 2]
```

目的値は28.389分で、全探索の最適35.527分より短く、1台で回る31.805分よりも短い値です。選ばれた辺を読むと、depotからは顧客4だけの経路と顧客6だけの経路が出ています。残りの顧客1,3の輪と、顧客2,7,5の輪は、depotにつながっていません。どの車もこの5人を回らないのに、各顧客の入る辺と出る辺は1本ずつなので、次数の式は満たされています。

![depotと顧客の地図を2枚並べた図。次数の制約だけの解（費用28.389）は、depotから顧客4と顧客6へそれぞれ1本、顧客1と3、顧客2と5と7の輪が赤で残る。積載の制約を足した解（費用35.527）では、輪が消えて2本の経路になる。](./figures/vrp-subtour.svg "次数の制約だけの解と、積載の制約つきの最適解：depot 1個・顧客7人・容量9の2台。輪の向きは解によって逆になることがある")

### 7顧客の例・時間窓を1つ足す

顧客1に、時刻7までに着くという条件（時間窓の終了 $l_1=7$）を足します。車はdepotを時刻0に出発し、移動時間は距離と同じ、荷下ろしの時間は0とします。まず、先の最適な経路の到着時刻を見ます。

```python
def arrival(route):
    t, here, out = 0.0, 0, []
    for j in route:
        t, here = t + d[here][j], j
        out.append(round(t, 3))
    return out


print(arrival(splits[0][1]), arrival(splits[0][2]))
# [2.828, 7.301, 13.383, 14.383] [6.0, 10.243, 13.405]

late = {1: 7}  # 顧客1は時刻7までに着く


def legal(route):
    return all(t <= late.get(j, 1e9) for j, t in zip(route, arrival(route)))


ok = []
for mask in range(1, 2 ** (n - 1) - 1):
    A = tuple(i for i in range(1, n) if mask >> (i - 1) & 1)
    B = tuple(i for i in range(1, n) if not mask >> (i - 1) & 1)
    if not (A < B and sum(q[i] for i in A) <= Q and sum(q[i] for i in B) <= Q):
        continue
    ra = min((p for p in itertools.permutations(A) if legal(p)), key=length, default=None)
    rb = min((p for p in itertools.permutations(B) if legal(p)), key=length, default=None)
    if ra and rb:
        ok.append((length(ra) + length(rb), ra, rb))
ok.sort()
print(len(ok), [(round(v, 3), a, b) for v, a, b in ok[:2]])
# 22 [(36.221, (1, 3, 4, 6), (2, 7, 5)), (38.508, (1, 3, 2), (4, 5, 7, 6))]
res = solve(deadline=late)
print(res.status, round(res.fun, 3), read(res)[0])
# 0 36.221 [[1, 3, 4, 6], [5, 7, 2]]
print(arrival((1, 3, 4, 6)), arrival((1, 3, 2)))
# [6.0, 10.472, 14.078, 15.078] [6.0, 10.472, 18.718]
print(f"{ok[0][0] / best - 1:.1%}", f"{total / ok[0][0] - 1:.1%}")
# 2.0% 6.3%
print(solve(deadline={1: 5}).status)  # 顧客1は depot から距離6なので、時刻5には着けない
# 2
```

先の最適な経路の1本目、顧客3,1,4,6では、顧客1に時刻7.301に着きます。窓の終了7を0.301分過ぎるので、この経路は使えません。条件を足したときの最適は、顧客1,3,4,6と顧客2,7,5（または、2本目を逆向きに回る顧客5,7,2）で、合計36.221分です。顧客1を先に回すと、depotから6.0分で着きます。窓がない場合の35.527分より0.694分、2.0%長くなります。全探索とMILPは同じ値と経路を返します。MILPでは、到着時刻 $t_j\ge t_i+d_{ij}-M(1-x_{ij})$ と上限 $t_i\le l_i$ を、big-M（$M=100$）で加えました。

最近傍法と2-optの橙の経路は、顧客1に時刻6.0で着くので、窓を満たしたままです。窓を足した後の最適36.221分に対しては、6.3%長い結果です。窓の終了を5にすると、顧客1はdepotから距離6なので、どの経路でも間に合いません。MILPの `status` は2（実行不可能）になります。

## つまずきやすい点

- **次数の式を満たせば、車が回れる解だと考える**: 次数の式だけのモデルは、費用28.389の解を返しました。顧客1,3の輪と、顧客2,7,5の輪は、depotにつながらないので、車は回れません。しかも、この値は最適35.527より短く、容量を無視した1台の31.805より短いので、「安い解が出た」ことが誤りの手がかりになります。輪を禁じる式（積載の式など）を入れて、解いた後にも、depotにつながらない輪がないかを確かめます。
- **1台で回る最短の順番（TSP）の値を、2台の答えとして使う**: 7顧客を1周する最短は31.805分ですが、荷物の合計16は容量9を超えます。容量を守る2台の最適は35.527分で、31.805分より3.722分長くなります。31.805分は2台の下界として使えますが、実現できる値ではありません。
- **2-optで改善できなくなったら、最適だと考える**: 橙の経路は、2-optでも、移動と入れ替えの近傍でも、これ以上短くなりません。それでも、最適35.527分より8.4%長い結果です。最適な分け方には、顧客3人の移動が必要で、1回の近傍の動きでは届きません。最適との差を言えるのは、全探索やMILPの下界のように、別の方法で最適値や下界が分かるときだけです。
- **時間窓を、解いた後の確認で済ませる**: 窓がない場合の最適な経路は、顧客1に7.301分で着くので、窓 $l_1=7$ を破ります。この経路を取り除き、窓を満たす経路の中から選び直すと、36.221分になり、経路も変わります。窓を、費用への罰則にせず、守る条件としてモデルに入れておくと、窓を満たす最良の経路が直接出ます。窓が到達できる時刻より早いなら、どの経路でも実行不可能です。
- **この小ささでの結果を、顧客が増えたときに当てはめる**: 7顧客では、全探索は $7!=5040$ 通りで一瞬です。しかし、15人なら $15!$ は1307674368000通りです。この例でMILPが一瞬で解けたことも、大きな例での速さを表すものではありません。MILPと近似法のどちらが向くかは、顧客数、容量の厳しさ、時間窓の幅、必要な期限で変わります。

## 課題から定式化する

「2台で7軒に届けたい」という課題だけでは、まだこの型とは決まりません。次の4つを順に確かめます。

1. **何を決めるか**: 各車が回る顧客と順番です。顧客の分け方だけ、または1本の順番だけを決める問題なら、別の型です。
2. **どの量を最小にするか**: 総移動時間（または距離）です。車の台数を減らしたい、遅れを最小にしたい、というときは、目的が変わります。
3. **何を必ず守るか**: 各顧客をちょうど1回訪れる、積載が容量以下、depotを出て戻る、の3つです。
4. **時間の条件があるか**: 顧客ごとに、着いてよい時刻の範囲があるなら、窓の式を足します。窓を破ると使えない（守る条件）なら、費用への罰則にせず、制約として入れます。

depotを出て戻る経路を、容量の下で選び、各顧客を1回ずつ訪れて、総移動時間を最小にするとき、この記事の型になります。

## 困りごとから関連する問題へ

実際の課題で、次の症状が出たら、対応する記事へ進めます。

- 1台で全顧客を回り、容量もない → この記事の $K=1$、$Q=\infty$ の場合で、巡回セールスマン問題（TSP）です。上の例では、31.805分がこの値でした
- 顧客ごとに着いてよい時刻が決まっている → この記事の時間窓の節と、ギャラリーの[時間窓付き配送ルートを10分以内に組む](#/gallery/EC019)
- 始点から終点まで、1本の最短の道だけが欲しい → [最短路](#/formulations/PA029)
- 顧客と車の組み合わせだけを決め、回る順番は決めない → [割当・matching](#/formulations/PA030)
- 式を整数計画のソルバーに渡し、最適性の証明まで欲しい → [混合整数線形計画](#/formulations/PA023)
- 時間や順序に、論理の条件が多い → [CP-SAT](#/learn/cp-sat)、[制約プログラミング探索](#/learn/cp-search)
- 近似の結果が、最適にどれだけ近いか知りたい → [組合せ局所探索](#/learn/local-search-combinatorial)と、この記事の全探索・下界の比べ方

### 配送経路問題と関連する問題の関係

- [混合整数線形計画](#/formulations/PA023): 条件付きで書き直せます。上のMTZの式のように、積載の式で輪を禁じれば、配送経路問題はMILPです。ただし、実用の規模では、専用のroutingのヒューリスティクスが主に使われます。
- [最短路](#/formulations/PA029): 形が似ているだけです。始点から終点への1本の最短路は、多項式の時間で解けますが、複数の顧客を回る巡回路は、NP困難とされています。
- TSP: この記事の特別な場合です。車が1台で、容量の式がないとき、積載の式の役目は輪の禁止だけになります。
- 時間窓付きの配送経路（VRPTW）: この記事に窓の式を足した型です。この教材の実行可能な定義（`PROBLEM_TIME_WINDOW_ROUTING`）は、1本の固定した経路の窓の判定だけを扱い、この記事の最適化とは別のものです。

## 数値計算の方法を選ぶ

どの方法も、使う情報と得られる保証が違います。顧客数、必要な保証（最適か、実行可能解か）、期限で分けて考えます。

| 系統 | 使う情報 | 向く条件・避ける条件 |
|---|---|---|
| 全探索 | 距離と需要 | 顧客が7人程度なら、最適を確かめられます。顧客数が増えると、組み合わせが急に増えるので、使えません |
| [Branch-and-Cut](#/learn/branch-and-cut)（MILP、HiGHS、SCIP、Gurobiなど） | 距離、需要、時間窓の式 | 最適性やギャップを報告したいときです。LP緩和と最適の差（この例では29.696分と35.527分）は、探索で詰めます。差が大きいと、探索が長引きます |
| [CP-SAT](#/learn/cp-sat) | 論理と時間窓の制約 | 論理の条件が多く、小さな例のときに、モデルを自然に書けます。最適性の証明まで出るかは、規模と制約によります |
| [局所探索](#/learn/local-search-combinatorial)（最近傍法の初期解、2-opt、OR-Tools Routingの探索など） | 近傍の定義と、経路の評価 | 期限があり、実行可能な良い解を早く得たいときです。最適との差は、別の下界や厳密解がなければ分かりません |
| [動的計画法](#/learn/dynamic-programming) | 状態の分け方 | アトラスは、汎用の最適化の前に確認する手法として挙げています。状態の数が多くなると使えません |

OR-Tools Routing（S023）やGurobi（S024）などの設定の既定値は、使うソフトウェアの既定であり、配送経路問題一般での推奨ではありません。上のコードのHiGHSの許容誤差も、この7顧客の例のためのものです。選ぶときは、顧客数、容量の厳しさ、時間窓の幅、期限、報告したい保証（実行可能解か、最適性の証明か）を確かめます。この記事の比較は、1つの7顧客の例での値で、どの方法が優れているかを示すものではありません。
