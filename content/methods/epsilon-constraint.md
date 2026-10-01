---
content_id: epsilon-constraint
kind: method
method_id: M_EPSILON_CONSTRAINT
title_ja: ε-constraint法
title_en: Epsilon-Constraint Method
summary: 一つの目的を最適化し、ほかの目的を許容上限・下限の制約へ移して、その閾値を変えながらPareto候補を集める方法です。
source_ids: [S039, S055]
related_ids: [multi-objective]
status: published
last_reviewed: 2026-09-30
---

一つの目的を最適化し、ほかの目的を許容上限・下限の制約へ移して、その閾値を変えながらPareto候補を集める方法です。

## 30秒でつかむ

車を選ぶとき、価格を最小にしつつ燃費には下限を置く場面を考えます。ε-constraint法は、目的の一つを許容条件に移して選びます。

この手法の気持ちは、複数目的を根拠のない一つの得点へ足し合わせず、最も重視する目的を一つ選ぶことです。
残りの目的は「ここまでは許す」という条件へ移します。

- 見るもの: 主目的、他目的の値、可行性、Pareto支配
- 動かすもの: ε 閾値と各単目的部分問題の解
- 前進の判断: 異なる交換関係領域で実行可能解を得られたか

重み付き和で取りにくい非凸Paretoフロントの領域も候補にできます。
一方で、閾値ごとに部分問題を解く予算が必要です。

## 一手の意味

### 仕組み

二目的最小化を例に、$f_1$を主目的、$f_2$を制約へ移します。

$$
\min_x f_1(x)\quad \text{subject to}\quad f_2(x)\leq \epsilon,\; x\in X
$$

$\epsilon$を変えて複数回解き、得られた実行可能解から非支配解を残します。
目的数が増えると閾値の組も増えるため、意思決定上重要な領域へ絞る必要があります。

## 小さな例

需要18以上の生産計画を、Python節の整数列挙で解きます。
技術Xは生産量3・費用8・排出6、技術Yは生産量2・費用7・排出2です。
排出上限を変える最初の3回は、次の結果になります。

| 排出上限 $\epsilon$ | X | Y | 費用 | 排出 |
|---|---:|---:|---:|---:|
| 36 | 6 | 0 | 48 | 36 |
| 30 | 4 | 3 | 53 | 30 |
| 24 | 2 | 6 | 58 | 24 |

上限を厳しくすると費用が増え、低排出の技術Yへ置き換わります。
同じ問題の反復ではなく、閾値を変えた3回の求解です。

## 向く条件・避ける条件

### まず確認すること

| 項目 | 確認内容 |
|---|---|
| 目的の方向 | 各目的が最小化か最大化か |
| 主目的 | 一時的に主目的として選べるか |
| 範囲 | 各目的の現実的な範囲を把握できるか |
| 内部の解法 | εを制約にした単目的問題を解けるか |
| 可行性 | 閾値ごとの実行不能性を区別できるか |
| 予算 | 閾値の個数と部分問題ごとの評価コストを許容できるか |
| 意思決定での使用 | 最終的に誰が交換関係から選ぶか |

目的値を正規化せずに閾値幅を決めると、単位の大きな目的だけを細かく調べる場合があります。

向きやすい条件:

- 目的の一つを主目的として説明しやすい
- `backend solver`が制約付き部分問題を安定に解ける
- 非凸フロントも含め特定交換関係領域を調べたい
- 許容値に実務的意味がある

避ける条件:

- 閾値範囲が不明
- 多数目的で格子が爆発する
- 部分問題一回が極端に高価
- 実際には単一効用が明確で複数解不要

## Python

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    x_count: int
    y_count: int
    output: int
    cost: int
    emissions: int


def enumerate_plans(demand: int = 18) -> list[Plan]:
    plans = []
    for x_count in range(11):
        for y_count in range(11):
            output = 3 * x_count + 2 * y_count
            if output < demand:
                continue
            plans.append(
                Plan(
                    x_count=x_count,
                    y_count=y_count,
                    output=output,
                    cost=8 * x_count + 7 * y_count,
                    emissions=6 * x_count + 2 * y_count,
                )
            )
    return plans


