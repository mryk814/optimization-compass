---
content_id: weighted-sum
kind: method
method_id: M_WEIGHTED_SUM
title_ja: 重み付き和scalarization
title_en: Weighted-sum Scalarization
summary: 複数目的を重み付き和で単一目的へ変換し、重みを変えながら単目的solverを繰り返し解いてPareto候補を集める方法です。
source_ids: [S055, S039]
prerequisites: [concept.convexity]
related_ids: [epsilon-constraint, multi-objective, moead]
status: published
last_reviewed: 2026-07-16
---

複数目的を重み付き和で単一目的へ変換し、重みを変えながら単目的solverを繰り返し解いてPareto候補を集める方法です。

## 複数の目的を一つの目的関数にする

$m$個の目的 $f_1, \dots, f_m$ を最小化したいときは、非負の重み $w_1, \dots, w_m$ を使って次の単一目的問題に置き換えます。

$$
\min_x \sum_{i=1}^{m} w_i f_i(x), \qquad w_i \geq 0
$$

重みの組を一つ固定すると、既存の単目的solverをそのまま呼び出せます。
重みを何通りも変えて同じ問題を解くと、得られた解の集合がトレードオフ（trade-off）の候補になります。

## 重みを変えて到達できるPareto解の範囲

重みをすべて正にして得られた最適解は、Pareto最適解の必要条件を満たします。
ただし、重みを掃引しても、すべてのPareto最適解に到達できるとは限りません。
目的空間でPareto front（パレートフロント）が凸である部分は、重みの組み合わせで到達できます。
一方、Pareto frontが非凸に凹んでいる部分の解は、どのような正の重みを選んでも、重み付き和の最適解として現れません。
加重和の等高線は直線（超平面）であり、非凸領域の点はその直線群の接点になり得ないためです（[凸性](#/learn/concept.convexity)を参照）。
非凸領域の候補も調べたい場合は、[ε-constraint法](#/learn/epsilon-constraint)のように制約側からthresholdを動かす方法が候補になります。

## 目的のscaleが重みの意味を変える

重み $w_i$ は、「目的$i$を1単位改善するために、ほかの目的をどれだけ犠牲にできるか」という交換率を表します。
目的ごとのscale（単位や値の桁）が大きく異なると、同じ重みでも実質的な影響力が偏ります。
重みを決める前に、各目的をideal点やnadir点などの基準で正規化（normalize）しておくと、重みの比が意図した優先度に近づきます。

## 向いている条件

- 目的間の優先度をweight（重み）として表現しやすい
- Pareto frontが凸に近いと想定できる、または非凸領域を無視してよい
- 単目的solverを繰り返し呼び出せる評価予算がある
- 目的のscale（尺度）をnormalize（正規化）できる

非凸領域の解も網羅したい場合は、[ε-constraint法](#/learn/epsilon-constraint)への切り替えを検討します。
目的ごとに「ここまでは許す」という許容値の方が説明しやすい場合も、この方法が候補になります。

## Python

```python
import numpy as np
from scipy.optimize import minimize


def f1(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + x[1] ** 2)


def f2(x: np.ndarray) -> float:
    return float(x[0] ** 2 + (x[1] - 1.0) ** 2)


def weighted_sum(x: np.ndarray, w1: float, w2: float) -> float:
    return w1 * f1(x) + w2 * f2(x)


def solve_for_weight(w1: float) -> tuple[float, float]:
    w2 = 1.0 - w1
    result = minimize(weighted_sum, x0=np.array([0.5, 0.5]), args=(w1, w2))
    return f1(result.x), f2(result.x)


candidates = [solve_for_weight(w1) for w1 in np.linspace(0.0, 1.0, 6)]
print(candidates)
```

各重みで得た`(f1, f2)`の組を並べると、trade-off曲線上の候補点が見えます。
重みを細かく振っても同じ点に集まる区間は、その付近でweightに対する解の感度が低いことを示します。
`scipy.optimize.minimize`のoptionやalgorithm選択は、利用versionの[公式リファレンス](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)で確認します。

## 診断値

- hypervolume（得られた解集合が覆う目的空間の体積）
- spacing（解間の間隔の均一さ）
- epsilon indicator（既知の参照集合との近さ）
- feasible fraction（制約付き問題でのfeasibleな解の割合)

## 失敗・切替の兆候

- 重みを変えても解が同じ点に集中し、coverageが乏しい
- 目的のscaleを揃えず、重みの意図と実際の交換率がずれている
- 想定した優先度と異なる極端な解ばかり得られる
- 重みgridを増やしても候補solutionのarchiveが際限なく膨らむ
- 評価予算が非常に小さく、複数回の単目的求解を許容できない

::: warning
重みを細かく振っても、非凸Pareto frontの一部は原理的に得られません。
coverageが不足しているように見えるとき、重み分割を細かくするだけでは解決しない場合があります。
:::

多目的最適化全体の枠組みは[多目的最適化とPareto front](#/learn/multi-objective)で確認できます。
目的数が多く重みgridが重くなる場合の分解的な代替は、[MOEA/D](#/learn/moead)で確認できます。
