---
content_id: adjoint-sensitivity
kind: method
method_id: M_ADJOINT_SENSITIVITY
title_ja: 随伴感度
title_en: Adjoint Sensitivity Analysis
summary: 随伴感度は、状態方程式の解を使って、設計変数が目的関数へ与える感度を少ない追加求解で計算する方法です。
source_ids: [S101]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [shape-optimization, geometry-update-failure-modes, simp-topology, density-filter, optimality-criteria-topology]
visualization_ids: [topology-optimization-field-evolution, pde-state-tolerance-tight, pde-state-solve-failure]
comparison_ids: [COMPARE_PDE_STATE_TOLERANCE_COST]
aliases: [/learn/adjoint-sensitivity]
status: published
last_reviewed: 2026-10-03
---

随伴感度は、状態方程式の解を使って、設計変数が目的関数へ与える感度を少ない追加求解で計算する方法です。

## 30秒でつかむ

水道のバルブを少し変えたとき、下流の水量がどちらへ変わるかを調べる感覚です。
多数の設計変数が状態を通じて目的へ影響するとき、その感度をまとめて計算します。

- **見るもの**：状態方程式の残差、随伴の残差、設計感度
- **動かすもの**：感度を計算するための随伴変数
- **前進の判断**：残差が小さく、有限差分と感度が整合すること

## 一手の意味：符号と転置をそろえる

状態方程式を $R(u,m)=0$、状態を消去した目的を $\widehat J(m)=J(u(m),m)$ とします。以下では勾配は列ベクトル、$R_u,R_m$ はヤコビ行列です。状態を微分すると

$$
R_u\,du+R_m\,dm=0.
$$

$R_u$ が局所的に可逆なら、$du=-R_u^{-1}R_mdm$ を代入できます。ただし設計変数が多数だと、$du/dm$ を全列求めるのは高価です。そこで一つのスカラー目的に対し

$$
R_u^T\lambda=\nabla_uJ,\qquad
\nabla_m\widehat J=\nabla_mJ-R_m^T\lambda
$$

を使います。これは $\mathcal L=J-\lambda^TR$ という符号の選び方と対応しています。$\mathcal L=J+\lambda^TR$ を使う資料では随伴の符号も変わるので、式を片方だけ移植しません。

多数の設計変数に対しても、一つの目的なら原則として一つの転置線形系で感度を組み立てられます。ただし状態求解、ヤコビ行列の構築、$R_m^T\lambda$ の計算は残ります。目的や独立した制約が増えれば、必要な随伴右辺も増えます。直接感度法は少数の設計方向、多数の出力を調べるときに有利な場合があります。

## 小さな例：状態・随伴・感度を一つずつ計算する

設計変数は $m>0$、状態方程式は $R(u,m)=mu-1=0$、目的は $J(u,m)=\tfrac12(u-1)^2$ です。状態の目標は1です。$m=2$ では、次の順に進みます。

1. 状態を解く：$u=1/m=0.5$
2. 目的の状態微分を作る：$J_u=u-1=-0.5$
3. 随伴を解く：$R_u\lambda=J_u$ より $2\lambda=-0.5$、$\lambda=-0.25$
4. 設計感度を組み立てる：$J_m=0$、$R_m=u=0.5$ より $d\widehat J/dm=-\lambda u=0.125$

ここで $\widehat J(m)=J(u(m),m)$ は、状態を解いた後の目的です。$J_m=0$ は「状態を固定して見た直接の影響がない」という意味で、設計を変えても目的が変わらないという意味ではありません。

![設計mから状態uと目的Jへ進む順方向、目的から随伴λと設計感度へ戻る逆方向。右は同じm=2におけるTaylor残差の二次減少。](./media/adjoint-scalar-chain.svg "状態を解く、随伴を解く、感度を組み立てる三段階。感度が正なら小さな下降更新はmを減らす向き。更新幅はこの図では決めていない。")

解析的に状態を代入しても

$$
\widehat J(m)=\frac12\left(\frac1m-1\right)^2,
\qquad \widehat J'(m)=\frac{m-1}{m^3}
$$

となり、$m=2$ で0.125と一致します。正の感度なので、目的を下げるには $m$ を少し減らします。$m^+=2-0.5\times0.125=1.9375$ とすれば、新しい状態は約0.5161、目的は約0.1171です。

