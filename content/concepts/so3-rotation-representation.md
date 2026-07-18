---
content_id: concept.so3-rotation-representation
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_MANIFOLD
title_ja: SO(3)の回転表現
title_en: Rotation Representations on SO(3)
summary: SO(3)の回転は行列、quaternion、Lie algebraで表せますが、表現ごとに可行性の保ち方、誤差の測り方、特異点の扱いが異なります。
source_ids: [S044, S045, S071]
prerequisites: [concept.manifold]
related_ids: [concept.manifold, concept.variable-domain, family.manifold, riemannian-gradient, riemannian-trust-region]
status: draft
last_reviewed: 2026-07-19
---

SO(3)の回転は行列、quaternion、Lie algebraで表せますが、表現ごとに可行性の保ち方、誤差の測り方、特異点の扱いが異なります。

## 回転は3自由度の集合

3次元の回転は、9個の成分を持つ行列として書けます。
ただし、任意の9成分が回転を表すわけではありません。

$$
SO(3)=\{R\in\mathbb{R}^{3\times3}\mid R^{\mathsf{T}}R=I,\ \det R=1\}
$$

直交性と向きの条件が成分を縛るため、自由度は3です。
この集合を通常のEuclidean空間の変数として更新すると、次の点で回転から外れます。

- $R^{\mathsf{T}}R=I$ が崩れ、長さや角度を保たなくなる
- $\det R=1$ が崩れ、鏡映を含む行列になる場合がある
- 行列の差が小さくても、回転としての距離や誤差が小さいとは限らない

したがって、回転の最適化では「3つの数をどう持つか」だけでなく、「一歩をどの空間で作るか」を決めます。

## 行列は制約を直接確認できる

行列表現の利点は、回転の条件をそのまま診断できることです。
反復点 $R$ について、直交性の残差 $\lVert R^{\mathsf{T}}R-I\rVert_F$ と $\det R-1$ を記録すれば、行列が $SO(3)$ からどれだけ外れたかを確認できます。

一方、単純なEuclidean update

$$
R_{\mathrm{trial}}=R-\eta G
$$

は、一般にはこの集合の外へ出ます。
そこでSVDやpolar factorを使って近い回転へ戻す方法がありますが、これはambient spaceで作った候補を修正する `projection` です。
接空間で作ったstepを `retraction` で戻す方法や、Lie algebraを通じて `exponential map` を使う方法とは、更新則も目的関数の変化も同じではありません。

projectionを使うなら、修正前後の距離 $\lVert R_{\mathrm{trial}}-R_{\mathrm{projected}}\rVert_F$ を残します。
この距離が大きいとき、solverが作ったstepの多くを幾何の修正が消している可能性があります。

## quaternionは冗長な表現を持つ

単位quaternion $q\in\mathbb{R}^4$ は、次の条件で回転を表します。

$$
\lVert q\rVert_2=1
$$

quaternionは4成分からなりますが、単位normの条件があるため自由度は3です。
行列の直交性を毎回扱わずに済み、更新後にnormで割るだけで単位quaternionへ戻せる場合があります。

ただし、quaternionには表現の非一意性があります。

$$
q\quad\text{と}\quad -q
$$

は同じ回転を表します。
そのため、時系列の差分やparameterの距離を計算する前にsign conventionをそろえないと、回転が連続なのにquaternionの差だけが大きく見えることがあります。
normが1であることは回転としての可行性の一部を示しますが、signの整合性や目的関数の残差までは示しません。

## Lie algebraは局所的な一歩を表す

回転の接空間は3次元のvector $\xi\in\mathbb{R}^3$ として扱えます。
このvectorから歪対称行列 $[\xi]_{\times}$ を作り、現在の回転に右から掛けると、接空間のstepを回転へ写せます。

$$
R_{\mathrm{new}}=R\exp([\xi]_{\times})
$$

この形では、solverが決めるstepは回転行列の9成分ではなく、現在点の近くでの3成分です。
回転の差を

$$
\xi=\log(R_{\mathrm{ref}}^{\mathsf{T}}R)^{\vee}
$$

から読むと、`geodesic distance` と回転軸の情報を同時に扱えます。

ただし、Lie algebraはSO(3)全体を一つの滑らかな座標で覆うものではありません。
回転角が $\pi$ に近づくと、軸の向きが入れ替わる複数の表現が近くなり、`log` の選択が不安定になります。
この領域では、角度だけを見て軸の連続性を仮定するわけにはいきません。

