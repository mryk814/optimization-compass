---
content_id: concept.simplex
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_SIMPLEX
title_ja: Simplex・確率ベクトル
title_en: Simplex and Probability Vectors
summary: Simplexは非負の成分の和が1になる集合で、配合比・確率・資源配分を最適化するときに、可行性を保つ更新則と境界の意味を明確にします。
source_ids: [S055, S056, S066]
related_ids: [projected-gradient, mirror-descent, family.manifold]
status: published
last_reviewed: 2026-07-18
---

Simplexは非負の成分の和が1になる集合で、配合比・確率・資源配分を最適化するときに、可行性を保つ更新則と境界の意味を明確にします。

## 直感: 比率の集合

$n$成分のprobability simplexは、非負の成分の和が1になる集合です。

$$
\Delta^{n-1}=\left\{x\in\mathbb{R}^n \mid x_i\geq0,\ \sum_{i=1}^{n}x_i=1\right\}.
$$

成分は、各選択肢への確率、混合比、予算配分、attention weightなどを表します。自由度は$n$ではありません。和が1という等式制約を除いた$n-1$です。

ここでいうsimplexは、LPのbasisを辿る**Primal Simplex法**や、Nelder–Meadの探索点を並べた**単体**とは別の意味です。このページは「解ベクトルが比率として存在する集合」を扱います。

![青緑の三角形の内部がsimplexの可行領域で、外側の候補が橙の矢印で辺上の青緑の点へ戻される模式図](./media/simplex-feasible-geometry.png "外側の候補をsimplexへ戻す操作と、内部・境界の違いを示す教育用模式図です。")

## Euclidean stepで失われるもの

無制約の勾配step $y=x-\eta\nabla f(x)$ は、一般に負の成分を作ります。成分の和も1からずれます。たとえば`[-0.1, 0.6, 0.5]`は合計こそ1でも、確率・配合比としては不正です。

`y / y.sum()`のような正規化も万能ではありません。負の成分を直せず、和が0に近いと不安定です。最も近いsimplex上の点を選ぶ操作でもありません。解釈できる比率を各反復で保ちたいなら、更新後にどの方法で集合へ戻すかを最初に決めます。

| 方策 | 常に保つもの | 境界の0を表せるか | 主な注意 |
| --- | --- | ---: | --- |
| Euclidean projection | 非負・和1 | はい | projectionの費用とactive faceを確認 |
| softmax parameterization | 正・和1 | 通常はいいえ | logitに同じ定数を足しても解が同じ |
| entropy mirror update | 正・和1（正の初期値なら） | 通常はいいえ | log / underflow、mirror mapとstep schedule |
| penaltyだけを加える | 反復中の可行性は保証しない | 場合による | penalty係数と残る違反を別に診断 |

## Projectionとparameterizationを分けて選ぶ

Euclidean projectionは、更新候補$y$に最も近いsimplex上の点を求めます。

$$
\Pi_{\Delta}(y)=\arg\min_{x\in\Delta^{n-1}}\|x-y\|_2^2.
$$

この方法では、最適解がある成分をちょうど0にするなら、その境界へ到達できます。「混合物から成分を完全に外す」「配分先をゼロにする」ことが必要なら、projectionは自然な候補です。

[射影勾配法](#/learn/projected-gradient)では、このprojectionを各勾配stepの後に行います。

一方、logit $z\in\mathbb{R}^n$ をsoftmaxで変換するparameterizationは

$$
x_i=\frac{\exp(z_i)}{\sum_j\exp(z_j)}
$$

により内部点を保ちます。`z`に同じ定数を加えても$x$は変わらないため、logit自体の一意性はありません。有限のlogitでは$x_i=0$を厳密には表せません。これは欠点ではありません。境界の解を必要とするかどうかで選ぶ性質です。

## Mirror Descentは比率のgeometryを使う

[Mirror Descent](#/learn/mirror-descent)では、negative entropyのようなmirror mapを使い、simplex上でmultiplicativeな更新を作れます。正の初期値から始めるexponentiated-gradient型の更新は、正の成分と和1を保ちます。そのため、確率・online allocationではEuclidean距離より自然な場合があります。

ただし、entropy geometryが常に優れるわけではありません。boundaryの0が必要な場合、logを取る成分がunderflowする場合、選んだmirror mapでdual側の計算が難しい場合は、projectionや別のparameterizationを比較します。方法名だけでなく、mirror map・初期点・step scheduleを記録します。

## Python

次の関数は、任意の実ベクトルをsum=1かつ非負な点へ射影します。更新後に`sum`と最小成分を確認するところまでを、最小の検証単位にします。

```python
import numpy as np


def project_to_simplex(values: np.ndarray) -> np.ndarray:
    descending = np.sort(values)[::-1]
    offsets = np.cumsum(descending) - 1.0
    indices = np.arange(1, values.size + 1)
    active = np.nonzero(descending - offsets / indices > 0.0)[0]
    threshold = offsets[active[-1]] / indices[active[-1]]
    return np.maximum(values - threshold, 0.0)


candidate = np.array([-0.30, 0.85, 1.20, -0.05])
probability = project_to_simplex(candidate)

print(probability)
assert np.all(probability >= -1e-12)
assert np.isclose(probability.sum(), 1.0)
```

これはsimplex制約を保つための部品です。目的関数が凸か、勾配が正しいか、step sizeが適切かは別に確認します。projection後の可行性だけから大域最適性を結論付けません。

## 診断値と切替の兆候

- 成分和の誤差と最小成分（数値上の可行性）
- 0に張り付く成分とactive faceの変化
- projection distanceまたはBregman stepの大きさ
- objective、projected-gradient mapping、またはregret
- step size、line search、underflow / overflow
- 0成分を許すべき問題なのにsoftmax内部点に張り付いていないか

切替の目安は次のとおりです。projectionが計算時間を支配するなら、parameterization・分解・別のprimal-dual法を検討します。softmaxで必要な0配分へ近づけないなら、境界を表せるprojectionへ戻します。成分が頻繁に0と正を行き来するなら、step size、scale、目的のnoise、または配分の粗さを見直します。

::: warning
simplex上の可行解は「配分として成立する」ことを意味しますが、実験・生産・制御の下限量、整数ロット、時間変化する制約までは含みません。元の問題にある制約を別途評価します。
:::

## 次に読む

各反復で集合へ戻す方法は[射影勾配法](#/learn/projected-gradient)、entropyなど問題に合う距離で更新する方法は[Mirror Descent](#/learn/mirror-descent)を参照してください。より一般の集合とretractionの考え方は[manifold最適化](#/learn/family.manifold)へ進みます。
