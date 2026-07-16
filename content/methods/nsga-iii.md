---
content_id: nsga-iii
kind: method
method_id: M_NSGA_III
title_ja: NSGA-III
title_en: NSGA-III
summary: 多数目的でcrowding distanceだけでは分布を保ちにくいとき、reference directionへ解を対応付けてPareto候補の広がりを維持する進化的手法です。
source_ids: [S039]
related_ids: [multi-objective, epsilon-constraint]
status: published
last_reviewed: 2026-07-16
---

多数目的でcrowding distanceだけでは分布を保ちにくいとき、reference directionへ解を対応付けてPareto候補の広がりを維持する進化的手法です。

## 30秒でつかむ

この手法の気持ちは、**目的が3個、5個、10個と増えて「混んでいる場所」が分かりにくくなっても、あらかじめ置いた方向ごとに代表候補を残してtrade-off全体を広く見たい**というものです。

- 見ているもの: objective vector、Pareto rank、reference directionとの距離
- 動かしているもの: population、association、selection
- 前進の判断: 非支配候補の質とreference方向のcoverage
- 恐れていること: objective scaling、方向数の爆発、実行不可能解の偏り

NSGA-IIの単純な上位版ではありません。目的数と意思決定上必要な分布に応じて選びます。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| objective count | 2目的か、many-objectiveか |
| direction | 各目的がminimize / maximizeのどちらか |
| scaling | objectiveの単位とrangeを揃えられるか |
| reference directions | 必要な方向数と関心領域を定義できるか |
| constraints | feasible populationを維持できるか |
| budget | population × generationの評価数を許容できるか |

2目的ならNSGA-IIやε-constraintの方が説明しやすく、少ない評価で済む場合があります。

## 仕組み

まずPareto dominanceでfrontを分けます。最後に一部だけ選ぶfrontでは、objective vectorを正規化し、各解を最も近いreference directionへ対応付けます。候補が不足している方向を優先し、population全体の広がりを保ちます。

reference directionは「真のPareto front」ではありません。どのtrade-off方向を均等に見たいかという探索上の設計です。

## 向く条件・避ける条件

向きやすい条件:

- 3目的以上のmany-objective問題
- 非凸・black-boxでgradientを使いにくい
- 一つの解ではなく多様な候補集合が必要
- parallel evaluationを利用できる

避ける条件:

- 目的が2個で関心領域も狭い
- 一評価が高価でpopulationを維持できない
- objective scaleやdirectionが未整理
- 最終選択のpreferenceを全く議論しない

## うまくいったサインと切替サイン

見る値:

- occupied reference direction数
- non-dominated solution数
- hypervolumeやIGDなどの指標
- feasible fraction
- objective normalizationの範囲
- seed間のcoverage差
- population diversity

切替サイン:

- 多くの方向が空のまま → population、方向数、variation operatorを見直す
- 極端解だけ残る → normalizationとconstraint handlingを確認
- 関心のない領域へ評価を使う → preference-aware directionへ絞る
- 目的数が2〜3でbackend solverが強い → ε-constraintへ
- 評価budgetが不足 → surrogate-assisted multi-objective法を検討

## Python

```python
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.optimize import minimize
from pymoo.problems import get_problem
from pymoo.util.ref_dirs import get_reference_directions

problem = get_problem("dtlz2", n_obj=3)
reference_directions = get_reference_directions("das-dennis", 3, n_partitions=8)
algorithm = NSGA3(pop_size=len(reference_directions), ref_dirs=reference_directions)
result = minimize(problem, algorithm, ("n_gen", 100), seed=7, verbose=False)
print(result.F.shape)
```

実務ではproblem、reference directions、population、seed、evaluation budgetを保存します。

## コラム: 可視化できないことを前提にする

4目的以上ではPareto集合を一枚の散布図へ正確に置けません。pair plot、parallel coordinates、reference direction occupancy、選択中の解のtableを組み合わせます。3Dを使っても目的数そのものは減りません。

[多目的最適化とPareto front](#/learn/multi-objective)でdominanceを確認し、preferenceを閾値で表せる場合は[ε-constraint法](#/learn/epsilon-constraint)も比較してください。