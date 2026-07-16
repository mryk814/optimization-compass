---
content_id: family.evolutionary
kind: method
method_id: MF_EVOLUTIONARY
title_ja: 進化計算・population探索の選び分け
title_en: Choosing an Evolutionary or Population-Based Method
summary: 個体群を選択・変異・交叉・共分散適応などで更新しながら評価予算を使って改善する進化計算・population探索手法を条件に応じて選び分けるための入口です。
source_ids: [S032, S033, S040, S058, S074]
prerequisites: []
related_ids: [cma-es, genetic-algorithm, particle-swarm, differential-evolution, family.global-search]
status: published
last_reviewed: 2026-07-16
---

個体群を選択・変異・交叉・共分散適応などで更新しながら評価予算を使って改善する進化計算・population探索手法を条件に応じて選び分けるための入口です。

## 30秒でつかむ

このfamilyの気持ちは、**一点ではなく候補の集団を持ち、選択・変異・組み替え、または探索分布そのものの更新によって、微分なしで良い候補を増やしていくこと**です。個々の候補は目的関数値の順位や適応度だけで比較され、勾配は使いません。

- 見ているもの: 各候補のfunction evaluation結果、集団内の順位や適応度
- 動かすもの: 候補の集団、または集団を生成する確率分布のparameter
- 前進の判断: best-so-farの改善、集団の多様性が保たれていること
- 主な弱点: 大量のfunction evaluationを要すること、保証がないこと、変数表現とoperatorのparameterに依存すること

「進化計算が微分不要問題で常に上位」という順位ではありません。微分を使わずに済む代わりに、評価回数と表現設計の手間を引き受けています。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 評価回数の予算 | 予算が小さいなら、このfamilyより高価なblack-box向けfamilyを検討する |
| 変数が連続か離散・順列構造か | 連続ならCMA-ES/DEが標準的な出発点、離散・順列ならGA系のencodingが本質になる |
| bounds・制約の扱い方 | penalty、repair、feasibility ruleのどれで可行性を保つかを事前に決める必要がある |
| 並列評価が可能か | 集団単位の評価は並列化しやすく、予算あたりの実時間を短縮できる |
| 乱数seedの管理 | 同じ設定でも実行ごとに結果が変わるため、複数seedでの評価が前提になる |
| 1回の評価コスト | 評価が非常に高価な場合はsurrogateを使うBayesian Optimization系へ切り替える判断が必要 |

変数の表現（encoding）と、そこに対応するoperator（変異・交叉・共分散更新）の整合性が、このfamily全体で最も重要な設計判断です。表現を変えるとoperatorの意味も変わるため、既存のoperatorをそのまま流用できるとは限りません。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 連続空間の標準的な出発点 | [CMA-ES](#/learn/cma-es) | 連続変数で、有望な方向とscaleを分布として学びたい | 変数次元が非常に大きく共分散推定が重い、離散変数が中心 |
| 離散・順列構造の表現設計 | [遺伝的アルゴリズム](#/learn/genetic-algorithm) | 離散・組合せ・混合空間で、encodingとoperatorを問題に合わせたい | 表現設計が難しく収束が安定しない |
| 群知能による連続探索 | [Particle Swarm](#/learn/particle-swarm) | 連続black-boxで、個体と群のbest経験を使った単純な更新則を試したい | 早期収束が起きやすい問題で多様性を保てない |
| 差分vectorによる連続探索 | [Differential Evolution](#/learn/differential-evolution) | bounded連続空間で、少ないparameterで頑健な探索をしたい | 次元が高く差分vectorの多様性が不足する |

これは一般性能rankingではありません。同じproblem instance、population size、評価予算、seed数で比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、次の観測が揃います。

- best-so-farの値が評価回数とともに継続的に改善する
- population diversityが極端に潰れない
- feasible fractionが十分に保たれる（制約がある場合）
- 異なるseedでも同程度の解に到達する

切替サイン:

- 多様性崩壊（diversity loss）が起き、best-so-farが早期に停滞する → operatorやparameterを見直す、または再起動を導入する
- 可行個体がほとんど生成されない → penalty/repair/encodingの設計を見直す
- 評価回数が予算に対して大きくなりすぎる → 評価が高価ならfamily.expensive-black-boxのsurrogate系へ切り替える
- 問題が実は滑らかで勾配が得られる → family.smooth-localの局所法の方が少ない評価回数で済む場合がある

## 小さな比較の型

実装比較では評価回数、population size、seed数を揃えて記録します。

```python
experiment = {
    "problem_instance": "same-bounded-objective",
    "population_size": 40,
    "evaluation_budget": 20000,
    "seeds": [0, 1, 2, 3, 4],
    "encoding": "real-vector",
    "methods": ["cma-es", "differential-evolution", "particle-swarm"],
}

assert experiment["evaluation_budget"] > 0
```

## コラム: なぜ表現とoperatorの整合が最優先なのか

進化計算の理論的な収束性は多くの場合弱く、実務上の性能は表現（encoding）とoperator（変異・交叉・共分散更新）の組み合わせに強く依存します。連続変数をそのまま実数vectorとして扱うCMA-ESやDEは、encodingとoperatorが自然に対応しますが、離散・順列構造（巡回路や割り当てなど）を実数vectorへ無理に写像すると、変異や交叉が意味のある近傍を作らなくなることがあります。

このため、GA系を離散問題へ適用するときは、まずどのencodingを使うかを決め、それに対応するcrossoverとmutationが「近い個体を近い評価値に写像するか」を確認します。この対応が崩れている場合、population sizeや評価回数を増やしても改善は得られません。

## 次に読む

多峰性・大域探索全体の文脈で位置づけたい場合は[大域探索・多峰性問題の選び分け](#/learn/family.global-search)へ進みます。
