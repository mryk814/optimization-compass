---
content_id: concept.so3-rotation-representation
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_MANIFOLD
title_ja: SO(3)の行列・接空間表現
title_en: Matrix and Tangent Representations on SO(3)
summary: SO(3)の回転を最適化するときは、行列の可行性と接空間のステップを分けて扱います。射影、レトラクション、指数写像は同じ更新ではありません。
source_ids: [S044, S045, S071, S107]
prerequisites: [concept.manifold]
related_ids: [concept.manifold, concept.variable-domain, family.manifold, riemannian-gradient, riemannian-trust-region]
visualization_ids: [so3-projected-alignment, so3-riemannian-alignment]
comparison_ids: [COMPARE_SO3_PROJECTED_RIEMANNIAN]
status: published
last_reviewed: 2026-07-19
---

SO(3)の回転を最適化するときは、行列の可行性と接空間のステップを分けて扱います。射影、レトラクション、指数写像は同じ更新ではありません。

## 回転行列の条件

三次元の回転は $3\times3$ 行列として書けます。
ただし、任意の九成分が回転を表すわけではありません。

$$
SO(3)=\{R\in\mathbb{R}^{3\times3}\mid R^{\mathsf{T}}R=I,\ \det R=1\}
$$

直交性は長さと角度を保つ条件です。
行列式が $1$ である条件は鏡映を除きます。
これらの制約により、行列の九成分に対して自由度は三つです。

行列表現では、構造残差を直接監視できます。
$\lVert R^{\mathsf{T}}R-I\rVert_F$ と $|\det R-1|$ を別に記録します。

## 接空間で一歩を作る

現在点 $R$ での接ベクトルは $R\Omega$ と書けます。
$\Omega$ は $\Omega^{\mathsf{T}}=-\Omega$ を満たす歪対称行列です。
三次元の歪対称行列は三つの独立成分を持ちます。

周囲の空間の勾配をそのまま行列へ足すと、一般には $SO(3)$ から外れます。
リーマンソルバーは勾配を接空間へ移し、そこでステップを作ります。
この分離により、探索方向と可行性を保つ写像を別に検証できます。

$$
R_{\mathrm{trial}}=R+R\Omega
$$

$R_{\mathrm{trial}}$ は接方向を表しますが、有限ステップでは回転行列とは限りません。
次にレトラクションなどを使い、接空間の候補を多様体上へ戻します。

## 射影とレトラクションを区別する

射影は周囲の空間にある行列を、近い回転行列へ修正する操作として使われます。
一方、レトラクションは現在点の接空間から多様体へ写す局所的な操作です。
同じ行列を返す場合があっても、入力となるステップと理論上の役割は同じではありません。

PymanoptのSO(3)実装では、QRまたは極分解を使うレトラクションが選べます。
QRによるレトラクションは指数写像の一次近似です。
指数写像そのものと同一ではないため、手法と設定を記録します。

射影を使う場合は、修正前後の距離を保存します。
レトラクションを使う場合は、接空間ステップのノルムを保存します。
二つを同じ「更新量」として混ぜないことが重要です。

## 指数写像との違い

リー代数の歪対称行列 $\Omega$ を使うと、指数写像は次の更新を与えます。

$$
R_{\mathrm{new}}=R\exp(\Omega)
$$

この更新は $SO(3)$ 上に残ります。
ただし、レトラクションは計算を軽くするために別の局所写像を使えます。
ソルバーの一反復を比較するときは、同じステップ幅でも到達点が一致するとは限りません。

多様体上の距離も周囲の空間にある行列差と区別します。
Frobenius ノルムによる差と測地距離は異なる量です。
停止判定に使った距離と、最終評価に使う誤差を明示します。

## 診断値

| 診断値 | 読み方 |
| --- | --- |
| $\lVert R^{\mathsf{T}}R-I\rVert_F$ | 直交性が保たれているか |
| $|\det R-1|$ | 鏡映側へ外れていないか |
| 接空間ステップノルム | 接空間でどれだけ動かしたか |
| 射影距離 | 周囲の空間にある候補をどれだけ修正したか |
| リーマン勾配ノルム | 多様体上の一階停止条件へ近いか |
| 目的と予算 | 可行性を保つだけでなく改善しているか |

可行性と収束は別の判定です。
構造残差が小さくても、目的やリーマン勾配ノルムが改善するとは限りません。

## 失敗・切替の兆候

- 直交性残差が増える場合は、更新後に使う写像と数値精度を確認します。
- 射影距離がステップノルムに比べて大きい場合は、周囲の空間の更新を見直します。
- 目的が改善せずステップだけ小さくなる場合は、勾配と停止条件を確認します。
- QRと極分解で結果が変わる場合は、レトラクションを実験条件として固定します。
- 測地距離と行列差の判断が食い違う場合は、評価指標の意味へ戻ります。

::: warning
各反復点がSO(3)上にあることは、局所解や大域最適性の保証ではありません。構造残差と最適化の停止条件を別に記録します。
:::

## 事例・可視化・比較で読む

[SO(3)姿勢合わせ事例](#/gallery/so3-attitude-alignment)で、二つの更新経路を同じ教材問題へ接続します。
一方は周囲の空間にある射影更新、もう一方は接空間からのリーマン更新です。
[射影可視化](#/theater/learning/SCENARIO_SO3_PROJECTED_ALIGNMENT)で、射影を含む更新経路と構造残差を確認します。
[リーマン可視化](#/theater/learning/SCENARIO_SO3_RIEMANNIAN_ALIGNMENT)では、接空間のステップと構造残差を追います。
[射影／リーマン比較](#/compare/COMPARE_SO3_PROJECTED_RIEMANNIAN)は、二つの実行を同じ評価予算へ同期します。
目的と直交性残差を分けて読みます。
射影距離とリーマン勾配ノルムも別の診断値です。

## 次に読む

[多様体値変数](#/learn/concept.manifold)で、接空間とレトラクションの共通原則を確認できます。
[Riemann多様体最適化の選び分け](#/learn/family.manifold)では、一次法と信頼領域法の使い分けを整理します。
[Riemann勾配法](#/learn/riemannian-gradient)と[Riemann 信頼領域法](#/learn/riemannian-trust-region)で更新則を比較できます。
