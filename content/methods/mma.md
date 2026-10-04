---
content_id: mma
kind: method
method_id: M_MMA
title_ja: MMA
title_en: Method of Moving Asymptotes
summary: MMAは、目的と制約を変数分離形の凸関数で近似し、移動漸近線を更新しながら、制約で結び付いた近似問題を解く逐次近似手法です。
source_ids: [S100]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [optimality-criteria-topology, simp-topology]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/mma]
status: published
last_reviewed: 2026-10-03
---

MMAは、目的と制約を変数分離形の凸関数で近似し、移動漸近線を更新しながら、制約で結び付いた近似問題を解く逐次近似手法です。

## 30秒でつかむ

地図を一度に信じて遠くへ進まず、現在地の周囲の近似を作り直しながら設計を変えます。

- 見るもの: 目的と制約の感度、更新履歴
- 動かすもの: 設計変数と上下の漸近線
- 前進の判断: 元の問題の可行性と目的値が改善すること

## 一手の意味

上下の漸近線へ近づくほど近似値が大きくなる、逆数の項を使います。

$$
\tilde f_i(x)=r_i+\sum_j\left(\frac{p_{ij}}{U_j-x_j}+\frac{q_{ij}}{x_j-L_j}\right),\qquad p_{ij},q_{ij}\ge0
$$

係数を現在点の値と感度に合わせ、上下限と更新幅の範囲で近似問題を解きます。

### 更新問題を近似して解く

元の目的関数や制約をそのまま一度に解くのではなく、現在点の周辺で近似問題を作ります。
各変数の近似には上下の漸近線があり、反復の履歴に応じて次の更新範囲が変わります。

トポロジー最適化では、密度場の各要素が大量の設計変数になります。
MMAはこのような変数数の多い制約付き問題を、感度情報を使う逐次更新として扱います。

### OCとの違い

OCはコンプライアンス最小化と体積率の構造に強く結びついた更新則です。
MMAは近似問題を毎回組み立てるため、追加の制約や異なる目的へ拡張しやすい一方、漸近線や近似の設定を持ちます。

同じ問題で比べるときは、MMAが一般に優れていると決めつけません。
生成器／予算／初期密度／制約／フィルターを揃えます。
密度場の変化と停止状態を一緒に見ます。

MMAの「凸な近似」は、元のトポロジー最適化問題が凸になるという意味ではありません。
各反復で解く近似部分問題の形を管理し、制約違反や過大な更新を抑えながら、元の非線形問題の局所的な改善を積み重ねます。
したがって、近似問題が解けたことと、元の問題の大域最適性や製造可能性が示されたことを分けて記録します。

## 小さな例

### 固定幅の逆数近似から始める

1変数の $f(x)=(x-2)^2$ で、漸近線の間に近似を作る操作を追います。
現在点 $x_k$ の上下1に漸近線を置き、更新幅を0.5以下にします。
正負の勾配を分け、各係数に0.01を足した逆数近似を使います。

| 反復 | 漸近線 $(L,U)$ | 更新後の $x$ | 元の目的 $f(x)$ |
|---|---|---:|---:|
| 1 | $(-1,1)$ | 0.5 | 2.25 |
| 2 | $(-0.5,1.5)$ | 1.0 | 1.00 |
| 3 | $(0,2)$ | 1.5 | 0.25 |

近似の最小点は更新幅の外にあるため、3回とも更新幅の端を採ります。
これは固定幅の漸近線と制約のない逆数近似の教材です。
履歴に応じた漸近線調整や制約付き部分問題を持つ完全なMMA実装ではありません。

### 近似が現在点で「値と傾き」を合わせる理由

導入の固定幅では $U-x_k=x_k-L=1$ でした。幅が変わる場合には、その距離も係数へ入れます。$g_i=f_i'(x_k)$、$g_i^+=\max(g_i,0)$、$g_i^-=\max(-g_i,0)$ として

$$
p_i=(U-x_k)^2(g_i^++\varepsilon_i),\quad
q_i=(x_k-L)^2(g_i^-+\varepsilon_i),
$$
$$
r_i=f_i(x_k)-\frac{p_i}{U-x_k}-\frac{q_i}{x_k-L}
$$

と置けば、$\widetilde f_i(x_k)=f_i(x_k)$ かつ $\widetilde f_i'(x_k)=g_i$ です。導入の $0.01$ は教材用の正則化です。次の拡張コードは、Svanbergの2007年版係数に合わせ、$\varepsilon_i=0.001|g_i|+\rho/(x_{\max}-x_{\min})$、$\rho=10^{-5}$ を使います。

逆数近似は $(L,U)$ の中で凸ですが、接触する値と傾きが正しくても、元関数全体の上界になるとは限りません。「凸な部分問題」と「保守的な近似」は別の性質です。

### 同じ目的に、一つの非線形制約を足す

