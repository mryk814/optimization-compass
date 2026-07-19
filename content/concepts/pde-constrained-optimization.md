---
content_id: concept.pde-constrained-optimization
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_STRUCTURE_PDE_CONSTRAINED
title_ja: PDE制約付き最適化
title_en: PDE-Constrained Optimization
summary: PDE制約付き最適化では、設計変数から状態fieldを解き、離散化した状態方程式の残差と最適化制約の可行性を分けて確認します。
source_ids: [S019, S054, S056, S097, S098, S101, S110, S111]
related_ids: [topology-optimization, adjoint-sensitivity, concept.constraint-class, concept.variable-domain, density-filter]
status: published
last_reviewed: 2026-07-19
---

PDE制約付き最適化では、設計変数から状態fieldを解き、離散化した状態方程式の残差と最適化制約の可行性を分けて確認します。

## まず「設計」と「状態」を分ける

PDEを含む問題では、最適化が直接動かす変数と、設計から計算する変数を分けます。前者を設計変数（design variable）、後者を状態変数（state variable）と呼びます。

設計変数は材料密度、形状、境界入力などです。状態変数は変位、温度、圧力など、PDEを解いて得るfieldです。

典型的な形は次のとおりです。

$$
\min_{m,u} J(u,m)
\quad\text{subject to}\quad
R(u,m)=0,\quad c(u,m)\le 0.
$$

ここで$m$は設計、$u$は状態、$R$は状態方程式、$c$は目的とは別に守る制約です。設計を1回更新するたびに、state solve、目的と制約の評価、必要なら感度計算を行います。

