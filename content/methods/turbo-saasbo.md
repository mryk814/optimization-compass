---
content_id: turbo-saasbo
kind: method
method_id: M_TURBO_SAASBO
title_ja: 高次元Bayesian最適化（TuRBO / SAASBO）
title_en: TuRBO / SAASBO
summary: 高次元では、ガウス過程（Gaussian process）を使うベイズ最適化（Bayesian Optimization, BO）は性能を落としやすくなります。TuRBOは局所的な探索領域（信頼領域）に絞り、SAASBOは有効次元が少ないという仮定を置くことで、この難しさを緩和します。どちらも高次元のベイズ最適化に使う手法です。
source_ids: [S035, S036, S059]
prerequisites: []
related_ids: [bayesian-optimization, smac, family.expensive-black-box]
status: published
last_reviewed: 2026-10-01
---

高次元では、ガウス過程（Gaussian process）を使うベイズ最適化（Bayesian Optimization, BO）は性能を落としやすくなります。TuRBOは局所的な探索領域（信頼領域）に絞り、SAASBOは有効次元が少ないという仮定を置くことで、この難しさを緩和します。どちらも高次元のベイズ最適化に使う手法です。

## 30秒でつかむ

広い地図を一度に細かく調べず、見込みのある近所を重点的に調べるのがTuRBOです。SAASBOは、多数の条件のうち本当に効くものが少ないという仮定を使います。

- 見るもの: 候補の目的値と可行性
- 動かすもの: 次に試す候補と探索の状態
- 前進の判断: 固定した評価予算で良い候補が残ること

## 一手の意味

TuRBOの局所領域は、中心 $x^*$ と長さ $L$ で表します。

$$
\ell_i=\max(0,x_i^*-L/2),\qquad u_i=\min(1,x_i^*+L/2)
$$

これは単位区間へ正規化した等方的な箱です。
実装では座標ごとの長さも調整します。SAASBOの疎な事前分布とは別の仕組みです。

### 高次元で標準的なGP-BOが苦しむ理由

