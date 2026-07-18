---
content_id: tpe
kind: method
method_id: M_TPE
title_ja: TPE（Tree-structured Parzen Estimator）
title_en: Tree-Structured Parzen Estimator
summary: 観測済みtrialを良い群と悪い群に分け、条件付きsearch spaceでも良い群に現れやすいparameterを提案する逐次探索です。
source_ids: [S034]
related_ids: [family.expensive-black-box, bayesian-optimization]
status: published
last_reviewed: 2026-07-18
---

観測済みtrialを良い群と悪い群に分け、条件付きsearch spaceでも良い群に現れやすいparameterを提案する逐次探索です。

## 30秒でつかむ

この手法の気持ちは、**目的関数そのものを滑らかな曲面として当てるより、これまで良かったtrialではどんなparameterが多く、悪かったtrialでは何が多かったかを比べたい**というものです。

- 見ているもの: trial履歴、objective、parameter、trial status
- 動かしているもの: 良い群・悪い群の密度modelと次の提案
- 前進の判断: best-so-far改善と良い群へのdensity ratio
- 別に確認するもの: trial budget、parallelism、failed / pruned trialの扱い
- 恐れていること: 少ない履歴、条件付きparameterの誤表現、失敗trialの偏り

Gaussian-process BOと同じ「履歴を使う逐次探索」ですが、model化する向きと得意なsearch spaceが異なります。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| search space | 連続、整数、カテゴリ、条件付きparameterを明示できるか |
| trial budget | densityを学ぶだけの履歴が得られるか |
| objective | directionとtrial間の比較が安定しているか |
| failures | prune、timeout、crashをどう扱うか |
| parallelism | sequentialかbatch / asynchronousか |
| baseline | random searchより履歴活用に価値があるか |

parameter名だけでなく、log scale、step、条件付き有効範囲、default値をsearch-space contractとして保存します。

## 仕組み

観測値の上位側を良い群 $l(x)$、残りを悪い群 $g(x)$としてparameter densityを推定します。次の候補は概念的には、良い群で起きやすく悪い群では起きにくい場所を優先します。

$$
\text{prefer } x \text{ with large } \frac{l(x)}{g(x)}
$$

実装ではstartup trial、良い群の分位、独立・多変量model、条件付きparameter、並列suggestionなどのoptionが挙動を変えます。

## 向く条件・避ける条件

向きやすい条件:

- hyperparameter optimization
- カテゴリ・整数・条件付きparameterが混在
- trial履歴を再利用したい
- GPの距離やkernelを自然に定義しにくい

避ける条件:

- 一回の評価が安価でrandom searchを大量並列できる
- 履歴が極端に少ない
- search spaceが時間とともに変わり比較不能
- 大域最適性certificateが必要

## 診断値

見る値:

- best-so-farとtrial数
- startup trial比率
- parameterごとの提案分布
- duplicate / boundary suggestion率
- failed / pruned trial率
- seed間のbest分布
- random-search baselineとの差

best-so-far、提案分布、失敗trial、seed間のばらつきは、同じtrial budgetと停止条件で比較します。

## 失敗・切替の兆候

- 良い群のsampleが少なすぎる → startup数やbudgetを増やす
- 同じカテゴリへ偏り続ける → prior、multivariate設定、space設計を見直す
- 連続低次元でuncertaintyを読みたい → GP-BOと比較
- intermediate metricが利用可能 → Hyperband / ASHAとの組合せを検討
- 多数並列でsuggestionが似る → asynchronous policyやrandom fractionを見直す

## Python

```python
import optuna


def objective(trial: optuna.Trial) -> float:
    learning_rate = trial.suggest_float("learning_rate", 1e-4, 1e-1, log=True)
    depth = trial.suggest_int("depth", 2, 8)
    booster = trial.suggest_categorical("booster", ["linear", "tree"])
    penalty = 0.1 if booster == "tree" else 0.0
    return (learning_rate - 0.01) ** 2 + (depth - 5) ** 2 + penalty


sampler = optuna.samplers.TPESampler(seed=7)
study = optuna.create_study(direction="minimize", sampler=sampler)
study.optimize(objective, n_trials=40)
print(study.best_value, study.best_params)
```

実務ではstudy storage、search-space version、sampler option、失敗trialも保存します。

## コラム: TPEは木を探索するalgorithmではない

名前の`Tree-structured`は、条件付きparameterでsearch spaceが木構造になることに由来します。decision tree modelを必ず使うという意味ではありません。

[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)でGP-BO、SMAC、Hyperband、Random Searchとの役割を確認してください。
