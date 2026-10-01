---
content_id: active-set
kind: method
method_id: M_ACTIVE_SET
title_ja: Active-set法
title_en: Active-Set Methods
summary: 解で等号になる制約の集合（active set）を推定し、その面の上の等式制約付き問題を解きながら、制約を追加・削除する方法です。
source_ids: [S004, S016, S055, S056]
prerequisites: [constrained-continuous]
related_ids: [constrained-continuous, projected-gradient, slsqp, dual-simplex, active-set-qp, concept.convex-quadratic-program]
aliases: [/learn/active-set]
status: published
last_reviewed: 2026-09-30
---

解で等号になる制約の集合（active set）を推定し、その面の上の等式制約付き問題を解きながら、制約を追加・削除する方法です。

## 30秒でつかむ

柵に囲まれた庭で、谷底を探すところを想像してください。
柵に触れているあいだは、その柵を手すりにして、手すりに沿って下ります。下る途中で別の柵にぶつかったら、その柵も手すりに加えます。
握っている手すりを離した方が下れると分かったら、その手すりは離します。

握っている手すりの集まりが、作業集合（working set）です。

- **見るもの**: 作業集合の乗数の符号、主・双対の残差、最初に触れる制約（blocking constraint）
- **動かすもの**: 作業集合 $W_k$、探索方向、歩幅、制約の追加と削除
- **前進の判断**: 等式制約付きの問題が進み、実行可能性・停留性・乗数の符号・相補性が整うこと
- **恐れていること**: 作業集合の振動、退化（degeneracy）や巡回（cycling）、実行不能なモデル

![多角形の実行可能領域の内側から候補点が辺へ進み、青緑のactiveな辺に沿って橙のblocking constraintへ近づく模式図](./media/active-set-feasible-face.png "作業集合を等式として扱い、候補が実行可能領域の面を移る直感を示す教育用の模式図です。実際の追加・削除規則や乗数の符号までは、図だけでは決まりません。")

## 一手の意味

不等式 $g_i(x)\le0$ が解で $g_i(x)=0$ になるとき、その制約はactive（有効）です。
active-set法は、現在の候補の集合 $W_k$ を等式として扱い、その面の上で小さな問題を解きます。一手は、次の四つのうち一つです。

1. $W_k$ の上で、探索方向を計算する
2. 作業集合の外の制約に当たるまで進む
3. 当たったら、その制約を作業集合に加える
4. 乗数が不適切なら、その制約を作業集合から外す

QPでは、正しい作業集合が分かれば、等式制約付きのQPに帰着できます。
$W_k$ を等式とみなしたときの探索方向 $d$ と乗数 $\lambda$ は、次の連立方程式で求めます。$B$ は目的のHessianまたはその近似、$A_W$ は作業集合の制約の係数です。

$$
\begin{bmatrix}B & A_W^\top\\ A_W & 0\end{bmatrix}
\begin{bmatrix}d\\ \lambda\end{bmatrix}
=
\begin{bmatrix}-\nabla f(x)\\ 0\end{bmatrix}
$$

$d\ne0$ なら動けます。$d=0$ なら、乗数の符号で判断します。

### 乗数の役割

作業集合にある制約の乗数が符号条件（$\lambda\ge0$）を満たさないとき、その制約は作業集合から外す候補になります。
負の乗数は、「その制約を握っているせいで、目的が悪くなる」ことを表します。そのため、次の四つを一緒に確認します。

- 主実行可能性（primal feasibility）
- 停留性（stationarity）
- 乗数の符号
- 相補性（complementarity）

### warm start

近いQPを繰り返し解くときは、前回の作業集合が良い出発点になります。次の場面で有効です。

- モデル予測制御（MPC）
- 逐次二次計画法（SQP）の部分問題
- パラメータを少しずつ変える掃引（sweep）
- 上下限が少し変わるポートフォリオや配分の問題

## 小さな例

