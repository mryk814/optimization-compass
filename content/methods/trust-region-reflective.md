---
content_id: trust-region-reflective
kind: method
method_id: M_TRUST_REGION_REFLECTIVE
title_ja: Trust Region Reflective法
title_en: Trust Region Reflective
summary: bounds付き非線形最小二乗で、境界までの距離に応じてtrust regionを変形し、反射方向も使って局所解を探すGauss–Newton系手法です。
source_ids: [S003, S096]
related_ids: [least-squares, gauss-newton, trust-krylov, lbfgsb, slsqp]
visualization_ids: [exponential-fit-trf, exponential-fit-trf-poor-init]
comparison_ids: [COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS]
status: published
last_reviewed: 2026-09-30
---

bounds付き非線形最小二乗で、境界までの距離に応じてtrust regionを変形し、反射方向も使って局所解を探すGauss–Newton系手法です。

## 30秒でつかむ

柵で囲われた庭を、暗がりの中で歩く場面を想像してください。足元の地面の傾きは分かりますが、柵は見えません。
柵に近いほど歩幅を小さくし、柵の手前で向きを変えれば、柵にぶつからずに進めます。Trust Region Reflective法（TRF）は、パラメータの上下限を柵として、この歩き方をします。

- **見るもの**: 残差ベクトル、Jacobian、勾配、上下限までの距離
- **動かすもの**: 現在点と、信頼領域（trust region）の形。候補は、Gauss–Newtonの一手と反射した一手
- **前進の判断**: 実際の目的値の低下と、局所モデルが予測した低下が一致すること

恐れるのは、悪いJacobianとランク不足です。パラメータの尺度の不一致と、境界上での停滞も兆候になります。

## 一手の意味

非線形最小二乗は、残差ベクトル $r(x)$ から次の目的を最小化します。

$$
F(x)=\frac{1}{2}\lVert r(x)\rVert_2^2
$$