| 更新回数 | $m$ | 状態 $u$ | 随伴 $\lambda$ | 感度 | 目的値 |
|---|---:|---:|---:|---:|---:|
| 0 | 2.0000 | 0.5000 | -0.2500 | 0.1250 | 0.1250 |
| 1 | 1.9375 | 0.5161 | -0.2497 | 0.1289 | 0.1171 |
| 2 | 1.8731 | 0.5339 | -0.2489 | 0.1329 | 0.1086 |

幅0.5は感度の利用例として別に選んだ勾配降下法の係数です。随伴法は更新幅、制約の処理、候補の受理まで自動で決める最適化アルゴリズムではありません。

### 微分が合うかは、一つの刻み幅だけで決めない

中心差分 $[\widehat J(m+h)-\widehat J(m-h)]/(2h)$ を $h=10^{-5}$ で計算すると、上の3点の絶対誤差は $4\times10^{-12}$ 未満です。小数の一致桁数を保証するものではなく、丸めや状態求解精度に依存する実行上の誤差です。

さらに、一次項を引いたTaylor残差

$$
E(h)=|\widehat J(m+h)-\widehat J(m)-h\widehat J'(m)|
$$

を調べます。滑らかな目的と正しい感度なら $E(h)=O(h^2)$。$m=2$ では $h=0.1,0.05,0.025$ に対し約 $3.12\times10^{-4},7.81\times10^{-5},1.95\times10^{-5}$ で、半分の幅にすると約1/4です。図の緑の傾きがその検査です。幅を極端に小さくすると差の桁落ちが支配し、きれいな二次減少は続きません。

状態残差と随伴残差も独立に検査します。例えば $m=2$ で状態を誤って $u=(1+\varepsilon)/2$ と解くと、状態残差は $\varepsilon$ です。この状態で随伴を正確に解いても、計算した感度は $0.125-\varepsilon^2/8$。この点では一次の誤差が偶然相殺されます。感度がよく合うことだけで、状態が正確だと判断しない理由です。

## 向く条件・避ける条件

状態方程式があり、設計変数が多く、目的関数の数が少ない問題に向きます。
接触や離散的な材料切替のように微分が不連続な場合は、滑らかな近似とその限界を明示します。

## Python

小さな例では、状態と随伴の求解を別々に実行します。
その後、感度を確認できます。

```python
import numpy as np

J = lambda m: 0.5 * (1.0 / m - 1.0)**2
m = 2.0
for iteration in range(3):
    u = 1.0 / m
    adjoint = (u - 1.0) / m
    gradient = -adjoint * u
    h = 1e-5
    fd = (J(m + h) - J(m - h)) / (2 * h)
    analytic = (m - 1.0) / m**3
    assert abs(m * u - 1.0) < 1e-12
    assert abs(m * adjoint - (u - 1.0)) < 1e-12
    assert abs(gradient - analytic) < 1e-12
    assert abs(gradient - fd) < 1e-9
    print(iteration, m, u, adjoint, gradient, J(m), abs(gradient-fd))
    m -= 0.5 * gradient  # This is a separate gradient-descent update.

m, gradient = 2.0, 0.125
previous = None
for h in (0.2, 0.1, 0.05, 0.025, 0.0125):
    remainder = abs(J(m + h) - J(m) - h * gradient)
    rate = np.log2(previous / remainder) if previous else None
    print('Taylor:', h, remainder, rate)
    previous = remainder
```

3回とも、状態残差 $mu-1$ と随伴残差 $m\lambda-(u-1)$ は丸め誤差の範囲で0です。
PDEの実装へ進む場合は、次の計算順序を使います。

実装では、状態求解と随伴求解を分けて記録します。
設計感度の組み立ても別の段階です。
次の擬似コードは、更新則や境界条件を省いた感度計算の骨格です。

```text
state = solve_state(design)
adjoint = solve_transpose_jacobian(state, objective)
sensitivity = direct_derivative(state, design) - residual_derivative(state, design).T @ adjoint
```

## 診断値

随伴感度は、単独の更新則ではありません。
状態求解が収束していること、残差とヤコビ行列が正しく定義されていること、感度の符号が有限差分と整合することが前提です。

- 状態残差
- 随伴残差
- 加工前の感度とフィルター後の感度
- 有限差分または勾配検査

## 失敗・切替の兆候


