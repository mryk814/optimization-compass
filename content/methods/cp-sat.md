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
last_reviewed: 2026-10-03
---

真偽値・整数・論理・スケジューリング制約を、伝播・SAT学習・探索の組合せで解き、実行可能解と界から停止状態を読む離散最適化法です。

## 30秒でつかむ

4つの仕事を3人へ振り分け、費用12の予定ができました。全員が容量以内なら、もう探索を止めてよいでしょうか。予定を採用することはできますが、それだけでは「最も安い」とは言えません。

CP-SATは、真偽値・整数・論理・区間の条件を組み合わせて解きます。最小化では、見つけた可行解が上界、「これより安くできない」という情報が下界です。両者の差を見れば、まだ改善できる余地を読み取れます。本稿の割当では、費用11の解と下界11が一致します。

- **見るもの**: 条件を守る解、その費用、最良下界、終了状態
- **変えるもの**: 担当の候補や探索枝。既に不可能と分かった候補は制約で除く
- **止め方の違い**: 時間内に可行解を採用することと、最適性まで証明することを分ける

## 一手の意味

仕事 $t$ の担当者を一人に決め、各人の仕事数を容量以下にします。

$$
\sum_w a_{wt}=1,\qquad \sum_t a_{wt}\le c_w,\qquad a_{wt}\in\{0,1\}
$$

これらの制約から候補を絞り、目的の下界と可行解を更新します。

### 現実の問いをモデルへ移す

| 項目 | 例 |
|---|---|
| 決定変数 | 人・仕事・時間帯の割当、順序、任意参加の作業 |
| 目的値 | 費用、遅延、希望違反、全作業の完了時刻 |
| 必ず守る制約 | 必要人数、資格、相互排他、先行関係、時間窓 |
| 違反を許す制約 | 希望、安定性、変更量をペナルティとして表す |
| 問題の特徴 | 有限候補集合、論理関係、全体のスケジューリング制約 |

必須制約と罰則を分けます。
すべてを大きなペナルティへ押し込むと、本当に禁止したい条件と単に避けたい条件を区別しにくくなります。

### 探索で何が起きるか

CP-SATは単純な木の列挙ではありません。
実装は、

- 候補集合伝播
- 真偽値符号化
- 衝突分析 / 学習節
- 前処理
- 線形緩和や切除平面の利用
- 可行解探索ヒューリスティック
- 分岐 / 再始動

などを統合します。
したがって教育用探索木は最良可行解・界・ギャップ・枝刈りの概念を示しますが、実ソルバー内部を完全再現する図ではありません。

## 小さな例

Python節の3人、4仕事、各人の容量2という割当を使います。
仕事0〜3の担当者を並べ、容量と費用を計算します。行が人、列が仕事で、数字が割当費用です。各仕事はちょうど1人、各人は最大2仕事を担当します。

| 人\仕事 | 0 | 1 | 2 | 3 |
|---|---:|---:|---:|---:|
| 0 | 3 | 8 | 4 | 6 |
| 1 | 5 | 2 | 7 | 3 |
| 2 | 6 | 4 | 3 | 5 |

担当を $(0,1,0,1)$ と書くのは、仕事0と2を人0、仕事1と3を人1へ渡す意味です。費用は $3+2+4+3=12$ です。

| 候補 | 各人の仕事数 | 費用 | 判定 |
|---|---|---:|---|
| $(0,0,0,0)$ | $(4,0,0)$ | 21 | 容量違反 |
| $(0,1,0,1)$ | $(2,2,0)$ | 12 | 可行 |
| $(0,1,2,1)$ | $(1,2,1)$ | 11 | 可行 |

容量違反の21を、可行解の目的値と比較しません。
全 $3^4=81$ 割当を確認した最小費用は11です。
表は三つの候補を比較する教材であり、CP-SAT内部の探索順を再現しません。

