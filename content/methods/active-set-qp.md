---
content_id: active-set-qp
kind: method
method_id: M_ACTIVE_SET_QP
title_ja: Active-set QP
title_en: Active-Set QP
summary: 凸二次計画（convex QP）で「どの不等式制約が解で等号になるか」を表す作業集合（working set）を推定・更新しながら、等式制約付きQPを繰り返し解く方法です。
source_ids: [S012, S016, S055, S056]
prerequisites: [concept.convexity]
related_ids: [active-set, admm-qp, barrier-lp-qp, lp-qp-conic, concept.convex-quadratic-program]
status: published
last_reviewed: 2026-09-30
---

凸二次計画（convex QP）で「どの不等式制約が解で等号になるか」を表す作業集合（working set）を推定・更新しながら、等式制約付きQPを繰り返し解く方法です。

## 30秒でつかむ

谷底を探して、柵に囲まれた庭を歩くところを考えます。
柵に触れているあいだは、その柵を手すりにして、手すりに沿って下ります。
下る途中で別の柵にぶつかったら、その柵も手すりに加えます。
いま握っている手すりを離した方が下れると分かったら、その手すりを離します。

握っている手すりの集まりが作業集合（working set）です。

- **見るもの**: 作業集合に入れた制約の乗数の符号と、作業集合の上で最小になる方向
- **動かすもの**: 作業集合（制約を加える・外す）と、その上での位置
- **前進の判断**: 動ける方向があれば進む。方向が0で、乗数がすべて0以上なら最適

LPのsimplex法が頂点を渡り歩くのに対し、QPでは「有効な制約の面」を渡り歩きます。

## 一手の意味

一手は、作業集合を等式とみなした小さなQPを一回解き、その結果で「進む」「制約を加える」「制約を外す」のどれかを決める操作です。

凸QPの標準形を考えます（$P\succeq0$）。

$$
\min_x\; \tfrac{1}{2}x^\top Px+q^\top x \quad\text{subject to}\quad Ax\le b
$$

最適解では、不等式制約の一部だけが等号 $A_ix=b_i$ で成立し、残りの制約には余裕があります。
作業集合 $W_k$ は、等号になると推定した制約の集まりです。

$W_k$ を固定し、いまの点 $x$ から作業集合の面を保ったまま動く方向 $d$ と乗数 $\lambda$ を、次のKKT系（最適性条件の連立方程式）で求めます。

$$
\begin{bmatrix}P & A_{W_k}^\top\\ A_{W_k} & 0\end{bmatrix}
\begin{bmatrix}d\\ \lambda\end{bmatrix}
=
\begin{bmatrix}-(Px+q)\\ 0\end{bmatrix}
$$

この系は「作業集合の面の上で、目的が最も下がる方向」を求める、等式制約付きQPと同じです。結果は次の三通りに分かれます。

- **方向 $d\neq0$**: 動ける。実行可能な範囲まで進み、最初に触れた制約（blocking constraint）を作業集合に加える。
- **方向 $d=0$ で、負の乗数がある**: その制約は手すりにならない。負の乗数の制約を作業集合から外す。
- **方向 $d=0$ で、乗数がすべて0以上**: KKT条件を満たす。凸QPなので最適で止まる。

歩幅 $\alpha$ は、作業集合に入っていない制約 $a_i$ のうち、方向へ進むと近づくものだけを見て決めます。

$$
\alpha=\min\Bigl(1,\ \min_{i\notin W_k,\ a_i^\top d>0}\frac{b_i-a_i^\top x}{a_i^\top d}\Bigr)
$$

$\alpha=1$ のときは、作業集合の面の上の最小点まで着きます。$\alpha<1$ のときは、途中で別の制約に触れて止まります。

