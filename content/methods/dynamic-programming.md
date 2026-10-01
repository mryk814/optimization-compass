---
content_id: dynamic-programming
kind: method
method_id: M_DYNAMIC_PROGRAMMING
title_ja: 動的計画法
title_en: Dynamic Programming
summary: 問題を状態（state）と段階（stage）に分け、同じ部分問題を再利用してBellman再帰を解く、離散問題向けの厳密法です。
source_ids: [S054]
prerequisites: []
related_ids: [dijkstra-astar, cp-sat, branch-and-bound]
aliases: [/learn/dynamic-programming]
status: published
last_reviewed: 2026-09-30
---

問題を状態（state）と段階（stage）に分け、同じ部分問題を再利用してBellman再帰を解く、離散問題向けの厳密法です。

## 30秒でつかむ

登山用のリュックに、荷物を一つずつ詰めるところを考えます。
次の荷物を入れるかどうかを決めるとき、必要なのは「残りの容量がいくつか」だけです。
それまでにどの荷物をどの順に入れたかは、これからの判断に関係しません。

このように、履歴を「状態」へ縮められるとき、同じ状態への到達は一つの部分問題として使い回せます。
小さな部分問題の答えを表に書き込み、それを足場にして大きな問題を解く方法が、動的計画法（dynamic programming, DP）です。

- **見るもの**: 状態。何段階まで決め終えたか、資源があとどれだけ残っているか
- **動かすもの**: 表（table）。小さい部分問題から順に、各セルの最良値を埋める
- **前進の判断**: すべてのセルが埋まれば終わる。最後のセルが元の問題の最適値になる

選択そのものは表に残りません。最後のセルから表を逆にたどって、選んだ品目を復元します。

## 一手の意味

一手は、一つのセルの値を、すでに埋まった小さな部分問題の値から一行の式で決める操作です。

DPでは、意思決定の履歴をすべて保持しません。将来の評価に必要な情報だけを`state`へまとめます。
Bellman再帰は、現在の`state`から選べる`action`と、その後の最適値を組み合わせます。

$$
V_t(s)=\min_a\left\{c_t(s,a)+V_{t+1}(T(s,a))\right\}
$$

- $s$: 現在の`state`
- $a$: 選べる`action`
- $T(s,a)$: 次の`state`
- $V_t(s)$: その`state`以降の最適値

重要なのは、`state`が将来を正しく評価できる十分な情報を持つことです。
同じ`state`へ到達した履歴を一つの部分問題として再利用します。

0-1 knapsackは、品目ごとに入れるか入れないかを選び、価値の合計を最大にする問題です。この問題の`state`は、「何品目まで見たか $i$」と「使える容量 $a$」の組です。
セルの値 $T[i][a]$ は、最初の $i$ 品目だけで、容量 $a$ に収まる価値の最大です。

$$
T[i][a]=\max\bigl(T[i-1][a],\;T[i-1][a-w_i]+v_i\bigr)\qquad (w_i\le a)
$$

第1項は「品目 $i$ を入れない」場合で、一つ前の行の同じ容量の値です。第2項は「入れる」場合で、重さ $w_i$ を除いた容量の値に価値 $v_i$ を足します。
$w_i>a$ で入らないときは、第1項だけを使います。大きいほうを、そのセルの値にします。

## 小さな例

