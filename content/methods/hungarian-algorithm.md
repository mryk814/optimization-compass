---
content_id: hungarian-algorithm
kind: method
method_id: M_HUNGARIAN
title_ja: Hungarian Algorithm（割当問題）
title_en: Hungarian Algorithm
summary: 二部グラフの最小費用完全matching（割当問題）を多項式時間で厳密に解く、専用構造に特化したアルゴリズムです。
source_ids: [S054]
prerequisites: []
related_ids: [dijkstra-astar, dynamic-programming, family.discrete-structure]
status: published
last_reviewed: 2026-07-16
---

二部グラフの最小費用完全matching（割当問題）を多項式時間で厳密に解く、専用構造に特化したアルゴリズムです。

## 何を解いているか

$n$人の作業者と$n$個の仕事があり、作業者$i$を仕事$j$に割り当てる費用が$c_{ij}$で与えられているとします。Hungarian algorithmは、各作業者にちょうど1つの仕事を割り当て、各仕事にちょうど1人が割り当たる完全matchingのうち、費用の合計が最小のものを求めます。汎用のMILPやLPにこの問題を投げても解けますが、割当問題の構造（二部グラフの完全matching）だけを使う専用アルゴリズムは、同じ最適解を汎用solverより高速に、かつ組合せ的な保証つきで返します。「問題の構造を知っていれば専用アルゴリズムを選ぶ」という判断の代表例です。

## 費用行列をどう簡約するか

直感的には、各行から行内最小値を引き、続けて各列から列内最小値を引くと、費用0の要素が増えます。この0の位置だけで完全matchingが作れれば、それが最適解です。作れない場合は、0を覆う最小本数の直線を引き、覆われていない部分をさらに調整して0を増やす操作を繰り返します。この行・列reductionはLPの双対変数（potentialまたはlabelと呼ばれる値）を更新する操作と対応していますが、双対理論の詳細には立ち入らず、「reductionのたびに実行可能な双対解が改善されていく」という関係だけを押さえておけば十分です。

## 向いている条件

- 割当が二部グラフの完全matchingとして表現できる
- 費用行列が事前に確定している、または容易に構築できる
- side constraints（作業者ごとの人数上限など）がない、または後で緩和・分割できる
- 厳密な最適解と多項式時間の保証が必要

## 専用構造が壊れるとき

割当問題に追加のside constraints（複数の仕事をまとめて1人が担当する、特定の組み合わせを禁止するなど）が加わると、二部完全matchingという構造そのものが崩れ、Hungarian algorithmの前提が成り立たなくなります。また、完全matchingではなく一部の作業者や仕事が割り当てられない状況を許す場合も、素朴な適用はできません。こうした場合は、MILPやCP-SATのような汎用solverへ戻り、side constraintsを明示的な制約式として表現する方が安全です。

## Python

```python
import numpy as np
from scipy.optimize import linear_sum_assignment


def build_cost_matrix() -> np.ndarray:
    return np.array(
        [
            [4.0, 1.0, 3.0],
            [2.0, 0.0, 5.0],
            [3.0, 2.0, 2.0],
        ]
    )


cost = build_cost_matrix()
row_indices, col_indices = linear_sum_assignment(cost)
total_cost = float(cost[row_indices, col_indices].sum())

print(row_indices, col_indices, total_cost)
```

`row_indices`と`col_indices`は同じ長さの配列で、`row_indices[k]`が`col_indices[k]`へ割り当てられたことを表します。最大化問題として使う場合や矩形行列を扱う場合の挙動は、利用versionの[公式リファレンス](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html)で確認します。

## 診断値

- states（探索中に扱う部分matching・labelの状態数）
- edges（費用行列が表す二部グラフの辺数）
- labels（reduction中に維持するpotential/labelの値）
- memory（費用行列と補助構造が使うmemory量）
- optimality condition（0だけで完全matchingが作れているかどうか）

## 失敗・切替の兆候

- 追加のside constraintsで二部完全matchingという前提が崩れている
- 割当が完全matchingでなく、一部が unassigned のままでよい設定になっている
- 状態や作業者・仕事の数が非常に大きく、費用行列の構築自体が重い
- 費用が負の閉路や不正な前提（対称性の誤仮定など）を含んでいる

::: note
専用アルゴリズムは、対象の問題が想定した構造から外れた瞬間に保証を失います。side constraintsを足したくなったら、MILPなど汎用の定式化に戻ることを検討します。
:::

同じ「構造を知っていれば専用法」という考え方は[Dijkstra法とA*](#/learn/dijkstra-astar)や[動的計画法](#/learn/dynamic-programming)にも共通します。離散・組合せ最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)を参照してください。
