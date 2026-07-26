---
content_id: cp-search
kind: method
method_id: M_CP_SEARCH
title_ja: 制約プログラミング探索
title_en: Constraint Programming Search
summary: 有限domainの変数からpropagationで候補を削り、branchingで残った探索を分ける制約プログラミングの探索法です。
source_ids: [S022, S053]
prerequisites: []
related_ids: [cp-sat, cdcl-sat, family.constraint-programming]
aliases: [/learn/cp-search]
status: published
last_reviewed: 2026-07-26
---

有限domainの変数からpropagationで候補を削り、branchingで残った探索を分ける制約プログラミングの探索法です。

## 30秒でつかむ

各変数は、取り得る値の集合（domain）を持ちます。
一つの値を仮決定したら、制約を満たせない値をほかのdomainから消します。

- 見ているもの: 各変数のdomainとconstraint violation
- 動かすもの: domainの縮小と探索木のbranch
- 前進の判断: domainが縮み、単一値へ近づいているか
- 矛盾の判断: どれか一つでもdomainが空になったか
- 恐れていること: 弱いpropagationで巨大な探索木を残すこと

先に値を消し、消し切れなかった部分だけを探す手法です。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| variables | Boolean・整数・有限集合で表せるか |
| constraints | alldifferent、cumulative、no-overlapなどで自然に書けるか |
| propagation | 仮決定から除外できる値があるか |
| search | どの変数・値からbranchするか |
| objective | feasibilityだけか、boundを更新する最適化か |
| scale | 連続量の整数化で必要な精度を保てるか |

本質的に連続で滑らかな問題を、粗い整数gridへ無理に移しません。

## domainを削ってからbranchする

propagatorは、現在の仮決定と制約から不可能な値を取り除きます。
すべてのdomainが単一値になれば解です。
一つでも空になれば、そのbranchには解がないため直前の分岐へ戻ります。

propagationだけで決まらない場合は、domainの小さい変数などを選んでbranchします。
仮決定のたびに、再びpropagationを実行します。

## 空domainを見つけたら戻る

次の固定実行は、4×4盤の各行へqueenを一つ置く4-Queensです。
domainの数字は列番号0–3を表し、同じ列と斜めにqueenを置けない制約を使います。

![4-Queensをforward checkingで解く制約プログラミング探索。初期状態ではQ1からQ4が列0から3を候補に持つ。Q1を列0へ置くと攻撃される6値がdomainから消える。その枝を進むとQ4のdomainが空になり、探索はbacktrackする。Q1を列1へ置く枝では全domainが単一値になり、列1、3、0、2の解へ到達する。下段の探索木はQ1が列0の二つの失敗枝と、Q1が列1の成功枝を分けて示す。](./media/cp-search-propagation-execution.svg "固定4-Queensをforward checkingと最小domain優先で解いた実行です。global constraint、学習節、restartを備える実solverの内部や一般性能は示しません。")

`Q1 = 0`は一見置ける候補です。
しかし先へ進むと`Q3 = ∅`または`Q4 = ∅`になり、その場で枝を捨てられます。

> 最終解だけでは、探索しなかった組合せが見えません。
> domainの縮小と空集合を残すと、propagationが探索を減らした場所を説明できます。

## 大域制約（global constraint）の強さ

`alldifferent`や`cumulative`のような`global constraint`は、条件全体を一つの構造として伝播します。
同じ条件を小さな制約へ分解すると、論理的には同値でも早期に消せる値が減る場合があります。

強いpropagationは探索木を小さくできますが、1 nodeあたりの処理は重くなります。
したがってbranch数だけでなく、propagation数と`wall time`も見ます。

## 向く条件・避ける条件

向きやすい条件:

- 変数がBoolean・整数・有限集合
- scheduling、割当、配置などfeasibilityが難しい
- `global constraint`で問題構造を直接表せる
- 矛盾を早い段階で検出したい

避ける条件:

- 本質的に連続で滑らかな問題
- 整数化で必要な精度を失う問題
- domainが巨大でpropagationがほとんど効かない問題
- 問題構造に合う専用graph algorithmや動的計画法がある場合

## Python

```python
from __future__ import annotations

size = 4
stats = {"nodes": 0, "pruned": 0, "conflicts": 0, "backtracks": 0}


def search(domains, assigned):
    if len(assigned) == size:
        return assigned

    row = min(
        (candidate for candidate in range(size) if candidate not in assigned),
        key=lambda candidate: (len(domains[candidate]), candidate),
    )
    for column in domains[row]:
        stats["nodes"] += 1
        next_domains = [list(values) for values in domains]
        stats["pruned"] += len(next_domains[row]) - 1
        next_domains[row] = [column]
        next_assigned = {**assigned, row: column}
        conflict = False

        for other_row in range(size):
            if other_row in next_assigned:
                continue
            previous = next_domains[other_row]
            next_domains[other_row] = [
                candidate
                for candidate in previous
                if candidate != column
                and abs(candidate - column) != abs(other_row - row)
            ]
            stats["pruned"] += len(previous) - len(next_domains[other_row])
            conflict |= not next_domains[other_row]

        if conflict:
            stats["conflicts"] += 1
            continue

        solution = search(next_domains, next_assigned)
        if solution is not None:
            return solution

    stats["backtracks"] += 1
    return None


initial_domains = [list(range(size)) for _ in range(size)]
solution = search(initial_domains, {})
columns = [solution[row] for row in range(size)]
print(f"solution columns: {columns}")
print(
    f"nodes={stats['nodes']}, pruned={stats['pruned']}, "
    f"conflicts={stats['conflicts']}, backtracks={stats['backtracks']}"
)
```

```text
solution columns: [1, 3, 0, 2]
nodes=8, pruned=29, conflicts=2, backtracks=2
```

`pruned=29`は、探索した各branchで削除した値の累積です。
一意な値29個を消したという意味ではありません。

このコードはforward checkingの教育用実装です。
[OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)や[MiniZinc](https://docs.minizinc.dev/en/stable/)のsolver内部を再現しません。

## 診断値

- domain sizeの推移
- pruned value数とpropagation数
- conflicts / branches / backtracks
- nodeあたりのpropagation cost
- feasible solution数
- objective / best bound / gap（最適化時）
- random seed、worker数、wall time

## 失敗・切替の兆候

- domainが縮まらない → global constraintやencodingを見直す
- branch数だけ増える → variable / value orderingを見直す
- 同じ形の部分木を反復する → symmetry breakingを加える
- 1 nodeが重すぎる → propagation strengthとのtrade-offを測る
- 整数scaleが過大 → 単位・精度・別familyを見直す
- 線形緩和が強い → MILPのBranch-and-Cutとも比較する

## 次に読む

- propagationとSAT学習を統合する: [CP-SAT](#/learn/cp-sat)
- conflictから学習節を作る: [CDCL SAT](#/learn/cdcl-sat)
- 離散手法全体から選ぶ: [制約プログラミング・SATの選び分け](#/learn/family.constraint-programming)