制約を外す判断は、点を動かさずに乗数の符号を見て行います。制約を加える判断は、面の上を進んで最初の制約に触れた時点で行います。
「1反復＝1つの等式制約QPを解く」という構造は、[一般NLPのactive-set法](#/learn/active-set)にも共通します。QP専用の実装では、KKT行列がQPの係数だけで決まります。そのため、階数1の更新やSchur補行列を使った分解の更新に特化しやすい点が異なります。

## 小さな例

[凸二次計画](#/learn/concept.convex-quadratic-program)の小さな例を、active-set法で解きます。

$$
\min_{x}\; (x_1-3)^2+(x_2-2)^2 \quad \text{s.t.}\quad x_1+x_2\le 3,\; x\ge 0
$$

目標 $(3,2)$ に最も近い点を、範囲の中から選ぶ問題です。原点（実行可能）から出発し、作業集合を $\{x_1\ge0,\;x_2\ge0\}$ とします。
目的の勾配は $\nabla f=2(x-(3,2))$ です。

| 反復 | 点 | 作業集合 | 方向 $d$ | 乗数 | 起きること |
|---:|---|---|---|---|---|
| 1 | $(0,\,0)$ | $x_1\ge0$, $x_2\ge0$ | $(0,\,0)$ | $(-6,\,-4)$ | 負の乗数がある。最も負の $x_1\ge0$ を外す |
| 2 | $(0,\,0)$ | $x_2\ge0$ | $(3,\,0)$ | | 歩幅1で $(3,\,0)$ へ進み、ちょうど $x_1+x_2\le3$ に触れて加える |
| 3 | $(3,\,0)$ | $x_2\ge0$, $x_1+x_2\le3$ | $(0,\,0)$ | $(-4,\,0)$ | 負の乗数がある。$x_2\ge0$ を外す |
| 4 | $(3,\,0)$ | $x_1+x_2\le3$ | $(-1,\,1)$ | | 歩幅1で $(2,\,1)$ へ進む |
| 5 | $(2,\,1)$ | $x_1+x_2\le3$ | $(0,\,0)$ | $2$ | 乗数が0以上。最適 |

目的値 $(x_1-3)^2+(x_2-2)^2$ は、原点の $13$ から $(3,\,0)$ の $4$ へ、さらに $(2,\,1)$ の $2$ へ下がりました。

反復1では、原点で二本の下限に触れています。二本とも「離した方が下れる」（乗数が負）と示されたので、より強く負の方を外します。
反復2では、$x_1$ 方向に動けるようになり、面の上の最小点 $(3,\,0)$ へ一歩で着きます。この点はちょうど $x_1+x_2=3$ の上にあるので、その制約を作業集合に加えます。

反復3では、$(3,\,0)$ に二本の手すりがあります。$x_2\ge0$ の乗数が負なので、こちらを外します。乗数が $0$ の $x_1+x_2\le3$ は、触れているだけで押し返してはいません。
反復4で、直線 $x_1+x_2=3$ に沿って $(2,\,1)$ まで進みます。反復5の乗数 $2$ は、[凸二次計画](#/learn/concept.convex-quadratic-program)で求めた乗数と一致します。

答え $(2,\,1)$ は辺の途中にあり、頂点ではありません。作業集合が1本になり、その直線の上を動いて最小点に着きました。LPのsimplex法では起きない動きです。

### 別の例を図で見る

次の図は、別の2変数の固定QPを原点から解いた実行です。

![2変数の固定convex QPを原点から解くactive-set実行。原点Aではx1下限制約を外す。x2下限のface上をBまで進んでx1上限制約を加える。同じ点Bでx2下限制約を外す。斜めの制約へ進みCで最適になる。下段はremove → add → remove → add → optimalの5 eventを示す。](./media/active-set-qp-execution.svg "working setから制約を外し、blocking constraintを加える固定active-set QP実行")

図のAとBでは、`direction = 0` のまま負の乗数を持つ制約を外しています。
BとCへ向かう橙の線では、実行可能性を保つ歩幅を選び、最初に触れた制約を加えています。

> この図は2変数の固定convex QPをfeasibleな原点から解いた教材です。
> 目的値は `0.000 → -4.125`、最終点は `(1.5, 0.5)` です。
> degeneracyやcyclingは含みません。
> factorization更新costやactive-set QP一般の性能も示していません。

## 向く条件・避ける条件

LPのsimplex法は、頂点から頂点へ基底を更新しながら進みます。active-set QPは、等号制約の組である作業集合を更新します。この意味で、simplex法のQP版とみなせます。
この類似から、前回の作業集合を初期値として使うwarm startが自然に働きます。特に、次のように直前の解に近いQPを何度も解く場面では、作業集合がほとんど変わりません。そのため、少ない反復で収束しやすくなります。

- model predictive control（MPC）で、毎周期わずかに変わるQPを再解する
- sequential quadratic programmingの部分問題を繰り返し解く
- 上下限が少しずつ変わるポートフォリオの再最適化

| 条件 | 理由 |
|---|---|
| 凸QP（$P\succeq0$）として明示できる | KKT系の対称性・分解の更新がこの構造に依存するため |
| 小中規模、または作業集合の変化が小さいMPC的な再解 | 作業集合の探索回数が少なく済むため |
| warm startできる近接問題を繰り返し解く | 前回の作業集合をそのまま初期値にできるため |
| 高精度な基底や有効な制約の情報が必要 | 等式制約QPを厳密に解くため、中間状態の解釈がしやすいため |

避ける、または切り替える場面は次のとおりです。

- 制約数が多く、作業集合が反復ごとに大きく変わる。正しい作業集合に着くまでの反復数が、組合せ的に増える場合があります。
- 非凸QPを凸として誤って扱っている。$P$ の固有値を確かめます。
- 大規模で疎なQP。[operator-splitting QP](#/learn/admm-qp)や[primal-dual barrier法](#/learn/barrier-lp-qp)のほうが安定することがあります。

## Python

小さな例と図の例を、作業集合を一制約ずつ更新して解きます。
方向が0なら乗数を調べ、動けるなら最初に触れる制約まで進みます。歩幅がちょうど制約に届くときも、その制約を作業集合に加えます。

```python
import numpy as np


def active_set_qp(hessian, linear, a_ub, b_ub, labels, x, working):
    """凸QP  min 1/2 x'Hx + q'x  s.t.  A x <= b  を、実行可能な x と working set から解く。"""
    x, working, events = x.astype(float), list(working), []
    for _ in range(20):
        gradient = hessian @ x + linear
        a_w = a_ub[working]
        kkt = np.block([
            [hessian, a_w.T],
            [a_w, np.zeros((len(working), len(working)))],
        ])
        solution = np.linalg.solve(kkt, np.r_[-gradient, np.zeros(len(working))])
        direction, multipliers = solution[: len(x)], solution[len(x):]

        if np.linalg.norm(direction) <= 1e-10:  # 方向が 0: 乗数の符号を調べる
            if np.all(multipliers >= -1e-10):
                events.append(("optimal", None))
                break
            removed = working.pop(int(np.argmin(multipliers)))  # 最も負の乗数の制約を外す
            events.append(("remove", labels[removed]))
            continue

        step, blocker = 1.0, None  # 動ける: 歩幅は 1 まで、途中で触れた制約で止まる
        for index, normal in enumerate(a_ub):
            if index in working or normal @ direction <= 1e-10:
                continue
            candidate = (b_ub[index] - normal @ x) / (normal @ direction)
            if candidate <= step + 1e-12:
                step, blocker = float(candidate), index
        x = x + step * direction
        if blocker is None:
            events.append(("move", None))
        else:
            working.append(blocker)
            events.append(("add", labels[blocker]))
    return x, events


# 小さな例: min (x1-3)^2 + (x2-2)^2  s.t.  x1 + x2 <= 3, x >= 0（定数 13 を除いた形）
hessian, linear = 2 * np.eye(2), np.array([-6.0, -4.0])
a_ub = np.array([[-1.0, 0.0], [0.0, -1.0], [1.0, 1.0]])
b_ub = np.array([0.0, 0.0, 3.0])
labels = ["x1 >= 0", "x2 >= 0", "x1 + x2 <= 3"]
x, events = active_set_qp(hessian, linear, a_ub, b_ub, labels, np.zeros(2), [0, 1])
print(events)
print(x, 0.5 * x @ hessian @ x + linear @ x + 13)

# 図の例（原点から出発。下の制約が 2 本とも有効な状態で始める）
hessian = np.diag([2.0, 1.0])
linear = np.array([-4.0, -1.0])
a_ub = np.array([[-1.0, 0.0], [0.0, -1.0], [1.0, 0.0], [1.0, 1.0]])
b_ub = np.array([0.0, 0.0, 1.5, 2.0])
labels = ["x1 >= 0", "x2 >= 0", "x1 <= 1.5", "x1 + x2 <= 2"]
x, events = active_set_qp(hessian, linear, a_ub, b_ub, labels, np.zeros(2), [0, 1])
print(events)
print(x, 0.5 * x @ hessian @ x + linear @ x)
```

```text
[('remove', 'x1 >= 0'), ('add', 'x1 + x2 <= 3'), ('remove', 'x2 >= 0'), ('move', None), ('optimal', None)]
[2. 1.] 2.0
[('remove', 'x1 >= 0'), ('add', 'x1 <= 1.5'), ('remove', 'x2 >= 0'), ('add', 'x1 + x2 <= 2'), ('optimal', None)]
[1.5 0.5] -4.125
```

一つ目の出力は小さな例の表と対応し、`remove → add → remove → move → optimal` の順です。最終点は `[2. 1.]`、元の目的値は `2.0` です。
二つ目の出力は図の例で、`remove → add → remove → add → optimal` の順です。最終点は `[1.5, 0.5]`、目的関数値は `-4.125` です。

実務のactive-set型ソルバーは、分解を更新して、等式制約QPを毎回ゼロから解く費用を抑えます。
OSQPのようなoperator-splitting型は、作業集合とは別の反復を使います。利用versionのAPIや既定のパラメータは、[OSQP公式ドキュメント](https://osqp.org/docs/)や[HiGHSドキュメント](https://highs.dev/)で確認します。

## 診断値

- 作業集合の大きさ（有効な制約の数）
- 加えた制約・外した制約
- 等式制約QPを解いたときのstatus
- 主問題・双対問題の残差
- 乗数の符号違反（multiplier sign violation）
- 歩幅と、止めたblocking constraint
- 退化（degeneracy）
- iteration数
- warm startの再利用の有無

判断の目安は次のとおりです。
方向が許容誤差の範囲で0で、乗数がすべて0以上なら、最適で止まります。
制約の加減が繰り返されるなら、作業集合が安定しない原因（退化、$P$ の凸性）を調べます。

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処 |
|---|---|---|
| 作業集合が安定せず、加減を繰り返す | cycling | 退化への対処を持つ実装を使う。許容誤差を確認する |
| 乗数の符号判定が不安定 | 退化。複数の制約が同時に触れている | 許容誤差を確認する。条件の重複した制約を整理する |
| 制約数が多く、分解の更新の費用が支配的になる | 作業集合の変化が大きい | [operator-splitting QP](#/learn/admm-qp)や[primal-dual barrier法](#/learn/barrier-lp-qp)へ切り替える |
| 非凸QP（$P$ が不定）をそのまま扱っている | 凸性の確認漏れ | $P$ の固有値を確かめる。非凸なら別の手法・定式化を検討する |
| infeasibleやunboundedを目的値だけで見落とす | statusを確認していない | statusと残差を必ず記録する |

## 次に読む

- [凸二次計画](#/learn/concept.convex-quadratic-program)：小さな例の問題を定式化から読み直す
- [Active-set法](#/learn/active-set)：一般の非線形制約に対する違い
- [Operator-splitting QP](#/learn/admm-qp)：同じ凸QPを別の反復法で解く考え方
- [Primal-dual barrier法](#/learn/barrier-lp-qp)：内部を通って進む道との対比
- [LP・QP・錐最適化](#/learn/lp-qp-conic)：QPを含む凸最適化familyでの位置づけ
