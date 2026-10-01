---
content_id: cp-sat
kind: method
method_id: M_CP_SAT
title_ja: CP-SATと制約プログラミング
title_en: CP-SAT and Constraint Programming
summary: 真偽値・整数・論理・スケジューリング制約を、伝播・SAT学習・探索の組合せで解き、実行可能解と界から停止状態を読む離散最適化法です。
source_ids: [S022, S053]
prerequisites: [branch-and-bound]
related_ids: [branch-and-bound, branch-and-cut, dynamic-programming]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: []
aliases: [/learn/cp-sat]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-09-30
---

真偽値・整数・論理・スケジューリング制約を、伝播・SAT学習・探索の組合せで解き、実行可能解と界から停止状態を読む離散最適化法です。

## 30秒でつかむ

勤務表を埋めるとき、決まった勤務から不可能な候補を消し、行き詰まった条件も覚えて探索します。

- 見るもの: 可行解、探索の下界、矛盾
- 動かすもの: 整数の割当と探索枝
- 前進の判断: 可行解と下界の差が縮むこと

## 一手の意味

仕事 $t$ の担当者を一人に決め、各人の仕事数を容量以下にします。

$$
\sum_w a_{wt}=1,\qquad \sum_t a_{wt}\le c_w,\qquad a_{wt}\in\{0,1\}
$$

これらの制約から候補を絞り、目的の下界と可行解を更新します。

### 現実の問いをモデルへ移す

| 項目 | 例 |
|---|---|
| decision variables | 人・仕事・時間帯の割当、順序、optional task |
| 目的値 | 費用、遅延、希望違反、makespan |
| hard constraints | 必要人数、資格、相互排他、precedence、time window |
| soft constraints | 希望、安定性、変更量をpenaltyとして表す |
| problem features | 有限候補集合、論理関係、global スケジューリング 制約 |

必須制約と罰則を分けます。
すべてを大きなpenaltyへ押し込むと、本当に禁止したい条件と単に避けたい条件を区別しにくくなります。

### 探索で何が起きるか

CP-SATは単純な木 enumerationではありません。
実装は、

- 候補集合 伝播
- 真偽値 符号化
- 衝突 analysis / 学習節
- 前処理
- 線形緩和や切除平面の利用
- 可行解探索ヒューリスティック
- 分岐 / 再始動

などを統合します。
したがって教育用Search Treeは最良可行解・界・gap・pruneの概念を示しますが、実ソルバー内部を完全再現する図ではありません。

## 小さな例

Python節の3人、4仕事、各人の容量2という割当を使います。
仕事0〜3の担当者を並べ、容量と費用を計算します。

| 候補 | 各人の仕事数 | 費用 | 判定 |
|---|---|---:|---|
| $(0,0,0,0)$ | $(4,0,0)$ | 21 | 容量違反 |
| $(0,1,0,1)$ | $(2,2,0)$ | 12 | 可行 |
| $(0,1,2,1)$ | $(1,2,1)$ | 11 | 可行 |

容量違反の21を、可行解の目的値と比較しません。
全 $3^4=81$ 割当を確認した最小費用は11です。
この表は候補の検査順であり、CP-SAT内部の探索順を再現しません。

## 向く条件・避ける条件

### 整数化と尺度

実数係数を整数へ尺度する場合、丸め誤差と係数範囲を確認します。

- 通貨を円・銭のどちらで持つか
- 時間を秒・分のどちらで離散化するか
- 小数係数を何倍して整数化するか
- overflowや巨大係数で伝播が弱くならないか

「整数化できた」ことと、現実の精度を保ったことは別です。

### まず確認すること

- 変数を真偽値・整数・有限候補集合として表せるか
- 必須制約と罰則を分けられているか
- 整数化の尺度が、必要な精度と係数範囲に収まっているか
- 制限時間内の良い解だけでなく、界や証明も必要か

### 向いている条件

- 真偽値・整数・有限候補集合変数
- 論理含意、optional interval、no-overlap、cumulativeなど
- スケジューリング・assignment・packing
- feasibility自体が難しい
- 制限時間内の良い解と界が欲しい

### Alternative-first

- pure shortest path / マッチング / 流量 → 専用graph algorithm
- small state DP → [動的計画法](#/learn/dynamic-programming)
- 強い線形緩和を持つMILP → [Branch-and-Cut](#/learn/branch-and-cut)
- 本質的に連続・滑らか → NLP/QP系

## Python

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
workers = range(3)
tasks = range(4)
assignment = {
    (worker, task): model.new_bool_var(f"assign_{worker}_{task}")
    for worker in workers
    for task in tasks
}

for task in tasks:
    model.add(sum(assignment[worker, task] for worker in workers) == 1)

capacity = [2, 2, 2]
for worker in workers:
    model.add(sum(assignment[worker, task] for task in tasks) <= capacity[worker])

cost = [
    [3, 8, 4, 6],
    [5, 2, 7, 3],
    [6, 4, 3, 5],
]
model.minimize(
    sum(cost[worker][task] * assignment[worker, task] for worker in workers for task in tasks)
)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10.0
solver.parameters.random_seed = 7
status = solver.solve(model)

print(status, solver.objective_value, solver.best_objective_bound)
```

実行後は状態を確認してからvalueを読みます。
`FEASIBLE`は実行可能解を得たが、最適性は未証明です。
`OPTIMAL`は設定した許容誤差のもとで最適性を証明済みです。
`INFEASIBLE`はモデルが矛盾し、`UNKNOWN`は計算予算などの理由で結論がない状態です。

## 診断値

- 状態
- 目的値 / best 界 / gap
- conflicts
- branches
- propagations
- restarts
- 実時間
- first 実行可能までの時間
- solution count
- 前処理 簡約
- random seed / worker count

並列worker数を変えると探索順と再現性が変わる場合があります。

## 失敗・切替の兆候

- 候補集合が巨大で伝播が弱い
- 対称性により同等解を反復
- 罰則の尺度が目的値を歪める
- 係数の整数尺度が過大
- 実行可能 solutionが長時間見つからない
- `UNKNOWN`を`INFEASIBLE`と誤読
- 連続 物理現象を粗い整数gridへ無理に離散化

::: warning
CP-SAT、MIP、専用DPは同じ離散問題を異なる表現で解けます。
手法名だけで比較しません。
モデルと制限時間に加え、ハードウェア／乱数の種／並列ワーカー数／ギャップを揃えます。
:::

## 次に読む

強い線形緩和を使うMILPなら[Branch-and-Cut](#/learn/branch-and-cut)、state再利用が中心なら[動的計画法](#/learn/dynamic-programming)と比較します。

- 問題の形を確認する: [混合整数線形計画](#/formulations/PA023)
