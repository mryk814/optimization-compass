---
content_id: concept.spd-matrix-geometry
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_MANIFOLD
title_ja: SPD matrixの表現と境界
title_en: Representations and Boundaries of SPD Matrices
summary: SPD matrixでは、正定値の内部とPSD境界を分け、表現方法と更新則が保つ範囲を診断します。
source_ids: [S044, S071, S108]
prerequisites: [concept.manifold]
related_ids: [concept.manifold, concept.simplex, family.manifold, riemannian-gradient, riemannian-trust-region]
status: published
last_reviewed: 2026-07-24
---

SPD matrixでは、正定値の内部とPSD境界を分け、表現方法と更新則が保つ範囲を診断します。

## 直感: 境界を越えると正定値ではなくなる

SPD matrixの固有値はすべて正です。
更新後に最小固有値が0へ近づけば、matrixはpositive semidefinite（PSD）境界へ近づきます。
負になれば、SPDの集合から外れています。

次の図では、SPDの内部から出たtrialをclipで戻す流れを見ます。

![青緑のSPD領域内の点から橙の矢印が赤い領域外のtrialへ進み、別の青緑の点へ修正される模式図](./media/spd-boundary-repair.svg "SPD内部から外れたtrialを修正して戻す関係だけを示す模式図です。修正が元のstepや選んだmetricと同じであることは示しません。")

clip後の点はfeasibleでも、元のstepと同じ一歩ではありません。
正定値性と更新の意味を分けて読みます。

## 定義と自由度

$n\times n$の対称正定値（symmetric positive-definite; SPD）matrixが属する集合は次のとおりです。

$$
\mathbb{S}_{++}^n
=\{X\in\mathbb{R}^{n\times n}\mid X=X^{\mathsf T},\ z^{\mathsf T}Xz>0\ \text{for all }z\ne0\}
$$

独立成分は$n(n+1)/2$個です。
covariance、diffusion tensor、metric matrixなどで現れます。

PSD matrix $\mathbb{S}_+^n$は固有値0を許します。
rankが変わり得るPSD境界を、SPDの内部と同じ滑らかな多様体として無条件に扱いません。

## Euclidean updateが破るもの

対称なSPD matrix $X$へambient gradient $G$を使ったstepを適用します。

$$
X_{trial}=X-\eta G
$$

このtrialは、対称性や正定値性を保つとは限りません。
少なくとも次の四つを別々に測ります。

| 診断 | 例 | 読み方 |
| --- | --- | --- |
| symmetry error | $\lVert X-X^{\mathsf T}\rVert_F$ | matrixが対称か |
| minimum eigenvalue | $\lambda_{min}(X)$ | 0より十分大きいか |
| condition number | $\lambda_{max}/\lambda_{min}$ | 境界近傍で数値的に不安定でないか |
| projection correction | $\lVert X_{projected}-X_{trial}\rVert_F$ | ambient stepをどれだけ修正したか |

小さな固有値を一定値へclipすれば、SPDへ戻せます。
ただし、clip前後で目的関数とstepの意味が変わります。
projection後のfeasibilityだけを見て、元のstepと同じ一歩だったとは解釈しません。

## 表現方法を選ぶ

### Cholesky

$X=LL^{\mathsf T}$と置きます。
$L$をlower triangularとし、対角を正に保てばSPDの内部に留まります。
例えば、対角を$\exp(d_i)$で表せます。

- 長所: positive definitenessをconstructionで保てる
- 注意: factorのscaleとconditionがoptimization geometryへ入る
- 境界: 有限の$d_i$ではexact zero eigenvalueを直接表さない

### 行列指数関数（matrix exponential）

対称matrix $S$から$X=\exp(S)$と置く方法も、SPDの内部を表します。
matrix logarithmと組み合わせるlog-Euclidean metricは一つの選択肢です。
affine-invariant Riemannian metricとは別のmetricです。

### Riemannian update

SPD manifoldにmetricを選び、接vectorからretractionまたはexponential mapで戻します。
metric、retraction、vector transportを実験条件として固定します。
Pymanoptの`SymmetricPositiveDefinite`が提供するgeometryは、利用versionの公式referenceで確認します。

## 固定2×2 covarianceで診断する

次のtargetはSPDです。

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

この例はtargetをfactorizeするだけで、optimization algorithmの性能を示しません。
比較条件には、同じinitial matrix・目的関数・metric・budget・toleranceを使います。
各evaluationでは、目的関数・minimum eigenvalue・condition number・step normを記録します。

## 境界と非一意性

- Choleskyの正の対角はSPD内部を保ちますが、PSD境界を有限parameterで直接表しません。
- fixed-rank PSD factor $X=YY^{\mathsf T}$では、$Q$を直交行列とすると、$YQ$も同じ$X$を表すquotientの非一意性があります。
- eigenvalue clippingはfeasibility repairであり、選んだRiemannian metricのexponential mapとは限りません。
- condition numberが増大したら、objectiveの改善と数値的な境界接近を分けて判断します。

::: warning
feasibleなSPD iterateは、covariance modelの妥当性を保証しません。
PSD境界でのrank選択、局所解、大域最適性も保証しません。
表現方法、metric、boundary policyを明示します。
:::

## 次に読む

[多様体値変数](#/learn/concept.manifold)で共通の接空間とretractionを確認できます。
[Riemann多様体最適化の選び分け](#/learn/family.manifold)では一次法とtrust-region法を比較します。
比率vectorの境界は[Simplex・確率ベクトル](#/learn/concept.simplex)で確認できます。
そこではprojectionとmirror geometryを区別します。