[凸二次計画](#/learn/concept.convex-quadratic-program)の小さな例を、active-set法で二通りの出発点から解きます。

$$
\min_{x}\; (x_1-3)^2+(x_2-2)^2 \quad \text{s.t.}\quad x_1+x_2\le 3,\; x\ge 0
$$

目標 $(3,2)$ に最も近い点を、範囲の中から選ぶ問題です。答えは $(2,1)$ で、辺 $x_1+x_2=3$ の途中にあります。目的値は $2$、乗数は $2$ です。
出発点はどちらも、実行可能な点です。

**出発点 $(1,\,0.5)$（範囲の内部）**。作業集合は空です。

| 反復 | 点 | 作業集合 | 方向 $d$ | 歩幅 $\alpha$ | 起きること |
|---:|---|---|---|---:|---|
| 0 | $(1,\,0.5)$ | 空 | $(2,\,1.5)$ | $3/7\approx0.429$ | 制約なしの最小点 $(3,2)$ へ向かうが、$x_1+x_2\le3$ に当たる。その制約を加える |
| 1 | $(1.857,\,1.143)$ | $x_1+x_2\le3$ | $(0.143,\,-0.143)$ | 1 | 辺に沿って、作業集合の上の最小点 $(2,1)$ へ着く |
| 2 | $(2,\,1)$ | $x_1+x_2\le3$ | $(0,\,0)$ | | 乗数が $2\ge0$。最適 |

目的値は $6.25\to2.04\to2$ と下がります。反復0で歩幅が $1$ でなく $3/7$ なのは、制約の縁が先に来るからです。当たった制約を加えると、以後は縁の上だけを動きます。

**出発点 $(0,\,3)$（頂点）**。作業集合は、二本の制約 $\{x_1+x_2\le3,\; x_1\ge0\}$ です。

| 反復 | 点 | 作業集合 | 方向 $d$ | 乗数 | 起きること |
|---:|---|---|---|---|---|
| 0 | $(0,\,3)$ | $x_1+x_2\le3$, $x_1\ge0$ | $(0,\,0)$ | $(-2,\,-8)$ | 動けず、乗数がどちらも負。より負の $x_1\ge0$ を外す |
| 1 | $(0,\,3)$ | $x_1+x_2\le3$ | $(2,\,-2)$ | | 歩幅1で、辺の上の最小点 $(2,1)$ へ着く |
| 2 | $(2,\,1)$ | $x_1+x_2\le3$ | $(0,\,0)$ | $2$ | 乗数が $2\ge0$。最適 |

目的値は $10\to10\to2$ です。反復0では、点が動かないまま、握る手すりだけが変わります。
どの乗数を外すかの規則は、実装によって異なります。ここでは、最も負の乗数を選びました。

経路は違っても、最後の作業集合は $\{x_1+x_2\le3\}$ の一本になり、答えは同じ $(2,1)$ です。答えは辺の途中にあり、頂点ではありません。
QP専用の実装で、原点から出発する様子は[Active-set QP](#/learn/active-set-qp)で読めます。

## 向く条件・避ける条件

active-set法は、解でactiveな制約が比較的少ないLPや凸QPで、高精度な解や基底が欲しいときに向きます。
標準形は[制約付きNLP](#/formulations/PA009)と[凸二次計画](#/learn/concept.convex-quadratic-program)で読めます。

| 条件 | 理由 |
|---|---|
| LPまたは凸QPである | 作業集合の上の問題が、線形方程式で解けるため |
| 解でactiveな制約が比較的少ない | 作業集合が小さく保たれるため |
| 高精度な解や基底が必要 | 等式制約付きの問題を厳密に解くため |
| 前回に近い問題をwarm startで解く | 前回の作業集合を出発点にできるため |
| 不等式の構造を明示できる | どの制約が効くかを、追加・削除で追えるため |

避ける、または切り替える条件です。

- 作業集合が頻繁に大きく変わる → 内点法など、作業集合を推定しない方法を検討する
- 退化や巡回が起きる → 実装の巡回対策を確認する
- 制約が多く、分解の更新が重い → 大規模な疎な問題に向く方法を検討する
- 非凸QPで、局所性を無視している → 局所解であることを確認する
- 制約が非滑らか、またはノイズを含む → 別の定式化を検討する
- 実行不能なモデル → 制約を見直す

上下限だけの問題は[上下限付きの滑らかな最小化](#/formulations/PA008)に当たり、[射影勾配法](#/learn/projected-gradient)や[L-BFGS-B](#/learn/lbfgsb)も候補になります。

## Python

次の例は、小さな例の二つの表を再現します。作業集合を等式とみなしたKKT系を解き、方向が $0$ なら乗数の符号を見て制約を外し、動けるなら最初に触れる制約まで進みます。
2変数の教育用なので、制約をすべて調べています。実際のソルバーは、分解を更新しながら進みます。

```python
import numpy as np

target = np.array([3.0, 2.0])
# 制約 A x <= b : x1 + x2 <= 3,  -x1 <= 0,  -x2 <= 0
A = np.array([[1.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
b = np.array([3.0, 0.0, 0.0])
names = ["x1+x2<=3", "x1>=0", "x2>=0"]


def gradient(x: np.ndarray) -> np.ndarray:
    return 2.0 * (x - target)  # 目的 (x1-3)^2 + (x2-2)^2 のHessianは 2I


def active_set(x, working):
    x, working = np.array(x, dtype=float), list(working)
    for k in range(20):
        # 作業集合を等式とみなし、2d + A_W^T λ = -∇f, A_W d = 0 を解く。
        aw = A[working]
        kkt = np.block([[2.0 * np.eye(2), aw.T], [aw, np.zeros((len(working),) * 2)]])
        solution = np.linalg.solve(kkt, np.concatenate([-gradient(x), np.zeros(len(working))]))
        d, lam = solution[:2], solution[2:]
        label = [names[i] for i in working]
        if np.linalg.norm(d) < 1e-10:
            if lam.min(initial=0.0) >= -1e-10:
                print(k, x.round(4), label, "d =", d.round(4), "lam =", lam.round(4), "optimal")
                return x
            drop = working.pop(int(np.argmin(lam)))  # 最も負の乗数の制約を外す
            print(k, x.round(4), label, "d =", d.round(4), "lam =", lam.round(4), "drop", names[drop])
        else:
            step, blocking = 1.0, None
            for i in set(range(3)) - set(working):  # 最初に触れる制約を探す
                if A[i] @ d > 1e-12 and (b[i] - A[i] @ x) / (A[i] @ d) < step:
                    step, blocking = (b[i] - A[i] @ x) / (A[i] @ d), i
            action = f"add {names[blocking]}" if blocking is not None else "reach the minimum on W"
            print(k, x.round(4), label, "d =", d.round(4), "alpha =", round(step, 4), action)
            x = x + step * d
            if blocking is not None:
                working.append(blocking)
    return x


active_set([1.0, 0.5], [])  # 内部から出発する
active_set([0.0, 3.0], [0, 1])  # 頂点から出発する
```

```text
0 [1.  0.5] [] d = [2.  1.5] alpha = 0.4286 add x1+x2<=3
1 [1.8571 1.1429] ['x1+x2<=3'] d = [ 0.1429 -0.1429] alpha = 1.0 reach the minimum on W
2 [2. 1.] ['x1+x2<=3'] d = [0. 0.] lam = [2.] optimal
0 [0. 3.] ['x1+x2<=3', 'x1>=0'] d = [0. 0.] lam = [-2. -8.] drop x1>=0
1 [0. 3.] ['x1+x2<=3'] d = [ 2. -2.] alpha = 1.0 reach the minimum on W
2 [2. 1.] ['x1+x2<=3'] d = [0. 0.] lam = [2.] optimal
```

各行は、反復番号・点・作業集合・方向・（乗数か歩幅）・その反復での操作です。表の二つの経路と一致します。
`lam` は、作業集合の制約に対する乗数です。負の値があれば、その制約を外す候補です。

## 診断値

- 作業集合の大きさ
- 追加・削除した制約
- 主・双対の残差
- 乗数の符号の違反
- 等式制約付きの問題を解いた状態
- 歩幅と、最初に触れた制約
- 退化（degeneracy）
- 反復回数
- warm startの再利用

判断の目安です。乗数がすべて $0$ 以上で、方向が $0$ になり、残差が許容誤差以下なら停止します。
追加と削除が同じ制約の間で繰り返されるなら、下の表で切替先を選びます。

::: warning
作業集合が安定したことは、大域最適性の証明とは限りません。凸性・KKT残差・ソルバーの状態を確認します。
:::

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処 |
|---|---|---|
| 作業集合の追加・削除が振動する | 退化、巡回、分解の更新の誤差 | 巡回対策の有無を確認する。分解の更新を確認する |
| 乗数の符号の違反や、主・双対の残差が残る | KKT条件を満たしていない、または等式制約付きの問題を正しく解けていない | KKT条件と、等式制約付きの問題の状態を確認する |
| 最初に触れる制約が頻繁に変わる | 歩幅が短い、または作業集合が大きい | 歩幅と作業集合の大きさを確認する |
| 実行不能なモデルになる | 制約が矛盾している | active-set法を続けず、制約の実行可能性を確認する |
| 制約が多く、更新が重い | 大規模な問題 | 内点法（[非線形内点法](#/learn/interior-point-nlp)）を検討する |

## 次に読む

- [Active-set QP](#/learn/active-set-qp)：QP専用の作業集合の更新と、Schur補行列による分解の更新
- [Dual simplex法](#/learn/dual-simplex)：LPの基底の更新との関係
- [SLSQP](#/learn/slsqp)：一般の滑らかなNLPで、部分問題を毎回解く方法
- [制約付きNLP](#/formulations/PA009)：この手法が解く問題の標準形
