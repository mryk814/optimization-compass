---
content_id: concept.spd-matrix-geometry
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_MANIFOLD
title_ja: SPD matrixの表現と境界
title_en: Representations and Boundaries of SPD Matrices
summary: SPD matrixでは対称性・最小固有値・condition numberを診断し、各parametrizationとRiemannian updateが表す範囲を区別します。
source_ids: [S044, S071, S108]
prerequisites: [concept.manifold]
related_ids: [concept.manifold, concept.simplex, family.manifold, riemannian-gradient, riemannian-trust-region]
status: published
last_reviewed: 2026-07-19
---

SPD matrixでは対称性・最小固有値・condition numberを診断し、各parametrizationとRiemannian updateが表す範囲を区別します。

Cholesky、matrix exponential、Riemannian updateが表す範囲も区別します。

## Set definitionと自由度

$n\times n$のsymmetric positive-definite（SPD）matrixは、

$$
\mathbb{S}_{++}^n
=\{X\in\mathbb{R}^{n\times n}\mid X=X^{\mathsf T},\ z^{\mathsf T}Xz>0\ \text{for all }z\ne0\}
$$

に属します。独立成分は$n(n+1)/2$個です。covariance、diffusion tensor、metric matrixなどで現れます。

positive semidefinite（PSD）matrix $\mathbb{S}_+^n$は固有値0を許します。SPDの内部と、rankが変わり得るPSD境界を、一つの滑らかな多様体として無条件に扱いません。

## Naive Euclidean updateが壊すもの

対称なSPD matrix $X$にambient gradient $G$をそのまま足した

$$
X_{trial}=X-\eta G
$$

は、対称性や正定値性を保つとは限りません。少なくとも次を別々に測ります。

| 診断 | 例 | 読み方 |
| --- | --- | --- |
| symmetry error | $\lVert X-X^{\mathsf T}\rVert_F$ | matrixが対称か |
| minimum eigenvalue | $\lambda_{min}(X)$ | 0より十分大きいか |
| condition number | $\lambda_{max}/\lambda_{min}$ | 境界近傍で数値的に不安定でないか |
| projection correction | $\lVert X_{projected}-X_{trial}\rVert_F$ | ambient stepをどれだけ修正したか |

小さなeigenvalueを一定値へclipすればSPDへ戻せますが、clip前後でobjectiveとstepの意味が変わります。projection後のfeasibilityだけを見て、元のgradient stepと同じ一歩だったとは解釈しません。

## Parametrizationを選ぶ

### Cholesky

$X=LL^{\mathsf T}$と置き、$L$をlower triangular、対角を正に保てばSPDの内部に留まります。例えば対角を$\exp(d_i)$で表せます。

- 長所: positive definitenessをconstructionで保てる
- 注意: factorのscaleとconditionがoptimization geometryへ入る
- 境界: 有限の$d_i$ではexact zero eigenvalueを直接表さない

### Matrix exponential

対称matrix $S$から$X=\exp(S)$と置く方法もSPDの内部を表します。
matrix logarithmと組み合わせるlog-Euclidean metricは一つの選択肢です。
affine-invariant Riemannian metricとは別のmetricです。

### Riemannian update

SPD manifoldにmetricを選び、接vectorからretractionまたはexponential mapで戻します。metric、retraction、vector transportを実験条件として固定します。Pymanoptの`SymmetricPositiveDefinite`が提供するgeometryも、利用versionの公式referenceで確認します。

## 固定2×2 covariance例

次のtargetはSPDです。

$$
X_\star=\begin{bmatrix}2.0&0.6\\0.6&1.0\end{bmatrix}
$$

固有値、対称性、目的関数を一緒に確認する最小例です。

```python
import numpy as np

target = np.array([[2.0, 0.6], [0.6, 1.0]])
cholesky = np.linalg.cholesky(target)
reconstructed = cholesky @ cholesky.T

assert np.allclose(reconstructed, target)
assert np.linalg.eigvalsh(reconstructed).min() > 0.0
```

この例はtargetをfactorizeするだけで、optimization algorithmの性能を示しません。
比較では、同じinitial matrix・objective・metric・budget・toleranceを固定します。
各evaluationでobjective・minimum eigenvalue・condition number・step normを記録します。

## Boundaryと非一意性

- Choleskyの正の対角はSPD内部を保ちますが、PSD境界を有限parameterで直接表しません。
- fixed-rank PSD factor $X=YY^{\mathsf T}$では、$Q$を直交行列とすると、$YQ$も同じ$X$を表すquotientの非一意性があります。
- eigenvalue clippingはfeasibility repairであり、選んだRiemannian metricのexponential mapとは限りません。
- condition numberが増大したら、objectiveの改善と数値的な境界接近を分けて判断します。

::: warning
feasibleなSPD iterateは、covariance modelの妥当性を保証しません。
PSD境界でのrank選択や、局所解・大域最適性も保証しません。
representation、metric、boundary policyを明示します。
:::

## 次に読む

[多様体値変数](#/learn/concept.manifold)で共通の接空間とretractionを確認できます。
[Riemann多様体最適化の選び分け](#/learn/family.manifold)では一次法とtrust-region法を比較します。
比率vectorのboundaryは[Simplex・確率ベクトル](#/learn/concept.simplex)で確認できます。
そこではprojectionとmirror geometryを区別します。