たとえばトポロジー最適化では、密度fieldから剛性を作り、変位fieldをstate solveで求めます。complianceが改善しても、状態方程式を正しく解けたことやvolume constraintを守ったことまでは示しません。[トポロジー最適化](#/learn/topology-optimization)では、この設計fieldと状態fieldの対応を具体的に追えます。

## 離散化すると「残差」と「離散制約」になる

連続なPDEをmesh上で解くと、状態方程式は離散化した残差として表されます。

$$
R_h(u_h,m_h)=0.
$$

添字$h$は、meshや近似空間に依存することを表します。実際の計算では、残差のnormが許容値より小さいか、solverが指定したtoleranceまで到達したかを確認します。これは、固定したmesh上でstate solveが収束したかという判定です。

一方、最適化にはvolume、応力、境界、設計変数のboundsなど、別の制約があります。たとえば、

$$
\|R_h(u_h,m_h)\|\le\tau_{state},
\qquad c_h(u_h,m_h)\le\tau_{constraint}
$$

のように、状態残差と最適化制約を別々に記録します。残差が小さくてもvolumeを超えていれば、最適化の候補としては不適切です。逆に、制約値がよく見えてもstate solveが未収束なら、その目的値や感度はまだ確定していません。

## solverの収束と最適化の可行性は別の判定

「solverが収束した」と「最適化問題で可行な点を得た」は同じではありません。次の3段階を分けると、反復のどこで問題が起きたかを追えます。

| 判定 | 主に見るもの | 何が分かるか |
| --- | --- | --- |
| state solve | state residual、solver status、state tolerance | 固定した設計とmeshでPDEを解けたか |
| optimization feasibility | design bounds、volume、state/path constraintのviolation | 設計と状態が制約を満たすか |
| optimization progress | objective、gradient norm、KKT residual、design change | 最適化の停止条件に近づいたか |

この3つを1つの`success`フラグにまとめないでください。state solveが失敗した評価は、低い目的値を返した評価と同じではありません。失敗の条件、再試行したか、inexact solveとして扱ったかを別に記録します。

感度を使う場合も順番は変わりません。state solveの後にdirect sensitivityやadjoint solveを行い、gradient checkとadjoint residualを確認します。[adjoint sensitivity](#/learn/adjoint-sensitivity)は、設計変数が多いときに状態方程式を介した感度を計算する考え方を説明します。

## 境界条件はstateとadjointの両方で確認する

境界条件（boundary condition）は、PDEの解が境界でどのような値や流束を持つかを定めます。固定値を指定する境界（Dirichlet boundary condition）と、流束や荷重を指定する境界（Neumann boundary condition）などを、適用先とともに記録します。

境界条件を変えるとstateの意味が変わります。設計を比較するなら、荷重、固定支持、流入条件を揃えなければ、目的値の差を手法や設計の差として読めません。adjoint sensitivityを使うときは、stateだけでなくadjoint側の境界条件と固定自由度の扱いも確認します。

境界上の値だけでは、設定の正しさは判断できません。

- 境界条件が意図した自由度へ適用されているか
- 境界条件とloadの単位とscaleが揃っているか
- 境界近くのstate residualやgradientが不自然に大きくないか
- meshを変えたとき、境界の表現が変わっていないか

境界条件のミスは、solverを収束させたまま別の物理問題を解かせることがあります。

## mesh refinementは別の検証である

固定したmeshでstate residualを小さくしても、連続モデルの解が十分に近いとは限りません。mesh refinementでは、meshを細かくしたときの解、目的、制約、感度の変化を調べます。

次の2つは混ぜません。

| 検証 | 変更するもの | 解釈 |
| --- | --- | --- |
| state solveの収束 | 設計とmeshを固定し、solver iterationを進める | 離散化した方程式を数値的に解けたか |
| mesh refinement | mesh、自由度、必要なら設計表現を変える | 解がmeshの解像度に依存していないか |

meshを細かくすると、状態の自由度だけでなく、設計fieldの表現、感度、計算費も変わります。目的値が変わったときは、それがsolver toleranceの不足なのか、mesh依存性なのか、設計の局所解なのかを分けて確認します。トポロジー最適化でfilterやprojectionを使う場合も、mesh sizeとfilter radiusの関係を固定したまま比較できているかを確認します。

::: warning
離散化したPDEの残差が小さく、最適化制約を満たしていても、連続モデルや実物の安全性が自動的に保証されるわけではありません。mesh refinement、境界条件、model mismatch、必要な物理制約を別に検証します。
:::

## costはoptimizer iterationで数えない

simulation-constrained問題では、outer optimizerの1 iterationに複数の計算が入ります。少なくとも次を別々に数えます。

- stateまたはsimulator call数
- nonlinear／linear solverの反復数と終了reason
- objective・constraintの追加評価数
- direct sensitivityまたはadjoint solve数
- failed、timeout、censored evaluation数
- wall time、core-hours、memory、checkpointの再計算量

2つのrunを比べるときは、optimizer iterationではなく、問題に合う共通budgetへ同期します。[EC026](#/gallery/EC026)の教材では同じstate-solve call数でtoleranceだけを変え、[tolerance/cost Compare](#/compare/COMPARE_PDE_STATE_TOLERANCE_COST)でstate/adjoint残差と線形反復costを並べます。これは実装速度の順位ではなく、inner solveの精度がouter progressの解釈へどう影響するかを見るcontrastです。

## failed evaluationを目的値へ隠さない

state solveが最大反復、breakdown、NaN、preconditioner failureなどで停止したとき、目的値は未定義のままです。自動的に大きなpenalty値へ置き換えると、「物理的に悪い設計」と「計算できなかった設計」を区別できません。

failure recordには、候補design、state residual、solver reason、消費budget、retryとfallbackの有無を残します。penaltyやsurrogate処理を採用する場合も、それを観測値ではなく明示したpolicyとして保存します。[state-solve failure Theater](#/theater/learning/SCENARIO_PDE_STATE_SOLVE_FAILURE)では、preconditioner failureに架空のobjectiveを与えず、failed statusで停止します。

Diagnoseでは次を順に確認します。

1. 境界条件、単位、null space、行列の対称性などmodel／discretizationの問題か
2. tolerance、max iteration、preconditionerなどsolver policyの問題か
3. design updateが可解領域を外れた問題か
4. retry、trust region縮小、step拒否、failure-aware surrogateのどれを採用したか

## transientとmultiphysicsでは追加の軸を持つ

transient問題では、time stepごとのstateを保存するか、checkpointからforward solveを再計算してadjointを戻すかを決めます。比較ではtime-step数、checkpoint数、再計算したforward step数、storage、adjoint residualを固定または明示します。checkpoint policyが違うrunをoptimizer iterationだけで比べません。

multiphysicsでは、熱・流体・構造などfieldごとの残差とcoupling residualを分けます。一方向coupling、逐次反復、monolithic solveでは、1回の「simulation call」に含むsubsolve数が異なります。couplingが収束したことは、各物理modelの妥当性や離散化誤差が小さいことを意味しません。

follow-up Caseは、transient heat control、fluid–structure design、thermo-mechanical design、wave／acoustic inverse designの順で、同じdesign・state・cost・failure contractへ接続します。最初のsteady教材から、それらの性能や保証を推論しません。

## 次に読む

[制約class](#/learn/concept.constraint-class)で、状態方程式を含む制約と可行性の扱いを整理します。[adjoint sensitivity](#/learn/adjoint-sensitivity)でderivative routeを確認し、[density filter](#/learn/density-filter)でmesh上のfield更新とmesh依存性を読みます。その後に[EC026](#/gallery/EC026)からprimary／failure Theaterと[tolerance/cost Compare](#/compare/COMPARE_PDE_STATE_TOLERANCE_COST)へ進みます。
