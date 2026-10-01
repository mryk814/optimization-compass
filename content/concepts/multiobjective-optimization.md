---
content_id: concept.multiobjective-optimization
kind: concept
canonical_entity_type: problem
canonical_entity_id: PA038
title_ja: 多目的連続最適化
title_en: Multiobjective Continuous Optimization
summary: 多目的連続最適化は、コストと性能のように複数の目的を同時に小さくする定式化です。答えは一点ではなく、どれかを良くすると別のどれかが悪くなる点の集合（Pareto集合）です。
prerequisites: [concept.convexity]
related_ids: [multi-objective, weighted-sum, epsilon-constraint, moead, nsga-iii, family.multi-objective]
source_ids: [S055, S039, S068]
status: published
last_reviewed: 2026-09-30
---

多目的連続最適化は、コストと性能のように複数の目的を同時に小さくする定式化です。答えは一点ではなく、どれかを良くすると別のどれかが悪くなる点の集合（Pareto集合）です。

## 30秒でつかむ

部品の設計で、費用を抑えたいし、性能損失も抑えたいとします。
費用が最小の設計と、性能損失が最小の設計は、別の設計になるのがふつうです。どちらも最小にする設計が存在するとは限りません。

このとき「最良の一点」は定まりません。定まるのは、これ以上どちらも良くできない設計の集合です。
集合の中から一点を選ぶには、どちらをどれだけ重く見るかという判断が要ります。この判断は、数学ではなく、使う人が下します。

- **決めるもの**: 設計寸法や運転条件のような連続の量
- **良くしたいもの**: 費用や性能損失のような複数の目的。同時に小さくしたい
- **守ること**: 変数の上下限と、必要なら安全の制約

「重みを先に決めたくない」「選べる候補を並べて見たい」という言葉が出たら、この型が入口です。

## 標準形を読む

この型は、目的が1つの値ではなく、値の組（ベクトル）になっている最小化です。

$$
\min_{x\in X}\; \big(f_1(x),\dots,f_m(x)\big)
$$

| 記号 | 意味 |
|---|---|
| $x\in X$ | 決める変数と、守るべき可行集合 |
| $f_1,\dots,f_m$ | 同時に小さくしたい目的。$m\ge2$ |
| 支配（dominate） | $f_i(x_a)\le f_i(x_b)$ が全部の $i$ で成り立ち、少なくとも1つは $<$ のとき、$x_a$ は $x_b$ を支配する |
| Pareto最適 | 可行な他のどの点にも支配されない点 |

Pareto最適な点の集合を、変数の空間で見たものがPareto集合、目的の空間で見たものがPareto front（パレートフロント）です。
支配されない点では、片方を良くするには、もう片方を悪くするしかありません。点どうしの優劣は、数学だけでは決まりません。

目的の向きをそろえることが前提です。最大化したい目的は、符号を反転して最小化にそろえます。

## 小さな例

公開事例『コストと性能のパレートトレードオフを探索する』の教材と同じ問題です。

$$
f_1=x^2+y^2,\qquad f_2=(x-2)^2+(y-2)^2,\qquad 0\le x,y\le2
$$

$f_1$ は原点からの距離の二乗で、原点で最小（0）になります。$f_2$ は点 $(2,2)$ からの距離の二乗で、$(2,2)$ で最小になります。
$f_1$ を最小にする点は $(0,0)$ で $f_2=8$、$f_2$ を最小にする点は $(2,2)$ で $f_1=8$ です。一点で両方を最小にはできません。

### Pareto集合は線分になる

Pareto集合は、原点と $(2,2)$ を結ぶ線分 $x=y=t$（$0\le t\le2$）です。
この線分の外にある点は、線分の上の最も近い点へ動かすと、$f_1$ と $f_2$ の両方が小さくなります。だから支配されます。

