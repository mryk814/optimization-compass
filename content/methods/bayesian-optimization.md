---
content_id: bayesian-optimization
kind: method
method_id: M_BAYESIAN_OPT_GP
title_ja: ベイズ最適化
title_en: Bayesian Optimization
summary: 高価なblack-box評価を節約するため、観測履歴から代理モデル（surrogate model）と不確実性を更新し、獲得関数で次の評価点を選ぶ逐次最適化です。
source_ids: [S034, S035, S059, S075]
prerequisites: []
related_ids: [differential-evolution, cma-es, random-search, tpe, family.expensive-black-box]
visualization_ids: [ARTIFACT_BO_EXPLORE_NOISELESS, ARTIFACT_BO_EXPLORE_SMALL_NOISE, ARTIFACT_BO_MULTIFIDELITY_LEDGER, ARTIFACT_BO_LOW_FIDELITY_BIAS]
comparison_ids: [COMPARE_BO_ACQUISITION_NOISE_BASELINE, COMPARE_BO_MULTIFIDELITY_COST]
aliases: [/learn/bayesian-optimization]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-09-30
---

高価なblack-box評価を節約するため、観測履歴から代理モデル（surrogate model）と不確実性を更新し、獲得関数で次の評価点を選ぶ逐次最適化です。

## 30秒でつかむ

初めての街で、一週間に数回しか外食できないとします。
すでに当たりだった店へ通うか、まだ行っていない店を試すか。回数が限られているので、どちらも無駄にできません。
ベイズ最適化は、この迷いを、観測から作った予測と不確実性の表で決めます。

- **見るもの**: 観測済みの目的関数値、代理モデル（surrogate model）の予測と不確実性、獲得関数（acquisition function）
- **動かすもの**: 次に実際に評価する点と、観測を足した後の代理モデル
- **前進の判断**: 同じ評価予算で、最良値（best-so-far）が改善すること

一回の評価に数分から数日かかる問題で、評価の回数を節約するための手法です。

## 一手の意味

一巡は次の手順です。

1. 初期点で目的関数を評価する
2. 観測 $(x_i,y_i)$ から、代理モデルの事後分布（posterior）を更新する
3. 獲得関数を、探索空間の上で最適化する
4. 選んだ点を実際に評価する
5. 予算または停止条件まで繰り返す

Gaussian-processによるBOでは、各入力に予測平均 $\mu(x)$ と標準偏差 $\sigma(x)$ が付きます。
平均は現在の予測です。標準偏差は、未観測の領域について、モデル上の情報が足りない度合いです。

観測が増えれば、同じ場所を選び続けるのでしょうか。
固定seedの実行では、代理モデルと次の候補が、ともに動きます。

![固定seedの1次元black-boxでGaussian-process Bayesian Optimizationを実行し、実評価3回後と6回後のsurrogate平均、不確実性帯、観測点、Expected Improvement、次の評価点を比較した結果。観測の追加後は不確実性帯が縮み、次の評価点がx=1.73からx=2.10へ移る。](./media/bayesian-optimization-execution.svg "固定1次元・noiseless・RBF kernelのPython実行結果です。真の目的関数は教材用の答え合わせであり、optimizerは観測点以外の真値を参照しません。大域最適性や一般性能は示しません。")

上段は初期3点の直後、下段はさらに3点を評価した後です。
不確実性が縮む場所と、橙のExpected Improvementが選ぶ次の点を対応させて読みます。

### 獲得関数の意味

代表例です。

- Expected Improvement
- Probability of Improvement
- lower / upper confidence bound
- Thompson sampling
- knowledge gradient系

最小化のlower confidence boundなら、概念的には次の値が小さい点を選びます。

$$
a(x)=\mu(x)-\beta\sigma(x)
$$

この式は「予測が良く、かつ不確実性が大きい点ほど、次に評価する価値が高い」と読みます。
平均が良い場所を調べる**活用**と、不確実性が大きい場所を調べる**探索**を、一つの基準にまとめています。$\beta$ が大きいほど、探索に寄ります。

::: warning
獲得関数の最良点は、目的関数の最適点だと証明された場所ではありません。「次に評価する価値が高い」と、モデルが判断した候補です。
:::

