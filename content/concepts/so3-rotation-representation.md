---
content_id: concept.so3-rotation-representation
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_VARIABLE_MANIFOLD
title_ja: リー代数で回転を動かす：SO(3)の接空間
title_en: Moving Rotations with the Lie Algebra of SO(3)
summary: 回転を最適化するときは、行列の9つの成分を直接動かさず、今の向きから「どの軸のまわりに何rad回すか」を3つの数で決めます。3つの数が自由に動ける平らな空間がリー代数で、それを回転に変えるのが指数写像です。
source_ids: [S044, S045, S071, S107]
prerequisites: [concept.manifold]
related_ids: [concept.so3-se3-optimization, concept.manifold, concept.variable-domain, family.manifold, riemannian-gradient, riemannian-trust-region]
visualization_ids: [so3-projected-alignment, so3-riemannian-alignment]
comparison_ids: [COMPARE_SO3_PROJECTED_RIEMANNIAN]
status: published
last_reviewed: 2026-10-30
---

回転を最適化するときは、行列の9つの成分を直接動かさず、今の向きから「どの軸のまわりに何rad回すか」を3つの数で決めます。3つの数が自由に動ける平らな空間がリー代数で、それを回転に変えるのが指数写像です。

## 30秒でつかむ

[SO(3)/SE(3)上の最適化](#/learn/concept.so3-se3-optimization)の箱の例を使います。箱に付けた4つのマーカーをカメラで測り、設計図の4点を回して測定に重ねたい場面です。向きは $3\times3$ の回転行列で表し、少しずつ直して二乗和を減らします。

ところが、行列の9つの成分のどれを少し増やしても、行列は回転でなくなります。箱を伸ばしたり、ゆがめたりする行列になってしまいます。回転行列の集合は、9次元の空間の中で曲がった面になっているからです。

一方で、「今の向きからこの軸のまわりにこれだけ回す」という指示なら、いつでも回転のままでいられます。この指示は、向きが軸で長さが角度の矢印、つまり3つの数で書けます。

- **動かすもの**: 3つの数 $\delta$（今の向きから回す軸と角度）。制約なしに自由に選べる
- **回転に変える仕組み**: 指数写像 $\exp$。どんな $\delta$ からも回転行列を作る
- **毎回すること**: 向きを $R\leftarrow R\exp(\hat\delta)$ と更新し、$\delta$ を0に戻して次の一歩を決める

3次元の回転は紙の上に描けないので、平面の回転で同じ仕組みを見ます。平面の回転行列は次の形で、$a^2+b^2=1$ を満たします。

$$
\begin{pmatrix}a&-b\\ b&a\end{pmatrix}
$$

そのため、点 $(a,b)$ として描くと、回転はちょうど半径1の円に並びます。単位行列 $I$ は点 $(1,0)$ です。図では、「接線 θJ」の目盛り1にある橙の点 I+J と、円の上で目盛り1の位置にある紺の点 exp(J) を見比べてください。

![平面の回転行列を点(a, b)で表した図。回転は半径1の円に並び、単位行列Iは(1, 0)。Iでの接線の点I+θJは円の外にあり、θ=1のI+Jは(1, 1)で行列式2。exp(θJ)は接線を円に巻き付けた点で、θ=1のexp(J)は(0.540, 0.841)、Iからの弧の長さは1。目盛り0.5, 1, 1.5, 2は、接線と円で同じ長さに対応する。](./figures/so3-lie-algebra-circle.svg "平面の回転（角度1つ）での図です。3次元では、接線が3方向に広がる平らな空間になります。回転どうしの掛け算の順番による違いは、平面の図には現れません")

1. 接線の上の点 $I+\theta J$ は、$a=1$、$b=\theta$ の行列です。$\theta$ は自由に選べますが、行列式は $1+\theta^2$ で、$\theta=1$ では2です。面積を2倍にする行列なので、回転ではありません。
2. exp(J) は円の上の点 $(\cos 1,\sin 1)=(0.540,\,0.841)$ で、1 rad 回す回転です。$I$ からの弧の長さが、ちょうど接線の目盛りの1と同じです。接線のほかの目盛りも、円の上の同じ数の目盛りに移ります。$\exp$ は、接線を円に巻き付ける写像だと読めます。
3. $\theta$ が小さいうちは、接線の点と円の点はほとんど重なります。2点の距離は $\theta=0.1$ で0.005です。$\theta=0.5$ では0.124、$\theta=1$ では0.486に広がります。

平面では、接線は1本で、自由な数は角度1つでした。3次元の回転では、この接線にあたるものは何でしょうか。そして、3つの数はどうやって回転になるのでしょうか。

## リー代数を読む

### 足し算では回転のままでいられない

回転行列どうしを足したり平均したりすると、一般に回転ではなくなります。箱の例で、単位行列と答えの回転 $R_\star$（約160°の回転）の平均 $(I+R_\star)/2$ を作ると、行列式は0.031です。3つの列の長さは0.31から0.81に縮み、箱を大きく縮める行列です。

一方、回転を2回続けた $R_1R_2$ は、必ず回転です。回転の集合は、掛け算では閉じていて、足し算では閉じていません。このため、向きの更新は「足す」ではなく「回転を掛ける」で行います。

### 単位行列のそばの回転は、3つの数で決まる

単位行列から少しずつ回っていく回転 $R(t)$ を考えます（$R(0)=I$）。どの時刻でも $R(t)^{\mathsf T}R(t)=I$ なので、$t=0$ で微分すると、動き出しの速さ $\Omega=\dot R(0)$ は次の条件を満たします。

$$
\Omega^{\mathsf T}+\Omega=0
$$

この条件を満たす行列を歪対称行列と呼びます。対角は0で、残りの成分は3つの数 $\omega=(\omega_1,\omega_2,\omega_3)$ で決まります。3つの数を行列に並べる操作を、ハット $\hat{\ }$ で書きます。

$$
\hat\omega=\begin{pmatrix}0&-\omega_3&\omega_2\\ \omega_3&0&-\omega_1\\ -\omega_2&\omega_1&0\end{pmatrix}
$$

この式は「点 $p$ を、軸 $\omega$ のまわりに回すときの速度」を表します。実際、$\hat\omega p=\omega\times p$（外積）です。つまり $\omega$ は角速度のベクトルで、向きが回転軸、長さが回る速さです。

歪対称行列は、足しても数倍しても歪対称のままです。そのため、歪対称行列の全体は制約のない3次元の平らな空間になります。この空間を $\mathfrak{so}(3)$ と書き、$SO(3)$ のリー代数と呼びます。30秒でつかむの図の接線にあたるのが、この空間です。単位行列以外の向き $R$ では、接空間は $R\Omega$（$\Omega$ は歪対称）の形の行列の集まりになります。

| 記号 | 意味 | 箱の例では |
|---|---|---|
| $R$ | 今の向き（回転行列） | 単位行列から始め、最後は約160°の回転 $R_\star$ |
| $\delta\in\mathbb{R}^3$ | 今の向きから回す量。向きが軸、長さが角度（rad） | 最初の一歩で $(0.420,\,0.050,\,0.267)$、長さ0.501 rad（28.69°） |
| $\hat\delta$ | $\delta$ を並べた歪対称行列。$\mathfrak{so}(3)$ の要素 | $\hat\delta p=\delta\times p$ |
| $\exp$ | $\mathfrak{so}(3)$ から回転への写像（指数写像） | どの $\delta$ からも回転行列を作る |
| $\log$ | $\exp$ の逆。回転から3つの数へ戻す | $R_\star$ では長さ2.787 rad（159.69°） |

### exp：3つの数を回転にする

次の式は「角速度 $\hat\omega$ で1秒間回し続けたときの向き」を表します。

$$
\exp(\hat\omega)=I+\hat\omega+\frac{1}{2!}\hat\omega^2+\frac{1}{3!}\hat\omega^3+\cdots
$$

$\theta=\lVert\omega\rVert$ とおくと、この無限和は次の短い式（Rodriguesの式）にまとまります。

$$
\exp(\hat\omega)=I+\frac{\sin\theta}{\theta}\hat\omega+\frac{1-\cos\theta}{\theta^2}\hat\omega^2
$$

この式は「軸 $\omega/\theta$ のまわりに $\theta$ rad 回す回転」と読みます。平面の図の巻き付けと同じく、矢印の長さがそのまま回転角になります。

どんな $\omega$ を選んでも、$\exp(\hat\omega)$ は必ず回転です。理由は2つの短い計算で確かめられます。

- 転置すると $\exp(\hat\omega)^{\mathsf T}=\exp(\hat\omega^{\mathsf T})=\exp(-\hat\omega)$ です。$\hat\omega$ と $-\hat\omega$ は掛ける順番を変えても同じです。そのため、2つの指数をまとめて $\exp(-\hat\omega)\exp(\hat\omega)=\exp(0)=I$ になります。
- 行列式は $\det\exp(\hat\omega)=e^{\mathrm{tr}\,\hat\omega}=e^0=1$ です。歪対称行列の対角は0だからです。

そのため、$\delta$ を制約なしに選んで $R\exp(\hat\delta)$ で更新すれば、射影や補正をしなくても行列は回転のままです。

比べる相手として、無限和の最初の2項だけを使った $I+\hat\delta$ を見ます。この行列の行列式は $1+\lVert\delta\rVert^2$ で、平面の図の $1+\theta^2$ と同じ形です。$\delta$ が小さいうちは $\exp(\hat\delta)$ とほとんど同じですが、回転ではありません。

### log：回転から3つの数へ戻す

$\log$ は $\exp$ の逆で、回転行列から回転角 $\theta$ と軸を読み取ります。

$$
\theta=\arccos\frac{\mathrm{tr}\,R-1}{2}
$$

$$
\omega=\frac{\theta}{2\sin\theta}\,\bigl(R-R^{\mathsf T}\bigr)^{\vee}
$$

$(\cdot)^{\vee}$ はハットの逆で、歪対称行列から3つの数を取り出す操作です。箱の例の $R_\star$ では $\mathrm{tr}\,R_\star=-0.876$ なので、$\theta=2.787$ rad（159.69°）です。

2つの回転 $R_1,R_2$ の近さは、$R_1^{\mathsf T}R_2$ の回転角で測ります。式では $\lVert\log(R_1^{\mathsf T}R_2)\rVert$ です。これは、回転の集合の上を最短でたどったときの角度です（Hartleyらの Rotation Averaging）。平面の図で、円の上の弧の長さにあたります。回転角が $\pi$ に近いと、$\log$ が返す軸の向きが入れ替わります。その例は[SO(3)/SE(3)上の最適化](#/learn/concept.so3-se3-optimization)のつまずきやすい点にあります。

### 右から掛けるか、左から掛けるか

更新には $R\exp(\hat\delta)$ と $\exp(\hat\delta)R$ の2通りがあります。右から掛けると、$\delta$ は箱の設計図の座標で表した軸になります。左から掛けると、カメラの座標で表した軸になります。2つは $\exp(\hat\delta)R=R\exp\bigl(\widehat{R^{\mathsf T}\delta}\bigr)$ の関係で結ばれています。行き着く回転の集合は同じですが、同じ3つの数 $\delta$ が表す回し方は違います。

この記事では右から掛ける形を使います。PymanoptのSO(3)も、指数写像を `point @ expm(tangent_vector)` と右から掛ける形で実装しています。

## 最適化の一手にする

次の式は「今の向き $R$ のまわりで、3つの数 $\delta$ だけを変数にした普通の関数を作る」を表します。

$$
\phi_R(\delta)=f\bigl(R\exp(\hat\delta)\bigr),\qquad \delta\in\mathbb{R}^3
$$

$\phi_R$ には制約がありません。$\phi_R(0)=f(R)$ で、$\delta$ をどう選んでも $R\exp(\hat\delta)$ は回転です。そのため、勾配法やGauss–Newton法のような制約のない問題の道具を、$\phi_R$ にそのまま使えます。

### 勾配は3つの数になる

$f$ を行列の9つの成分の関数と見たときの勾配を $G$（$3\times3$）とします。$\phi_R$ の $\delta=0$ での勾配は次の3つの数です。

$$
\nabla\phi_R(0)=\bigl(A-A^{\mathsf T}\bigr)^{\vee},\qquad A=R^{\mathsf T}G
$$

この式は「9つの成分の勾配のうち、回す向きの成分だけを残す」と読みます。$A$ の対称な部分は、箱を伸ばしたり縮めたりする向きの勾配です。回転のままでは動けない向きなので、捨てます。

### Gauss–Newton法では、3つの未知数の最小二乗になる

二乗和 $f(R)=\sum_i\lVert Rp_i-q_i\rVert^2$ では、各点の残差を $\delta$ について一次式で近似します。近似には $\exp(\hat\delta)\approx I+\hat\delta$ を使います。さらに外積の順番を $\delta\times p_i=-\hat p_i\delta$ と入れ替えると、次の式になります。

$$
R\exp(\hat\delta)p_i-q_i\approx\bigl(Rp_i-q_i\bigr)-R\hat p_i\,\delta
$$

右辺は $\delta$ について一次式なので、$\delta$ の3成分を普通の線形最小二乗で決められます。一次の近似を使うのは $\delta$ を決めるときだけです。更新には $\exp$ を使うので、行列は回転のままです。

1回の反復は次の4段です。

1. 今の $R$ で残差（または勾配 $G$）を計算します。本物の $f$ を評価するのはここです。
2. $\phi_R$ を減らす一歩 $\delta$ を、3変数の制約のない問題として決めます。
3. $R\leftarrow R\exp(\hat\delta)$ と更新します。
4. 新しい $R$ のまわりで $\phi$ を作り直します。$\delta$ は0に戻ります。

### なぜ毎回 $\delta$ を0に戻すのか

$\phi_R$ は、今の向きのまわりで描いた平らな地図のようなものです。地球の地図が、描いた場所の近くでだけ正確なのと同じです。遠くまで一つの地図で済ませると、ゆがみがたまります。

ゆがみの原因は、回転の掛け算の順番を入れ替えられないことです。そのため、一般に $\exp(\hat a)\exp(\hat b)\neq\exp(\widehat{a+b})$ です。ただし、$a,b$ が小さいと差も小さく、2つの長さの積の大きさになります。$a=(0.05,0,0)$、$b=(0,0.05,0)$ では、2つの回転の差は0.0716°です。これは $\lVert a\times b\rVert/2$ と一致します。一歩ごとに地図を描き直せば、ゆがみがたまりません。

## 小さな例

データは[SO(3)/SE(3)上の最適化](#/learn/concept.so3-se3-optimization)の小さな例の4つのマーカーで、重心を引いて回転だけの問題にしてあります。初期の向きは単位行列 $I$ で、二乗和は $f(I)=3871.4$ です。閉形式（特異値分解）で求めた答え $R_\star$ の二乗和は1.646で、$I$ から159.69°回した向きです。

### 箱の例・単位行列での勾配を3つの数にする

単位行列での、9つの成分についての勾配 $G$ は次の行列です。$R=I$ なので $A=G$ です。

$$
G=\begin{pmatrix}2550&-456&-374\\ -1045.5&1063&-174.5\\ -145.5&-545&231.5\end{pmatrix}
$$

$G-G^{\mathsf T}$ から3つの数を取り出すと、次のとおりです。

$$
\nabla\phi_I(0)=\begin{pmatrix}-545+174.5\\ -374+145.5\\ -1045.5+456\end{pmatrix}=\begin{pmatrix}-370.5\\ -228.5\\ -589.5\end{pmatrix}
$$

対角の3つの成分は、箱の辺を伸び縮みさせる向きの勾配です。この3つの数には入りません。長さは732.8です。

### 箱の例・最初の一歩をexpで回転にする

Gauss–Newton法の最初の一歩は $\delta=(0.420,\,0.050,\,0.267)$ です。長さは0.501 rad（28.69°）です。同じ $\delta$ を、$\exp$ と、無限和の2項だけの $I+\hat\delta$ で行列にして比べます。

| | $\exp(\hat\delta)$ | $I+\hat\delta$ |
|---|---:|---:|
| 二乗和 | 3428.1 | 3708.9 |
| 行列式 | 1 | 1.251 |
| 回転からのはずれ $\lVert M^{\mathsf T}M-I\rVert$ | 0 | 0.355 |

$I+\hat\delta$ の行列式1.251は、$1+0.501^2$ と一致します。$\exp$ で作った行列は回転のままで、二乗和は3871.4から3428.1に下がります。

### 箱の例・地図を描き直しながら7回進む

同じ手順を7回くり返します。表の $\lVert\delta\rVert$ は、その反復で回した角度です。

| 反復 | $\lVert\delta\rVert$（°） | 二乗和 | $R_\star$ までの角度（°） |
|---:|---:|---:|---:|
| 0 | — | 3871.4 | 159.69 |
| 1 | 28.69 | 3428.1 | 140.00 |
| 2 | 46.55 | 2270.6 | 104.77 |
| 3 | 60.22 | 613.0 | 53.60 |
| 4 | 47.30 | 13.64 | 9.15 |
| 5 | 9.43 | 1.692 | 0.46 |
| 6 | 0.48 | 1.646 | 0.02 |
| 7 | 0.03 | 1.646 | 0.00 |

表は次のように読めます。

- **反復1〜4**: 一歩で30°〜60°回します。大きく回しても、毎回その場で地図を描き直すので、二乗和は毎回下がります。
- **反復5〜7**: 一歩が0.5°、0.03°と小さくなります。今の向きの地図で、もう回す必要がない（勾配が0に近い）ことを表します。二乗和は閉形式の答えと同じ1.646になり、$R_\star$ との差は0.00°です。

7回の間、行列 $R$ は $\lVert R^{\mathsf T}R-I\rVert<10^{-14}$ のまま、つまり常に回転でした。反復の回数は、この例と初期点で決まった値で、方法の速さを比べるものではありません。

## つまずきやすい点

- **$I+\hat\delta$ を回転として使い続ける**: $\delta$ の決め方はそのままで、更新を $R(I+\hat\delta)$ にします。8回後の行列は、行列式が6.25で、$\lVert R^{\mathsf T}R-I\rVert=5.95$ です。二乗和は952.0で、1.646に届きません。一歩ごとに行列式が $1+\lVert\delta\rVert^2$ 倍になるからです。更新には $\exp$ か、回転へ戻すレトラクション（ライブラリでの書き方の節）を使います。
- **$\delta$ を足し合わせて1つの回転ベクトルにする**: 小さな例の8回分の $\delta$ を足すと、長さは159.93°です。$R_\star$ の159.69°とほぼ同じです。ところが、足したベクトルの $\exp$ は $R_\star$ から60.81°離れた向きで、二乗和は392.9です。最初の2歩を掛けた回転と、2歩を足してから $\exp$ にした回転だけでも、2.84°違います。向きは行列（または四元数）として持ち、更新は掛け算で重ねてください。
- **右から掛けるための $\delta$ を、左から掛ける**: 小さな例の反復3の向きは、$R_\star$ まで53.60°です。ここで次の $\delta$ を右から掛けると、二乗和は613.0から13.64に下がります。左から掛けると811.47に上がります。単位行列では左右が一致するので、$I$ から始めるテストではこの誤りに気づけません。勾配の式と更新の式で、掛ける側をそろえます。
- **回転の距離を、尺度を確かめずに比べる**: 同じ $I$ と $R_\star$ の距離は、回転角では2.787です。Pymanoptの `dist` は $\log$ の歪対称行列のFrobeniusノルムで、回転角の $\sqrt2$ 倍の3.942になります。行列の差 $\lVert R_\star-I\rVert_F$ は2.784です。勾配の長さも同様で、単位行列での $\nabla\phi_I(0)$ の長さ732.8に対し、Pymanoptの勾配ノルムは518.2（$1/\sqrt2$ 倍）です。停止の許容誤差と最終評価の誤差は、同じ尺度で書きます。

## Python

次のコードは、小さな例とつまずきやすい点の数値をすべて計算します。必要なのは NumPy だけです。

```python
import numpy as np

# 箱の座標でのマーカー p_i と、カメラが測った位置 q_i（単位 cm）。重心を引いて回転だけにする
P = np.array([[0, 0, 0], [30, 0, 0], [0, 20, 0], [0, 0, 10]], dtype=float)
Q = np.array([[50.6, 19.2, 80.1], [25.7, 36.2, 87.0], [49.6, 12.2, 98.2], [56.9, 27.5, 83.0]])
pc, qc = P - P.mean(axis=0), Q - Q.mean(axis=0)


def f(R):
    return np.sum((pc @ R.T - qc) ** 2)


def hat(w):
    """3つの数 w を歪対称行列にする。hat(w) @ p は外積 w × p と同じ"""
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0]])


def vee(S):
    return np.array([S[2, 1], S[0, 2], S[1, 0]])


def exp_so3(w):
    """軸 w/|w| のまわりに |w| rad 回す回転（Rodrigues の式）"""
    theta = np.linalg.norm(w)
    if theta < 1e-12:
        return np.eye(3) + hat(w)
    K = hat(w / theta)
    return np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * K @ K


def angle_deg(R):
    return np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))


def orth(M):
    return np.linalg.norm(M.T @ M - np.eye(3))


def grad_delta(R):
    """f(R exp(hat δ)) を δ の関数と見たときの、δ=0 での勾配（3つの数）"""
    A = R.T @ (2 * (R @ pc.T - qc.T) @ pc)
    return vee(A - A.T)


def gauss_newton_delta(R):
    """R exp(hat δ) p ≈ R p − R hat(p) δ と線形化し、δ の3成分だけを最小二乗で解く"""
    r = (pc @ R.T - qc).ravel()
    J = np.vstack([-R @ hat(p) for p in pc])
    return np.linalg.lstsq(J, -r, rcond=None)[0]


U, _, Vt = np.linalg.svd(qc.T @ pc)
R_best = U @ Vt  # 閉形式の答え（この例では行列式の補正は不要）

# 1. 単位行列での勾配は3つの数
R = np.eye(3)
print(round(f(R), 1), grad_delta(R))  # 3871.4 [-370.5 -228.5 -589.5]

# 2. 同じ δ でも、exp なら回転、I + hat(δ) なら回転ではない
d = gauss_newton_delta(R)
print(d.round(3), round(np.degrees(np.linalg.norm(d)), 2))  # [0.42  0.05  0.267] 28.69
print(round(orth(exp_so3(d)), 12), round(np.linalg.det(exp_so3(d)), 6))  # 0.0 1.0
print(round(orth(np.eye(3) + hat(d)), 3), round(np.linalg.det(np.eye(3) + hat(d)), 3))  # 0.355 1.251

# 3. Gauss–Newton：δ を解き、右から exp を掛け、δ を0に戻す
deltas = []
for k in range(8):
    d = gauss_newton_delta(R)
    deltas.append(d)
    R = R @ exp_so3(d)
    print(k + 1, round(np.degrees(np.linalg.norm(d)), 2), round(f(R), 3), round(angle_deg(R.T @ R_best), 2))
# 1 28.69 3428.085 140.0
# 2 46.55 2270.573 104.77
# 3 60.22 613.028 53.6
# 4 47.3 13.644 9.15
# 5 9.43 1.692 0.46
# 6 0.48 1.646 0.02
# 7 0.03 1.646 0.0
# 8 0.0 1.646 0.0
print(orth(R) < 1e-14)  # True

# 4. δ を足し合わせて1つの回転ベクトルにすると、別の向きになる
w = np.sum(deltas, axis=0)
print(round(np.degrees(np.linalg.norm(w)), 2), round(angle_deg(exp_so3(w).T @ R_best), 2), round(f(exp_so3(w)), 1))
# 159.93 60.81 392.9
a, b = np.array([0.05, 0, 0]), np.array([0, 0.05, 0])
print(round(angle_deg((exp_so3(a) @ exp_so3(b)).T @ exp_so3(a + b)), 4))  # 0.0716

# 5. 更新を I + hat(δ) のままにすると、回転から離れていく
R = np.eye(3)
for k in range(8):
    R = R @ (np.eye(3) + hat(gauss_newton_delta(R)))
print(round(f(R), 1), round(orth(R), 2), round(np.linalg.det(R), 2))  # 952.0 5.95 6.25

# 6. 右から掛けるための δ を、左から掛ける
R = np.eye(3)
for k in range(3):
    R = R @ exp_so3(gauss_newton_delta(R))
d = gauss_newton_delta(R)
print(round(f(R), 2), round(f(R @ exp_so3(d)), 2), round(f(exp_so3(d) @ R), 2))  # 613.03 13.64 811.47

# 7. 同じ2つの回転の「距離」を3通りに測る
theta = np.radians(angle_deg(R_best))
print(round(theta, 3), round(np.sqrt(2) * theta, 3), round(np.linalg.norm(R_best - np.eye(3)), 3))
# 2.787 3.942 2.784
```

1の行は、単位行列での二乗和と、9つの成分の勾配から取り出した3つの数です。2の行は、最初の一歩 $\delta$ を2通りに行列にした結果です。$\exp$ では回転のまま（はずれ0、行列式1）で、$I+\hat\delta$ では行列式が1.251になります。

3の行は、小さな例の表と同じ反復です。各行の4つの値は、反復の番号と回した角度（°）、二乗和と $R_\star$ までの角度（°）です。最後の `True` は、8回の後も行列が回転のままであることを表します。

4から7の行は、つまずきやすい点の数値です。7の行は、同じ2つの回転の距離を3通りに出しています。順に、回転角とPymanoptの `dist` と同じ $\sqrt2$ 倍の尺度、行列の差のFrobeniusノルムです。

## ライブラリでの書き方

ライブラリは、ここまでの「3つの数で一歩を作って回転へ戻す」手順を、多様体という部品にまとめています。回転へ戻す方法は一つではありません。

- **指数写像**: この記事の更新です。PymanoptのSO(3)（`SpecialOrthogonalGroup`）は、接ベクトルを歪対称行列 $\Omega$（リー代数の要素）で持ちます。`exp` は $X\,\mathrm{expm}(\Omega)$ です。
- **レトラクション**: $X+X\Omega$ を作り、QR分解や極分解で回転に戻します。Pymanoptの既定はQR分解です。$\Omega$ が小さいと $\exp$ とほぼ一致しますが、有限の一歩では行き先が違います。小さな例の最初の一歩 $\delta$ では、$\exp$ が28.69°回します。同じ $\delta$ で、QR分解は26.46°、極分解は26.60°しか回しません。行き先の回転は $\exp$ の行き先からそれぞれ3.83°、2.09°離れています。
- **射影**: 9つの成分を普通に動かしてから、最も近い回転へ戻します。戻す前の候補が回転からどれだけ離れていたかが、毎回変わります。行き先は、接空間で作った一歩とは別の更新則で決まります（[SO(3)/SE(3)上の最適化](#/learn/concept.so3-se3-optimization)の30秒でつかむの図）。

どの方法でも反復点は回転ですが、同じ一歩の大きさでも行き先は一致しません。比べるときは、どの写像を使ったかを実験の条件として記録します（Absilらの教科書では、指数写像はレトラクションの一つの例として扱われます）。

## 診断値

| 診断値 | 読み方 |
|---|---|
| $\lVert R^{\mathsf T}R-I\rVert_F$ と $\lvert\det R-1\rvert$ | 行列が回転のままか。$\exp$ で更新していれば丸め誤差の大きさに留まる |
| 一歩の大きさ $\lVert\delta\rVert$ | 今の地図でどれだけ回したか。角度として読める |
| 地図の上の勾配 $\lVert\nabla\phi_R(0)\rVert$ | 回転のままで二乗和を減らせる余地。0に近いと停留点に近い |
| 目的関数の値 | 回転のままでいることとは別に、改善しているか |
| 基準の回転までの角度 $\lVert\log(R^{\mathsf T}R_{\mathrm{ref}})\rVert$ | 向きの誤差。ライブラリの距離の尺度（$\sqrt2$ 倍など）を書き添える |

次の兆候が出たら、更新の書き方を見直します。

- 回転からのはずれが反復とともに増える → 更新が $I+\hat\delta$ のままになっていないか、レトラクションの後で戻しているかを確かめる
- 単位行列から始めると下がるのに、別の初期点では上がる → 勾配の式と更新の式で、掛ける側（右か左か）がそろっているかを確かめる
- QR分解と極分解で結果が変わる → レトラクションを実験の条件として固定する
- 回転角が $\pi$ の近くで向きの誤差が跳ぶ → $\log$ の軸の入れ替わりを疑う

::: warning
反復点がいつも回転であることは、局所解や大域最適解に着いたことを保証しません。回転のままであることと、勾配が0に近づくことは、別々に記録します。
:::

## 事例・可視化・比較で読む

[SO(3)姿勢合わせ事例](#/gallery/so3-attitude-alignment)は、2つの更新経路を同じ教材問題で並べます。一方は9つの成分を動かしてから回転へ戻す射影更新、もう一方は接空間で一歩を作るリーマン更新です。

[射影可視化](#/theater/learning/SCENARIO_SO3_PROJECTED_ALIGNMENT)では、射影を含む更新経路と、回転からのはずれを追えます。[リーマン可視化](#/theater/learning/SCENARIO_SO3_RIEMANNIAN_ALIGNMENT)では、接空間の一歩と、回転からのはずれを追えます。[射影／リーマン比較](#/compare/COMPARE_SO3_PROJECTED_RIEMANNIAN)は、2つの実行を同じ評価予算にそろえて並べます。目的関数の値と回転からのはずれ、射影距離と勾配の大きさは、それぞれ別の診断値として読みます。

## 次に読む

- [SO(3)/SE(3)上の最適化](#/learn/concept.so3-se3-optimization)：箱の例の定式化と、閉形式（特異値分解）の解き方
- [多様体値変数](#/learn/concept.manifold)：球面やStiefel多様体を含む、曲がった集合の上での接空間とレトラクションの共通原則
- [Riemann勾配法](#/learn/riemannian-gradient)と[Riemann信頼領域法](#/learn/riemannian-trust-region)：この記事の一歩を、勾配法と信頼領域法として組み立てる方法
- [Riemann多様体最適化の選び分け](#/learn/family.manifold)：一次法と信頼領域法の使い分け