[Bayesian Optimization](#/learn/bayesian-optimization)では、観測全体から予測モデル（通常はガウス過程）を作り、獲得関数（獲得関数）を最大化する点を次に評価します。
次元が増えると、この枠組みは複数の点で不利になります。

- 同じ観測数でも次元あたりの情報密度が下がり、探索空間全体を覆う予測モデルの信頼性が下がる
- 獲得関数自体が高次元関数になり、その大域最適化が難しくなる
- 標準的なBOでは超立方体の境界付近に標本が集中しやすく、中心付近の探索が薄くなりやすい

BOが原理的に使えないわけではありません。
大域の予測モデルと大域の獲得関数の最適化を組み合わせる設計が、次元とともに難しくなるということです。
TuRBOとSAASBOは、この難しさに対する異なる緩和策です。

### TuRBOが何をしているか

TuRBOは、探索全体を1つの大域の予測モデルに任せません。
現在の最良点周辺に**信頼領域**（箱領域）を持ち、その内側だけでBOを回します。

- 信頼領域内の観測だけで局所予測モデルと獲得関数を扱う
- 連続して改善が続けば（成功）信頼領域を拡大する
- 連続して改善が止まれば（失敗）信頼領域を縮小する
- 信頼領域が十分小さくなったら、その領域を放棄し新しい位置から再始動する

局所化すると、予測モデルと獲得関数最適化の対象領域を絞れます。
高次元でも扱いやすい規模に保てます。
探索範囲は狭まります。
その代わり、信頼領域の外側にある大域的に有望な領域を見逃す可能性は残ります。

### SAASBOが何をしているか

SAASBOは、探索空間の次元が多くても、**実際に目的関数へ効く次元は少数**だと仮定します。
この仮定をGPのカーネルに直接組み込みます。
各次元の長さ尺度（またはその逆数）に強い疎性を促す事前分布（horseshoe事前分布など）を与え、完全ベイズ推論で事後分布を求めます。
関係の薄い次元は長さ尺度が大きく（＝影響が小さく）推定され、有効な次元だけが予測モデルの予測に強く寄与します。

TuRBOは探索領域を局所化し、SAASBOは予測モデルの構造そのものに次元選択的な仮定を入れます。
両者は排他的ではありません。
局所信頼領域と疎な事前分布を組み合わせる実装もあります。

## 小さな例

### 局所箱の変化を図で見る

![固定seedの二次元objectiveでtrust regionの中心移動と縮小を示す教材。](./media/turbo-trust-region-execution.svg "TuRBO型trust regionの拡大と縮小")

左は時点の異なる局所箱、右は箱の長さと最良値の改善量の履歴です。
改善した点へ中心を移し、停滞が続くと探索範囲を狭める制御を読み取れます。

> **この図の範囲**
> 次のPython例とは目的関数・乱数生成器・長さ更新の規則が異なり、trust-region controllerだけを実行します。
> Gaussian process・acquisition・SAAS priorは実装していません。
> TuRBOとSAASBOの性能比較でもありません。

### 最初の3候補を数値で追う

Python節の局所箱の教材を、乱数種7で実行しました。
$f(x)=\sum_i(x_i-0.5)^2$、初期点 $(0.8,0.2)$、長さ $0.4$ を使います。
最初の3候補は次のとおりです。

| 更新 | 候補 | 候補の目的値 | これまでの最良値 | 長さ |
|---|---|---:|---:|---:|
| 1 | $(0.850038,0.358886)$ | 0.142440 | 0.142440 | 0.4 |
| 2 | $(0.921499,0.248968)$ | 0.240678 | 0.142440 | 0.4 |
| 3 | $(0.755085,0.508307)$ | 0.065137 | 0.065137 | 0.4 |

候補選択は一様乱数です。GPも獲得関数も用いないため、TuRBOそのものの実行例ではありません。
長さの更新と最良点の保持だけを読み取ります。

## 向く条件・避ける条件

### 向いている条件

- 探索空間の形式次元は高いが、実際に効く次元が少ない、または局所探索で十分と考えられる
- 1評価が高価で、予算が数十〜数百回程度に限られる
- 変数が主に連続で、標準的なGP-BOが獲得関数最適化や境界集中で苦戦している

避ける／切り替える条件:

- 有効次元が実質的に全次元に近く、疎性の仮定（SAASBO）が成立しない
- 大域的に離れた複数の有望領域があり、単一の信頼領域（TuRBO）では取りこぼす
- 評価が安価で大量並列に実行できる場合は、[Random Search](#/learn/random-search)や進化的手法のほうが単純な場合がある
- カテゴリ変数や条件付きパラメータが中心なら、[SMAC](#/learn/smac)のような木に基づく予測モデルを検討する

## Python

次はTuRBOの核となる、局所箱と成功 / 失敗に応じた長さの更新だけを取り出した最小例です。
実際の候補選択は、局所予測モデルと獲得関数が担います。

```python
import numpy as np

rng = np.random.default_rng(7)
best_x = np.array([0.8, 0.2])
best_y = float(np.sum((best_x - 0.5) ** 2))
length = 0.4
successes = 0
failures = 0

for _ in range(12):
    lower = np.maximum(0.0, best_x - length / 2.0)
    upper = np.minimum(1.0, best_x + length / 2.0)
    candidate = rng.uniform(lower, upper)
    value = float(np.sum((candidate - 0.5) ** 2))
    if value < best_y:
        best_x, best_y = candidate, value
        successes, failures = successes + 1, 0
    else:
        successes, failures = 0, failures + 1
    if successes >= 2:
        length = min(1.0, 2.0 * length)
        successes = 0
    elif failures >= 3:
        length = max(0.05, length / 2.0)
        failures = 0

print("best:", best_x, best_y, "trust-region length:", length)
```

TuRBOとSAASBOの実装は、[BoTorch](https://botorch.org/)と[Ax](https://ax.dev/)の公式参照で確認します。
両者を組み合わせた獲得関数最適化や疎なGPの具体的な挙動も、利用する版に対応する説明を参照してください。
標準的なBOの背景は[A Tutorial on Bayesian Optimization](https://arxiv.org/abs/1807.02811)で確認できます。

## 診断値

- これまでの最良値
- TuRBOの信頼領域の長さと、その拡大・縮小の推移
- 連続成功 / 失敗回数
- SAASBOの次元ごとの長さ尺度または採用確率（有効次元の推定）
- 予測モデルの較正と交差検証誤差
- 再始動回数と各再始動後の改善量

## 失敗・切替の兆候

- 信頼領域が縮小してすぐ再始動を繰り返し、これまでの最良値が進まない
- SAASBOの長さ尺度がほぼ全次元で同程度になり、疎性の仮定が支持されない
- 獲得関数が依然として信頼領域内の境界付近に標本を集中させる
- 複数の初期点・再始動で到達する最良値が大きくばらつく
- 予測モデルの交差検証誤差が高い、または不確実性が未校正

局所信頼領域を使わない標準的なBOは、[Bayesian Optimization](#/learn/bayesian-optimization)で確認できます。
カテゴリ変数や条件付き空間を扱う木に基づく予測モデルは、[SMAC](#/learn/smac)で確認できます。
高価なブラックボックス全体の選び分けは、[高価なブラックボックス・HPOの選び分け](#/learn/family.expensive-black-box)にまとめています。

## 次に読む

- [関連する手法の記事](#/learn/bayesian-optimization)：一手の意味と選び分けを比べます。

- [この手法を使う問題の定式化](#/formulations/PA015)：決定変数と目的を確認します。