勾配検査が合わない場合は、更新則より先に微分実装を点検します。
状態残差が大きい場合は、状態方程式と境界条件を確認します。
格子を変えたとき感度の分布だけが大きく変わる場合も、更新を続けません。
コンプライアンスの値がもっともらしくても、感度が誤っていれば場更新は誤った方向へ進みます。

形状変数を扱う場合は、感度の検査対象が密度場から境界や配置パラメータへ移ります。
形状の更新と格子の品質を同じ反復に記録します。
状態求解も対応付け、無効な格子を通った感度を物理的な勾配として扱いません。

### 可視化は正常系から失敗へ読む

1. [場更新の実行記録](#/theater/learning/SCENARIO_TOPOLOGY_SIMP_OC)で、状態求解と感度が密度の更新へ入る位置を確認する
2. [厳しい許容誤差の評価記録](#/theater/learning/SCENARIO_PDE_STATE_TOLERANCE_TIGHT)で、状態残差と随伴残差を同じシミュレーター呼び出し軸で追う
3. [許容誤差/費用比較](#/compare/COMPARE_PDE_STATE_TOLERANCE_COST)で、許容誤差だけを変えた緩い許容誤差実行を開く
4. [状態-求解失敗の評価記録](#/theater/learning/SCENARIO_PDE_STATE_SOLVE_FAILURE)で、失敗を架空の目的値に置き換えず状態区分として読む

前面に置く代表可視化は、全体像・正常系・失敗の3つです。
緩い許容誤差の個別実行は比較が引き受け、同格の入口を増やしません。
各画面は固定格子と固定予算の教育用実行記録であり、実行時間や格子変更への安定性を示しません。

### トポロジー最適化での読み方

SIMPでは、まず密度場から剛性を作り、状態求解で変位を得ます。
その後、随伴感度を使って各要素の密度を増減したときのコンプライアンスの変化を計算します。
この順番を分けて記録すると、更新が止まった原因が「状態方程式の収束」なのか「感度の符号」なのかを切り分けられます。

教育用実行記録では、加工前の感度とフィルター後の感度を同じ反復番号で並べます。
これは実装の実行時間性能を順位付けするためではなく、どの情報が次の密度の更新を決めるかを観察するためです。

## 次に読む

[PDE制約付き最適化](#/formulations/PA045)で、設計変数と状態を分ける定式化を確認します。

[形状最適化の設計変数](#/learn/shape-optimization)で変数の表現の意味を確認し、[SIMP密度法](#/learn/simp-topology)で感度を使う更新を確認します。[密度フィルター](#/learn/density-filter)は離散場の正則化、[形状更新の失敗モード](#/learn/geometry-update-failure-modes)は格子と状態の切り分けを扱います。

## 発展：時間依存系では境界項を落とさない

上の主例は静的な代数方程式です。終端時刻 $T$ を固定した時間依存系 $\dot x=f(x,m)$、$x(0)=x_0(m)$、$J=\int_0^T L(x,m)dt+\Phi(x(T),m)$ へ進むと、同じ符号で $\mathcal L=J-\int_0^T\lambda^T(\dot x-f)dt$ と置き、部分積分します。終端状態が自由なら

$$
-\dot\lambda=L_x+f_x^T\lambda,\quad
\lambda(T)=\Phi_x,\quad
\nabla_m\widehat J=\Phi_m+\int_0^T(L_m+f_m^T\lambda)dt
+\left(\frac{\partial x_0}{\partial m}\right)^T\lambda(0).
$$

右辺の初期条件の項は、$x_0$ が設計に依存する場合に必要です。固定初期条件なら0です。終端等式がある場合は、その乗数による終端条件も加わるため、この自由終端の式をそのまま使いません。PDEでは空間の部分積分と境界条件にも同じ注意が必要です。

離散化した残差を微分する離散随伴と、連続系で随伴を導いて離散化する連続随伴は、有限の格子では一般に同じ勾配とは限りません。検査する有限差分は、実際に最適化している離散目的と同じ求解・境界条件に対して行います。

## 一次資料

[dolfin-adjointの微分の導出](https://www.dolfin-adjoint.org/en/latest/documentation/maths/3-gradients.html) と [Taylor残差による検証](https://www.dolfin-adjoint.org/en/latest/documentation/verification.html) に、随伴の計算と勾配検査が分けて説明されています。次の設計更新を決める手法は [MMA](#/learn/mma) へ進みます。
