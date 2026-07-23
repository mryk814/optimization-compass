---
content_id: family.expensive-black-box
kind: method
method_id: MF_SURROGATE_HPO
title_ja: 高価なblack-box・HPOの選び分け
title_en: Choosing an Expensive Black-Box Strategy
summary: 一回の実験やsimulationが高価な問題の入口です。Bayesian Optimization／TPE／multi-fidelity／random・evolutionary baselineを選び分けます。
source_ids: [S034, S035, S036, S037, S038, S059, S069, S075]
related_ids: [bayesian-optimization, cma-es, differential-evolution]
status: published
last_reviewed: 2026-07-24
---

一回の実験やsimulationが高価な問題の入口です。Bayesian Optimization／TPE／multi-fidelity／random・evolutionary baselineを選び分けます。

## 30秒でつかむ

このfamilyの気持ちは、**少ない評価をどこへ使うかを学習し、良さそうな場所とまだ分からない場所の両方を意識して次の試行を選ぶこと**です。

- 見ているもの: 観測履歴、surrogate、uncertainty、trial status、resource
- 動かすもの: 次の評価点、batch、探索空間、trialへ割り当てるbudget
- 前進の判断: best-so-far改善と、次の評価が持つ情報価値
- 主な弱点: model mismatch、高次元、条件付き空間、失敗trial、非定常性

surrogateの予測平均やacquisitionの最大点は、真の最適点の証明ではありません。次に試す価値を表すmodel上の判断です。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 1評価の時間・費用 | surrogate構築に価値があるほど高価か |
| total budget | 数十、数百、数千trialのどれか |
| 変数型 | 連続、整数、カテゴリ、条件付きの混合 |
| noise | 同じ点を再評価できるか |
| parallelism | sequential、batch、asynchronousのどれか |
| fidelity | epoch、sample数、meshなど途中budgetを変えられるか |
| failure | timeout、crash、infeasibleをどう記録するか |

評価が安価で大量に実行できるなら、複雑なsurrogateよりrandom searchやpopulation法が堅実なbaselineになることがあります。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| uncertaintyを明示 | [Gaussian-process BO](#/learn/bayesian-optimization) | 低〜中次元、数十〜数百評価、連続変数中心 | 観測数・次元が増えfit/acquisitionが重い |
| 条件付き・混合空間 | [TPE](#/methods/M_TPE) | HPO、カテゴリや条件付きparameterが多い | density modelが良い領域を分離できない |
| 木系surrogate | [SMAC](#/methods/M_SMAC) | mixed space、algorithm configuration、失敗trial | surrogate calibrationが悪い、並列性が不足 |
| 早期停止でresource配分 | [Hyperband](#/methods/M_HYPERBAND) | 中間評価が最終性能をある程度予測する | early metricが誤解を招き良いtrialを落とす |
| 何も仮定しない基準 | Random Search | baseline、並列性、search space sanity check | budgetが小さく履歴活用が必要 |
| 並列black-box探索 | [CMA-ES](#/learn/cma-es) / [DE](#/learn/differential-evolution) | 連続・多峰性、十分な並列budget | 一評価が極端に高価、populationを維持できない |

「Bayesian Optimizationが常に最少評価」とは限りません。search space／noise model／initial design／acquisition optimizerが不適切なら、baselineに負けます。

## 推薦の前に4つの層を監査する

1. **method**: GP-BO、TPE、Hyperbandなどの更新原理と必要な仮定
2. **implementation**: library version、kernel、transform、sampler、acquisition optimizerなどのdefault
3. **evaluation policy**: initial design、fidelity cost、parallelism、batch / asynchronous、failure・retry、stopping
4. **recommendation priority**: problem条件と、公平なbudgetで得た比較証拠に基づく候補順

implementation defaultは再現に必要ですが、手法の定義でも普遍的な推奨でもありません。evaluation policyが違うrunは、optimizer iterationだけで並べません。同じtotal costまたはhigh-fidelity-equivalent costへ同期します。推薦は固定教材の勝敗ではなく、変数型／budget／noise／failure構造／複数seedの証拠から更新します。

[同じcostでfidelity配分を読むCompare](#/compare/COMPARE_BO_MULTIFIDELITY_COST)では、次の条件を揃えます。

- initial designとdeterministic noise
- fidelity cost
- parallel workers=1
- tuning
- 失敗をnullのまま記録し、costを課してretryしないpolicy

変更するのはmixed low/highとhigh-onlyの配分だけです。この1次元・単一seedのcontrastから一般的なpolicy順位は決めません。

## うまくいったサインと切替サイン

追うべき値:

- best-so-farとtrial数
- surrogate cross-validation error
- uncertainty calibration
- acquisition valueとselected point
- duplicate suggestion率
- failed / infeasible trial率
- batch idle time
- fidelity別のranking correlation

切替サイン:

- 同じ点や境界ばかり提案 → acquisition optimizer、kernel、encodingを見直す
- uncertaintyが過小で探索しない → noise model、prior、exploration parameterを見直す
- カテゴリ・条件付き空間が不自然 → TPE/SMACなど別surrogateへ
- trialが大量に並列実行可能 → batch BOまたはrandom/evolutionary baselineへ
- 途中metricと最終metricの相関が弱い → Hyperband型早期停止を弱める
- search spaceが広すぎる → domain knowledgeでbounds・parameterizationを再設計

multi-fidelityでは、同じ候補をlow/highで照合した残差と順位相関も追います。次のsignalがあれば、discrepancy modelまたはkernelの仮定を見直します。

- low fidelityの順位が反転する
- high fidelity residualが領域ごとに偏る
- scaling変更で提案が不安定になる

failed領域の近傍を繰り返す場合は、目的値penaltyだけで隠しません。status／feasibility／retry／boundsを監査します。

## 小さな比較の型

比較ではinitial designと失敗trialの扱いを揃えます。

```python
study_contract = {
    "search_space_version": "v1",
    "objective_direction": "minimize",
    "initial_design": "same-8-points",
    "trial_budget": 80,
    "parallel_workers": 4,
    "seeds": [11, 12, 13],
    "failure_policy": "record-and-penalize-explicitly",
    "methods": ["GP-BO", "TPE", "random-search"],
}

assert study_contract["trial_budget"] >= 1
```

## コラム: 探索空間はmodelの一部

次のsearch space設計は、surrogateが学習する地形そのものを歪めます。

- log-scaleにすべきparameterをlinearに置く
- 無効な組合せを一つの箱へ押し込む
- カテゴリへ架空の距離を与える

AIやsolverへ渡す前に、parameterの意味／単位／条件付き関係／無効領域／default値を明示します。良いoptimizerを選ぶことより、良いsearch spaceを作ることが支配的な場合があります。

## 次に読む

一評価が安価で多峰性を広く探せるなら[大域探索の選び分け](#/learn/family.global-search)、gradientをmini-batchで利用できる学習問題なら[確率勾配optimizerの選び分け](#/learn/family.stochastic-ml)へ進みます。
