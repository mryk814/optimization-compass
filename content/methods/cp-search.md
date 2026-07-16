---
content_id: cp-search
kind: method
method_id: M_CP_SEARCH
title_ja: 制約プログラミング探索
title_en: Constraint Programming Search
summary: global constraint propagationとbranchingで有限domainを探索します。
source_ids: [S022, S053]
prerequisites: []
related_ids: [cp-sat, cdcl-sat, family.constraint-programming]
aliases: [/learn/cp-search]
status: published
last_reviewed: 2026-07-16
---

global constraint propagationとbranchingで有限domainを探索します。

## domainをどう削っているか

制約プログラミング探索では、各変数が取り得る値の集合（domain）を明示的に持ちます。各制約は「この制約を満たせない値をdomainから消してよいか」を判定するpropagatorとして働き、矛盾なく消せる値を繰り返し取り除きます。domainがすべて単一値になれば解、どこかのdomainが空になれば矛盾です。全変数のdomainを縮められなくなった時点で、1つの変数を選んで値を仮決定し（branching）、再びpropagationへ戻ります。

## global constraintの宣言力

alldifferent（全変数が異なる値を取る）やcumulative（資源使用量が容量を超えない）のようなglobal constraintは、同じ条件を等号・不等号の組み合わせへ分解するより強い伝播を行えます。alldifferentは、単なるペアごとの不等号制約の集合として書くよりも、ある値を1つの変数が確定した時点で他の変数のdomainから即座にその値を除去でき、矛盾をより早く検出します。global constraintの選び方は、モデルの読みやすさだけでなく、伝播の強さそのものを左右します。

## 伝播の強さと分岐戦略の関係

伝播が強いほどdomainは早く縮みますが、伝播だけで解に至らない問題も多く、分岐戦略（どの変数を先に決めるか、どの値から試すか）が探索木の大きさを左右します。伝播が弱い制約表現では分岐の負担が増え、逆に高コストな強い伝播を使うと1 nodeあたりの計算が重くなります。目的関数がある場合は、見つかった解の目的値より良い値を要求する新しいbound制約を都度追加し、伝播と探索を反復して最適解へ絞り込みます。モデリング言語（[MiniZinc](https://docs.minizinc.dev/en/stable/)など）はモデルの記述とsolverの探索戦略を分離しており、同じモデルを異なるsolver backendで実行できます。

## 向いている条件

- 変数が有限domainの整数・Boolean
- alldifferent、cumulative、no-overlapなどglobal constraintで問題が自然に書ける
- scheduling・割当・pathのようなfeasibility中心の問題
- 目的関数があっても、bound制約の反復で最適化を扱える規模

本質的に連続で滑らかな問題や、実数精度を整数scaleで表せない問題では、このアプローチを第一候補にしません。

## Python

```python
from __future__ import annotations

Domains = dict[str, list[int]]


def forward_check(domains: Domains, var: str, value: int) -> Domains | None:
    reduced = {name: list(values) for name, values in domains.items()}
    reduced[var] = [value]
    for other in reduced:
        if other == var:
            continue
        reduced[other] = [v for v in reduced[other] if v != value]
        if not reduced[other]:
            return None
    return reduced


def backtrack(domains: Domains, order: list[str]) -> dict[str, int] | None:
    if not order:
        return {name: values[0] for name, values in domains.items()}
    var, rest = order[0], order[1:]
    for value in domains[var]:
        reduced = forward_check(domains, var, value)
        if reduced is not None:
            result = backtrack(reduced, rest)
            if result is not None:
                return result
    return None


variables = ["a", "b", "c", "d"]
domains: Domains = {name: [0, 1, 2, 3] for name in variables}
solution = backtrack(domains, variables)
print(solution)
```

`forward_check`は、1つの変数へ値を仮決定するたびに他の変数のdomainからその値を除くalldifferentの簡易版propagationです。空になったdomainがあれば即座に打ち切ります。実務のglobal constraint propagatorやbranching戦略は、利用するsolver（[OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)や[MiniZinc](https://docs.minizinc.dev/en/stable/)経由のbackend）の公式referenceで、利用versionの説明を確認します。

## 診断値

- conflicts
- branches
- propagations
- best_bound（最適化時）
- feasible_solutions

## 失敗・切替の兆候

- conflict数やbranch数が増え続けて収束しない
- propagationを重ねてもdomainがほとんど縮まらない
- 整数scaleが過大で、変数のdomainが不必要に大きい
- symmetryにより等価な部分木を繰り返し探索する
- 一部制約だけ強い伝播を持つglobal constraintへ書き換えられていない

CDCLの学習節と非時系列バックトラックとの違いは[CDCL SAT](#/learn/cdcl-sat)、propagationと探索を統合した実装は[CP-SAT](#/learn/cp-sat)、制約プログラミング・SAT全体の選び分けは[制約プログラミング・SATの選び分け](#/learn/family.constraint-programming)で確認できます。
