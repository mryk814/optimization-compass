---
content_id: ilqr-ddp
kind: method
method_id: M_ILQR_DDP
title_ja: iLQR / DDP
title_en: Iterative LQR / Differential Dynamic Programming
summary: 現在の軌道の周りでdynamicsとcostを二次近似し、backward passでRiccati型のfeedback gainを求め、forward passで軌道を更新する反復的な軌道最適化法です。
source_ids: [S042, S043, S050, S076]
prerequisites: []
related_ids: [multiple-shooting, direct-collocation, dynamic-programming, family.optimal-control]
status: published
last_reviewed: 2026-07-16
---

現在の軌道の周りでdynamicsとcostを二次近似し、backward passでRiccati型のfeedback gainを求め、forward passで軌道を更新する反復的な軌道最適化法です。

## backward passとforward passで何をしているか

現在の候補軌道 $\bar{x}_k, \bar{u}_k$ の周りで、dynamics

$$
x_{k+1} = f(x_k, u_k)
$$

を1次または2次までTaylor展開し、costも2次近似します。backward passでは、終端から時刻を遡りながら価値関数の局所2次modelを更新し、各時刻でLQR部分問題を解いて、

- feedforward項 $k_k$
- feedback gain $K_k$

を求めます。forward passでは、実際のdynamicsに沿って

$$
u_k = \bar{u}_k + \alpha k_k + K_k(x_k - \bar{x}_k)
$$

でcontrolを計算し、軌道を再simulationします。$\alpha$はline searchのstep lengthで、costが改善しない場合は縮小して再試行します。改善した軌道を次の反復の$\bar{x}_k, \bar{u}_k$として、backward / forward passを繰り返します。

## iLQRとDDPの違い

iLQR（iterative LQR）は、dynamicsのTaylor展開を1次項までとし、2次のdynamics項を無視します。これはGauss-Newton近似に相当し、2階微分（Hessian）の計算を避けられる代わりに、非線形性が強いdynamicsでは価値関数の近似精度が落ちます。

DDP（differential dynamic programming）は、dynamicsの2次項（stateとcontrolに関するHessian-vector積相当の項）まで価値関数の展開に含めます。これにより局所的な近似精度は上がりますが、2階微分の計算とその評価costが必要になります。どちらも共通してbackward / forward passのRiccati再帰という骨格を持ち、iLQRはDDPの1次近似版として位置づけられます。

## direct法（shooting/collocation）との違い

[Direct Shooting](#/learn/direct-shooting)や[Direct Multiple Shooting](#/learn/multiple-shooting)、[Direct Collocation](#/learn/direct-collocation)は、離散化した軌道問題をひとつのNLPとして汎用solver（SQPやinterior-point法）に渡します。これに対しiLQR/DDPは、時間方向の構造を[動的計画法](#/learn/dynamic-programming)と同じ発想で使い、horizon全体のNLPを解く代わりに、時刻ごとの小さなLQR部分問題をbackwardに解いていきます。

この違いから、iLQR/DDPは反復のたびにfeedback gain $K_k$が副産物として得られ、real-time MPCでの再planningに使いやすいという利点があります。一方で、一般のpath制約や不等式制約をRiccati再帰へ組み込むのは、direct法がNLP solverの制約処理をそのまま使えるのに比べて弱点になりがちです。多くの実装は無制約または簡単なbox制約までを標準としており、一般制約を厳密に扱いたい場合はdirect collocationのような定式化を検討します。

## 向いている条件

- dynamicsが滑らかで微分可能（1次または2次の微分が計算できる）
- 高速なlocal trajectory refinementが必要（real-time MPCでの再planningなど）
- 良い初期軌道の推測を用意できる
- feedback則（$K_k$）を制御則としてそのまま使いたい

避ける／切り替える条件:

- dynamicsが未同定、または強くstochasticでmodel mismatchが大きい
- 不連続なevent（衝突、切り替えなど）をmeshやhybrid構造で明示していない
- 一般のpath制約や不等式制約が本質的で、Riccati再帰では扱いにくい
- real-time deadlineに対してbackward / forward passの計算時間が合わない

## Python

Riccati型のbackward passは2階微分の扱いも含めて実装が細かく、numpy/scipyだけで忠実に再現すると本質を見誤りやすい手法です。ここでは反復の骨格だけを教育用pseudocodeで示します。

```text
initialize trajectory: xbar[0..N], ubar[0..N-1]

repeat until cost_change is small or budget exhausted:
    # backward pass
    Vx, Vxx = terminal_cost_gradient_hessian(xbar[N])
    for k = N-1 down to 0:
        Ak, Bk = linearize_dynamics(xbar[k], ubar[k])
        lx, lu, lxx, luu, lux = quadratic_cost_expansion(xbar[k], ubar[k])
        Qx, Qu, Qxx, Quu, Qux = expand_value_function(
            Ak, Bk, lx, lu, lxx, luu, lux, Vx, Vxx
        )  # DDP adds second-order dynamics terms here; iLQR omits them
        Kk, kk = solve_local_lqr(Quu, Qux, Qu)
        Vx, Vxx = update_value_function(Qx, Qxx, Kk, kk, Qu, Quu, Qux)
        store(Kk, kk)

    # forward pass with line search on alpha
    for alpha in candidate_step_lengths:
        x_new, u_new = rollout(xbar, ubar, K, k, alpha)
        if cost(x_new, u_new) < cost(xbar, ubar):
            xbar, ubar = x_new, u_new
            break
```

実際の数値実装は[CasADi](https://web.casadi.org/docs/)や[acados](https://docs.acados.org/)、[Drake MathematicalProgram](https://drake.mit.edu/doxygen_cxx/group__solvers.html)などがiLQR/DDP系のsolverや自動微分によるlinearizationを提供しています。利用versionのAPI、regularizationの入れ方、line-search戦略は公式referenceで確認します。

## 診断値

- defect_norm（forward rollout後のdynamics整合性）
- constraint_violation
- KKT residual（制約付き変種を使う場合）
- mesh_error（離散化を変えたときの解の変化）
- rollout_stability

## 失敗・切替の兆候

- forward passのrolloutが発散し、line searchでcostが改善しない
- backward passで$Q_{uu}$が正定値でなくなり、regularizationを強めても解消しない
- 反復を重ねてもdefectやcostの変化が停滞する
- 離散化の時間刻みを変えると解やcostが大きく変わる
- 一般path制約の違反が反復後も残り続ける

segment分割で感度を抑える定式化は[Direct Multiple Shooting](#/learn/multiple-shooting)、path制約を密に扱いたい場合は[Direct Collocation](#/learn/direct-collocation)、時間構造を使う考え方の原型は[動的計画法](#/learn/dynamic-programming)、軌道最適化手法全体の選び分けは[最適制御・軌道最適化の選び分け](#/learn/family.optimal-control)で確認できます。
