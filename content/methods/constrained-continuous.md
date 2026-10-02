---
content_id: constrained-continuous
kind: method
method_id: MF_CONSTRAINED_NLP
title_ja: 制約付き連続最適化
title_en: Constrained Continuous Optimization
summary: 目的値だけでなく、実行可能性・停留性・有効な制約・停止理由を同時に追い、実行可能な連続解を求める最適化の手法群です。
source_ids: [S017, S029, S030, S055]
prerequisites: [concept.convexity]
related_ids: [concept.convexity, lp-qp-conic, direct-collocation, lbfgsb, family.constrained-nlp, sqp, concept.convex-quadratic-program]
visualization_ids: [constrained-disk-feasible-region]
comparison_ids: []
aliases: [/learn/constrained-continuous]
visualization_aliases: [constrained-disk-feasible-region|/theater/constrained-continuous]
comparison_aliases: []
status: published
last_reviewed: 2026-09-30
---

目的値だけでなく、実行可能性・停留性・有効な制約・停止理由を同時に追い、実行可能な連続解を求める最適化の手法群です。

## 30秒でつかむ

入場が制限された展望台で、いちばん景色の良い場所を探すところを想像してください。
立入禁止の場所がどれほど絶景でも、そこは候補になりません。まず入れる範囲を確かめ、その中で景色を比べます。
制約付きの問題では、目的値が低いだけでは解を採用できません。

- **見るもの**: 目的値、制約の残差、KKT条件の残差、有効な制約
- **動かすもの**: 変数と、制約を扱うための一歩
- **前進の判断**: 実行可能な点を保ったまま、目的値と停留性が改善するか
- **別に確認するもの**: 微分、尺度、初期点、ソルバーの状態
- **恐れていること**: 実行不能な低い目的値、悪条件、階数落ち、誤った許容誤差

**実行可能性・停留性・有効な制約・停止理由を分けて確認し、必ず満たす制約を満たす候補の中で、目的値を比べる**ことが出発点です。
ソルバーの `success` は、実行可能性や局所最適性を、一つで証明する値ではありません。

## 一手の意味

制約付きの問題は、次の形で書けます。$g_i$ は不等式、$h_j$ は等式、$l\le x\le u$ は上下限です。

$$
\min_x f(x)\quad\text{subject to}\quad g_i(x)\le0,\quad h_j(x)=0,\quad l\le x\le u
$$

実行不能な点は、目的値が低くても候補解ではありません。まず「何が必ず満たすべき制約か」と「どの許容誤差まで満たせば実行可能とみなすか」を決めます。

### KKT条件をどう読むか

正則性の下で、局所解は次のLagrangianについて、おおむね次の四つを満たします。

$$
L(x,\lambda,\nu)=f(x)+\sum_i\lambda_i g_i(x)+\sum_j\nu_j h_j(x)
$$

- 主実行可能性: 制約が満たされている
- 停留性: $\nabla_xL=0$
- 双対実行可能性: $\lambda_i\ge0$
- 相補性: $\lambda_i g_i(x)=0$

有効な制約は、解で等号になる不等式です。目的の改善方向が制約の境界に遮られ、境界の上が最適になることがあります。

### 制約の扱い方で、一手が分かれる

同じ「制約付きソルバー」でも、一手が何をするかは、制約の扱い方で変わります。

