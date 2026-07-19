---
content_id: shape-parameter-sensitivity
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_DERIVATIVE_ANALYTIC_GRADIENT
title_ja: 形状parameterと縮約感度
title_en: Shape Parameters and Reduced Sensitivities
summary: 形状parameterを更新する最適化では、geometryとmeshの妥当性をPDE stateの収束と分けて確認します。目的感度はparameterの直接効果とstateを介した効果に分解します。
source_ids: [S054, S056, S101, S104, S106]
prerequisites: [shape-optimization, adjoint-sensitivity]
related_ids: [geometry-update-failure-modes, concept.pde-constrained-optimization, concept.variable-domain, topology-optimization]
visualization_ids: [shape-diffuser-valid-update, shape-diffuser-invalid-geometry]
comparison_ids: [COMPARE_SHAPE_TOPOLOGY_REPRESENTATION]
aliases: [/learn/shape-parameter-sensitivity]
status: published
last_reviewed: 2026-07-19
---

形状parameterを更新する最適化では、geometryとmeshの妥当性をPDE stateの収束と分けて確認します。目的感度はparameterの直接効果とstateを介した効果に分解します。

## 計算の層を分ける

形状を表すparameterを $q$ とします。
$q$ から領域 $\Omega(q)$ とmesh $T(q)$ を作り、その上でstate $u(q)$ を計算します。
stateは形状に依存する方程式 $F(u,q)=0$ の解です。

目的関数 $J(u,q)$ はparameterへ直接依存する場合があります。
同時に、parameterがstateを変える経路でも値が変わります。
stateを解いた後の目的を一つの関数として見ると、縮約目的は次のように書けます。

$$
\widehat{J}(q)=J(u(q),q)
$$

この表記により、geometry生成とstate solveを別の層として追跡できます。
目的評価も独立した層として記録します。
数値が悪化した層を特定してから、感度や更新則を疑います。

## 有限差分で経路を確かめる

有限差分では $q$ を少し動かし、geometryからstateまでを再計算します。
中心差分なら $q+h$ と $q-h$ の両側で縮約目的を評価します。
一つのparameterを調べるたびに追加のstate solveが必要です。

差分値を感度として使う前に、両側の評価が同じ契約を満たすか確認します。
片側だけgeometryが無効なら、その差分は欠測です。
meshの細かさやsolver toleranceが違う場合も、同じ関数の差として読めません。

step $h$ を一つだけ試して一致しても十分ではありません。
$h$ を変えたgradient checkを行い、打切り誤差とsolver誤差の影響を分けます。

## adjointで縮約感度を得る

adjoint法はstate方程式を利用し、縮約目的のgradientを効率よく計算します。
評価するfunctionalが少なく、parameterが多い問題で特に有利です。
各parameterを個別に摂動する有限差分より、追加solve数を抑えられます。

ただし、adjoint solveは前段の失敗を修復しません。
無効なgeometryや反転したmeshでは、正しい縮約感度を期待できません。
state solveが未収束なら、目的値とadjointの入力も同じ状態ではありません。

実装後は小さな固定問題でgradient checkを行います。
有限差分との一致はadjoint実装の確認であり、連続体model全体の正しさの証明ではありません。

## 候補を評価する順序

形状の更新候補は、一つの目的値へ早く畳み込まないようにします。
次の順序で状態を記録すると、失敗した層を後から再現できます。

1. $q$ のboundsとupdate normを確認する。
2. 境界を生成し、固定境界と自己交差を検査する。
3. meshを生成し、要素qualityとJacobianを検査する。
4. stateを解き、residualとsolver statusを保存する。
5. 目的と制約を評価し、縮約感度を計算する。
6. 同じ設定の有限差分でgradient checkを行う。

失敗候補を大きな目的値へ置き換える場合も、失敗statusを別に保存します。
悪いが有効な候補と、評価できなかった候補を混ぜないためです。

## 診断値

| 層 | 診断値 | 読み方 |
| --- | --- | --- |
| parameter | update norm、bounds | 更新幅とparameterizationが適切か |
| geometry | 最小距離、自己交差 | 無効な形状を次の層へ渡していないか |
| mesh | 最小quality、負のJacobian数 | mesh motionや再生成が破綻していないか |
| state | residual、solver status | 同じ精度でstateを解けているか |
| sensitivity | gradient check、adjoint residual | 微分経路と実装が整合しているか |
| optimization | objective、constraint、budget | 有効な候補の中で改善しているか |

## 失敗・切替の兆候

- 有限差分の片側でgeometryが無効になる場合は、stepかparameterizationを見直します。
- mesh qualityがupdate normに応じて急落する場合は、mesh motionか再生成へ戻ります。
- state residualが候補ごとに揃わない場合は、目的の差より先にsolver設定を確認します。
- gradient checkがstepを変えても改善しない場合は、微分経路と境界条件を見直します。
- bounds内でも必要な形状を表せない場合は、parameterizationを切り替えます。

::: warning
gradient checkの成功や目的値の改善だけでは、連続体での妥当性を示せません。mesh refinementと物理制約の感度を別に確認します。
:::

[2D diffuser Case](#/gallery/shape-diffuser)では、3 parameterの有限差分／adjoint discussionをgeometry・mesh・state診断と同じ経路で確認できます。

## 次に読む

[形状最適化の設計変数](#/learn/shape-optimization)でgeometryの表現を確認できます。
[adjoint sensitivity](#/learn/adjoint-sensitivity)では、state方程式を介した感度を学べます。
[形状更新の失敗モード](#/learn/geometry-update-failure-modes)では、失敗を層ごとに切り分けます。