局所モデルは、[Gauss–Newton法](#/learn/gauss-newton)と同じです。Jacobian $J(x)$ で、近くの残差を線形化します。

$$
r(x+p)\approx r(x)+J(x)p
$$

TRFは、このモデルを信頼領域の内側で改善します。
信頼領域は、モデルを信じてよい範囲です。通常の球のまま使うのではなく、上下限までの距離と勾配の向きに応じて尺度を変えます。境界へ直接突っ込む一手を避けるためです。

### 反射方向を使う理由

候補の方向が境界へ向かうとき、境界で反射した方向も探索の候補にします。
これは、値を境界でクリップ（clip）するだけの処理とは異なります。

SciPyの実装は、理論上の条件を満たすために、反復点を境界の少し内側（strictly feasible）に保ちます。
そのため、終了時の `active_mask` は完全な等号の判定ではありません。許容誤差に基づく判定です。

この設計で、境界の近くの解を扱いながら、実行可能領域の内部で局所モデルを更新できます。

### Jacobianの規模と疎性

SciPyでは、Jacobianの表現に応じて、信頼領域の部分問題の解き方が変わります。

| 状況 | 主な内部求解 |
|---|---|
| 密で中小規模 | SVDに近い厳密な信頼領域の求解 |
| 大規模で疎 | LSMRによる近似Gauss–Newton方向と、尺度を付けた勾配の2次元部分空間 |
| `jac_sparsity` を指定 | 疎な有限差分とLSMRの経路を利用 |

同じ `method="trf"` でも、Jacobianの型・疎性・ランクにより、計算量と診断方法が変わります。

## 小さな例

[Gauss–Newton法](#/learn/gauss-newton)と同じ、指数減衰の当てはめに、上限を付けます。
時刻 $t=0,1,2,3,4$ の観測 $y=5.1,\,3.0,\,1.9,\,1.1,\,0.7$ に、モデル $y=a\,e^{-kt}$ を当てはめます。
初期値は $(a,k)=(1,\,0.1)$ で、範囲は $0\le a\le 10$、$0\le k\le 0.4$ とします。

上下限がなければ、解は $(a,k)\approx(5.079,\,0.505)$ で、目的値は約 $0.0041$ です。ところが $k$ の上限 $0.4$ は、この解の外にあります。
上限つきの解は境界上の $(4.733,\,0.4)$ になり、目的値は約 $0.194$ に上がります。

SciPy 1.18のTRFが受け入れた点を、反復ごとに示します。手法の内部の詳細はバージョンで変わり得るので、数値は目安です。

| 反復 | $a$ | $k$ | 目的値 | 一手の長さ | 最適性（optimality） |
|---:|---:|---:|---:|---:|---:|
| 0 | 1.000 | 0.1000 | 11.25 | | 64.5 |
| 1 | 2.365 | 0.1200 | 4.590 | 1.37 | 20.7 |
| 2 | 3.920 | 0.3673 | 0.7781 | 1.57 | 7.74 |
| 3 | 4.452 | 0.3826 | 0.3087 | 0.533 | 2.14 |
| 4 | 4.691 | 0.39965 | 0.1964 | 0.239 | 0.387 |
| 5 | 4.731 | 0.39999 | 0.19362 | 0.0402 | 0.0188 |
| 6 | 4.7329 | 0.4000 | 0.19359 | 0.00203 | $9.9\times10^{-5}$ |
| 7 | 4.7329 | 0.4000 | 0.19359 | $1.1\times10^{-5}$ | $2.4\times10^{-9}$ |

表の読み方です。

- 上限のない場合、Gauss–Newton法の最初の一手は $k$ を $0.1$ から $1.15$ へ動かそうとします。TRFの反復1は、$k$ を $0.12$ までしか動かしません。
- $k$ は、上限 $0.4$ の手前から近づきます。$0.3673 \to 0.3826 \to 0.39965 \to 0.39999$ と、上限を超えずに寄っていきます。
- 一方、$a$ は上限 $10$ から遠いので、ほぼ自由に動きます。

最後は `active_mask` が $k$ の上限で立ちます。解は境界上にあり、残る自由な $a$ の方向では勾配がほぼ $0$ です。
目的値が上下限なしの $0.0041$ から $0.194$ に上がっていることは、上限がデータと衝突している合図です。この上限が物理的に正しいかを、先に確認します。

## 向く条件・避ける条件

先に、次の項目を確認します。

| 項目 | 確認内容 |
|---|---|
| 定式化 | 目的を、観測ごとの残差ベクトルとして自然に表せるか |
| 上下限 | 上下限が、物理的・統計的に意味を持つか |
| Jacobian | 解析式、自動微分、または安定した差分で得られるか |
| 尺度 | パラメータごとの単位・桁が大きく異ならないか |
| 疎性 | 大規模な問題で、Jacobianの疎構造や `LinearOperator` を渡せるか |
| 目標 | 上下限の内側の局所解と、一階の診断で十分か |

一般の非線形制約や離散変数を扱う問題には、そのまま適用しません。
大域最適性の証明が必要な場合も対象外です。

向きやすい条件です。

- 上下限つきの非線形最小二乗である（[非線形最小二乗](#/learn/concept.nonlinear-least-squares)、[上下限つきの滑らかな最小化](#/formulations/PA008)）
- 残差とJacobianを直接扱える
- 大規模で疎なJacobianを持つパラメータ推定である
- 頑健な損失で、外れ値の影響を弱めたい
- LM法では上下限を扱えない

避ける、または切り替える条件です。

- 一般の非線形制約が本質である → SLSQP、trust-constr、内点法のNLPへ
- 残差への分解が不自然なスカラー目的である → [L-BFGS-B](#/learn/lbfgsb)
- 不連続、離散、モデル化されていない強いノイズがある
- 大域最適の証明が必要である
- 上下限が単なる推測で、解を人工的に固定してしまう

### 他の手法との違い

| 手法 | 主な対象 | 上下限 | 残差構造 | 注意点 |
|---|---|---:|---:|---|
| LM | 小規模・上下限なしの最小二乗 | なし | 使う | 解の近くで効率的だが、上下限と疎なJacobianに非対応 |
| TRF | 上下限つき、またはなしの最小二乗 | あり | 使う | SciPyの既定。大規模で疎にも対応するが、局所法 |
| dogbox | 小規模で上下限つきの最小二乗 | あり | 使う | ランク不足のJacobianでは遅くなりやすい |
| L-BFGS-B | 一般のスカラー目的 | あり | 潰してしまう | 残差別の診断や頑健な損失の構造を直接使わない |

LM法（[非線形最小二乗とLevenberg–Marquardt法](#/learn/least-squares)）は、局所的な最小二乗モデルを重視します。dogboxは矩形の信頼領域を使います。
L-BFGS-Bは、上下限つきの一般目的関数に対する準Newton更新です。非線形最小二乗の残差構造を直接使うTRFとは、観測する情報が異なります。

`least_squares` で解ける問題を、理由なくスカラーの損失に潰して `minimize` へ渡すと、残差・Jacobian・疎性の情報を失う場合があります。

## Python

次の例は、上の小さな例と同じ問題を、上限つきのTRFで解きます。

```python
import numpy as np
from scipy.optimize import least_squares

t = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
y = np.array([5.1, 3.0, 1.9, 1.1, 0.7])


def residuals(p: np.ndarray) -> np.ndarray:
    a, k = p
    return a * np.exp(-k * t) - y


def jacobian(p: np.ndarray) -> np.ndarray:
    a, k = p
    e = np.exp(-k * t)
    return np.column_stack([e, -a * t * e])


result = least_squares(
    residuals,
    x0=[1.0, 0.1],
    jac=jacobian,
    bounds=([0.0, 0.0], [10.0, 0.4]),
    method="trf",
)

print(result.x)
# [4.73287691 0.4       ]
print(result.cost, result.optimality, result.active_mask)
# 0.19358641280907976 2.4e-09 [0 1]
print(result.status, result.message, result.nfev, result.njev)
# 1 `gtol` termination condition is satisfied. 8 8

assert result.success
assert np.isclose(result.x[1], 0.4, atol=1e-6)
```

この例では、上下限なしの解 $k\approx 0.505$ が上限 $0.4$ の外にあります。そのため、解は上限の境界 `x[1] = 0.4` 上に移ります。
`active_mask` の `[0 1]` は、$a$ は自由で、$k$ が上限で止まっていることを表します。

## 診断値

- `cost` と残差のパターン
- `optimality`
- `active_mask`
- `nfev` と `njev`
- `status` と `message`
- Jacobianのランク、または特異値
- 異なる初期値からの解

## 失敗・切替の兆候

- `optimality` が下がらず、active boundが頻繁に入れ替わる → 上下限か尺度が合っていない → 上下限と尺度を確認する
- ランク不足が強い → 効果の同じパラメータがある → パラメータ化、正則化、実験設計を見直す
- 上下限なしの小規模問題で、評価回数を減らしたい → LM法と比べる
- 小規模で上下限つきの問題でTRFが重い → dogboxを同じ予算で比べる
- 一般制約が必要 → SLSQP、trust-constr、内点法のNLPへ移る
- 多数の初期値で異なる解に着く → 大域探索か識別可能性を確認する

## コラム: 診断probeの出力を見る

[TRF適用条件の共通診断probe](#/traces/exponential-fit-trf)では、推定値と残差のノルム、Jacobianのランクを同じ評価の軸で追います。
[悪い初期値から始めるprobe](#/traces/exponential-fit-trf-poor-init)では、同じ観測量で初期値への依存を確認します。
どちらもTRFの実行結果ではありません。
[solver条件の比較](#/compare/COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS)で、上下限への対応と残差ベクトルの入口の違いを読むための、固定の教材です。

![同じ指数減衰fitと12回の評価予算で、通常初期値と悪い初期値からsolver-independent診断probeを実行したresidual norm履歴。両方とも残差は下がるが、開始値と途中の経路が異なる。](./media/trf-probe-execution.svg "Optimization Compassのdamped Gauss–Newton診断probeを実行した結果です。初期値感度を読む教材であり、SciPy TRFの内部iterationや性能を示しません。")

線が下がったことだけでなく、出発点と途中の曲がり方を見ます。この図をTRFの収束履歴としては扱いません。初期値を変えて、同じ診断量を追う必要性を示すために使います。

## コラム: defaultは推薦順位ではない

ライブラリの既定（default）は、APIが対象とする広い問題で壊れにくい選択を提供するためのものです。
利用者の問題の大きさ、Jacobian、上下限を確認した最終推薦とは異なります。
ノイズと必要な保証も、別に確認します。

SciPyでは、`least_squares` の既定はTRFです。
一方、`curve_fit` の選び方は条件で変わります。上下限がなければLM、上下限を与えるとTRFです。
この条件はライブラリのバージョンとAPIごとに記録し、手法の一般的な性能ランキングとして扱いません。

## 次に読む

- [非線形最小二乗とLevenberg–Marquardt法](#/learn/least-squares)：残差の作り方と識別可能性
- [Gauss–Newton法](#/learn/gauss-newton)：曲率近似の基礎
- [非線形最小二乗](#/learn/concept.nonlinear-least-squares)・[上下限つきの滑らかな最小化](#/formulations/PA008)：この手法が解く問題の標準形
- [制約付き非線形最適化の選び分け](#/learn/family.constrained-nlp)：一般制約がある場合
