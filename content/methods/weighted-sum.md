---
content_id: weighted-sum
kind: method
method_id: M_WEIGHTED_SUM
title_ja: 重み付き和scalarization
title_en: Weighted-sum Scalarization
summary: 複数目的を重み付き和で単一目的へ変換し、重みを変えながら単目的ソルバーを繰り返し解いてPareto候補を集める方法です。
source_ids: [S039, S055, S068]
prerequisites: [concept.convexity]
related_ids: [epsilon-constraint, multi-objective, moead]
visualization_ids: [biobjective-quadratic-pareto-front]
comparison_ids: [COMPARE_PARETO_PREFERENCE]
status: published
last_reviewed: 2026-09-30
---

複数目的を重み付き和で単一目的へ変換し、重みを変えながら単目的ソルバーを繰り返し解いてPareto候補を集める方法です。

## 30秒でつかむ

買い物で価格と移動距離に重みを付け、合計点で候補を比べます。重み付き和も、目的間の交換率を決めて一つの問題へまとめます。

- 見るもの: 候補の目的値と可行性
- 動かすもの: 次に試す候補と探索の状態
- 前進の判断: 固定した評価予算で良い候補が残ること

## 一手の意味

### 複数の目的を一つの目的関数にする

$m$個の目的 $f_1, \dots, f_m$ を最小化したいときは、非負の重み $w_1, \dots, w_m$ を使って次の単一目的問題に置き換えます。

$$
\min_x \sum_{i=1}^{m} w_i f_i(x), \qquad w_i \geq 0
$$

重みの組を一つ固定すると、既存の単目的ソルバーをそのまま呼び出せます。
重みを何通りも変えて同じ問題を解くと、得られた解の集合がトレードオフ（交換関係）の候補になります。

### 重みを変えて到達できるPareto解の範囲

重みをすべて正にして得られた最適解は、Pareto最適解の必要条件を満たします。
ただし、重みを掃引しても、すべてのPareto最適解に到達できるとは限りません。
目的空間でParetoフロント（パレートフロント）が凸である部分は、重みの組み合わせで到達できます。
一方、Paretoフロントが非凸に凹んでいる部分は別です。
どのような正の重みを選んでも、重み付き和の最適解として現れない解があります。
加重和の等高線は直線（超平面）であり、非凸領域の点はその直線群の接点になり得ないためです（[凸性](#/learn/concept.convexity)を参照）。
非凸領域の候補も調べたい場合は、[ε-constraint法](#/learn/epsilon-constraint)のように制約側から閾値を動かす方法が候補になります。

### 目的の尺度が重みの意味を変える

重み $w_i$ は、「目的$i$を1単位改善するために、ほかの目的をどれだけ犠牲にできるか」という交換率を表します。
目的ごとの尺度（単位や値の桁）が大きく異なると、同じ重みでも実質的な影響力が偏ります。
重みを決める前に、各目的を理想点やナディア点などの基準で正規化（正規化）しておくと、重みの比が意図した優先度に近づきます。

## 小さな例

Python節の $f_1=(x_1-1)^2+x_2^2$、$f_2=x_1^2+(x_2-1)^2$ を使います。
重みを $w_1=w,w_2=1-w$ とすると、解は $(w,1-w)$ です。
式を実行して、3通りの重みで目的値を確かめました。

| $w$ | 解 | $f_1$ | $f_2$ |
|---|---|---:|---:|
| 0.2 | $(0.2,0.8)$ | 1.28 | 0.08 |
| 0.5 | $(0.5,0.5)$ | 0.50 | 0.50 |
| 0.8 | $(0.8,0.2)$ | 0.08 | 1.28 |

$f_1$ の重みを増すと、$f_1$ は下がり $f_2$ は上がります。
この解析例は凸な目的を使い、非凸なフロントの網羅性は示しません。

## 向く条件・避ける条件

### 向いている条件

- 目的間の優先度を重み（重み）として表現しやすい
- Paretoフロントが凸に近いと想定できる、または非凸領域を無視してよい
- 単目的ソルバーを繰り返し呼び出せる評価予算がある
- 目的の尺度（尺度）を正規化（正規化）できる

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

各重みで得た`(f1, f2)`の組を並べると、交換関係曲線上の候補点が見えます。
重みを細かく振っても同じ点に集まる区間は、その付近で重みに対する解の感度が低いことを示します。
`scipy.optimize.minimize`の設定やアルゴリズム選択は、利用版の[公式リファレンス](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)で確認します。

## 診断値

- ハイパーボリューム（得られた解集合が覆う目的空間の体積）
- 間隔（解間の間隔の均一さ）
- ε指標（既知の参照集合との近さ）
- 可行な候補の割合（制約付き問題での可行な解の割合)

## 失敗・切替の兆候

- 重みを変えても解が同じ点に集中し、被覆範囲が乏しい
- 目的の尺度を揃えず、重みの意図と実際の交換率がずれている
- 想定した優先度と異なる極端な解ばかり得られる
- 重み格子を増やしても候補解の保存集合が際限なく膨らむ
- 評価予算が非常に小さく、複数回の単目的求解を許容できない

::: warning
重みを細かく振っても、非凸Paretoフロントの一部は原理的に得られません。
被覆範囲が不足しているように見えるとき、重み分割を細かくするだけでは解決しない場合があります。
:::

多目的最適化全体の枠組みは[多目的最適化とParetoフロント](#/learn/multi-objective)で確認できます。
目的数が多く重み格子が重くなる場合の分解的な代替は、[MOEA/D](#/learn/moead)で確認できます。

### Frontを作る計算と選ぶ判断を分ける

![81個の2目的候補から得たParetoフロント上で、重みw1を0.2、0.5、0.8へ変えると選択点が移動する固定実行結果。左下の理想点は二つの目的で同時には到達できない。](./media/pareto-preference-execution.svg "同じ解析的Pareto frontからweightで1点を選ぶ固定2目的教材です。weightの客観性や非凸frontの網羅性は示しません。")

青緑のフロントは計算で得る候補集合です。
橙の一点は、重みを与えた後の選択です。
フロントの生成と最終判断は同じ処理ではありません。

[選好感度のTheater](#/theater/learning/SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY)では、同じParetoフロントから重みで1点を選びます。
[選好を変えるCompare](#/compare/COMPARE_PARETO_PREFERENCE)は、81点の結果集合・目的方向・Pareto支配を固定します。
重みを0.2／0.5／0.8へ変え、フロント上の選択点だけを動かします。

このCompareはソルバーを再実行してフロントを改善する実験ではありません。
重みは意思決定上の選好であり、数学だけから客観的に決まる値でもありません。

これは凸で解析的な2目的教材です。
手法性能のベンチマークや一般性能順位ではなく、非凸フロントの欠落も解消しません。

## 次に読む

- [関連する手法の記事](#/learn/epsilon-constraint)：一手の意味と選び分けを比べます。

- [この手法を使う問題の定式化](#/formulations/PA038)：決定変数と目的を確認します。