容量8のリュックに、次の4品目から選びます。[knapsack・set cover](#/formulations/PA032)の小さな例です。

| 品目 | A | B | C | D |
|---|---:|---:|---:|---:|
| 重さ $w$ | 4 | 3 | 5 | 2 |
| 価値 $v$ | 8 | 5 | 6 | 4 |

表の行は「見終えた品目」、列は「使える容量」です。0行目は、品目が一つもないので、すべて0です。

| 見終えた品目 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| なし | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| A | 0 | 0 | 0 | 0 | 8 | 8 | 8 | 8 | 8 |
| A, B | 0 | 0 | 0 | 5 | 8 | 8 | 8 | 13 | 13 |
| A, B, C | 0 | 0 | 0 | 5 | 8 | 8 | 8 | 13 | 13 |
| A, B, C, D | 0 | 0 | 4 | 5 | 8 | 9 | 12 | 13 | 13 |

一部のセルを、式に当てはめて確かめます。

- 行「A」、容量4: 入れない場合は $0$、入れる場合は $T[0][0]+8=8$。大きいほうの $8$。
- 行「A, B」、容量7: 入れない場合は $8$。入れる場合は、容量 $7-3=4$ の一つ前の行の値 $8$ に価値 $5$ を足して $13$。大きいほうの $13$。
- 行「A, B, C」、容量8: 入れない場合は $13$。入れる場合は、容量 $8-5=3$ の値 $5$ に価値 $6$ を足して $11$。$13$ のまま。

品目Cを加えても、どのセルも増えていません。この4品目と容量の範囲では、Cを入れても価値が増えないと読み取れます。
最後の行の右端が、元の問題の答えです。容量8で最大の価値は $13$ です。

### 表を逆にたどる

最終セルの $13$ から、選択を復元します。

1. 行「A, B, C, D」、容量8。$13$ は一つ前の行の $13$ と同じなので、Dは入れない。
2. 行「A, B, C」、容量8。これも一つ前と同じ $13$ なので、Cは入れない。
3. 行「A, B」、容量8。一つ前の行の $8$ より大きい $13$ なので、Bを入れる。容量は $8-3=5$ に減る。
4. 行「A」、容量5。$8$ で、一つ前の行の $0$ より大きいので、Aを入れる。容量は $5-4=1$ に減る。

選んだのはAとBで、合計の重さは $7$、価値は $13$ です。使い残した容量は1です。

![capacity 8の固定0/1 knapsackを4 itemで解いたDP table。itemを考慮する段階を行、capacity 0から8を列として最大valueを記録する。最終cellのvalue 13から青緑の線をbacktrackingすると、item AとBを選び、合計weight 7、unused capacity 1になる。](./media/dynamic-programming-knapsack-execution.svg "固定4 itemの整数knapsackをpure Pythonで実行した結果です。DP tableは厳密に13を返しますが、別instance、連続量、近似、solver一般の性能や大規模state spaceでの実用性は示しません。")

橙が大きいvalueを持つcell、青緑が最終cellから選択を復元するbacktrackingです。
item CとDを追加してもcapacity 8の最良valueは13から増えません。
backtrackingではAとBを選び、weightを`8 → 5 → 1`と戻します。

> 最大valueは13、選択はAとB、合計weightは7です。
> tableを埋める処理と、選択したitemを復元する処理は分けています。
> 固定4 itemの教材であり、DP一般の性能rankingではありません。

## 向く条件・避ける条件

`state`を小さく定義でき、部分問題が重なる問題に向きます。

- knapsack
- 最短路（shortest path）
- 系列の整列（sequence alignment）
- ロットサイズ決定（lot sizing）
- 有限ホライズンの制御（finite-horizon control）
- 資源配分（resource allocation）
- `state`空間が小さいスケジューリング

汎用MIPへ書ける問題でも、`state`と遷移（transition）が小さければ、DPを直接使える場合があります。
厳密な保証と、表の各値を対応づけて説明しやすい点も特徴です。

避ける、または切り替える場面は次のとおりです。

- `state`に履歴を詰め込むほど表が指数的に増える。状態の圧縮や別の定式化を考えます。
- 論理制約が増えて、`state`で表せなくなる。[CP-SAT](#/learn/cp-sat)や混合整数計画へ移ります。
- 最短路へ特殊化できる。[Dijkstra / A*](#/learn/dijkstra-astar)のほうが直接的です。
- 界で枝を刈るほうが向く探索。[Branch-and-Bound](#/learn/branch-and-bound)を比べます。

## Python

小さな例の表を、そのまま作ります。2次元の表を残すので、図の全セルと逆たどりを同じ実行から再現できます。

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    name: str
    weight: int
    value: int


def knapsack(
    items: list[Item],
    capacity: int,
) -> tuple[int, list[str], list[list[int]]]:
    table = [[0] * (capacity + 1) for _ in range(len(items) + 1)]
    take = [[False] * (capacity + 1) for _ in range(len(items) + 1)]

    for item_count, item in enumerate(items, start=1):
        for available in range(capacity + 1):
            skip_value = table[item_count - 1][available]
            take_value = (
                table[item_count - 1][available - item.weight] + item.value
                if item.weight <= available
                else -1
            )
            if take_value > skip_value:
                table[item_count][available] = take_value
                take[item_count][available] = True
            else:
                table[item_count][available] = skip_value

    selected = []
    remaining = capacity
    for item_count in range(len(items), 0, -1):
        if take[item_count][remaining]:
            item = items[item_count - 1]
            selected.append(item.name)
            remaining -= item.weight
    selected.reverse()
    return table[-1][-1], selected, table


items = [
    Item("A", weight=4, value=8),
    Item("B", weight=3, value=5),
    Item("C", weight=5, value=6),
    Item("D", weight=2, value=4),
]
value, selected, table = knapsack(items, capacity=8)
weight = sum(item.weight for item in items if item.name in selected)
print(f"selected={selected}, weight={weight}, value={value}")
for item_count, row in enumerate(table):
    print(f"{item_count} items: {row}")
```

```text
selected=['A', 'B'], weight=7, value=13
0 items: [0, 0, 0, 0, 0, 0, 0, 0, 0]
1 items: [0, 0, 0, 0, 8, 8, 8, 8, 8]
2 items: [0, 0, 0, 5, 8, 8, 8, 13, 13]
3 items: [0, 0, 0, 5, 8, 8, 8, 13, 13]
4 items: [0, 0, 4, 5, 8, 9, 12, 13, 13]
```

出力の各行が、小さな例の表の各行に対応します。
memoryを減らすだけなら、1次元のrolling arrayへ置き換えられます。ただし、選択の復元には追加の情報が必要です。

## 診断値

- `state`の数
- `action`の数
- 遷移の数
- horizon（段階の数）
- memory
- 価値の範囲による擬多項式（pseudo-polynomial）性

DPが厳密でも、常に速いとは限りません。
knapsackの $O(nC)$ は、容量 $C$ の数値に依存します。入力のbit長に対する純粋な多項式時間とは限りません。

判断の目安は、`state`の数と表のmemoryを、実行する前に見積もることです。
`state`数が使えるmemoryに収まらないなら、状態の圧縮か別の手法を先に考えます。

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処 |
|---|---|---|
| 表が指数的に大きくなる | `state`に多くの履歴を入れている | dominanceによる`state`の刈り込み、疎な辞書（sparse dictionary）、rolling array |
| memoryが足りない | `state`空間そのものが大きい | 近似・離散化、問題の分解（decomposition） |
| 容量の数値を大きくすると急に遅くなる | 擬多項式の計算量 | 値の範囲を粗く取る近似を検討する |
| 論理制約が増えて`state`で表せない | 履歴に依存する条件 | [CP-SAT](#/learn/cp-sat)や混合整数計画へ切り替える |
| 最短路に帰着できる | 構造を見落としている | A*やlabel-settingなど、[Dijkstra / A*](#/learn/dijkstra-astar)へ |

::: warning
`state`を小さくするために必要な情報を落とすと、異なる履歴を誤って同一の`state`として扱います。
Markov性、または最適部分構造が成り立つかを確認します。
:::

## コラム: 結果の保証

全`state`と遷移を正しく評価して再帰を完了すれば、定義した離散モデルに対する厳密解を得られます。
ただし、連続量の離散化の誤差やモデルの単純化は別の問題です。

## 次に読む

- [knapsack・set cover](#/formulations/PA032)：小さな例の問題を定式化から読み直す
- [Dijkstra / A*](#/learn/dijkstra-astar)：最短路へ特殊化した専用法
- [Branch and Bound](#/learn/branch-and-bound)：界で探索を刈り込む別の厳密法
- [CP-SAT](#/learn/cp-sat)：一般の論理制約が増えたときの道具