![同じ費用行列の三つの担当案。左は人0が4仕事で容量違反、中央は各人2仕事以内で費用12、右は担当0 1 2 1で費用11。選択したセルだけを緑で示す。](./media/cp-sat-assignment-oracle.svg "全81割当の基準計算と同じ費用行列。ソルバーの探索履歴、ログ、best boundの時系列を描いた図ではありません。")

### 一つの担当を変える

中央の予定から、仕事2を人0ではなく人2へ移します。その費用は4から3へ下がり、担当数は $(2,2,0)$ から $(1,2,1)$ になります。全員が容量以内なので、費用11の新しい可行解です。単なる費用の足し算だけでなく、移動先と移動元の担当数も調べます。

ここまでは「11まで改善できた」という上界です。最適性には下界も必要です。

### 下界を手で作って一致させる

いったん「各人2仕事まで」を無視し、各仕事を最安の人へ独立に渡してみます。仕事ごとの最小費用は $3,2,3,3$ なので、合計は11。制約を外した問題は元より安くなってよいため、元の最小費用は11以上です。

この最安の組合せが、偶然にも容量を守る $(0,1,2,1)$ でした。したがって

$$11\;\text{（下界）}\le z^*\le11\;\text{（可行解）}$$

となり、最適値11が証明できました。この例は下界が特に簡単に一致するため、難しいSAT学習や枝刈りの挙動を実演する例ではありません。別の費用や容量では、仕事ごとの最安割当が同じ人へ集中し、下界だけでは解を作れなくなります。

なお、図の下界11はこの手計算で得た値です。実行していないCP-SATの `best_objective_bound` を測定した値として表示していません。

## 向く条件・避ける条件

### 整数化と尺度

実数係数を整数へ尺度する場合、丸め誤差と係数範囲を確認します。

- 通貨を円・銭のどちらで持つか
- 時間を秒・分のどちらで離散化するか
- 小数係数を何倍して整数化するか
- オーバーフローや巨大係数で伝播が弱くならないか

「整数化できた」ことと、現実の精度を保ったことは別です。

### まず確認すること

- 変数を真偽値・整数・有限候補集合として表せるか
- 必須制約と罰則を分けられているか
- 整数化の尺度が、必要な精度と係数範囲に収まっているか
- 制限時間内の良い解だけでなく、界や証明も必要か

### 向いている条件

- 真偽値・整数・有限候補集合変数
- 論理含意、任意参加の区間、no-overlap、cumulativeなど
- スケジューリング・割当・詰込み
- 実行可能性自体が難しい
- 制限時間内の良い解と界が欲しい

### 専用構造から先に検討する