def solve_for_epsilon(
    plans: list[Plan],
    epsilon: int,
) -> Plan | None:
    eligible = [plan for plan in plans if plan.emissions <= epsilon]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda plan: (plan.cost, plan.emissions, plan.x_count, plan.y_count),
    )


plans = enumerate_plans()
for epsilon in (36, 30, 24, 18, 12):
    solution = solve_for_epsilon(plans, epsilon)
    if solution is None:
        print(f"epsilon={epsilon}: infeasible")
        continue
    print(
        f"epsilon={epsilon}: X={solution.x_count}, Y={solution.y_count}, "
        f"cost={solution.cost}, emissions={solution.emissions}"
    )
```

```text
epsilon=36: X=6, Y=0, cost=48, emissions=36
epsilon=30: X=4, Y=3, cost=53, emissions=30
epsilon=24: X=2, Y=6, cost=58, emissions=24
epsilon=18: X=0, Y=9, cost=63, emissions=18
epsilon=12: infeasible
```

このコードは`backend solver`の代わりに全整数計画を列挙します。
比較では`backend`と初期点を固定します。
`tolerance`、閾値の組、部分問題数も揃えます。
Pareto候補数だけでなく、同じ総評価予算で覆えた領域も記録します。

## 診断値

見る値:

- 閾値ごとの可行性
- 得られた非支配解数
- 目的空間の被覆範囲
- 重複解率
- 内部ソルバー 終了状態 / ギャップ
- 意思決定者が関心を持つ領域の密度
- 閾値ごとの`evaluation cost`と総予算

- 別に確認するもの: 閾値の組、部分問題数、総評価予算
- 恐れていること: 閾値の選び方、目的尺度、実行不能部分問題、重複解

## 失敗・切替の兆候

### うまくいったサインと切替サイン

切替サイン:

- 多数の閾値が実行不能 → 目的範囲を再推定
- 同じ解ばかり出る → 閾値の間隔または`backend tolerance`を見直す
- 目的数が多く格子が重い → NSGA-IIIやMOEA/Dを検討
- 選好が明確になった → 関心領域だけへ閾値を集中
- 内部の解法が局所解のみ → Pareto集合も局所候補であることを明示

### 上限を下げると選択が移る

次の固定生産計画では、需要18以上を満たす技術XとYの組合せを整数列挙します。
主目的は`cost`、制約へ移す目的は`emissions`です。

![需要18以上を満たす技術XとYの整数生産計画を88個列挙したε-制約実行。上段の目的空間では橙が可行計画、青緑が4つのPareto 計画を示す。排出量上限を36、30、24、18と下げるたび、コスト最小の選択はXとYの組合せを変えながらParetoフロント上を移る。上限12では実行可能計画がない。](./media/epsilon-constraint-production-execution.svg "固定した2技術・需要18の整数列挙です。4つのthresholdはPareto planを一つずつ選び、ε=12はinfeasibleになります。別需要、連続変数、backend solver、threshold設計、ε-constraint一般の性能は示しません。")

上限36では低コストな`(X, Y) = (6, 0)`を選びます。
上限を18まで下げると、より低排出量な`(0, 9)`へ移ります。
上限12は実行可能領域より厳しいため、部分問題は実行不能です。

> 88 可行計画のうち、非支配計画は4個です。
> 4個の実行可能閾値は、それぞれ異なるPareto 計画を選びます。
> これは固定整数列挙であり、一般性能順位ではありません。

### コラム: εは重みではない

重み付き和の重みは目的間の交換率を表します。
`ε-constraint`の閾値は、ある目的に対する許容限界です。
意味が異なるため、同じ数字を対応させても同じ解になるとは限りません。

## 次に読む

- 支配とフロント全体を読む: [多目的最適化とParetoフロント](#/learn/multi-objective)
- 目的を重みでまとめる: [重み付き和単目的化](#/learn/weighted-sum)
- 多数目的へ進む: [NSGA-III](#/learn/nsga-iii)

- [この手法を使う問題の定式化](#/formulations/PA038)：決定変数と目的を確認します。
