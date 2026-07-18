---
content_id: concept.pde-constrained-optimization
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_STRUCTURE_PDE_CONSTRAINED
title_ja: PDE制約付き最適化
title_en: PDE-Constrained Optimization
summary: PDE制約付き最適化では、設計変数から状態fieldを解き、離散化した状態方程式の残差と最適化制約の可行性を分けて確認します。
source_ids: [S054, S056, S097, S098, S101]
related_ids: [topology-optimization, adjoint-sensitivity, concept.constraint-class, concept.variable-domain, density-filter]
status: published
last_reviewed: 2026-07-19
---

PDE制約付き最適化では、設計変数から状態fieldを解き、離散化した状態方程式の残差と最適化制約の可行性を分けて確認します。

## まず「設計」と「状態」を分ける

PDEを含む問題では、最適化が直接動かす設計変数と、設計から計算される状態変数を分けます。設計変数は材料密度、形状、境界入力などです。状態変数は変位、温度、圧力など、PDEを解いて得るfieldです。

典型的な形は次のとおりです。

$$
\min_{m,u} J(u,m)
\quad\text{subject to}\quad
R(u,m)=0,\quad c(u,m)\le 0.
$$

ここで$m$がdesign、$u$がstate、$R$が状態方程式、$c$が目的とは別に守る制約です。設計を1回更新するたびに、状態solve、目的・制約の評価、必要なら感度計算が続きます。

たとえばトポロジー最適化では、密度fieldから剛性を作り、変位fieldをstate solveで求めます。complianceの改善は設計更新の結果ですが、状態方程式を正しく解けたことやvolume constraintを守ったこととは別の事実です。[トポロジー最適化](#/learn/topology-optimization)では、この設計fieldと状態fieldの対応を具体的に追えます。

## 離散化すると「残差」と「離散制約」になる

連続なPDEをmesh上で解くと、状態方程式は離散化された残差として表されます。

$$
R_h(u_h,m_h)=0.
$$

添字$h$はmeshや近似空間に依存することを表します。実際の計算では、残差のnormが許容値より小さいか、solverが指定したtoleranceまで到達したかを確認します。これは固定したmesh上でのstate solveの収束です。

一方、最適化にはvolume、応力、境界、設計変数のboundsなど、別の制約があります。たとえば

$$
\|R_h(u_h,m_h)\|\le\tau_{state},
\qquad c_h(u_h,m_h)\le\tau_{constraint}
$$

のように、状態残差と最適化制約を別々に記録します。残差が小さくてもvolumeを超えていれば最適化の候補としては不適切です。逆に、制約値がよく見えてもstate solveが未収束なら、その目的値や感度はまだ確定していません。

## solverの収束と最適化の可行性は別の判定

「solverが収束した」と「最適化問題で可行な点を得た」は同じではありません。次の3段階を分けると、反復のどこで問題が起きたかを追えます。

| 判定 | 主に見るもの | 何が分かるか |
| --- | --- | --- |
| state solve | state residual、solver status、state tolerance | 固定した設計とmeshでPDEを解けたか |
| optimization feasibility | design bounds、volume、state/path constraintのviolation | 設計と状態が制約を満たすか |
| optimization progress | objective、gradient norm、KKT residual、design change | 最適化の停止条件に近づいたか |

この3つを1つの`success`フラグに潰さないでください。state solveが失敗した評価は、低い目的値を返した評価と同じではありません。失敗の条件、再試行、inexact solveとして扱ったかを別に記録します。

感度を使う場合も順番は変わりません。state solveのあとにdirect sensitivityやadjoint solveを行い、gradient checkとadjoint residualを確認します。[adjoint sensitivity](#/learn/adjoint-sensitivity)は、設計変数が多いときに状態方程式を介した感度を計算する考え方を説明します。

## 境界条件はstateとadjointの両方で確認する

境界条件（boundary conditions）は、PDEの解がどのような値や流束を境界で持つかを定めます。固定値を指定する境界（Dirichlet boundary condition）と、流束や荷重を指定する境界（Neumann boundary condition）などを、どの境界へ適用したかとともに記録します。

境界条件を変えるとstateの意味が変わります。設計の比較で荷重、固定支持、流入条件が揃っていなければ、目的値の差を手法や設計の差として読めません。adjoint sensitivityを使うときは、stateだけでなくadjoint側の境界条件と固定自由度の扱いも確認します。

ここで見るべきは境界上の値だけではありません。

- 境界条件が意図した自由度へ適用されているか
- 境界条件とloadの単位・scaleが揃っているか
- 境界近くのstate residualやgradientが不自然に大きくないか
- meshを変えたとき、境界の表現が変わっていないか

境界条件のミスは、solverを収束させたまま別の物理問題を解かせることがあります。

## mesh refinementは別の検証である

固定したmeshでstate residualを小さくしても、連続モデルの解が十分に近いとは限りません。mesh refinementは、meshを細かくして得られる解、目的、制約、感度の変化を調べる検証です。

次の2つは混ぜません。

| 検証 | 変更するもの | 解釈 |
| --- | --- | --- |
| state solveの収束 | 設計とmeshを固定し、solver iterationを進める | 離散化した方程式を数値的に解けたか |
| mesh refinement | mesh、自由度、必要なら設計表現を変える | 解がmeshの解像度に依存していないか |

meshを細かくすると、状態の自由度だけでなく設計fieldの表現、感度、計算費も変わります。目的値が変わったとき、それがsolver toleranceの不足なのか、mesh依存性なのか、設計の局所解なのかを分けて確認します。トポロジー最適化でfilterやprojectionを使う場合も、mesh sizeとfilter radiusの関係を固定したまま比較できているかを確認します。

::: warning
離散化したPDEの残差が小さく、最適化制約を満たしていても、連続モデルや実物の安全性が自動的に保証されるわけではありません。mesh refinement、境界条件、model mismatch、必要な物理制約を別に検証します。
:::

## 次に読む

[制約class](#/learn/concept.constraint-class)で、状態方程式を含む制約と可行性の扱いを整理します。[density filter](#/learn/density-filter)では、mesh上のfield更新とmesh依存性を確認できます。計算費やstate solveの失敗を含む比較は、問題ごとのbudget、tolerance、failed evaluationを揃えてから行います。
