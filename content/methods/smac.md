---
content_id: smac
kind: method
method_id: M_SMAC_RF
title_ja: SMAC（random forest surrogate）
title_en: SMAC with Random Forest Surrogate
summary: SMACは、ランダムフォレストを予測モデルに使う逐次モデルベース最適化です。カテゴリ変数や条件付きパラメータを含む探索空間を扱いやすい点に特徴があります。
source_ids: [S037, S059, S075]
prerequisites: []
related_ids: [bayesian-optimization, tpe, random-search, family.expensive-black-box]
aliases: [/learn/smac]
status: published
last_reviewed: 2026-09-30
---

SMACは、ランダムフォレストを予測モデルに使う逐次モデルベース最適化です。カテゴリ変数や条件付きパラメータを含む探索空間を扱いやすい点に特徴があります。

## 30秒でつかむ

何度か試した調理条件から複数の予測表を作り、平均と予測のばらつきで次の試作を選びます。SMACは木の集まりで評価値を予測します。

- 見るもの: 候補の目的値と可行性
- 動かすもの: 次に試す候補と探索の状態
- 前進の判断: 固定した評価予算で良い候補が残ること

## 一手の意味

木 $t$ の予測を $\mu_t(x)$ とすると、木ごとの予測をまとめて平均とばらつきの目安を得ます。

$$
\bar\mu(x)=\frac1T\sum_{t=1}^{T}\mu_t(x)
$$

獲得関数は予測値と不確実性を使って次の候補を選びます。
実際の分散の集約方法は実装に従います。

### 何を予測モデルに使うか

[Bayesian Optimization](#/learn/bayesian-optimization)では、多くの場合、ガウス過程（Gaussian process）を予測モデルに使います。
SMAC（Sequential Model-based Algorithm Configuration）は、ランダムフォレストを予測モデルとして使います。
評価したパラメータと評価値の組は、評価履歴として蓄積されます。
SMACはこの記録を使ってランダムフォレストを学習します。

ランダムフォレストでは、各木の予測のばらつきから不確実性の目安を得られます。
そのため、ガウス過程と同じように、予測平均と不確実性を獲得関数（獲得関数）に渡せます。
違いは、連続変数だけでなく、カテゴリ変数や条件付きパラメータも木構造の分岐として扱いやすいことです。

### 評価履歴と最良実測候補が持つ役割

SMACは、評価した点とその結果を評価履歴に保存し続けます。
評価履歴は予測モデルの学習データ（データ）であると同時に、途中経過を再現・再開するための記録でもあります。

これまでに評価した設定のうち、最も評価値がよいものを最良実測候補と呼びます。
最良実測候補は予測モデルの予測ではなく、実際の観測値から選ばれた候補です。
次に評価する候補は、獲得関数が予測モデルから選びます。
探索が進んで最良実測候補が更新されると、その後は更新されたこれまでの最良値を基準に進みます。

## 小さな例

3本の木の予測を平均する操作だけを切り出します。
下表の予測値は教材用に固定し、学習済みSMACの出力ではありません。
木ごとの予測から平均と母標準偏差を計算し、実測は $(x-1.5)^2$ としました。

| 候補 $x$ | 3本の予測 | 平均 | 予測の標準偏差 | 実測 |
|---|---|---:|---:|---:|
| 0 | 2,3,4 | 3.0 | 0.816497 | 2.25 |
| 1 | 0.2,0.3,0.4 | 0.3 | 0.081650 | 0.25 |
| 2 | 0.8,1.0,1.2 | 1.0 | 0.163299 | 0.25 |

$x=2$ は予測平均が悪くても、実測は $x=1$ と同じです。
予測を最良実測候補と混同しないことが大切です。
この3行は予測集約の確認であり、獲得関数の逐次更新ではありません。

## 向く条件・避ける条件

### GP-BOとの使い分け

探索空間の形が、GP-BOとランダムフォレストによる予測のどちらを検討するかの手がかりになります。

- 連続変数が中心で次元が低〜中程度なら、カーネルで距離を定義しやすいガウス過程系のBayesian Optimizationが候補になります。
- カテゴリ変数や条件付きパラメータが多いアルゴリズムの設定調整やハイパーパラメータ最適化では、木構造で分岐を表せるランダムフォレスト系（SMAC）が候補になります。

優劣の一般順位ではありません。
探索空間をどちらが表現しやすいかで選び分けます。

### 向いている条件

- カテゴリ変数（カテゴリ変数）、整数、条件付きパラメータが混在するアルゴリズムの設定調整
- 評価コストが高く、評価履歴を再利用する価値がある
- 連続変数だけの低次元探索空間に限られない
- 失敗した試行や時間切れを記録・活用したい

連続変数が中心の低次元探索空間で、カーネルによる不確実性を直接解釈したい場合は[ガウス過程 BO](#/learn/bayesian-optimization)を検討します。
評価が安価で大量に並列実行できる場合は、[Random Search](#/learn/random-search)や[TPE](#/learn/tpe)との比較も有効です。

## Python

次はSMAC3で1変数の設定空間を作り、決定的な目的関数（決定的な目的関数）を限られた試行数で最小化する最小例です。

```python
from ConfigSpace import Configuration, ConfigurationSpace, Float
from smac import HyperparameterOptimizationFacade, Scenario

space = ConfigurationSpace(
    space={"x": Float("x", bounds=(-5.0, 5.0), default=0.0)}
)


def objective(config: Configuration, seed: int = 0) -> float:
    del seed
    return float((config["x"] - 1.5) ** 2)


scenario = Scenario(space, deterministic=True, n_trials=20)
smac = HyperparameterOptimizationFacade(scenario, objective, overwrite=True)
incumbent = smac.optimize()

print(dict(incumbent), objective(incumbent))
```

実装については、[SMAC3](https://automl.github.io/SMAC3/latest/)の公式文書を参照してください。
探索空間の定義方法と、シナリオの種類に対応するfacadeを確認します。評価履歴の保存形式も、利用する版に対応する説明で確認します。

実行すると作業ディレクトリに評価履歴を保存します。
教材を試すときは空の一時ディレクトリで実行し、実験の保存先と分けます。

## 診断値

- これまでの最良値（最良実測候補の評価値）
- 予測誤差（ランダムフォレストの予測誤差）
- 較正（不確実性の較正）
- 獲得関数値
- 失敗試行数

## 失敗・切替の兆候

- 予測モデルの交差検証誤差が大きく改善しない
- 不確実性の較正が悪く、獲得関数が同じ領域ばかり提案する
- 条件付きパラメータの表現が誤っており、無効な組み合わせが提案され続ける
- 評価が安価すぎて予測モデル構築の追加費用が見合わない
- 評価履歴が少なすぎてランダムフォレストの分散推定が不安定

連続変数中心の低次元でガウス過程による不確実性を直接扱いたい場合は、[Bayesian Optimization](#/learn/bayesian-optimization)を検討します。
条件付き空間で密度比を使う別の予測モデルは[TPE](#/learn/tpe)、何も仮定しない比較基準は[Random Search](#/learn/random-search)です。
高価なブラックボックス探索全体の選び分けは、[高価なブラックボックス・HPOの選び分け](#/learn/family.expensive-black-box)で確認できます。

## 次に読む

- [関連する手法の記事](#/learn/bayesian-optimization)：一手の意味と選び分けを比べます。

- [この手法を使う問題の定式化](#/formulations/PA039)：決定変数と目的を確認します。