たとえば $(0,2)$ は $(f_1,f_2)=(4,4)$ です。$(\sqrt2,\sqrt2)$ は $(4,\,0.686)$ で、$f_1$ が同じまま $f_2$ が小さく、$(0,2)$ を支配します。

線分の上では、$f_1=2t^2$、$f_2=2(2-t)^2$ です。

| $t$ | 0 | 0.5 | 1 | 1.5 | 2 |
|---|---:|---:|---:|---:|---:|
| $f_1$ | 0 | 0.5 | 2 | 4.5 | 8 |
| $f_2$ | 8 | 4.5 | 2 | 0.5 | 0 |

$t$ を増やすと $f_1$ は悪化し、$f_2$ は改善します。どの $t$ の点も、他の点に支配されません。

### 読み取り: 一点を選ぶ二つの方法

一点を選ぶには、選好を式にします。

**重み付き和**は、$w f_1+(1-w)f_2$ を最小にします。この例では $t=2(1-w)$ です。$w=0.25$ なら $t=1.5$、$w=0.5$ なら $t=1$、$w=0.75$ なら $t=0.5$ です。
**ε制約法**は、$f_1$ を最小にしながら、$f_2\le\varepsilon$ を守らせます。$\varepsilon=2$ なら、$t=1$ です。

どちらも、単一の目的の問題を解いて、Pareto集合の1点を得ます。重みや $\varepsilon$ を変えれば、別の点が得られます。

### 重みが効かない front

$f_1=t$、$f_2=1-t^2$（$0\le t\le1$）は、front が原点から見て外側へ膨らんだ（非凸の）形をしています。
重み付き和 $wt+(1-w)(1-t^2)$ は、$t$ の凹関数なので、最小は $t=0$ か $t=1$ の端になります。重みをどう振っても、内側の点は出てきません。
$\varepsilon$ 制約法なら、$f_2\le\varepsilon$ の $\varepsilon$ を変えるだけで、内側の点も得られます。

### 事例との対応

公開事例『蓄電池運用のコストと充放電量を両方見る』と『信号制御の遅れと停止回数を両方見る』は、同じ二次の教材関数を、別の意味で読んでいます。
実際の運用では、変数は充放電のスケジュールや信号の秒数で、制約もあります。教材の $x,y$ は、そのトレードオフを読むための代理変数です。

## 見分け方

次の兆候があれば、この型を疑います。

- コストと性能、速さと精度のように、重みを先に決めたくない
- 目的が2つ以上あり、単位も意味も違う
- 「最良の一点」ではなく、選べる候補の一覧が欲しい

別の型へ向かう兆候もあります。

