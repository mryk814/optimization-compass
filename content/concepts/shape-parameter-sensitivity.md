---
content_id: shape-parameter-sensitivity
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_DERIVATIVE_ANALYTIC_GRADIENT
title_ja: 形状parameterと感度
title_en: Shape Parameters and Sensitivities
summary: 形状最適化では、形状parameterの感度とPDE状態を介した目的の感度を分け、geometryとmeshが妥当な候補だけを更新比較に使います。
source_ids: [S054, S056, S101]
prerequisites: [shape-optimization, adjoint-sensitivity]
related_ids: [geometry-update-failure-modes, concept.pde-constrained-optimization, concept.variable-domain, topology-optimization]
aliases: [/learn/shape-parameter-sensitivity]
status: draft
last_reviewed: 2026-07-19
---

形状最適化では、形状parameterの感度とPDE状態を介した目的の感度を分け、geometryとmeshが妥当な候補だけを更新比較に使います。

## 同じ微分でも、動かす対象が違う

形状を表すparameterを $q$、そのparameterから作る領域を $\Omega(q)$、meshを $T(q)$、状態を $u(q)$ とします。
状態は、形状に依存する離散方程式 $R(u,q)=0$ を解いて得ます。
目的関数 $J(u,q)$ の変化には、parameterの直接効果と、形状とmeshが変わった結果としてstateが変わる効果が含まれます。

parameter微分は、選んだbasisや節点の動かし方に対する微分です。
一方、shape derivativeは、境界をどの方向へどれだけ動かすかに対する感度として考えます。
同じ境界変形を別のparameterizationで表すと、parameter微分の成分は変わる場合があります。
そのため、感度の数値だけを比較せず、設計変数の定義と形状の更新経路を固定して読みます。

## stateを介した感度を分解する

有限差分では、$q+h$ と $q-h$ の両方でgeometryを作り直し、meshを生成してstate solveを行います。
どちらか一方でもgeometryが無効になったり、meshが反転したりした場合、その差分は目的関数の感度として使えません。
失敗した候補を大きな目的値に置き換える場合も、差分の欠測と罰則値を別の状態として記録します。

adjoint sensitivityでは、固定した設計とmeshでstate solveを行い、状態方程式に対応するadjoint solveから縮約された感度を計算します。
設計変数が多いときに、各parameterを個別に摂動する有限差分より追加solve数を抑えやすい方法です。
ただし、adjoint solveは無効なgeometry、meshの再生成による不連続性、未収束のstate solveを修復しません。

## 更新候補を比較する順序

形状の更新を一つの目的値だけで判断すると、geometryの失敗と物理状態の失敗が同じ値に隠れます。
候補ごとに、次の順序で状態を分けて記録します。

1. $q$ から境界とgeometryを生成し、固定境界、最小距離、自己交差を確認する。
2. geometryからmeshを生成し、要素quality、orientation、負のJacobianを確認する。
3. 有効なmeshでstate solveを行い、state residualとsolver statusを保存する。
4. 目的、制約、direct sensitivityまたはadjoint sensitivityを計算する。
5. 同じgeometry、mesh、toleranceでgradient checkや有限差分を比較する。

この順序なら、目的の改善が感度の改善なのか、meshの変化やstate solveの誤差なのかを分けて判断できます。

## 記録する診断値

| 層 | 記録する値 | 失敗時の読み方 |
| --- | --- | --- |
| parameter | update norm、bounds、parameterization | 表現の範囲や更新幅が適切か |
| geometry | 境界の最小距離、交差、固定境界 | 無効な形状を物理評価へ渡していないか |
| mesh | 最小quality、要素orientation、負のJacobian数 | mesh-motionや再meshが破綻していないか |
| state | state residual、solver status、tolerance | 状態方程式を同じ精度で解けているか |
| sensitivity | gradient check、adjoint residual、有限差分との差 | 微分経路と実装が整合しているか |

geometryとmeshの検査を通過しても、離散化した問題の解が連続体の形状や物理の妥当性を保証するわけではありません。
mesh refinement、境界条件、物理制約を変えたときに、目的、制約、形状がどの程度変わるかを別に確認します。

::: warning
adjoint sensitivityが計算できたことや目的関数が改善したことだけでは、形状更新の成功や連続体での最適性は示せません。
geometry validity、mesh quality、state residual、gradient checkを同じ更新履歴に残してください。
:::

## 向く条件・避ける条件

形状parameterと感度を同じ更新履歴で扱う方法は、次の条件で使いやすくなります。

- geometryとmeshを決定的に再生成できる。
- state solveの残差とsolver statusを取得できる。
- 境界のparameterizationと固定境界を明示できる。
- mesh refinementやgradient checkを小さな検証問題で実行できる。

次の状態では、感度だけで更新を続けず、parameterization、mesh-motion、再mesh、または評価の失敗処理を見直します。

- 有限差分の片側でgeometryが無効になる。
- mesh qualityが更新幅に応じて急に低下する。
- state residualが揃わないまま目的だけを比較している。
- parameterのboundsを守っていても、必要な形状を表現できない。

## 次に読む

[形状最適化の設計変数](#/learn/shape-optimization)でgeometryの表現を確認し、[adjoint sensitivity](#/learn/adjoint-sensitivity)で状態方程式を介した感度を読みます。
[形状更新の失敗モード](#/learn/geometry-update-failure-modes)では、geometry、mesh、state、optimizationの層を切り分けます。
