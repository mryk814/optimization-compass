---
content_id: outer-approximation-minlp
kind: method
method_id: M_OUTER_APPROX_MINLP
title_ja: MINLPのOuter Approximation
title_en: Outer Approximation for MINLP
summary: 整数変数を扱うmaster問題と、整数を固定した連続NLPを交互に解き、凸な非線形情報をcutとしてmasterへ戻す厳密探索法です。
source_ids: [S021, S024, S028, S056]
related_ids: [branch-and-cut, constrained-continuous]
status: published
last_reviewed: 2026-07-18
---

整数変数を扱うmaster問題と、整数を固定した連続NLPを交互に解き、凸な非線形情報をcutとしてmasterへ戻す厳密探索法です。

## 30秒でつかむ

この手法の気持ちは、**整数の組合せと連続非線形最適化を一度に丸抱えせず、整数候補を選ぶ問題と、その候補で連続変数を詰める問題へ分け、連続側で学んだことをcutとして整数側へ返したい**というものです。

- 見ているもの: MILP masterのbound、NLP subproblemの可行解、gradient、cut
- 動かしているもの: 整数候補、連続解、linearization cut、incumbent
- 前進の判断: master boundとfeasible incumbentのgapが縮むか
- 別に確認するもの: MILPとNLPそれぞれの計算cost、global gap、停止理由
- 恐れていること: 非凸連続部分、弱いcut、NLP failure、不適切なBig-M

有限反復のcertificateを期待できるのは、連続部分の凸性など必要な前提が満たされ、solverが正しく処理する場合です。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| variable | integer / binaryとcontinuousが混在するか |
| convexity | 整数を固定したNLPが凸か |
| derivatives | objective・constraint gradientを得られるか |
| formulation | indicator、Big-M、boundsが妥当か |
| feasibility | 整数候補ごとのNLPがinfeasibleになりうるか |
| guarantee | global gapやproofが必要か |

非凸MINLPでは通常のOuter Approximationのcutがglobalに有効とは限りません。spatial branch-and-boundなど別のglobal methodが必要です。

## 仕組み

基本サイクルは次です。

1. 線形化cutを含むMILP masterから整数候補を得る
2. その整数を固定してcontinuous NLPを解く
3. 可行ならincumbentを更新する
4. NLPのgradientからobjective・constraintのlinearization cutを作る
5. masterへcutを加え、boundとincumbentのgapが閉じるまで繰り返す

NLPがinfeasibleな場合にはfeasibility subproblemやno-good cutなど、実装ごとの処理が必要です。

## 向く条件・避ける条件

向きやすい条件:

- convex MINLP
- 整数を固定したNLPを安定して解ける
- gradientを利用できる
- MILP masterへ強いcutを追加できる
- feasible solutionとglobal gapの両方が必要

避ける条件:

- 一般非凸MINLPを凸とみなす
- black-box・noiseを含む非線形評価
- boundsがなくBig-Mが極端に大きい
- NLP subproblemが頻繁に失敗する

## 診断値

見る値:

- incumbentとmaster bound
- optimality gap
- master iteration数
- NLP success / infeasible数
- cut追加数とcut violation
- 同じ整数候補の再訪
- MILP node数とNLP evaluation cost

feasible incumbent、master bound、optimality gap、subproblem statusは別々に保存します。
どれか一つが改善しても、global certificateが成立したとは限りません。

## うまくいったサインと切替サイン

- cutを増やしてもboundが動かない → formulationとlinearizationを見直す
- NLP failureが多い → initial point、scaling、feasibility処理を確認
- 非凸性でcutが無効 → spatial branch-and-boundへ
- integer候補を何度も再訪 → no-good cutやmaster toleranceを確認
- 早い可行解だけ必要 → heuristicやtime-limit strategyを検討

## Python

```python
from dataclasses import dataclass


@dataclass
class SubproblemResult:
    feasible: bool
    objective: float
    point: tuple[float, ...]


def outer_approximation(max_iterations: int = 20) -> SubproblemResult | None:
    cuts: list[object] = []
    incumbent: SubproblemResult | None = None

    for _ in range(max_iterations):
        integer_candidate = solve_milp_master(cuts)
        subproblem = solve_fixed_integer_nlp(integer_candidate)

        if subproblem.feasible:
            if incumbent is None or subproblem.objective < incumbent.objective:
                incumbent = subproblem
            cuts.extend(linearize_at(subproblem.point))
        else:
            cuts.append(build_feasibility_cut(integer_candidate))

        if master_gap_is_closed(incumbent):
            break

    return incumbent
```

このコードはalgorithmの責務を示す教育用skeletonです。`solve_milp_master`などは利用solverに合わせて実装します。

## コラム: decompositionとglobality

整数と連続を分けたから自動的に簡単になるわけではありません。master relaxation、NLPのconditioning、cutの強さ、整数候補の数が全体costを決めます。

MILP側の探索は[Branch-and-Cut](#/learn/branch-and-cut)、連続subproblemは[制約付き連続最適化](#/learn/constrained-continuous)を参照し、両者のstatusを別々に保存してください。