| 方法 | 一手でしていること | 主に必要なもの |
|---|---|---|
| [SQP](#/learn/sqp) / [SLSQP](#/learn/slsqp) | 局所的なQPの部分問題を解き、メリット関数や直線探索で受け入れる | 勾配とヤコビ行列 |
| [内点法](#/learn/interior-point-nlp) | バリアで境界の内側を進み、主・双対の連立方程式を解く | 疎な微分、KKT系の分解 |
| [拡張Lagrangian法](#/learn/augmented-lagrangian) | 制約違反を乗数とペナルティで管理し、内側で制約なしの問題を解く | 内側のソルバー |
| [active-set法](#/learn/active-set) | 有効な制約の集合を更新し、その面の上で解く | 不等式の構造 |
| [射影勾配法](#/learn/projected-gradient) | 勾配の一歩のあとで、単純な集合へ射影する | 安価な射影 |
| 信頼領域を使う制約付きの方法 | 局所的な近似と実行可能性を、半径の内側で管理する | 局所的な近似の質 |

この違いのため、必要な微分・疎性・実行可能な初期点・ソルバーの状態の意味が、手法ごとに異なります。

## 小さな例

円盤の中で、原点にできるだけ近い点を探します。

$$
\min_{x,y}\ x^2+y^2\quad\text{s.t.}\quad g(x,y)=(x-1)^2+(y-1)^2-1\le0
$$

原点が目的の最小点ですが、円盤の外にあります。四つの候補点を、目的値だけでなく、実行可能性と停留性で調べます。
停留性の残差は、有効な制約があるとき、乗数 $\lambda\ge0$ を最も合うように選んだ $\|\nabla f+\lambda\nabla g\|$ です。

| 候補点 | 目的値 | 制約値 $g$ | 実行可能か | 勾配 $\nabla f$ | 停留性の残差 |
|---|---:|---:|---|---|---:|
| $(0,\,0)$ | 0 | 1.0 | いいえ（違反 1.0） | $(0,\,0)$ | 適用外 |
| $(0.5,\,0.5)$ | 0.5 | −0.5 | はい（内部） | $(1,\,1)$ | 1.414 |
| $(1,\,0)$ | 1.0 | 0 | はい（境界上） | $(2,\,0)$ | 2.0 |
| $(0.2929,\,0.2929)$ | 0.1716 | 0 | はい（境界上） | $(0.586,\,0.586)$ | 0 |

$(0,0)$ は、目的値が最小の $0$ ですが、$g=1$ で実行不能です。停留性を見る以前に、候補から外れます。

$(0.5,\,0.5)$ は実行可能ですが、円盤の内部で、勾配が $0$ ではありません。制約は効いておらず、原点の方向へまだ下れます。
$(1,\,0)$ は境界の上にありますが、勾配 $(2,0)$ と制約の勾配 $(0,-2)$ はつり合いません。境界に沿って、目的値がまだ下がる方向があります。

$(0.2929,\,0.2929)$ だけが、KKT条件を満たします。勾配 $(0.586,\,0.586)$ を、制約の勾配 $\nabla g=(-1.414,\,-1.414)$ の $\lambda=0.4142$ 倍が打ち消します。この $\lambda=\sqrt2-1$ が乗数です。
乗数が $0$ 以上で、制約が有効なので、停留性・双対実行可能性・相補性がそろいます。

![円内の実行可能領域に対して、制約を評価する経路は境界上の既知最適点へ到達し、制約を無視する経路は目的値を下げながら円外の実行不能点へ進む固定2次元実行結果。](./media/constrained-feasibility-execution.svg "同じ目的関数と初期点で、制約を評価する経路と無視する経路を実行した結果です。SLSQPやBFGSの実装性能は示しません。")

図の青緑の経路は、目的値と制約違反を同時に下げ、境界で止まります。
橙の経路は、目的値0へ近づきます。しかし制約違反が残るので、候補解になりません。

この手法群の記事は、二つの小さな例を使います。この円盤の問題は、[SQP](#/learn/sqp)と[射影勾配法](#/learn/projected-gradient)が使います。
[凸二次計画](#/learn/concept.convex-quadratic-program)の小さな例は、[SLSQP](#/learn/slsqp)・[非線形内点法](#/learn/interior-point-nlp)・[拡張Lagrangian法](#/learn/augmented-lagrangian)・[active-set法](#/learn/active-set)が使います。

## 向く条件・避ける条件

制約付きの手法群は、連続変数で、目的と制約が滑らかな問題に向きます（[制約付きNLP](#/formulations/PA009)）。選ぶ前に、次の項目を確認します。

| 項目 | 確認内容 |
|---|---|
| 必ず満たす制約 | 何を必ず満たす必要があるか |
| 許容誤差 | 実行可能性と停留性を、どの閾値で判定するか |
| 変数の型 | 連続変数だけか、離散の条件が混ざるか |
| 微分 | 目的と制約の勾配・ヤコビ行列を得られるか |
| 初期点 | 実行不能な初期点や、実行可能な初期点の条件は何か |
| 構造 | 疎性・上下限・凸性を利用できるか |

先に別の定式化を検討する条件です。

- LP・凸QP・錐の形 → [専用の凸ソルバー](#/learn/lp-qp-conic)（[凸二次計画](#/learn/concept.convex-quadratic-program)）
- 等式を、変数の消去で安全に除ける → 次元を減らす
- 上下限だけ → [L-BFGS-B](#/learn/lbfgsb)（[上下限付きの滑らかな最小化](#/formulations/PA008)）
- 軌道の力学が中心 → [Direct Collocation](#/learn/direct-collocation)
- 射影が閉じた式で得られる → [射影勾配法](#/learn/projected-gradient)や近接法

### 初期点

ソルバーによって、初期点の条件が異なります。

- 実行不能な初期点を許す
- 第一段階（phase-I）で、実行可能な点を探す
- 厳密に内部の初期点を必要とする
- 上下限へ射影する

初期点が実行不能なとき、目的の改善より先に、制約の回復（restoration）が進むことがあります。

### 尺度と微分

制約値・変数・目的の尺度が大きく違うと、KKT系が悪条件になります。次の項目を確認します。

- 勾配とヤコビ行列の方向微分による照合
- 疎なパターン
- 有限差分の刻み幅
- 変数の尺度
- 制約の正規化
- ヘッセ行列または準Newton法の選択
- 分解の状態

## Python

次の例は、上の小さな例の円盤の問題を、SLSQPで解きます。そのうえで、ソルバーの `success` に頼らず、違反・乗数・停留性の残差を自分で再計算します。

```python
import numpy as np
from scipy.optimize import minimize

center = np.array([1.0, 1.0])


def objective(x: np.ndarray) -> float:
    return float(x @ x)


def gradient(x: np.ndarray) -> np.ndarray:
    return 2.0 * x


def disk(x: np.ndarray) -> float:
    """SciPyの規約: ineq は関数値が 0 以上で実行可能。(x-1)^2 + (y-1)^2 <= 1 を表す。"""
    return float(1.0 - (x - center) @ (x - center))


def disk_gradient(x: np.ndarray) -> np.ndarray:
    return -2.0 * (x - center)


result = minimize(
    objective,
    x0=np.array([1.5, 1.5]),
    jac=gradient,
    method="SLSQP",
    constraints=[{"type": "ineq", "fun": disk, "jac": disk_gradient}],
    options={"ftol": 1e-10, "maxiter": 200},
)

# ソルバーの success ではなく、自分で再計算した値で判定する。
x = result.x
violation = max(0.0, -disk(x))
a = disk_gradient(x)
multiplier = max(0.0, float(gradient(x) @ a) / float(a @ a))
stationarity = np.linalg.norm(gradient(x) - multiplier * a)
print(result.success, x.round(5), round(result.fun, 5))
print(f"違反 {violation:.1e}, 乗数 {multiplier:.5f}, 停留性の残差 {stationarity:.1e}")
```

```text
True [0.29289 0.29289] 0.17157
違反 2.3e-12, 乗数 0.41421, 停留性の残差 1.4e-15
```

答えは、上の表の4番目の点と一致します。乗数 $0.41421$ は $\sqrt2-1$ です。
SciPyの `ineq` は、関数値が0以上を実行可能とみなします。モデリングシステムごとに、制約の符号の規約を確認します。

## 診断値

- 最大制約違反
- 等式制約の残差
- 停留性、またはKKT残差
- 相補性
- 有効な制約
- 目的値と、実行可能な最良の目的値
- 一歩のノルム、信頼半径、バリアの強さ
- 関数・勾配・ヤコビ行列の評価回数
- 終了の理由

[Feasible-region Theater](#/theater/constrained-continuous)では、制約なしの最適点・実行可能領域・制約付きの最適点・失敗の対比を、区別して表示します。

判断の目安です。最大制約違反と停留性の残差が、どちらも許容誤差以下なら止めます。
目的値・実行可能性・停留性・停止理由は、一つのスコアにまとめず、それぞれの許容範囲とともに保存します。

::: warning
目的値が良い実行不能な点と、目的値はやや悪い実行可能な点を、同じランキングへ入れません。実行可能性・最適性・許容誤差を、別々に報告します。
:::

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処 |
|---|---|---|
| 制約違反が減らない | 実行不能なモデル、または初期点が悪い | 制約の矛盾を確認する。実行可能な点を探す |
| KKT残差が停滞する | 尺度が悪い、または微分が不正確 | 尺度を揃える。微分を有限差分と照合する |
| `success` なのに違反が許容誤差を超える | ソルバー内部の許容誤差が、求める許容誤差と違う | 違反を自分で再計算する。許容誤差を見直す |
| ヤコビ行列の階数が落ちる、制約想定が崩れる | 冗長な制約、または退化 | 冗長な制約を除く。[拡張Lagrangian法](#/learn/augmented-lagrangian)を検討する |
| ペナルティを増やすと悪条件になる | ペナルティ法の限界 | 乗数を使う方法（[拡張Lagrangian法](#/learn/augmented-lagrangian)）へ切り替える |
| 尺度が悪く、一歩が極端に小さい | 変数・制約の尺度の不揃い | 変数と制約を正規化する |
| 非滑らか、またはノイズのある制約を、滑らかなNLPに入れている | 微分の前提が崩れている | 別の定式化を検討する |
| 離散の条件を、連続緩和の丸めだけで済ませている | 緩和の解が、離散の条件を満たさない | 離散の手法を検討する |

## 次に読む

- [制約付きNLP](#/formulations/PA009)：この手法群が解く問題の標準形
- [制約付き非線形最適化の選び分け](#/learn/family.constrained-nlp)：条件ごとの手法の選び分け
- [SQP](#/learn/sqp)：局所的なQPを毎回解く、代表的な枠組み
- [非線形内点法](#/learn/interior-point-nlp)：バリアで境界の内側を進む、大規模向けの方法
