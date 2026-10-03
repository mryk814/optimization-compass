---
content_id: concept.spd-matrix-geometry
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_MANIFOLD
title_ja: SPD行列の表現と境界
title_en: Representations and Boundaries of SPD Matrices
summary: SPD 行列では、正定値の内部とPSD境界を分け、表現方法と更新則が保つ範囲を診断します。
source_ids: [S044, S071, S108]
prerequisites: [concept.manifold]
related_ids: [concept.manifold, concept.simplex, family.manifold, riemannian-gradient, riemannian-trust-region]
status: published
last_reviewed: 2026-07-24
---

SPD 行列では、正定値の内部とPSD境界を分け、表現方法と更新則が保つ範囲を診断します。

## 直感: 境界を越えると正定値ではなくなる

SPD 行列の固有値はすべて正です。
更新後に最小固有値が0へ近づけば、行列は半正定値（PSD）境界へ近づきます。
負になれば、SPDの集合から外れています。

次の図では、SPDの内部から出た試行を範囲内への切り詰めで戻す流れを見ます。

![青緑のSPD領域内の点から橙の矢印が赤い領域外の試行へ進み、別の青緑の点へ修正される模式図](./media/spd-boundary-repair.svg "SPD内部から外れた試行を修正して戻す関係だけを示す模式図です。修正が元のステップや選んだ計量と同じであることは示しません。")

範囲内への切り詰め後の点は可行でも、元のステップと同じ一歩ではありません。
正定値性と更新の意味を分けて読みます。

## 定義と自由度

$n\times n$の対称正定値（SPD）行列が属する集合は次のとおりです。

$$
\mathbb{S}_{++}^n
=\{X\in\mathbb{R}^{n\times n}\mid X=X^{\mathsf T},\ z^{\mathsf T}Xz>0\ \text{for all }z\ne0\}
$$

独立成分は$n(n+1)/2$個です。
共分散、拡散テンソル、計量行列などで現れます。

PSD 行列 $\mathbb{S}_+^n$は固有値0を許します。
ランクが変わり得るPSD境界を、SPDの内部と同じ滑らかな多様体として無条件に扱いません。

## ユークリッド空間での更新が破るもの

対称なSPD 行列 $X$へ周囲の空間の勾配 $G$を使ったステップを適用します。

$$
X_{trial}=X-\eta G
$$

この試行は、対称性や正定値性を保つとは限りません。
少なくとも次の四つを別々に測ります。

| 診断 | 例 | 読み方 |
| --- | --- | --- |
| 対称性の誤差 | $\lVert X-X^{\mathsf T}\rVert_F$ | 行列が対称か |
| 最小固有値 | $\lambda_{min}(X)$ | 0より十分大きいか |
| 条件数 | $\lambda_{max}/\lambda_{min}$ | 境界近傍で数値的に不安定でないか |
| 射影修正量 | $\lVert X_{projected}-X_{trial}\rVert_F$ | 周囲の空間のステップをどれだけ修正したか |

小さな固有値を一定値へ切り詰めれば、SPDへ戻せます。
ただし、範囲内への切り詰め前後で目的関数とステップの意味が変わります。
射影後の可行性だけを見て、元のステップと同じ一歩だったとは解釈しません。

## 表現方法を選ぶ

### Cholesky

$X=LL^{\mathsf T}$と置きます。
$L$を下三角行列とし、対角を正に保てばSPDの内部に留まります。
例えば、対角を$\exp(d_i)$で表せます。

- 長所: 正定値性を構成で保てる
- 注意: 因子の尺度と数値条件が最適化の幾何へ入る
- 境界: 有限の$d_i$では厳密に0の固有値を直接表さない

### 行列指数関数

対称行列 $S$から$X=\exp(S)$と置く方法も、SPDの内部を表します。
行列対数関数と組み合わせる対数ユークリッド計量は一つの選択肢です。
アフィン不変リーマン計量とは別の計量です。

### リーマン更新

SPD多様体に計量を選び、接ベクトルからレトラクションまたは指数写像で戻します。
計量、レトラクション、ベクトル移動を実験条件として固定します。
Pymanoptの`SymmetricPositiveDefinite`が提供する幾何は、利用バージョンの公式リファレンスで確認します。

## 固定2×2 共分散で診断する

次の目標行列はSPDです。

$$
X_\star=\begin{bmatrix}2.0&0.6\\0.6&1.0\end{bmatrix}
$$

この最小例では、固有値・対称性・目的関数を一緒に確認します。

```python
import numpy as np

target = np.array([[2.0, 0.6], [0.6, 1.0]])
cholesky = np.linalg.cholesky(target)
reconstructed = cholesky @ cholesky.T

assert np.allclose(reconstructed, target)
assert np.linalg.eigvalsh(reconstructed).min() > 0.0
```

この例は目標行列を分解するだけで、最適化アルゴリズムの性能を示しません。
比較条件には、同じ初期行列・目的関数・計量・予算・許容誤差を使います。
各評価では、目的関数・最小固有値・条件数・ステップノルムを記録します。

## 境界と非一意性

- Choleskyの正の対角はSPD内部を保ちますが、PSD境界を有限パラメータで直接表しません。
- 固定ランク PSDの因子 $X=YY^{\mathsf T}$では、$Q$を直交行列とすると、$YQ$も同じ$X$を表す商空間の非一意性があります。
- 固有値の切り詰めは可行性を回復する修正であり、選んだリーマン計量の指数写像とは限りません。
- 条件数が増大したら、目的の改善と数値的な境界接近を分けて判断します。

::: warning
可行なSPD 反復点は、共分散モデルの妥当性を保証しません。
PSD境界でのランク選択、局所解、大域最適性も保証しません。
表現方法、計量、境界方針を明示します。
:::

## 次に読む

[多様体値変数](#/learn/concept.manifold)で共通の接空間とレトラクションを確認できます。
[Riemann多様体最適化の選び分け](#/learn/family.manifold)では一次法と信頼領域法を比較します。
比率ベクトルの境界は[単体・確率ベクトル](#/learn/concept.simplex)で確認できます。
そこでは射影とミラー法の幾何を区別します。
