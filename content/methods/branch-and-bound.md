---
content_id: branch-and-bound
kind: method
method_id: M_BRANCH_BOUND
title_ja: Branch-and-Bound（分枝限定法）
title_en: Branch and Bound
summary: 離散問題を部分問題へ分け、暫定解と緩和の界で改善できない枝を除きながら、最適性の証明まで進める厳密な探索法です。
source_ids: [S021, S022, S079]
prerequisites: []
related_ids: [branch-and-cut, cp-sat, dynamic-programming, concept.mixed-integer-linear-program]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: [COMPARE_KNAPSACK_BNB_BUDGET]
aliases: [/learn/branch-and-bound]
visualization_aliases: []
status: published
last_reviewed: 2026-09-30
---

離散問題を部分問題へ分け、暫定解と緩和の界で改善できない枝を除きながら、最適性の証明まで進める厳密な探索法です。

## 30秒でつかむ

分かれ道の多い山道を、宝を探して歩くところを考えます。
分かれ道の入口には、「この先で見つかる宝は、どんなに良くてもこの大きさまで」という看板が立っています。
手元にすでにそれより大きな宝があるなら、その道は歩かずに切り捨てられます。

- **見るもの**: 各部分問題（節点）の緩和の値（界）と、いま持っている最良の実行可能解（暫定解）
- **動かすもの**: 探索木。節点を一つ取り出し、変数を一つ選んで範囲を二つに分ける
- **前進の判断**: 緩和の値が暫定解を超えられない枝は切る。開いている節点がなくなれば、最適性が証明される

切り捨てた枝を「なぜ改善できないか」と説明できることが、この手法が全列挙と違う点です。

## 一手の意味

一手は、開いている節点を一つ取り出して緩和を解く操作です。結果に応じて、その節点を切る・暫定解を更新する・分ける、のいずれかを行います。

各節点は、元の問題に追加の固定条件や上下限を加えた部分問題です。節点では、次を順に判定します。

1. 実行不能か。そうなら、その枝を切る。
2. 緩和の値（界）は暫定解を改善できるか。できないなら、その枝を切る。
3. 緩和の解はもう離散の条件を満たしているか。そうなら、暫定解を更新する。
4. どれでもなければ、満たしていない変数を一つ選び、範囲を二つに分けて子節点を作る。

最小化では、節点の下界が暫定解の値以上なら、その枝は改善できないため切れます。最大化では向きが逆で、上界が暫定解の値以下なら切れます。

探索中の枝と次に調べる節点は、探索木の位置で見分けます。切った枝（枝刈り）は、探索を打ち切った状態として分けて読みます。

![濃紺の探索木のうち左側の探索済み経路が青緑、次に調べる節点が橙の輪、改善不能として打ち切った枝が赤い印で示された模式図](./media/branch-and-bound-pruning.png "探索済みの経路、未探索の節点、枝刈りした枝を分けて読む教育用模式図です。実際の節点選択順、界値、最適性の証明は図だけでは示しません。")

### 全列挙をどこまで省けるか

単純な全列挙は、すべての割り当てを調べます。分枝限定法は、次のような領域をまとめて捨てます。

- 制約に違反して実行不能
- 界が暫定解を改善できない
- 対称性や優越関係（支配関係）で、すでに調べた領域と重複する

調べなかった枝について、「なぜ改善できないか」を界で説明できることが重要です。

### 界とギャップをどう読むか

- **暫定解**: いままでに見つかった最良の実行可能解
- **全体の界**: 未探索の領域を含めた、最適値の理論上の限界
- **ギャップ**: 暫定解と全体の界の差

探索が完了する、またはギャップが許容値に達すれば、定義したモデルについて最適性を主張できます。
時間・節点数・メモリの予算で止まった場合、暫定解は実行可能な候補ですが、最適性は証明されていません。

## 小さな例