- 一つの目的に絞れる（優先順位が決まっている、または片方が制約で足りる） → [一般滑らか制約付きNLP（PA009）](#/formulations/PA009)
- 目的の評価が高価で、試せる回数が少ない → 多目的のベイズ最適化などが候補。土台は[PA014](#/formulations/PA014)の考え方
- 目的が多数になり、点の分布が偏る → 多数目的（many-objective）向けの手法。[NSGA-III](#/learn/nsga-iii)
- 手法を調整する場面で、検証損失と時間の二つを見たい → [ハイパーパラメータ最適化（PA039）](#/formulations/PA039)

## 近い定式化

- **一般滑らか制約付きNLP（PA009）**: 重み付き和や $\varepsilon$ 制約でスカラー化すると、この型の問題の列になります。1つの問題の答えが、Pareto集合の点になる条件は、方法ごとに別に確かめます。
- **重み付き和の性質**: 目的も可行集合も凸なら、正の重みの重み付き和の解は、Pareto最適です。逆に、Pareto最適な点は、ある非負の重みの解になります。凸でなければ、上の非凸の例のように、取りこぼす点が出ます。
- **ε制約法**: $\varepsilon$ を動かすと、非凸の front の内側も探れます。ただし、$\varepsilon$ が小さすぎると、可行な解が存在しません。

## 解き方の系統

- **スカラー化（重み付き和、$\varepsilon$ 制約）**: 単一の目的のsolverを、重みや $\varepsilon$ を変えて繰り返します。各問題の保証（局所解か大域解か）は、そのsolverから引き継ぎます。[重み付き和](#/learn/weighted-sum)と[ε制約法](#/learn/epsilon-constraint)にあります。
- **集団による方法（NSGA-II、NSGA-III、MOEA/D）**: 集団を進化させます。1回の実行で、Pareto集合の近似ができます。真のfrontは分からないので、近似の質は評価回数と乱数に左右されます。[NSGA-III](#/learn/nsga-iii)と[MOEA/D](#/learn/moead)にあります。
- **選好の使い方**: 先に重みを決めてから解く方法と、候補を並べてから選ぶ方法があります。全体の考え方は[多目的最適化](#/learn/multi-objective)にあります。

次のコードは、小さな例を重み付き和と $\varepsilon$ 制約法で解き、2つの補足の確認も同時にします。

```python
import numpy as np
from scipy.optimize import minimize


def objectives(z):
    x, y = z
    return np.array([x**2 + y**2, (x - 2) ** 2 + (y - 2) ** 2])


box = [(0, 2), (0, 2)]
start = [1.0, 0.3]

print("weighted sum: min w*f1 + (1-w)*f2")
for w in (0.1, 0.25, 0.5, 0.75, 0.9):
    r = minimize(lambda z: w * objectives(z)[0] + (1 - w) * objectives(z)[1], start, bounds=box, method="SLSQP")
    print(f"  w={w:<4} x={r.x.round(3)} f={objectives(r.x).round(3)}")

print("epsilon constraint: min f1 s.t. f2 <= eps")
for eps in (0.5, 2.0, 4.5):
    r = minimize(lambda z: objectives(z)[0], start, bounds=box, method="SLSQP",
                 constraints=[{"type": "ineq", "fun": lambda z, e=eps: e - objectives(z)[1]}])
    print(f"  eps={eps:<4} x={r.x.round(3)} f={objectives(r.x).round(3)}")

print("dominated point (0, 2):", objectives([0.0, 2.0]).round(3), "vs", objectives([2**0.5, 2**0.5]).round(3))

# f1 の単位を100倍にすると、同じ重み w=0.5 でも答えが動く
r = minimize(lambda z: 0.5 * 100 * objectives(z)[0] + 0.5 * objectives(z)[1], start, bounds=box, method="SLSQP")
print("f1 x100, w=0.5:", r.x.round(3), objectives(r.x).round(3))

# 非凸な front: f1 = t, f2 = 1 - t^2 (0 <= t <= 1)
t = np.linspace(0, 1, 1001)
weighted = {round(float(t[np.argmin(w * t + (1 - w) * (1 - t**2))]), 3) for w in np.arange(0.05, 1, 0.1)}
print("nonconvex, weighted-sum answers:", sorted(weighted))
answers = [float(t[(1 - t**2) <= e][0]) for e in (0.9, 0.75, 0.5, 0.25)]
print("nonconvex, epsilon answers:", [round(a, 3) for a in answers])
```

```text
weighted sum: min w*f1 + (1-w)*f2
  w=0.1  x=[1.8 1.8] f=[6.48 0.08]
  w=0.25 x=[1.5 1.5] f=[4.5 0.5]
  w=0.5  x=[1. 1.] f=[2. 2.]
  w=0.75 x=[0.5 0.5] f=[0.5 4.5]
  w=0.9  x=[0.2 0.2] f=[0.08 6.48]
epsilon constraint: min f1 s.t. f2 <= eps
  eps=0.5  x=[1.5 1.5] f=[4.5 0.5]
  eps=2.0  x=[1. 1.] f=[2. 2.]
  eps=4.5  x=[0.5 0.5] f=[0.5 4.5]
dominated point (0, 2): [4. 4.] vs [4.    0.686]
f1 x100, w=0.5: [0.02 0.02] [1.000e-03 7.842e+00]
nonconvex, weighted-sum answers: [0.0, 1.0]
nonconvex, epsilon answers: [0.317, 0.5, 0.708, 0.867]
```

重みごとの解は、手計算の $t=2(1-w)$ に一致します。$\varepsilon=2$ の解も、$t=1$ です。
非凸の例では、10通りの重みを試しても、答えは $t=0$ と $t=1$ の2つだけです。$\varepsilon$ 制約法は、内側の4点を返しました。

次のコードは、pymoo の NSGA-II で、同じ問題のPareto集合の近似を作ります。`pip install pymoo` が必要です。

```python
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize


class TwoObjectives(Problem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, xl=0.0, xu=2.0)

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = np.column_stack([x[:, 0] ** 2 + x[:, 1] ** 2, (x[:, 0] - 2) ** 2 + (x[:, 1] - 2) ** 2])


result = minimize(TwoObjectives(), NSGA2(pop_size=20), ("n_gen", 30), seed=1, verbose=False)

# 厳密な front（x = y の線分）と比べる。実問題では、この答え合わせはできない
t = np.linspace(0, 2, 2001)
front = np.column_stack([2 * t**2, 2 * (2 - t) ** 2])
gap = np.linalg.norm(result.F[:, None, :] - front[None, :, :], axis=2).min(axis=1)
print("solutions:", len(result.F), "evaluations:", result.algorithm.evaluator.n_eval)
print("f1 range:", result.F[:, 0].min().round(3), result.F[:, 0].max().round(3))
print("distance to exact front: mean", gap.mean().round(3), "max", gap.max().round(3))
```

```text
solutions: 20 evaluations: 600
f1 range: 0.0 7.897
distance to exact front: mean 0.058 max 0.239
```

20個体・600回の評価で、20点の非支配解を得ました。$f_1$ の範囲は端から端まで広がっています。
真のfrontからの距離は、平均0.058、最大0.239です。近似であり、線分の上にちょうど乗っているわけではありません。この結果は、seedと個体数に依存します。

## つまずきやすい点

- **重みは単位に依存する**: $f_1$ を100倍した単位で測ると、同じ $w=0.5$ でも解は $t=0.02$ に動きます。重みは選好そのものではなく、単位と組みになった数です。目的を正規化してから重みを決めるか、$\varepsilon$ 制約のように単位付きの上限で表します。
- **重みを振っても端しか出ない**: 上の非凸の例で、重みを10通り振っても、出てきたのは両端の2点だけでした。点が偏るときは、frontが非凸でないかを疑い、$\varepsilon$ 制約法などを試します。
- **近似のfrontを真のfrontと読む**: 集団による方法が返すのは近似です。上の例でも、平均0.058のずれがありました。比較するときは、評価回数・seed・正規化・停止条件をそろえます。
- **端の点を候補に入れる**: $t=0$ の点は $f_1=0$ ですが、$f_2=8$ で最悪の値です。Pareto最適でも、実務では受け入れられない端があります。最低限の性能などの制約で、領域を先に絞ります。
- **目的の向きが混ざる**: 最大化したい目的が混じると、支配の判定が逆になります。全部を最小化にそろえてから解きます。
- **frontが広がっただけで判断する**: 候補が多いことは、最終的な選択が決まったことではありません。選好に合う一点を選ぶ段階を、別に置きます。

## 次に読む

- [多目的最適化](#/learn/multi-objective)：支配・Pareto集合・選好を分けて扱う考え方
- [重み付き和](#/learn/weighted-sum)：スカラー化の一つ目と、取りこぼしの条件
- [ε制約法](#/learn/epsilon-constraint)：閾値を動かしてfrontをたどる
- [一般滑らか制約付きNLP](#/formulations/PA009)：スカラー化した後に解く問題の型
