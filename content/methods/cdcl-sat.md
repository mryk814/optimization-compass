---
content_id: cdcl-sat
kind: method
method_id: M_CDCL_SAT
title_ja: CDCL SAT
title_en: Conflict-Driven Clause Learning SAT
summary: Boolean制約のconflictからclauseを学習し、SATまたはUNSATの判定を証明まで進める探索法です。
source_ids: [S022, S053]
prerequisites: []
related_ids: [cp-sat, branch-and-bound, family.discrete-structure]
aliases: [/learn/cdcl-sat]
status: published
last_reviewed: 2026-07-18
---

Boolean制約のconflictからclauseを学習し、SATまたはUNSATの判定を証明まで進める探索法です。

## SATの割当と伝播

CDCL SATは、Boolean変数の集合に真偽値を割り当てて、CNF（連言標準形）で書かれた節の集合をすべて満たすかどうかを判定します。単純な全列挙と違い、各stepでunit propagationを行います。ある節でリテラルが1つを除いてすべて偽になっていれば、残る1つのリテラルの値は強制されます。これを繰り返して割当を広げ、決定変数の追加（分岐）が必要になった箇所だけ探索を分けます。

## 衝突から何を学ぶか

propagationの結果、ある節のリテラルがすべて偽になると衝突（conflict）が起きます。CDCLはここで単純に1手戻るのではなく、衝突へ至った決定と含意の関係をresolutionで遡り、衝突の原因を表す新しい節（学習節）を導出します。学習節を元の節集合へ追加すると、同じ原因による衝突を将来skipできます。また、学習節から衝突と無関係な決定levelへ直接戻る非時系列バックトラック（non-chronological backtracking）ができるため、直前の1手だけを戻す探索より無駄な再探索を避けやすくなります。

## SATとUNSATはどちらも証明か

SATと判定された場合、実際に見つかった割当がそのまま「すべての節を満たす」ことの証明になります。UNSATと判定された場合も、学習節の導出を遡ると空節（矛盾）に至るresolution過程が証明になります。この意味で、CDCL SATは可否を確率的に推定するのではなく、可否そのものを証明する手法です。目的関数を直接最小化する手法ではないため、最適化に使う場合はSATを繰り返し呼び出して解を改良する制約を追加していくか、重み付き節を扱うMaxSATのような拡張へ切り替えます。

## 向いている条件

- 変数がBoolean、またはBoolean encodingへ落とせる有限domain
- 論理制約（含意、排他、含意連鎖）が中心
- 可行性の有無自体が知りたい、またはUNSATの証明が必要
- 最適化よりも充足可能性判定が主目的

本質的に連続で滑らかな問題や、実数精度を整数・Boolean scaleへ表せない問題では、CDCL SATを第一候補にしません。最適化そのものが目的なら[CP-SAT](#/learn/cp-sat)のようにCDCLと線形緩和・探索を統合したsolverを検討します。

## Python

```python
from __future__ import annotations

Clause = list[int]
Formula = list[Clause]


def unit_propagate(formula: Formula, assignment: dict[int, bool]) -> bool:
    changed = True
    while changed:
        changed = False
        for clause in formula:
            literals = [
                lit
                for lit in clause
                if assignment.get(abs(lit)) is None or (lit > 0) == assignment[abs(lit)]
            ]
            if not literals:
                return False
            if len(literals) == 1 and abs(literals[0]) not in assignment:
                lit = literals[0]
                assignment[abs(lit)] = lit > 0
                changed = True
    return True


def dpll(
    formula: Formula, assignment: dict[int, bool], variables: list[int]
) -> dict[int, bool] | None:
    local = dict(assignment)
    if not unit_propagate(formula, local):
        return None
    unassigned = [v for v in variables if v not in local]
    if not unassigned:
        return local
    var = unassigned[0]
    for value in (True, False):
        local[var] = value
        result = dpll(formula, local, variables)
        if result is not None:
            return result
        del local[var]
    return None


formula: Formula = [[1, 2], [-1, 3], [-2, -3], [1, -3]]
solution = dpll(formula, {}, [1, 2, 3])
print(solution)
```

このコードはunit propagationと分岐だけを持つ教育用DPLLで、衝突分析と学習節を持つ本物のCDCLの簡略版です。実運用の学習節・非時系列バックトラック・restart戦略を持つsolverは[OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)や[MiniZinc](https://docs.minizinc.dev/en/stable/)経由のSAT backendで、利用versionの説明を確認します。

::: note
DPLLは分岐と単純なバックトラックだけで、CDCLの核心である学習節と非時系列バックトラックを持ちません。この違いは、衝突を何度も同じ原因で繰り返すかどうかに現れます。
:::

## 診断値

- conflicts
- branches
- propagations
- best_bound（最適化拡張時）
- feasible_solutions

## 失敗・切替の兆候

- conflict数やbranch数が増え続けて収束しない
- domainが縮まらず、propagationがほぼ機能していない
- 整数・Boolean scaleが過大でencodingが巨大になる
- symmetryにより等価な割当を繰り返し探索する
- `UNKNOWN`（打ち切り）を`UNSAT`と誤読する

## 次に読む

最適化の枠組みごと必要なら[CP-SAT](#/learn/cp-sat)、単純な列挙の比較対象としては[Branch-and-Bound](#/learn/branch-and-bound)、離散最適化全体の選び分けは[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)で確認できます。