[混合整数線形計画](#/learn/concept.mixed-integer-linear-program)の小さな例を、分枝限定法で解きます。

$$
\max\; 5x_1+4x_2 \quad \text{s.t.}\quad 6x_1+4x_2\le 24,\;\; x_1+2x_2\le 6,\;\; x_1,x_2\in\mathbb{Z}_{\ge 0}
$$

各節点では整数条件を外したLP（緩和）を解きます。最大化なので、緩和の値は上界です。
分けるときは、最初に見つかった分数の変数を選び、切り下げの枝を先に調べます。

| 順 | 節点（追加した条件） | 緩和の解 | 上界 | 判定 | 暫定解 | 全体の上界 |
|---:|---|---|---:|---|---:|---:|
| 1 | 根（なし） | $(3,\;1.5)$ | $21$ | $x_2$ が分数。$x_2\le1$ と $x_2\ge2$ に分ける | なし | $21$ |
| 2 | $x_2\le1$ | $(10/3,\;1)$ | $20.67$ | $x_1$ が分数。$x_1\le3$ と $x_1\ge4$ に分ける | なし | $21$ |
| 3 | $x_2\le1,\;x_1\le3$ | $(3,\;1)$ | $19$ | 整数解。暫定解を更新 | $19$ | $21$ |
| 4 | $x_2\le1,\;x_1\ge4$ | $(4,\;0)$ | $20$ | 整数解。暫定解を更新 | $20$ | $21$ |
| 5 | $x_2\ge2$ | $(2,\;2)$ | $18$ | 上界が暫定解 $20$ 以下。枝刈り | $20$ | $20$ |

五つの緩和を解いて、探索が終わりました。

順4で、最適解 $(4,\,0)$ が見つかっています。ただし、この時点の全体の上界は $21$ のままです。
順5の節点がまだ開いていて、その親の値 $21$ までは改善の余地が残っているためです。
順4の時点のギャップは $(21-20)/20=5\%$ です。順5でこの節点を切って、開いている節点がなくなり、全体の上界が $20$ に下がってギャップは0になります。

最適解を見つけることと、最適であると証明することは別の仕事です。
順4のあとで時間切れになったとします。暫定解 $20$ は実は最適解ですが、ギャップが $5\%$ 残るので、最適とは主張できません。

なお、緩和の解を丸めても答えには届きません。根の解 $(3,\,1.5)$ を丸めた $(3,\,1)$ の値は $19$ で、最適値 $20$ に及びません。

## 向く条件・避ける条件

まず確認することは次の三点です。

- 部分問題ごとに、実行可能解または界を計算できるか
- 最小化と最大化で、界の向きを取り違えていないか
- 最適性の証明まで必要か、予算内の実行可能解で足りるか

ここが決まると、界の強さと暫定解を見ながら、探索を続けるか止めるかを判断できます。

| 条件 | 理由 |
|---|---|
| 緩和で強い界が得られる（LP緩和が整数解に近い） | 早い段階で枝刈りでき、探索木が小さく済むため |
| 最適性の証明やギャップの報告が必要 | 全体の界と暫定解から、最適値からの距離を示せるため |
| 整数・0-1変数を含む線形の構造がある | LP緩和を各節点で解けるため |

避ける、または切り替える場面は次のとおりです。

- 界が弱く、ほぼ全列挙になる。定式化を見直すか、カットを足す[branch-and-cut](#/learn/branch-and-cut)へ進みます。
- 論理・順序・資源の条件が中心。[CP-SAT](#/learn/cp-sat)のような制約伝播が合う場合があります。
- 専用の動的計画法・フロー・マッチングで解ける構造がある。[動的計画法](#/learn/dynamic-programming)などの専用法のほうが自然です。
- ノイズのあるブラックボックスを、界なしで分けている。界が得られない問題には向きません。

## Python

小さな例の探索を、SciPyの `linprog` で再現します。深さ優先で、切り下げの枝を先に調べます。

```python
import math

import numpy as np
from scipy.optimize import linprog

c = [-5, -4]  # 最大化 5 x1 + 4 x2 を、最小化 -5 x1 - 4 x2 に直す
a_ub, b_ub = [[6, 4], [1, 2]], [24, 6]

incumbent, best_x = -math.inf, None
stack = [([0, None], [0, None], "根")]  # (x1 の範囲, x2 の範囲, node の名前)
solved = 0
while stack:
    bound1, bound2, name = stack.pop()
    relaxed = linprog(c, A_ub=a_ub, b_ub=b_ub, bounds=[bound1, bound2], method="highs")
    solved += 1
    if relaxed.status != 0:
        print(name, "実行不能: 切る")
        continue
    x, value = relaxed.x.round(6) + 0.0, -relaxed.fun  # 緩和の解と、その値（上界）
    if value <= incumbent + 1e-9:
        print(name, x.round(3), round(value, 3), "上界が incumbent 以下: 切る")
        continue
    fractional = [i for i in range(2) if abs(x[i] - round(x[i])) > 1e-6]
    if not fractional:
        incumbent, best_x = value, x.round()
        print(name, x.round(3), round(value, 3), "整数解: incumbent を更新")
        continue
    i = fractional[0]  # 最初の分数の変数で分ける
    print(name, x.round(3), round(value, 3), f"x{i + 1} が分数: 分枝")
    down = [bound1[:], bound2[:]]
    up = [bound1[:], bound2[:]]
    down[i][1] = math.floor(x[i])
    up[i][0] = math.ceil(x[i])
    stack.append((*up, f"{name}, x{i + 1}>={up[i][0]}"))
    stack.append((*down, f"{name}, x{i + 1}<={down[i][1]}"))

print("解いた緩和の数", solved, " 最適解", best_x, " 最適値", incumbent)
```

```text
根 [3.  1.5] 21.0 x2 が分数: 分枝
根, x2<=1 [3.333 1.   ] 20.667 x1 が分数: 分枝
根, x2<=1, x1<=3 [3. 1.] 19.0 整数解: incumbent を更新
根, x2<=1, x1>=4 [4. 0.] 20.0 整数解: incumbent を更新
根, x2>=2 [2. 2.] 18.0 上界が incumbent 以下: 切る
解いた緩和の数 5  最適解 [4. 0.]  最適値 20.0
```

出力の各行が、小さな例の表の各行に対応します。実際のMILPソルバーは、この骨組みに前処理・カット・ヒューリスティクスを組み合わせています。

### 0-1 ナップサックの教育用探索

次のコードは、探索木の教材と同じ4品目の0-1 ナップサックです。分数を許すナップサックの値を上界として使っています。

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    value: int
    weight: int


def solve_knapsack(items: list[Item], capacity: int) -> tuple[int, list[int]]:
    ordered = sorted(items, key=lambda item: item.value / item.weight, reverse=True)
    best_value = 0
    best_choice: list[int] = []

    def fractional_bound(index: int, weight: int, value: int) -> float:
        remaining = capacity - weight
        bound = float(value)
        for item in ordered[index:]:
            if item.weight <= remaining:
                remaining -= item.weight
                bound += item.value
            else:
                bound += item.value * remaining / item.weight
                break
        return bound

    def search(index: int, weight: int, value: int, choice: list[int]) -> None:
        nonlocal best_value, best_choice
        if weight > capacity:
            return
        if value > best_value:
            best_value = value
            best_choice = choice.copy()
        if index == len(ordered):
            return
        if fractional_bound(index, weight, value) <= best_value:
            return

        item = ordered[index]
        search(index + 1, weight + item.weight, value + item.value, [*choice, 1])
        search(index + 1, weight, value, [*choice, 0])

    search(0, 0, 0, [])
    return best_value, best_choice


items = [Item(8, 4), Item(5, 3), Item(6, 5), Item(4, 2)]
print(solve_knapsack(items, capacity=8))
```

```text
(13, [1, 0, 1])
```

選択は価値/重さの大きい順（品目 A・D・B・C）に並べた先頭からの判断で、`[1, 0, 1]` は「AとBを選び、Dは選ばない」を表します。残りは選びません。
一般のMILPでは、LP緩和・カット・前処理・ヒューリスティクスなどをソルバーが組み合わせます。

## 診断値

- 暫定解、全体の界、相対ギャップと絶対ギャップ
- 探索した節点数と、開いている節点数
- 根の緩和のギャップ
- 最初の実行可能解が見つかるまでの時間
- 枝刈りの理由別の節点数
- 探索木の深さ
- メモリ
- 停止した理由（termination reason）
- 実行可能性と整数性の許容誤差

判断の目安は次のとおりです。
ギャップが許容値以下になったら、最適性を主張して止められます。
開いている節点が増え続けるのにギャップが縮まなければ、界が弱いか対称性が大きいと疑い、定式化を見直します。

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処 |
|---|---|---|
| 界が弱く、ほぼ全列挙になる | 緩和が緩い。Big-Mや尺度が大きい | 定式化を締める。[branch-and-cut](#/learn/branch-and-cut)でカットを足す |
| 暫定解が長時間見つからない | 実行可能解を作る手がかりが弱い | 初期解を与える（ウォームスタート）。ヒューリスティクスを使う |
| 同等の節点を反復して探索する | 対称性 | 順序を付ける制約で対称性を崩す |
| 探索木がメモリを圧迫する | 幅優先に近い順序、節点の増えすぎ | 深さ優先寄りの順序を試す。定式化を見直す |
| ノイズのあるブラックボックスを、界なしで分けている | 界が得られない問題 | 分枝限定法をやめ、ブラックボックス向けの手法へ移る |
| 専用の動的計画法・フロー・マッチングで解ける構造がある | 構造の見落とし | [動的計画法](#/learn/dynamic-programming)や[Dijkstra / A*](#/learn/dijkstra-astar)などの専用法へ戻る |

::: warning
探索木が小さい一例だけでソルバー一般の性能を評価しません。
問題例・定式化・前処理・カット・ヒューリスティクス・計算機環境・時間制限を揃えます。
:::

## コラム: 探索の順序

節点を取り出す順序で、探索の性格が変わります。

- **best-bound**: 全体の界が高い（最小化なら低い）節点から進む。証明側を進めやすい。
- **深さ優先**: 深い節点から進む。メモリを抑え、暫定解を早く得られる場合がある。
- **幅優先**: 層ごとに探索する。メモリが増えやすい。
- **hybrid**: 探索の段階に応じて順序を切り替える。

分ける変数の選び方・節点の選び方・ヒューリスティクスは、性能に強く影響します。定式化の強さも同じくらい重要です。
小さな例の表は深さ優先の一例で、順序を変えると解く緩和の数も変わり得ます。

## コラム: 探索完了と予算停止を分けて見る

[証明完了の探索木](#/theater/search-tree/binary-knapsack-bnb-complete)では、暫定解と全体の界が一致するまでを追います。
[4節点で止まる探索木](#/theater/search-tree/binary-knapsack-bnb-budget)では、実行可能な暫定解があっても、正のギャップと未探索の節点が残る状態を確認します。

[二つの停止結果を並べる比較](#/compare/COMPARE_KNAPSACK_BNB_BUDGET)は、同じ4変数ナップサックを使います。
問題例・乱数シード・分岐の順・初期の暫定解・分数ナップサックの界を固定します。
9回の評価上限も共通にし、節点の停止上限だけを9から4へ変えます。

これは停止条件の読み方を学ぶ固定教材です。
CP-SATやMIPのソルバーの速度、総当たりとの一般性能順位付けを示すものではありません。

## 次に読む

- [混合整数線形計画](#/learn/concept.mixed-integer-linear-program)：小さな例の問題を定式化から読み直す
- [Branch-and-Cut](#/learn/branch-and-cut)：カットで緩和を締め、探索木を小さくする枠組み
- [双対単体法](#/learn/dual-simplex)：各節点のLPを親の基底から再最適化する仕組み
- [ナップサック・集合被覆](#/formulations/PA032)：探索木の教材で使った、制約1本の整数計画