## 小さな例

目的関数 $f(x)=(x-0.25)^2+0.1\sin(12x)$ を、区間 $[-1,1]$ で最小化します。
初期の観測は $x=-1$（$f=1.616$）と $x=0.8$（$f=0.285$）の2点です。
代理モデルは平均0・カーネル幅0.25のGaussian process、獲得関数は $\mu(x)-1.5\,\sigma(x)$ です。
このコードは乱数を使わないので、seed は不要です。同じコードは同じ点を選びます。

| 反復 | 選ばれた点 $x$ | 予測平均 $\mu$ | 標準偏差 $\sigma$ | 獲得関数の値 | 実際の $f(x)$ | 最良値 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | $-0.035$ | 0.002 | 1.000 | $-1.498$ | 0.040 | 0.040 |
| 2 | $0.360$ | 0.072 | 0.934 | $-1.330$ | $-0.080$ | $-0.080$ |
| 3 | $-0.420$ | 0.135 | 0.946 | $-1.284$ | 0.544 | $-0.080$ |

最初の3回は、いずれも標準偏差が1に近い点、つまり観測点から遠い点が選ばれています。
予測平均がほとんど差を作らないうちは、獲得関数は不確実性の大きさで決まります。
反復3の点は悪い値でしたが、この観測も代理モデルを更新します。

その後、観測が増えると標準偏差が縮みます。反復8では $x=0.4$（$\sigma=0.014$）、反復9では $x=0.375$（$\sigma=0.001$）が選ばれ、最良値は $-0.0821$ になります。
この区間の格子で調べた最小点も $x=0.375$ で、同じ値です。

ただし、反復9から12までは、提案が $x=0.375$ の繰り返しです。
ノイズのない設定では、同じ点を再び測っても新しい情報がありません。この例は、繰り返しの提案が停止や切替の合図になることも示しています。

## 向く条件・避ける条件

向く条件です。

- 一回の評価が数分〜数日かかるsimulationや実験
- 評価の回数が、数十〜数百程度に制限される
- 低〜中次元の探索空間
- 過去の観測を、次の点の選択へ活かしたい
- 勾配を直接得られない
- 観測のnoiseや失敗を、モデルに含められる

避ける、または切り替える条件です。

