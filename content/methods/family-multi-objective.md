---
content_id: family.multi-objective
kind: method
method_id: MF_MULTI_OBJECTIVE
title_ja: 多目的最適化の選び分け
title_en: Choosing a Multi-Objective Method
summary: 複数目的のtrade-offをscalarizationまたはpopulationで探索し、単一の最適解ではなくPareto解集合の近似を得るための多目的最適化手法を条件に応じて選び分ける入口です。
source_ids: [S039, S068]
prerequisites: []
related_ids: [weighted-sum, epsilon-constraint, multi-objective, nsga-iii, moead]
status: published
last_reviewed: 2026-07-16
---

複数目的のtrade-offをscalarizationまたはpopulationで探索し、単一の最適解ではなくPareto解集合の近似を得るための多目的最適化手法を条件に応じて選び分ける入口です。

## 30秒でつかむ

このfamilyの気持ちは、**「1つの最適解」を求めるのではなく、目的間のtrade-offを表すPareto frontを近似すること、またはその代表点を得ること**です。ある解が他のどの解にも支配されない（dominateされない）とき、その解はPareto最適候補として扱われます。

- 見ているもの: 複数目的の値、解同士のdomination関係
- 動かすもの: 単一solverへの重みやscalarization、または集団全体の分布
- 前進の判断: Pareto frontの近似がどれだけ広く、均等にcoverされているか
- 主な弱点: 目的のscaleやmetricへの依存、目的数が増えると探索・可視化が難しくなること

「多目的手法がscalarizationより常に優れている」という順位ではありません。事前の選好情報の有無と、目的数、front全体の品質評価の手間を交換しています。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 意思決定者の選好が事前にあるか | あるなら重みや制約閾値を決めてscalarizationで単目的solverを使える |
| 目的数が2〜3か、それ以上（many-objective）か | 目的数が増えるほどpopulation系の設計とfront品質評価が難しくなる |
| 各目的のscaleや単位 | scaleが揃っていないとweighted-sumの重みが意味を持ちにくい |
| 単目的solverの評価コスト | 高価ならscalarizationの反復回数を抑える設計が必要 |
| front全体を評価する指標 | hypervolumeなどでcoverageを測る前提を作れるか |

複数目的を根拠なく1つのscoreへ潰すと、trade-offの構造そのものが見えなくなります。まず「単一のutilityが実は明確にある」のか「trade-off自体が成果物」なのかを確認します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 選好を重みとして固定 | [重み付き和scalarization](#/learn/weighted-sum) | 目的間の相対重要度が決まっており、単目的solverを繰り返し使いたい | Pareto frontが非凸な部分を持ち、重み変化で捉えられない解がある |
| 1目的を制約へ移す | [ε制約法](#/learn/epsilon-constraint) | 主目的が明確で、他の目的を許容上限・下限として扱いたい | 閾値の候補が多く、反復ごとの単目的求解コストが大きい |
| 2〜3目的でfrontを近似 | [NSGA-II（multi-objective）](#/learn/multi-objective) | 事前の選好がなく、2〜3目的のfrontを集団で近似したい | 目的数が増えてcrowding distanceによる多様性維持が弱くなる |
| many-objectiveでfrontを近似 | [NSGA-III](#/learn/nsga-iii) | 目的数が多く、reference directionでfrontの広がりを維持したい | reference directionの設計が問題の形状に合わない |
| 分解によるfront近似 | [MOEA/D](#/learn/moead) | 多数のweightやreference方向でsubproblemに分解して近い候補同士を共有したい | subproblem間の近傍構造が問題に合わず収束が偏る |

これは一般性能rankingではありません。同じproblem instance、目的数、評価予算、seedで比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、次の観測が揃います。

- hypervolumeが評価回数とともに改善し、停滞しない
- spacingやepsilon indicatorが極端な偏りを示さない
- feasible fractionが十分に保たれる（制約がある場合）
- 得られた解集合が意思決定に使える程度に多様である

切替サイン:

- Pareto coverageが不足し、frontの一部しか得られない → population sizeやscalarizationの重み・閾値の刻みを見直す
- 解が両極端に偏り、trade-off候補として使えない → weighted-sumの非凸front限界を疑い、population系へ切り替える
- 目的数が増えてcrowding distanceベースの多様性維持が効かない → NSGA-IIIやMOEA/Dへ切り替える
- 実は単一utilityが明確だと分かった → 多目的として扱う必要がなくなり、単目的solverに戻す

## 小さな比較の型

実装比較では目的数、評価予算、front品質の指標を揃えて記録します。

```python
experiment = {
    "problem_instance": "same-biobjective-problem",
    "num_objectives": 2,
    "evaluation_budget": 10000,
    "seeds": [0, 1, 2],
    "quality_metric": "hypervolume",
    "methods": ["weighted-sum", "nsga2", "moead"],
}

assert experiment["num_objectives"] >= 2
```

## コラム: hypervolumeは何を測っているのか

hypervolumeは、得られた解集合と基準点（reference point）との間に囲まれる領域の体積として計算される指標で、front全体の「広さ」と「良さ」を同時に反映します。単一の解の目的値だけを見ても、front全体がどれだけ多様な選択肢を提供しているかは分かりません。hypervolumeやspacing、epsilon indicatorのような指標は、1つの解ではなく解集合全体の品質を評価するために使います。

ただし、これらの指標は基準点の取り方やscaleの正規化に依存します。目的間でscaleが大きく異なる場合、正規化を誤ると指標が実際のtrade-off構造を正しく反映しません。

## 次に読む

事前の選好が明確で単目的化できる場合は[重み付き和scalarization](#/learn/weighted-sum)から、目的数が多いmany-objective設定を詳しく検討する場合は[NSGA-III](#/learn/nsga-iii)へ進みます。
