---
content_id: hungarian-algorithm
kind: method
method_id: M_HUNGARIAN
title_ja: Hungarian Algorithm（割当問題）
title_en: Hungarian Algorithm
summary: 二部グラフの完全matchingとして表せる割当問題を、専用構造を使って多項式時間で厳密に解くアルゴリズムです。
source_ids: [S054]
prerequisites: []
related_ids: [dijkstra-astar, dynamic-programming, family.discrete-structure]
status: published
last_reviewed: 2026-07-24
---

二部グラフの完全matchingとして表せる割当問題を、専用構造を使って多項式時間で厳密に解くアルゴリズムです。

## 割当問題をどう表すか

$n$人の作業者と$n$個の仕事があり、作業者$i$を仕事$j$に割り当てる費用が$c_{ij}$で与えられているとします。
Hungarian algorithmでは、各作業者にちょうど1つの仕事を割り当てます。
各仕事にも、ちょうど1人だけを割り当てます。
この完全matchingの中から、費用の合計が最小のものを求めます。
汎用のMILPやLPにこの問題を投げても解けます。
割当問題の構造（二部グラフの完全matching）だけを使う専用アルゴリズムは、同じ最適解を汎用solverより高速に、かつ組合せ的な保証つきで返します。
「問題の構造を知っていれば専用アルゴリズムを選ぶ」という判断の代表例です。

次の図では、費用行列の各行から一つ、各列から一つだけ選びます。
青緑の3セルが、作業者と仕事を一対一に結ぶ費用5のmatchingです。

![3行3列の費用行列で、作業者1と仕事B、作業者2と仕事A、作業者3と仕事Cのセルが青緑で選ばれ、各行と各列が一度ずつ使われている](./media/hungarian-assignment-matrix.svg "固定した3×3費用行列で、一対一の割当と合計費用5を読む教育用模式図です。別の費用行列やside constraintsで同じ割当が最適になることは示しません。")

## 費用行列をどう簡約するか

簡約では、費用の相対関係を保ちながら0の候補を増やします。

1. 各行から、その行の最小値を引きます。
2. 続けて各列から、その列の最小値を引きます。
3. 0の位置だけで完全matchingを作れるか確認します。

完全matchingを作れない場合は、0を覆う最小本数の直線を引きます。
覆われていない部分を調整し、新しい0を増やしてから再判定します。

行・列reductionは、LPの双対変数（potentialまたはlabel）を更新する操作に対応します。
ここでは「reductionのたびに実行可能な双対解が改善される」という関係を押さえます。
双対理論の詳細を追わなくても、0だけで完全matchingを作れるかを停止判断に使えます。

## 向いている条件

- 割当が二部グラフの完全matchingとして表現できる
- 費用行列が事前に確定している、または容易に構築できる
- side constraints（作業者ごとの人数上限など）がない、または後で緩和・分割できる
- 厳密な最適解と多項式時間の保証が必要

## 避ける／切り替える条件

複数の仕事をまとめて1人が担当する場合や、特定の組み合わせを禁止する場合は、追加のside constraintsが必要です。
このとき二部完全matchingという構造が崩れ、Hungarian algorithmの前提が成り立たなくなります。
一部の作業者や仕事をunassignedのまま許す場合も、素朴には適用できません。
こうした場合はMILPやCP-SATへ戻り、side constraintsを明示的な制約式として表現します。

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

## 次に読む

同じ「構造を知っていれば専用法」という考え方は[Dijkstra法とA*](#/learn/dijkstra-astar)や[動的計画法](#/learn/dynamic-programming)にも共通します。離散・組合せ最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)を参照してください。