## 同じデータでも誤差の意味が変わる

回転推定やrotation averagingでは、基準回転 $R_{\mathrm{ref}}$ と観測回転 $R$ の差を何で測るかが結果を左右します。

| 誤差 | 式 | 見ているもの |
| --- | --- | --- |
| chordal error | $\lVert R-R_{\mathrm{ref}}\rVert_F$ | 行列を置いたEuclidean空間での差 |
| geodesic error | $\lVert\log(R_{\mathrm{ref}}^{\mathsf{T}}R)^{\vee}\rVert_2$ | 回転群の上での最短角度 |
| structure residual | $\lVert R^{\mathsf{T}}R-I\rVert_F$, $\det R-1$ | 候補がSO(3)に留まっているか |

chordal errorが小さいことと、geodesic errorが小さいことは、同じ診断ではありません。
さらに、projectionで可行性を戻した候補と、Lie algebraのstepで得た候補は、同じ回転を表していても更新履歴が異なります。
比較では、表現、update、residual、budgetを固定して記録します。

## 表現を選ぶときの確認

| 表現 | 向いている条件 | 先に決めること |
| --- | --- | --- |
| 行列 | 物理式や既存APIが行列を要求し、構造残差を直接監視したい | projectionの定義、determinantの補正、projection distance |
| quaternion | 4成分のparameterizationと単位normの維持を使いたい | $q$ と $-q$ のsign convention、normの検査、残差の定義 |
| Lie algebra | 現在の回転の近くで接空間のstepと角度誤差を使いたい | `exp` と `log` の範囲、near-πの扱い、左右どちらから更新するか |

どれか一つが常に優れているわけではありません。
行列projectionは実装しやすくても、stepの意味を変える場合があります。
quaternionはnormを保ちやすくても、signをそろえない比較を誤らせます。
Lie algebraは局所的な幾何を表しやすくても、near-πの分岐を隠せません。

## 可行性と収束を分けて記録する

回転表現が健全かどうかと、最適化が進んでいるかどうかは別の判定です。

| 判定 | 診断値 | 判断 |
| --- | --- | --- |
| 行列の可行性 | $\lVert R^{\mathsf{T}}R-I\rVert_F$, $\det R-1$ | 回転行列の条件を満たすか |
| quaternionの可行性 | $\lVert q\rVert_2-1$ | 単位quaternionから外れていないか |
| 表現の連続性 | sign変更、axis変更、chartの切替 | 座標の不連続を解の変化と誤認していないか |
| 幾何上の進展 | geodesic error、geodesic step | 回転としてどれだけ動いたか |
| 最適化の停止 | Riemann gradient norm、objective、budget | 局所的な停止条件へ近づいたか |

retractionやnormalizationで各iterateをfeasibleに保てても、局所解や大域最適性は保証されません。
停止を判断するときは、構造残差、幾何上の誤差、objective、Riemann gradient normを別々に読める状態にします。

## 失敗・切替の兆候

- projection distanceが大きくなり続ける場合は、Euclidean updateのstep幅か、行列projectionの使い方を見直します。
- quaternionの符号が反復ごとに反転する場合は、回転差を計算する前にsign conventionを確認します。
- near-πで`log`の軸が急に変わる場合は、角度だけでなく軸の非一意性を記録し、別の残差やparameterizationを検討します。
- objectiveが改善しているのにgeodesic errorが改善しない場合は、最適化した残差と評価した残差が一致しているかを確認します。
- 構造残差が小さくてもRiemann gradient normが下がらない場合は、可行性の維持と収束を混同せず、接空間射影やgradient checkを見直します。

## 次に読む

多様体値変数の共通原則は[多様体値変数](#/learn/concept.manifold)で確認できます。
solverの選び分けは[Riemann多様体最適化の選び分け](#/learn/family.manifold)へ進み、一次法と二階法の違いは[Riemann勾配法](#/learn/riemannian-gradient)と[Riemann trust-region法](#/learn/riemannian-trust-region)で比較します。
[Pymanopt](https://pymanopt.org/)と[Manopt](https://www.manopt.org/)の公式referenceでは、回転を含む多様体の実装とsolverの対応を利用versionに合わせて確認できます。