今度は $f_0(x)=(x-2)^2$ を保ち、$f_1(x)=x^2-1.25^2\le0$、$0\le x\le3$ を加えます。元問題の可行域は $[0,1.25]$。この区間で目的は減少するので、答えは $x^*=1.25$、費用は0.5625です。

各回、目的だけでなく制約にも逆数近似を作り、$\widetilde f_1(x)\le0$ を部分問題の中で課します。近似目的を最小化した後に、都合よく元制約へ押し戻す処理ではありません。

漸近線、元の上下限、move limitは別のものです。

- 漸近線 $L,U$：逆数近似の曲がり方を決める。元の可行領域の端とは限らない
- 元の上下限 $0,3$：設計変数の条件
- move limit $|x-x_k|\le0.5$：この教材で加えた一回の移動上限

さらに漸近線へ近づきすぎないよう、$x\in[0.9L+0.1x_k,\,0.9U+0.1x_k]$ とし、これら三つの区間の共通部分を $[\alpha,\beta]$ にします。

![固定幅の導入toyの元目的と逆数近似、制約付き3手目の元制約と近似制約、実行履歴、人工的な同方向と反転履歴による漸近線規則の検査を示す4パネル図。](./media/mma-reciprocal-constraints.svg "左上は既存の固定幅toy。右上と左下は同じ目的にx²≤1.25²を足した実行。右下は規則を確かめるために指定した履歴で、最適化実行のログではない。")

### 漸近線の幅は、直前の二つの動きを見て変える

最初の2回は、変数の範囲幅3の半分を両側へ取り、$L=x_k-1.5,U=x_k+1.5$ とします。以後、

$$
s=(x_k-x_{k-1})(x_{k-1}-x_{k-2})
$$

が正なら距離を1.2倍、負なら0.7倍、0なら維持する規則を使います。具体的には

$$
L_k=x_k-\gamma(x_{k-1}-L_{k-1}),\quad
U_k=x_k+\gamma(U_{k-1}-x_{k-1}).
$$

同方向が続くと広げ、向きが反転すると狭める仕組みです。コードでは過小・過大な距離にも上限下限を設けます。これらの倍率は一つの標準的な設定であり、すべてのMMA実装に固定された数ではありません。

図の右下は、旧距離を1に固定した単体テストです。履歴 $(0.6,0.8,1.0)$ なら現在点1の両側距離は1.2、$(1.0,1.2,1.0)$ なら0.7です。本例の実際の最適化は単調に進むため、反転分岐を通ったと装わず、別の履歴で検査しています。

| 提案番号 | 現在点 | 次の候補 | 元の制約 $f_1$ | 距離倍率 |
|---|---:|---:|---:|---:|
| 0 | 0 | 0.5000 | -1.3125 | 初期設定 |
| 1 | 0.5000 | 1.0000 | -0.5625 | 初期設定 |
| 2 | 1.0000 | 1.2432 | -0.0170 | 1.2 |
| 3 | 1.2432 | 1.2500 | 約 $-7.27\times10^{-6}$ | 1.2 |
| 4 | 1.2500 | 1.2500 | $10^{-10}$以内 | 1.2 |

3手目では、目的が望む大きな候補を近似制約が止めます。近似制約の境界は約1.2432で、元制約の境界1.25より少し手前です。次の点でモデルを作り直すことで、その差が小さくなります。

### このコードが教える範囲

次の実装は、実際の係数・漸近線履歴・move limit・一つの近似制約を持つ1変数の教材です。スカラーなので可行区間の端を二分系の根探索で求め、目的の解析的な停留点をその区間内へ制限できます。

多変数MMAの汎用部分問題ソルバー、補助変数による制約緩和、GCMMAの保守性を確認する内側反復は含みません。元問題が非可行な初期点でも使える完全実装ではなく、ここで再現した例の範囲に限ります。GCMMAも非凸問題の大域最適解を保証するという意味ではありません。

## 向く条件・避ける条件