- 純粋な最短路 / マッチング / 流量 → 専用グラフアルゴリズム
- 小さな状態の DP → [動的計画法](#/learn/dynamic-programming)
- 強い線形緩和を持つMILP → [Branch-and-Cut](#/learn/branch-and-cut)
- 本質的に連続・滑らか → NLP/QP系

## Python

### 最初に全列挙で答えを確かめる

標準ライブラリだけで全 $3^4=81$ 割当を調べます。大きい問題を解くアルゴリズムとして使うのではなく、定式化とソルバー出力を照合する基準計算です。

```python
from itertools import product

cost = [[3, 8, 4, 6], [5, 2, 7, 3], [6, 4, 3, 5]]
capacity = [2, 2, 2]
feasible = []
for a in product(range(3), repeat=4):
    if any(a.count(w) > capacity[w] for w in range(3)):
        continue
    value = sum(cost[a[t]][t] for t in range(4))
    feasible.append((value, a))
value, assignment = min(feasible)
lower_bound = sum(min(cost[w][t] for w in range(3)) for t in range(4))
assert value == lower_bound == 11
print("feasible =", len(feasible), "of 81")
print("best =", assignment, "cost =", value, "lower bound =", lower_bound)
```

```text
feasible = 54 of 81
best = (0, 1, 2, 1) cost = 11 lower bound = 11
```

この出力は全列挙を実行して確認しました。容量違反は残り27通りです。

### 同じ問題をCP-SATで書く

次はOR-Toolsが導入されている環境向けのコードです。今回の検証環境ではOR-Toolsを実行していないため、ソルバーの実測ログや終了状態を添えてはいません。上のoracleの11と照合してください。変数・求解・状態確認のAPIは[公式CP-SAT例](https://developers.google.com/optimization/cp/cp_solver)に従います。

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
solver.parameters.num_search_workers = 1
status = solver.solve(model)

print("status =", solver.status_name(status))
if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
    picked = tuple(
        next(w for w in workers if solver.value(assignment[w, t]))
        for t in tasks
    )
    # 元のデータへ戻して可行性と費用を検査する
    assert all(picked.count(w) <= capacity[w] for w in workers)
    actual_cost = sum(cost[picked[t]][t] for t in tasks)
    assert abs(actual_cost - solver.objective_value) < 1e-6
    print("assignment =", picked)
    print("objective =", solver.objective_value)
    print("best bound =", solver.best_objective_bound)
    if status == cp_model.OPTIMAL:
        assert actual_cost == 11  # この小例のoracleと照合
else:
    print("採用できる解は確認できていません")
```

実行後は、まず状態を確認してから解の値を読みます。

| 状態 | 読み方 |
|---|---|
| `FEASIBLE` | 可行解はあるが、最適性はまだ証明されていない |
| `OPTIMAL` | 最適な可行解。ギャップ許容値を指定した場合はその停止条件も確認する |
| `INFEASIBLE` | このモデルに可行解がないことが証明された |
| `MODEL_INVALID` | モデルの検証に通っていない。現実の問題が矛盾するという意味ではない |
| `UNKNOWN` | 時間などの制限までに可行解や実行不能性の結論が得られていない |

状態は[公式説明](https://developers.google.com/optimization/cp/cp_solver)に定義されています。非ゼロの絶対・相対ギャップを停止条件に設定すると、`OPTIMAL` でもその許容ギャップに達して止まる場合があるため、[公式パラメータ定義](https://github.com/google/or-tools/blob/stable/ortools/sat/sat_parameters.proto)と合わせて、目的値と界を読みます。上のコードはギャップ許容値を変更していません。

## 診断値

最小化なら、停止時の最良可行値を $U$、最良下界を $L$ として $L\le z^*\le U$ です。たとえば費用12の可行解と下界11なら、まだ1の改善余地があります。費用11と下界11なら差は0です。前者でも業務上は採用できる場合がありますが、「最適と証明済み」とは分けて伝えます。

- 状態
- 目的値 / 最良界 / ギャップ
- 矛盾件数
- 分岐数
- 伝播数
- 再始動回数
- 実時間
- 最初の実行可能解までの時間
- 解の数
- 前処理簡約
- 乱数シード / 並列ワーカー数

並列ワーカー数を変えると探索順と再現性が変わる場合があります。

## 失敗・切替の兆候

- 候補集合が巨大で伝播が弱い
- 対称性により同等解を反復
- 罰則の尺度が目的値を歪める
- 係数の整数尺度が過大
- 実行可能解が長時間見つからない
- `UNKNOWN`を`INFEASIBLE`と誤読
- 連続物理現象を粗い整数格子へ無理に離散化

::: warning
CP-SAT、MIP、専用DPは同じ離散問題を異なる表現で解けます。
手法名だけで比較しません。
モデルと制限時間に加え、ハードウェア／乱数の種／並列ワーカー数／ギャップを揃えます。
:::

## 次に読む

強い線形緩和を使うMILPなら[Branch-and-Cut](#/learn/branch-and-cut)、状態再利用が中心なら[動的計画法](#/learn/dynamic-programming)と比較します。

- 問題の形を確認する: [混合整数線形計画](#/formulations/PA023)
