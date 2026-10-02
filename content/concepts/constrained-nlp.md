---
content_id: concept.constrained-nlp
kind: concept
canonical_entity_type: problem
canonical_entity_id: PA009
title_ja: 一般滑らか制約付きNLP
title_en: Smooth Constrained Nonlinear Program
summary: 一般滑らか制約付きNLPは、滑らかな非線形の目的を、滑らかな不等式・等式制約を守りながら最小にする定式化です。得られるのは局所解で、その点が満たす目安がKKT条件です。
prerequisites: [concept.convexity]
related_ids: [sqp, slsqp, interior-point-nlp, augmented-lagrangian, cobyla, family.constrained-nlp, constrained-continuous]
source_ids: [S056, S017, S029, S030, S064, S055, S002]
status: published
last_reviewed: 2026-10-02
---

一般滑らか制約付きNLPは、滑らかな非線形の目的を、滑らかな不等式・等式制約を守りながら最小にする定式化です。得られるのは局所解で、その点が満たす目安がKKT条件です。

## 30秒でつかむ

部品をできるだけ軽くしたい場面を考えます。軽くするほど、材料は薄くなります。
一方で、強度の式が決めた限度を割り込んではいけません。強度の式は、寸法の非線形な関数です。

軽さだけを追えば、答えは危険な薄さになります。強度だけを追えば、答えは重すぎる部品になります。
最良の設計は、多くの場合、強度の限度にちょうど触れる境界の上にあります。

- **決めるもの**: 寸法や設計パラメータのような連続の量
- **良くしたいもの**: 重さ、費用、損失のような滑らかな目的 $f(x)$
- **守ること**: 強度や安全率のような滑らかな不等式 $g(x)\le0$ と、つり合いのような等式 $h(x)=0$

「滑らか」は、目的と制約の勾配を計算できることを指します。この情報を使う方法が、この型の主役です。