感度や近似を、対象の構造に合わせて計算できるか確認します。
実際の制約と必要精度が近似の前提から外れる場合は、[制約付き連続最適化](#/learn/constrained-continuous)で表現を見直します。

## Python

### 導入の固定幅toyを再現する

最初の3回の表を再現します。制約付きMMA全体の実装ではありません。

```python
from math import sqrt

x = 0.0
for iteration in range(1, 4):
    lower, upper = x - 1.0, x + 1.0
    gradient = 2.0 * (x - 2.0)
    p = max(gradient, 0.0) + 0.01
    q = max(-gradient, 0.0) + 0.01
    stationary = (sqrt(q) * upper + sqrt(p) * lower) / (sqrt(p) + sqrt(q))
    candidate = max(x - 0.5, min(x + 0.5, stationary))
    print(iteration, lower, upper, candidate, (candidate - 2.0) ** 2)
    x = candidate
```

### 制約付きの小例を再現する

```python
import numpy as np
from scipy.optimize import brentq

# Scalar worked example using MMA reciprocal coefficients and asymptote history.
# No slack variables, no GCMMA inner loop; not a general MMA implementation.
def values(x):
    return np.array([(x - 2)**2, x*x - 1.25**2])

def gradients(x):
    return np.array([2 * (x - 2), 2 * x])

def approximation(x, L, U):
    g = gradients(x)
    positive, negative = np.maximum(g, 0), np.maximum(-g, 0)
    p = (U - x)**2 * (1.001 * positive + .001 * negative + 1e-5 / 3)
    q = (x - L)**2 * (.001 * positive + 1.001 * negative + 1e-5 / 3)
    r = values(x) - p / (U - x) - q / (x - L)
    return p, q, r

def solve():
    x = 0.0
    points, history = [], []
    previous_L = previous_U = None
    for k in range(15):
        if k < 2:
            L, U, factor = x - 1.5, x + 1.5, 1.0
        else:
            last, older = points[-1], points[-2]
            product = (x - last) * (last - older)
            factor = 1.2 if product > 0 else .7 if product < 0 else 1.0
            L = x - np.clip(factor * (last - previous_L), .03, 30.)
            U = x + np.clip(factor * (previous_U - last), .03, 30.)
        alpha = max(0., .9 * L + .1 * x, x - .5)
        beta = min(3., .9 * U + .1 * x, x + .5)
        p, q, r = approximation(x, L, U)
        model = lambda z: r + p / (U - z) + q / (z - L)
        # Scalar convex constraint: find the feasible interval around current x.
        low = alpha if model(alpha)[1] <= 0 else brentq(lambda z:model(z)[1], alpha, x)
        high = beta if model(beta)[1] <= 0 else brentq(lambda z:model(z)[1], x, beta)
        stationary = (np.sqrt(q[0]) * U + np.sqrt(p[0]) * L) / (np.sqrt(p[0]) + np.sqrt(q[0]))
        candidate = float(np.clip(stationary, low, high))
        history.append(dict(k=k, x=x, L=float(L), U=float(U), factor=factor,
                            alpha=float(alpha), beta=float(beta), candidate=candidate,
                            f=float(values(candidate)[0]), original_constraint=float(values(candidate)[1]),
                            approximate_constraint=float(model(candidate)[1])))
        points.append(x)
        previous_L, previous_U = L, U
        # For this scalar problem, an active constraint with opposing gradients
        # satisfies the original KKT conditions (within numerical tolerance).
        if (abs(values(candidate)[1]) < 1e-10 and gradients(candidate)[0] < 0
                and gradients(candidate)[1] > 0) or abs(candidate - x) < 1e-10:
            break
        x = candidate
    return history

if __name__ == '__main__':
    for row in solve():
        print(row['k'], round(row['x'], 6), round(row['candidate'], 6),
              round(row['original_constraint'], 6), row['factor'])
```

### 実装で受け渡す情報

```text
asymptotes = update_asymptotes(current_design, design_history)
approximation = build_objective_and_constraint_models(current_design, asymptotes)
candidate = solve_subproblem(approximation, variable_bounds, move_limits)
original_values = evaluate_original_objective_and_constraints(candidate)
record_and_check(candidate, original_values)
```

## 診断値

まず元の目的と元の制約、近似側の制約、接触値・勾配の誤差を別々に記録します。候補が近似制約を満たしても、元の制約を満たしたことにはなりません。上の小例では双方を毎回検査しています。

トポロジー最適化へ進んだ場合は、`compliance`と`volume_fraction`を保存します。
近似問題の更新幅とその上限に加え、中間密度率と交互模様の指標も保存します。
近似問題が元の問題をどの程度表しているかは、反復ごとの値で確認します。

## 失敗・切替の兆候

更新が振動する、または体積率を守っても荷重経路が安定しない場合は、漸近線と更新幅の上限を点検します。
近似問題の設定に結果が強く依存する場合も同様です。
構造が単純なコンプライアンス最小化に戻るなら、OCとの比較を残して選び分けます。

## 次に読む

[OCとMMAの比較](#/compare/COMPARE_TOPOLOGY_OC_MMA)で同じ密度場を読み、[SIMP密度法](#/learn/simp-topology)で感度がどこから来るかを確認します。

- 問題の形を確認する: [PDE制約付き最適化](#/formulations/PA045)

## 一次資料と検算

原著は Svanberg (1987), [The method of moving asymptotes—a new method for structural optimization](https://doi.org/10.1002/nme.1620240207) です。拡張例の係数と履歴規則は、同著者の2007年技術資料「MMA and GCMMA, versions September 2007」の式(3.2)〜(3.9)に対応します。[COMSOL公式文書](https://doc.comsol.com/6.3/doc/com.comsol.help.opt/opt_ug_solver.8.16.html) では古典的MMAと内側反復を持つGCMMAを区別しています。

本例は値と勾配の接触を解析式・中心差分で検査し、各部分問題を独立なSLSQPと照合しています。最後は元問題の解析解1.25と比較します。大規模な密度場の性能や製造可能性を検証したものではありません。
