---
content_id: concept.manifold
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_MANIFOLD
title_ja: 多様体値変数
title_en: Manifold-Valued Variables
summary: 多様体値変数では、球面・直交行列・回転などの集合を解空間として扱い、接空間のstepとretractionで幾何構造を保ちます。
source_ids: [S044, S045, S071]
related_ids: [concept.variable-domain, concept.simplex, family.manifold, riemannian-gradient, riemannian-trust-region]
status: published
last_reviewed: 2026-07-19
---

多様体値変数では、球面・直交行列・回転などの集合を解空間として扱い、接空間のstepとretractionで幾何構造を保ちます。

## 直感: 解は曲がった集合の上にある

多様体（manifold）は、各点の近くでは低次元のEuclidean空間のように見える集合です。変数$x$を単に$\mathbb{R}^n$のvectorとして更新するのではなく、$x\in\mathcal{M}$という集合の上にある点として扱います。

![青緑の球面上の点から接平面へ橙のstepが伸び、曲線の矢印で球面上の新しい点へ戻る模式図](./media/manifold-tangent-retraction.png "接空間で候補を作り、retractionで多様体へ戻す教育用模式図です。sphere以外の集合やmetricの選択までは示しません。")

典型的な集合と自由度は次のとおりです。

| 集合 | 変数の例 | 自由度・注意 |
| --- | --- | --- |
| sphere $S^{n-1}$ | 単位vector、正規化されたembedding | $n-1$。符号やchartの選び方に注意 |
| Stiefel manifold | 直交列を持つmatrix | $X^TX=I$。matrixの成分数より自由度が小さい |
| Grassmann manifold | 部分空間、低次元の基底 | 基底の取り方が違っても同じ部分空間を表す |
| $SO(2)$ / $SO(3)$ | 2D / 3Dの回転 | 行列、quaternion、Lie algebraで表せる |
| SPD manifold | 正定値covariance matrix | 固有値が正。PSDの境界は別の扱いになる |

確率vectorのsimplexも特殊な集合ですが、0の境界にはcornerがあります。したがって、simplexの境界まで扱うときは、滑らかな多様体として無条件に扱わず、[Simplex・確率ベクトル](#/learn/concept.simplex)のprojectionやmirror geometryと照合します。

## Euclidean updateで壊れるもの

無制約のstep $y=x-\eta g$ は、一般には$\mathcal{M}$の外へ出ます。sphereなら$\|y\|_2=1$が失われます。直交行列なら$Y^TY=I$が崩れ、rotation matrixならdeterminantが1でなくなる場合があります。SPD matrixなら対称性や正定値性を失う可能性があります。

| 破綻する条件 | その場で見る量 | 単純な修正が意味すること |
| --- | --- | --- |
| sphere | $\|x\|_2-1$ | normalizeは球面上へ戻すが、選んだmetricのexact geodesicとは限らない |
| Stiefel | $\|X^TX-I\|$ | QRやpolar factorはretraction候補だが、実装とmetricを確認する |
| $SO(3)$ | $R^TR-I$、$\det R-1$ | 行列projectionとLie algebra updateは別の更新則である |
| SPD | 対称性、最小固有値 | CholeskyはSPDの内部を表すが、PSD境界を直接表さない |

成分ごとのclipやpenaltyだけでは、集合の構造を保てるとは限りません。修正後の点がfeasibleでも、修正によって目的関数の変化やstepの意味が変わるため、projection distanceも記録します。

## 接空間から集合へ戻す

多様体上の現在点$x$では、まず接空間$T_x\mathcal{M}$に勾配を射影します。接空間のvector$\xi$を作ったら、次のいずれかで集合上の点へ戻します。

- **parameterization**: quaternion、Cholesky、低次元chartなどで、別の変数から$\mathcal{M}$を表します。
- **projection**: ambient spaceの候補を集合へ戻します。非一意性やprojection costを確認します。
- **retraction**: $x$と接vector$\xi$から、近傍の集合上の点$R_x(\xi)$を作ります。
- **exponential map**: 選んだRiemannian metricのgeodesicを厳密にたどります。retractionと同じとは限りません。

```python
import numpy as np


def sphere_retraction(point: np.ndarray, tangent_step: np.ndarray) -> np.ndarray:
    candidate = point + tangent_step
    return candidate / np.linalg.norm(candidate)


point = np.array([1.0, 0.0, 0.0])
ambient_gradient = np.array([0.2, -1.0, 0.4])
tangent_gradient = ambient_gradient - point * np.dot(point, ambient_gradient)
next_point = sphere_retraction(point, -0.1 * tangent_gradient)

assert np.isclose(np.linalg.norm(next_point), 1.0)
```

この例はsphereのnormalize retractionだけを示します。SPD、Stiefel、Grassmann、回転群では、接空間射影・metric・retractionの組を対応させます。自作する場合は、有限差分によるgradient checkと、retraction後の構造残差を別々に確認します。

## 表現の非一意性と特異点

多様体の式を満たしても、表現が一意とは限りません。

- quaternionの$q$と$-q$は同じrotationを表します。
- Grassmannでは、同じ部分空間を異なるbasis matrixが表します。
- rotationのlocal chartは、特定の角度付近で不安定になる場合があります。
- SPDのCholesky parameterizationは、正定値の内部を保ちますが、固有値0のPSD境界を同じ形では表せません。
- fixed-rank matrixは、rankが変わる場所で同じ滑らかな多様体として扱えません。

このため、座標上の距離やparameterの差を、そのまま解の差と解釈しません。回転ならgeodesic distance、部分空間ならprincipal angleなど、対象に合う診断を選びます。

## feasible iterateと収束は別の判定

retractionで毎回feasibleな点を作れても、最適性や大域性が保証されたわけではありません。少なくとも次を分けて記録します。

| 判定 | 主に見るもの | 分かること |
| --- | --- | --- |
| 幾何feasibility | norm、直交残差、determinant、最小固有値 | 反復点が指定した集合にいるか |
| 一階の進展 | Riemann gradient norm、objective、geodesic step | 局所的な停止条件へ近づいているか |
| 二階法の判断 | actual / predicted reduction、trust-region radius | modelがstepを予測できているか |
| 表現の健全性 | chart切替、sign convention、condition number | 座標の問題を解の問題と取り違えていないか |

切替の兆候は、構造残差の増大、retraction errorの蓄積、chart近傍でのstep不安定、初期点による結果の大きな差です。[Riemann勾配法](#/learn/riemannian-gradient)は一次法の入口、[Riemann trust-region法](#/learn/riemannian-trust-region)は二階情報や局所的な頑健性を確認したいときの候補です。

::: warning
各反復のfeasibilityは、局所解・大域最適性・連続モデルでの安全性を保証しません。多様体の選択、metric、retraction、停止条件、実装の数値誤差を分けて検証します。
:::

## 次に読む

変数の集合をsolver選択へつなぐ全体像は[変数のdomain](#/learn/concept.variable-domain)で確認できます。手法の選び分けは[Riemann多様体最適化の選び分け](#/learn/family.manifold)へ進み、simplexの境界を含む比率問題は[Simplex・確率ベクトル](#/learn/concept.simplex)と比較します。
