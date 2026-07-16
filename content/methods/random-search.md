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
aliases: [/learn/random-search]
status: published
last_reviewed: 2026-07-16
---

search spaceから同じ分布に従って独立にsamplingし評価するだけの、hyperparameter optimizationにおける最も単純なbaselineです。

## 何を仮定しない手法か

random searchは、各trialでsearch spaceの分布（uniform、log-uniform、categoricalなど）から独立にparameterを1組samplingし、目的関数を評価するだけです。過去のtrialのobjectiveやparameterを次のsamplingに反映しません。履歴を使わないということは、objectiveとparameterの関係についてどんなmodelも仮定しないということでもあります。TPEやBayesian Optimizationのようなmodel-based法が抱えるmodel misspecification（surrogateが実際の関係を誤って表現するリスク）がそもそも発生しません。

## grid searchに対する利点

同じtrial数を各次元へ均等に割り当てるgrid searchでは、実際に重要な次元がごく一部だけの場合、重要でない次元の組み合わせを何度も繰り返すだけで無駄が生じます。random samplingでは各次元の値がtrialごとに変わるため、重要な少数次元に対しても実質的に多様な値を試せる配置になりやすい、という違いがあります。ただしこれは次元の呪いを免除するものではなく、高次元で有望な領域の体積が小さい場合はrandom searchでも十分な被覆は保証されません。

## 並列性と履歴を使わないことの意味

各trialが他のtrialの結果に依存しないため、random searchは完全に並列実行できます。workerの数だけ同時に評価を投げてよく、逐次的なsuggestion待ちが発生しません。この独立性は、model-based法のようにacquisitionの最適化や逐次的なsurrogate更新を挟む余地がないという意味でもあり、実装が単純である代わりに履歴からの学習効果は得られません。

## 向いている条件

| 条件 | 理由 |
|---|---|
| baseline・sanity checkとして使う | model misspecificationがなく、他手法の改善量を測る基準になるため |
| parameter間の相関が低いHPO | 履歴を使う手法の優位性が出にくい設定のため |
| 多数のworkerで並列実行できる | trial間に依存がなく完全並列できるため |
| search spaceの理解が浅い初期段階 | model構築より先に大まかな挙動を把握できるため |

評価が安価で大量に実行できる場合や、極端に高次元でsamplingだけでは有望な領域に届きにくい場合は、model-based法やmulti-fidelity法との比較が必要になります。

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

`history`はtrialごとのbest-so-farです。増加せず単調に減っていく（今回は最小化）区間が長いほど、追加trialの限界効用が下がっていることを示します。seedを固定しても、実務のHPO frameworkでは並列実行順序やtie-breakによって結果がわずかに変わる場合があるため、再現性の条件として並列度も記録します。OptunaのRandomSamplerやRay Tuneのrandom searchなど、実装ごとのsampling分布・seed policyは各frameworkの公式ドキュメントで利用versionの説明を確認します。

## 診断値

- best-so-far（evaluation数に対する改善曲線）
- failed / invalid trial数
- evaluation budgetの消費量
- 次元ごとのsample coverage（範囲内にどれだけ分布しているか）

## 失敗・切替の兆候

- budgetを使い切ってもbest-so-farがほとんど改善しない
- 高次元で有望な領域の体積が小さく、samplingが有効な組み合わせに当たらない
- 明らかに相関の強いparameter間の関係を無視して非効率にsamplingし続けている

model-based法へ切り替えた後にsurrogateのcross validationが悪い、uncertaintyが較正されていない、acquisitionが同じ点ばかり提案するといった兆候が出た場合は、model化がうまくいっていないサインです。その場合はrandom searchのbaselineに一度戻して比較する方が安全です。

履歴を使ってsuggestionを絞り込む手法は[TPE](#/learn/tpe)や[ベイズ最適化](#/learn/bayesian-optimization)、中間成績で評価resourceを再配分する手法は[Hyperband / ASHA](#/learn/hyperband-asha)、高価なblack-box全体の選び分けは[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)で確認できます。