[ロボットアームの障害物回避を3Dで見る](#/theater/physical/arm)では、時刻ごとの関節角を選び、腕全体の離隔と関節速度を制約にします。
同じ始点と終点でも、手先の移動距離と関節の滑らかさの重みを変えると、得られる軌道が変わります。
この教材は幾何学的な軌道を求めるもので、関節torqueや実機の追従誤差は含みません。

## 標準形を読む

この型は、目的を下げる動きと制約を守る動きを、一つの式にまとめます。

$$
\min_{x}\; f(x) \;\text{ s.t. }\; g(x)\le 0,\; h(x)=0
$$

| 記号 | 意味 |
|---|---|
| $x$ | 決める変数のベクトル。連続値 |
| $f(x)$ | 最小にしたい目的。滑らかな非線形でよい |
| $g_i(x)\le0$ | 不等式制約。$g_i(x)=0$ の点を「効いている（active）」と呼ぶ |
| $h_j(x)=0$ | 等式制約 |

$f,g,h$ が線形なら線形計画、$f$ が凸二次で制約が線形なら凸二次計画です。この型は、それらを特別な場合として含む一般の形です。

最適点の目安は、KKT条件（Karush–Kuhn–Tucker条件）で書きます。乗数（multiplier）$\lambda_i,\mu_j$ を使います。

$$
\nabla f(x)+\sum_i\lambda_i\nabla g_i(x)+\sum_j\mu_j\nabla h_j(x)=0,\qquad
\lambda_i\ge0,\quad \lambda_i\,g_i(x)=0
$$

第1式は、目的の勾配が制約の勾配とつり合うことを表します。$\lambda_i g_i(x)=0$ は、効いていない制約の乗数が0になることを表します。
もちろん、$g_i(x)\le0$ と $h_j(x)=0$ も満たしていなければなりません。

KKT条件が最適解の必要条件になるには、制約にも条件が要ります（制約想定, constraint qualification）。たとえば、効いている制約の勾配が一次独立であることです。
また、この条件を満たす点が、局所解であるとは限りません。鞍点や極大点でもあり得ます。
$f,g$ が凸で $h$ が線形なら、KKT条件を満たす点は大域解です。

solverごとに、不等式の向きが違います。$g(x)\le0$ を守る側とする形と、$g(x)\ge0$ を守る側とする形の両方があります。入力の前に必ず確かめます。

## 小さな例

公開事例『強度制約を守りながら軽量設計を探す』の教材と同じ問題です。

$$
\min_{x,y}\; x^2+y^2 \quad \text{s.t.}\quad (x-1)^2+(y-1)^2\le1,\;\; -1\le x,y\le3
$$

目的 $x^2+y^2$ は、原点からの距離の二乗です。制約は、中心 $(1,1)$、半径1の円板を表します。
原点から中心までの距離は $\sqrt2\approx1.414$ で、半径より大きいので、原点は円板の外にあります。円板の外の点は、目的が低くても実行不可能です。

答えは、円板の中で原点に最も近い点です。原点と中心を結ぶ線上の境界にあります。

$$
x^\star=y^\star=1-\tfrac1{\sqrt2}\approx0.2929,\qquad f(x^\star)=3-2\sqrt2\approx0.1716
$$

### 読み取り: 乗数は「制約を緩めたときの得」

この点でKKT条件を確かめます。勾配は $\nabla f=2x^\star\approx(0.586,\,0.586)$ です。制約 $g=(x-1)^2+(y-1)^2-1$ の勾配は $\nabla g=2(x^\star-1)\approx(-1.414,\,-1.414)$ です。

二つは同じ向きの直線上にあり、つり合う乗数は $\lambda=\sqrt2-1\approx0.4142$ です。$\lambda\ge0$ で、$g=0$ なので、KKT条件を満たします。上下限 $-1\le x,y\le3$ は効いていません。

$\lambda$ は、制約を少し緩めたときの目的の下がり方です。半径の二乗を1から1.1にすると、最適値は0.1716から0.1335へ、約0.0381下がります。$\lambda\times0.1=0.0414$ に近い値です。
$\lambda$ が大きい制約ほど、その制約が最適値を強く押さえています。

この問題は、目的も円板も凸なので、KKT点は大域解でもあります。ただし、この型全体では、凸とは限りません。

### 局所解が複数ある例

次の問題は、可行集合が二つに分かれています。

$$
\min_{x}\; x_1+x_2 \quad \text{s.t.}\quad x_1x_2\ge1,\;\; -3\le x_1,x_2\le3
$$

$x_1x_2\ge1$ の領域は、第1象限と第3象限にあります。第1象限では、$x=(1,1)$ が局所解で、値は2です。乗数は1で、KKT条件を満たします。
第3象限では、上下限に当たる $x=(-3,-3)$ が解で、値は $-6$ です。

どちらもKKT点で、局所解です。大域解は $(-3,-3)$ だけです。第1象限から出発すると、$(1,1)$ で止まります。

## 見分け方

次の兆候があれば、この型を疑います。

- 性能を上げたいが、強度・重量・安全率などの条件を式で守る必要がある
- 目的も制約も、変数の滑らかな関数として書け、勾配を計算できる
- 変数はすべて連続で、上下限以外にも、式で書いた制約がある

別の型へ向かう兆候もあります。

- 目的が線形で制約も線形 → [線形計画（PA017）](#/formulations/PA017)
- 目的が凸二次で制約が線形 → [凸二次計画（PA018）](#/formulations/PA018)。どちらも専用のsolverが使え、大域解が得られる
- 制約が上下限だけ → [上下限制約付き滑らか（PA008）](#/formulations/PA008)
- 決める量の一部が整数 → [混合整数非線形計画（PA025）](#/formulations/PA025)
- 目的や制約が勾配を返せない（simulationの出力など） → [微分なし最適化](#/learn/concept.derivative-free)の型。評価が高価なら[PA014](#/formulations/PA014)
- 決める量が単体（合計1、非負）の上にある → [単体上の最適化（PA036）](#/formulations/PA036)

## 近い定式化

この型は、多くの型の行き先になっています。関係は、成り立つ条件と一緒に読みます。

- **上下限制約付き滑らか（PA008）**: 上下限は、一般の不等式制約のうち最も単純なものです。この型の特別な場合です。
- **単体上の最適化（PA036）**: 単体の制約は、線形の等式1本と非負制約の組です。これも特別な場合です。
- **混合整数非線形計画（PA025）**: 整数条件を外すと、この型になります。非凸なら、緩和で得た局所解は、元の問題の下界になりません。
- **多目的連続最適化（PA038）**: 重み付き和や $\varepsilon$ 制約でスカラー化すると、この型の問題の列になります。1つの問題の答えが、Pareto集合の点になる条件は、方法ごとに別に確かめます。
- **最適制御（PA042）とPDE制約付き最適化（PA045）**: 時間や空間を離散化すると、有限次元のこの型になります。離散化した問題の保証は、元の連続の問題の保証とは別です。離散化の細かさを変えて、答えの変化を確かめます。

## 解き方の系統

どの方法も、初期点から出発して、KKT条件を満たす点を探します。得られるのは局所解で、大域解ではありません。

- **逐次二次計画法（SQP, SLSQP）**: 各反復で、目的の二次近似と制約の線形近似から、二次計画の部分問題を作ります。その解を探索方向にします。[SQP](#/learn/sqp)、[SLSQP](#/learn/slsqp)にあります。
- **内点法**: 不等式制約に壁（barrier）を置き、主変数と乗数を同時に更新します。大規模で疎な問題に向きます。Ipoptなどが実装です。[NLP内点法](#/learn/interior-point-nlp)にあります。
- **拡張Lagrange法**: 制約違反への罰則と乗数の更新を組み合わせます。罰則を極端に大きくせずに、制約を満たす点へ近づけます。[拡張Lagrange法](#/learn/augmented-lagrangian)にあります。
- **微分不要法（COBYLAなど）**: 勾配を使わず、値だけから局所モデルを作ります。勾配が計算できる問題では、一般に不向きです。[COBYLA](#/learn/cobyla)にあります。

次のコードは、小さな例をSLSQPとtrust-constrで解きます。`scipy.optimize.minimize` を使います。

```python
import numpy as np
from scipy.optimize import Bounds, NonlinearConstraint, minimize


def f(z):
    return z[0] ** 2 + z[1] ** 2


def grad_f(z):
    return 2 * z


def g(z):  # g(z) <= 0 が「守る」側
    return (z[0] - 1) ** 2 + (z[1] - 1) ** 2 - 1


def grad_g(z):
    return 2 * (z - 1)


box = Bounds([-1, -1], [3, 3])

# SLSQP。scipy の "ineq" は fun >= 0 が守る側なので、符号を反転して渡す
slsqp = minimize(
    f, [2.0, 2.0], jac=grad_f, method="SLSQP", bounds=box,
    constraints=[{"type": "ineq", "fun": lambda z: -g(z), "jac": lambda z: -grad_g(z)}],
)
x = slsqp.x
lam = -(grad_f(x) @ grad_g(x)) / (grad_g(x) @ grad_g(x))  # 停留条件をみたす乗数
print("SLSQP:", x.round(4), round(slsqp.fun, 4), slsqp.success)
print("lambda:", round(lam, 4), "stationarity:", np.abs(grad_f(x) + lam * grad_g(x)).max().round(8))

# trust-constr は乗数 v も返す
tc = minimize(
    f, [2.0, 2.0], jac=grad_f, method="trust-constr", bounds=box,
    constraints=[NonlinearConstraint(g, -np.inf, 0.0)],
)
print("trust-constr:", tc.x.round(3), round(tc.fun, 4), "multiplier:", round(float(tc.v[0][0]), 3))

# 符号を取り違えると、別の問題を解いて success=True で返る
wrong = minimize(f, [2.0, 2.0], method="SLSQP", bounds=box, constraints=[{"type": "ineq", "fun": g}])
print("wrong sign:", wrong.x.round(3), round(wrong.fun, 3), wrong.success)
```

```text
SLSQP: [0.2929 0.2929] 0.1716 True
lambda: 0.4142 stationarity: 0.0
trust-constr: [0.293 0.293] 0.1716 multiplier: 0.414
wrong sign: [1.707 1.707] 5.828 True
```

二つの方法は、手計算の $(0.2929,\,0.2929)$ と、乗数 $0.4142$ に一致しました。
`stationarity` は、乗数を最小二乗で求めたあとに残る差です。0なので、二つの勾配は平行です。最後の行が、符号を取り違えたときの結果です。

局所解が複数ある例は、初期点を変えて解きます。

```python
import numpy as np
from scipy.optimize import minimize

# x1*x2 >= 1 の可行集合は、第1象限と第3象限の2つに分かれる
constraint = [{"type": "ineq", "fun": lambda z: z[0] * z[1] - 1}]
for start in ([2.0, 2.0], [-2.0, -2.0]):
    r = minimize(lambda z: z[0] + z[1], start, method="SLSQP",
                 bounds=[(-3, 3), (-3, 3)], constraints=constraint)
    print(start, "->", r.x.round(3), round(r.fun, 3), r.success)
```

```text
[2.0, 2.0] -> [1. 1.] 2.0 True
[-2.0, -2.0] -> [-3. -3.] -6.0 True
```

どちらの実行も `success=True` です。ソルバーの成功は「その初期点の近くでKKT条件を満たした」という意味で、大域解の保証ではありません。

## つまずきやすい点

- **不等式の符号**: scipy の `"ineq"` は、`fun >= 0` を守る側とします。$g(x)\le0$ の形の式をそのまま渡すと、円板の外側を可行と読みます。上の例では、境界の円の上で目的が最大になる点 $(1.707,\,1.707)$ で、`success=True` を返しました。式の符号を確かめます。下限と上限の組で指定するsolverでは、その組の意味も確かめます。
- **成功の意味**: `success=True` は、KKT条件を許容誤差の範囲で満たしたという意味です。局所解か鞍点かは、これだけでは区別できません。初期点を変えて何度か実行し、答えが一致するかを見ます。
- **停止した点の制約違反**: 許容誤差の範囲で、制約を少し破って止まることがあります。停止した点で $g(x)$ と $h(x)$ の値を出し、許容できる大きさかを確かめます。
- **制約想定が崩れる**: $\min x$ s.t. $x^2\le0$ の実行可能集合は $\{0\}$ だけで、$x=0$ が解です。ところが $\nabla g(0)=0$ なので、$1+\lambda\cdot0=0$ を満たす乗数がありません。最適点でもKKT条件が成り立たない例です。制約の勾配が消える点では、収束が遅くなったり、止まったりすることがあります。
- **離散化した問題の保証**: 微分方程式を離散化した問題を解いた結果は、離散化した問題の局所解です。連続の問題の解であることは別に確かめます。

## 次に読む

- [SLSQP](#/learn/slsqp)：二次計画を繰り返して、KKT条件を満たす点へ進む仕組み
- [NLP内点法](#/learn/interior-point-nlp)：大規模な問題でbarrierを使う方法
- [凸性](#/learn/concept.convexity)：KKT点が大域解になる条件
- [凸二次計画](#/learn/concept.convex-quadratic-program)：この型を特別な場合として含む、扱いやすい型
