---
content_id: random-search
kind: method
method_id: M_RANDOM_SEARCH
title_ja: Random Search
title_en: Random Search
summary: search spaceから同じ分布に従って独立にsamplingし評価するだけの、hyperparameter optimizationにおける最も単純なbaselineです。
source_ids: [S034, S038, S069]
prerequisites: []
related_ids: [tpe, hyperband-asha, bayesian-optimization, family.expensive-black-box]
visualization_ids: [ARTIFACT_BO_EXPLORE_NOISELESS_RANDOM_BASELINE]
comparison_ids: [COMPARE_BO_ACQUISITION_NOISE_BASELINE]
aliases: [/learn/random-search]
status: published
last_reviewed: 2026-07-24
---

search spaceから同じ分布に従って独立にsamplingし評価するだけの、hyperparameter optimizationにおける最も単純なbaselineです。

## 何を仮定しない手法か

random searchは、各trialでsearch spaceの分布からparameterを1組samplingします。
分布にはuniform、log-uniform、categoricalなどがあります。
samplingしたparameterで目的関数を評価し、過去のobjectiveを次のsamplingに反映しません。

履歴を使わないため、objectiveとparameterの関係を表すmodelも置きません。
TPEやBayesian Optimizationとは異なり、surrogateのmodel misspecificationは発生しません。

## grid searchに対する利点

grid searchは、同じtrial数を各次元へ均等に割り当てます。
重要な次元がごく一部だけなら、重要でない次元の組み合わせを何度も繰り返します。

random samplingでは各次元の値がtrialごとに変わります。
そのため、重要な少数次元でも多様な値を試しやすくなります。
ただし、次元の呪いを免れるわけではありません。
高次元で有望な領域の体積が小さければ、random searchでも十分な被覆は保証されません。

## 並列性と履歴を使わないことの意味

各trialが他のtrialの結果に依存しないため、random searchは完全に並列実行できます。
workerの数だけ同時に評価でき、逐次的なsuggestion待ちは発生しません。

一方で、acquisitionの最適化やsurrogateの更新は行いません。
実装が単純な代わりに、履歴からの学習効果は得られません。

## 同じbudgetで比較する

[acquisition・noise・Random Searchの比較](#/compare/COMPARE_BO_ACQUISITION_NOISE_BASELINE)は、同じ初期designとdomainを使う固定教材です。
seedとobjective evaluation budgetも揃えています。
Random Searchのrunでは、提案点とbest-so-farを評価回数に沿って読みます。
単一seed・1次元・10 evaluationの差から、手法の一般的なrankingは決めません。

## 向いている条件

| 条件 | 理由 |
|---|---|
| baseline・sanity checkとして使う | model misspecificationがなく、他手法の改善量を測る基準になるため |
| parameter間の相関が低いHPO | 履歴を使う手法の優位性が出にくい設定のため |
| 多数のworkerで並列実行できる | trial間に依存がなく完全並列できるため |
| search spaceの理解が浅い初期段階 | model構築より先に大まかな挙動を把握できるため |

評価が安価で大量に実行できる場合は、random searchを候補にできます。
極端に高次元で有望な領域に届きにくい場合は、model-based法やmulti-fidelity法と比較します。

## Python

```python
import numpy as np


def objective(x: np.ndarray) -> float:
    return float((x[0] - 0.3) ** 2 + (x[1] + 0.5) ** 2 + 0.05 * np.sin(20.0 * x[0]))


def random_search(
    n_trials: int, bounds: np.ndarray, seed: int
) -> tuple[np.ndarray, float, np.ndarray]:
    rng = np.random.default_rng(seed)
    best_x = bounds[:, 0]
    best_value = np.inf
    history = np.empty(n_trials)
    for trial in range(n_trials):
        x = rng.uniform(bounds[:, 0], bounds[:, 1])
        value = objective(x)
        if value < best_value:
            best_value = value
            best_x = x
        history[trial] = best_value
    return best_x, best_value, history


bounds = np.array([[-1.0, 1.0], [-1.0, 1.0]])
best_x, best_value, history = random_search(n_trials=200, bounds=bounds, seed=7)
print(best_x, best_value, history[-1])
```

`history`はtrialごとのbest-so-farです。
今回は最小化なので、値は増加せず単調に減ります。
横ばいの区間が長ければ、追加trialの限界効用が下がっています。

seedを固定しても、並列実行順序やtie-breakで結果が変わる場合があります。
再現性の条件として並列度も記録します。
OptunaのRandomSamplerやRay Tuneでは、sampling分布とseed policyを公式ドキュメントで確認します。
利用versionも併記します。

## 診断値

- best-so-far（evaluation数に対する改善曲線）
- failed / invalid trial数
- evaluation budgetの消費量
- 次元ごとのsample coverage（範囲内にどれだけ分布しているか）

## 失敗・切替の兆候

- budgetを使い切ってもbest-so-farがほとんど改善しない
- 高次元で有望な領域の体積が小さく、samplingが有効な組み合わせに当たらない
- 明らかに相関の強いparameter間の関係を無視して非効率にsamplingし続けている

model-based法へ切り替えた後も、surrogateのcross validationを確認します。
uncertaintyが較正されていない場合や、acquisitionが同じ点ばかり提案する場合は、model化を見直します。
その場合はrandom searchのbaselineへ戻り、同じbudgetで比較します。

## 次に読む

履歴を使ってsuggestionを絞る場合は、[TPE](#/learn/tpe)や[ベイズ最適化](#/learn/bayesian-optimization)へ進みます。
中間成績で評価resourceを再配分する場合は、[Hyperband / ASHA](#/learn/hyperband-asha)を確認します。
全体の選び分けは[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)で確認できます。