- 評価が安価で、大量に並列で回せる → [Random Search](#/learn/random-search)や集団を使う探索のほうが単純な場合がある
- 極端な高次元 → カーネルや獲得関数の最適化が難しい。[高次元のblack-box最適化（PA015）](#/formulations/PA015)を確認する
- 条件付き・カテゴリカルな探索空間 → 符号化や専用の代理モデルが必要。[TPE](#/learn/tpe)も候補
- 目的関数が時間や場所で性質を変える（非定常） → 固定カーネルが過去の観測を誤解する
- 評価の失敗を、欠損として無視する → 実行可能性のモデルが必要
- モデルの不確実性を、実世界の安全の保証と誤認する

hyperparameterを選ぶ場面なら、[hyperparameter optimization（PA039）](#/formulations/PA039)が具体的な入口になります。

## Python

次の例は、ここまでの目的関数を、素朴なGaussian processと下側信頼限界で最小化します。

```python
import numpy as np


def objective(x: np.ndarray) -> np.ndarray:
    return (x - 0.25) ** 2 + 0.1 * np.sin(12.0 * x)


def rbf_kernel(left: np.ndarray, right: np.ndarray, length_scale: float) -> np.ndarray:
    squared_distance = (left[:, None] - right[None, :]) ** 2
    return np.exp(-0.5 * squared_distance / length_scale**2)


observed_x = np.array([-1.0, 0.8])
observed_y = objective(observed_x)
grid = np.linspace(-1.0, 1.0, 401)

for _ in range(12):
    kernel = rbf_kernel(observed_x, observed_x, 0.25) + 1e-6 * np.eye(len(observed_x))
    cross = rbf_kernel(grid, observed_x, 0.25)
    weights = np.linalg.solve(kernel, observed_y)
    mean = cross @ weights
    solved = np.linalg.solve(kernel, cross.T)
    variance = np.maximum(1.0 - np.sum(cross * solved.T, axis=1), 1e-12)
    acquisition = mean - 1.5 * np.sqrt(variance)

    next_x = grid[np.argmin(acquisition)]
    observed_x = np.append(observed_x, next_x)
    observed_y = np.append(observed_y, objective(np.array([next_x]))[0])

best_index = np.argmin(observed_y)
print(observed_x[best_index], observed_y[best_index])
# 0.375 -0.0821280117665097
```

これは平均0・固定カーネル・noiseなしに近い教育例です。
実務では、平均関数を明示します。カーネルのhyperparameterとnoiseも明示します。
数値の安定性と、獲得関数の最適化の方法も記録します。

## 診断値

評価の回数に対する改善と、代理モデルの信頼度を分けて見ます。

| 診断値 | 見方 | 判断 |
|---|---|---|
| 評価数に対する最良値 | 同じ予算で下がっているか | 下がり続けるなら継続。横ばいが長ければ、停止か[Random Search](#/learn/random-search)との比較 |
| 代理モデルの予測誤差 | 交差検証（cross validation）の残差 | 領域ごとに偏るなら、カーネルの不一致を疑う |
| 不確実性の較正（calibration） | 予測の幅と実際の誤差が合うか | 幅が小さいのに誤差が大きければ、モデルを見直す |
| 獲得関数の値 | 次の候補にどれだけ価値があるか | 改善の見込みが小さいまま続くなら、停止を検討する |
| 繰り返し・近接した提案 | 同じ点や近い点ばかり選んでいないか | 続くなら、停止か、失敗の扱いとモデルの確認 |
| 失敗した試行の数 | 評価が返らなかった回数 | 増えるなら、実行可能性のモデルを入れる |
| モデルの当てはめ時間と獲得関数の最適化時間 | 一巡の計算時間 | 評価時間に近づくなら、手法の負担を見直す |
| seedと初期設計の間の分散 | 結果が初期条件に依存するか | 大きければ、複数のseedで比べる |

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処・切替先 |
|---|---|---|
| 同じ点、近い点を繰り返し提案する | ノイズなしのモデルで不確実性が潰れた。または失敗した領域の近傍を選び続けている | 停止するか、状態（status）と実行可能性のモデルを監査する。失敗を大きな目的値に置き換えない |
| 入力や出力の尺度を変えると、事後分布や提案が大きく崩れる | カーネルの不一致 | 尺度を揃えて再学習する。カーネルを見直す |
| 交差検証の残差が、領域ごとに偏る | カーネルの不一致、非定常な目的関数 | カーネルを見直す。別の代理モデルを検討する |
| 不確実性が小さいのに、高忠実度（high fidelity）での誤差が大きい | 低忠実度と高忠実度の食い違い（model discrepancy） | 共通点で両方を評価し、食い違いをモデル化する |
| 探索空間が条件付き・カテゴリカル | 連続値のカーネルが合わない | 符号化を見直す。[TPE](#/learn/tpe)や専用の代理モデルへ |
| 評価が安価で大量に並列で回せる | 逐次に選ぶ利点が小さい | [Random Search](#/learn/random-search)や集団法へ |
| 観測のばらつきが大きい | noiseが目的値の差より大きい | noiseを明示する。[noiseを含むblack-box（PA013）](#/formulations/PA013)を確認する |

症状のうち、繰り返しの提案は、この例のように気づきやすい合図です。

## コラム: 画面の読み方

[Bayesian Optimization Theater](#/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS)では、次を混同しないようにします。

| 表示 | 意味 |
|---|---|
| observed points | 実際に高価な関数を評価した結果 |
| true objective | 教育用scenarioでだけ既知の関数 |
| surrogate mean | 現在の代理モデルの予測 |
| uncertainty | 代理モデル上の不確実性 |
| acquisition | 次の点を選ぶ基準 |
| incumbent | 観測済みの最良値（best-so-far） |
| next point | 次に実際に評価する候補 |

実務では、真の目的関数（true objective）の曲線は見えません。見えるのは観測とモデルだけです。

教材は、次の順に見ると、情報を一度に抱えずに済みます。

1. Theaterで、観測から次の評価点を選ぶ一巡を追う
2. [獲得関数・noise・Random Searchの比較](#/compare/COMPARE_BO_ACQUISITION_NOISE_BASELINE)で、変えた条件を一つずつ読む
3. [同一costのmulti-fidelity比較](#/compare/COMPARE_BO_MULTIFIDELITY_COST)で、反復の回数でなく支払ったcostを揃える

個別のsensitivity runとbaselineは、比較ページから開けます。

## コラム: 理論・実装default・評価policy・推薦を分ける

ベイズ最適化の核は、観測から代理モデルを更新し、獲得関数で次の評価候補を決めることです。
特定のlibraryが選ぶ既定のカーネルや入力変換は、手法そのものではありません。
noiseの処理は実装ごとに違います。獲得関数の最適化と初期点の数も違います。

BoTorchの公式資料には、既知のfidelityのcostを使う、cost-awareな構成例があります。
ただし、libraryを選んだだけでは、評価費用（cost）のモデルと目標のfidelityは確定しません。
補正するモデルも別に設計します。
libraryのversionと既定値は実装の記録として残し、普遍的な推奨値にはしません。

評価policyはさらに別です。
実行の前に、初期設計と並列workerの数を固定します。低・高fidelityのcostも固定します。
バッチ・非同期、retry、失敗・打ち切り・timeoutの扱いも記録します。
停止条件を、結果を見た後に変更しません。

手法の推薦の優先度は、問題の変数の型と予算から決めます。
noiseの性質も確認します。
失敗の構造と比較の証拠も必要です。
固定された一回の実行の最良値や、libraryの既定値だけで、推薦の順位を上げません。

| 層 | 固定・記録するもの | ここから言えないこと |
| --- | --- | --- |
| method | 代理モデルと獲得関数の役割 | 特定のカーネルが常に適切 |
| implementation | library version、カーネル、変換、最適化の既定値 | 既定値が一般的な推奨 |
| evaluation policy | 初期設計、cost、並列度、失敗、retry、停止 | 反復の回数だけで公平 |
| recommendation | 問題の条件と、複数seedの比較の証拠 | 単一の教材の勝者が常に第一候補 |

## コラム: 代理モデルとfidelityの食い違いを監査する

低忠実度（low fidelity）は、高忠実度（high fidelity）の真値ではありません。
共通点を両方のfidelityで評価し、残差と候補の順位を別々に記録します。
高fidelityで再確認した結果も分けて残します。

[low-fidelity biasのfailure Theater](#/theater/bayesian-optimization/SCENARIO_BO_1D_LOW_FIDELITY_BIAS)では、同じ2候補の順位が、低fidelityと高fidelityで反転します。
これは特定のbiasを持つ最小教材です。
実問題での発生頻度や、補正モデルの性能は示しません。

入力や出力の尺度を変えたとき、事後分布や提案が大きく崩れる場合は、カーネルの不一致を疑います。
交差検証の残差が領域ごとに偏る場合も同様です。
不確実性が小さいのに高fidelityの誤差が大きければ、モデルの食い違いを確認します。

失敗した領域の近くを繰り返し提案する場合は、失敗を大きな目的値へ置き換えません。
評価の状態（status）と、実行可能性のモデルを監査します。
探索空間とretryの方針も確認します。

## コラム: 公平な比較

Random SearchやDifferential Evolutionと比較するときは、次を揃えます。CMA-ESなどの場合も同じです。

- 同じ問題のinstanceと上下限
- 同じ初期設計、またはそのcost
- 同じ目的関数の評価予算
- 同じnoiseと失敗の扱い
- 複数のseed
- wall-clockの負担は別に記録する

単一の軌跡の勝敗を、一般的なrankingにはしません。

## 次に読む

- [高価な低次元評価（PA014）](#/formulations/PA014)：ベイズ最適化が想定する問題の型
- [hyperparameter optimization（PA039）](#/formulations/PA039)：検証損失を高価なblack-box評価として選ぶ場面
- [Random Search](#/learn/random-search)：同じ予算で比べる基準になる、最も単純な探索
- [高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)：条件から手法を比べる
