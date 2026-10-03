---
content_id: direct-shooting
kind: method
method_id: M_DIRECT_SHOOTING
title_ja: Direct Shooting
title_en: Direct Shooting
summary: 時間ごとの制御入力を最適化変数にし、初期状態から動力学を前進シミュレーションして得た軌道の費用と制約を改善する最適制御法です。
source_ids: [S042, S043, S050, S076]
prerequisites: [concept.trajectory-variable, concept.time-discretization]
related_ids: [concept.dynamics-defect, concept.path-terminal-constraints, concept.receding-horizon, direct-collocation]
status: published
last_reviewed: 2026-09-30
---

時間ごとの制御入力を最適化変数にし、初期状態から動力学を前進シミュレーションして得た軌道の費用と制約を改善する最適制御法です。

## 30秒でつかむ

この手法の気持ちは、状態をすべて独立には決めないことです。
**制御入力を仮定してシミュレーションし、軌道が目標へ近づくよう調整します。**

- 見るもの: 前進シミュレーション軌道、費用、終端誤差、制約違反
- 動かすもの: 制御入力の列またはそのパラメータ
- 前進の判断: 費用が下がり、可行性が保たれているか
- 別に確認するもの: 前進シミュレーションの実時間、前回の解からの再開の効き、締切への余裕
- 恐れていること: 不安定動力学、長い計画期間、初期制御入力依存、感度の悪条件化

状態はシミュレーションで決まるため、変数数を減らせます。
一方、長い計画期間では早い時刻の制御入力が後半状態へ強く影響します。
その結果、最適化が難しくなります。

## 一手の意味

離散動力学を例にします。

$$
x_{t+1}=F(x_t,u_t)
$$

最適化変数は制御入力列 $u_0,\ldots,u_{T-1}$です。候補制御入力で前進シミュレーションし、軌道費用と制約を評価します。勾配を使う場合は、制御入力変更が将来状態へ伝わる感度を計算します。

状態を独立変数にしないため、前進シミュレーション上の動力学等式制約は自動的に満たされます。
その代わり、費用を下げても経路制約や終端条件を満たすとは限りません。
不安定な前進シミュレーションや長期感度が、制御入力の改善を後半の状態へ伝える段階で難しさになります。

上段の制御入力列だけが最適化変数です。
下段の状態軌道は、その制御入力列を先頭からシミュレーションした結果です。

![減衰のある1状態の動力学を20ステップ前進シミュレーションした固定Direct Shooting実行。最適化した制御入力は前半の約0.51から増える。後半11個は上限1に達する。初期制御入力の状態は0のままである。最適化した制御入力の状態は0.950まで進む。目標 1との差は0.0496残る。](./media/direct-shooting-rollout-execution.svg "制御入力列を変数として更新し、状態軌道を前進シミュレーションで得る固定Direct Shooting実行")

上段を変えるたびに、下段は初期状態から前進シミュレーションし直します。
この教材では終端目標を厳密な制約にせず、制御入力費用と一緒に目的関数へ入れています。
そのため、最終状態は目標へ完全一致せず `x20 = 0.950` で止まります。

> 固定動力学 `x[t+1] = 0.92 x[t] + 0.1 u[t]` を80回更新した教材です。
> 目的関数は `1.000 → 0.0344`、20個中11個の制御入力が上限へ達します。
> 経路制約や不安定な動力学は含みません。
> モデルと実際のずれやDirect Shooting一般の性能も示していません。

## 小さな例

Python例と同じ、減衰のある状態 $x_{t+1}=0.92x_t+0.1u_t$ を使います。
初期制御はすべて0で、目標状態は1です。
制御入力を上下限 $[-1,1]$ に戻す勾配更新を、幅4で実行しました。

| 更新回数 | 目的値 | 最終状態 |
|---|---:|---:|
| 0 | 1.0000 | 0.0000 |
| 1 | 0.2558 | 0.5023 |
| 2 | 0.0965 | 0.7171 |
| 3 | 0.0652 | 0.7876 |

制御列を更新するたびに、状態列を初期状態から計算し直します。
3回目で目標へ近づいていますが、まだ終端誤差が残ります。
終端一致は目的の罰則として入れており、厳密な等式制約ではありません。
80回後の目的値約0.0344、最終状態約0.9504も、同じ実行で確認できます。

## 向く条件・避ける条件

### まず確認すること

| 項目 | 確認内容 |
|---|---|
| 動力学 | 数値的に安定してシミュレーションできるか |
| 制御入力変数の表現 | 区分的に一定など妥当な表現か |
| 計画期間 | 長すぎて感度が消失・爆発しないか |
| 制約 | 経路制約を前進シミュレーションだけで評価できるか |
| 微分 | 感度や自動微分を利用できるか |
| 初期化 | 妥当な初期制御入力を用意できるか |

実時間制御では求解時間、前回の解からの再開、代替の制御器を費用や可行性とは別の運用条件として記録します。

### 向く条件・避ける条件

向いている条件:

- 計画期間が比較的短い
- 動力学シミュレーションが安定・高速
- 状態制約が少ない、または扱いやすい
- 制御入力次元を低く表現できる

### うまくいったサインと切替サイン

次の条件では、変数を減らせる利点よりも前進シミュレーションの不安定さが支配的になります。

- 長い計画期間で不安定動力学
- 多数の厳しい経路制約
- 事象や不連続を未処理
- モデルと実際のずれが大きくシミュレーションを信用できない

## Python

```python
HORIZON = 20
DECAY = 0.92
DT = 0.1
TARGET = 1.0
CONTROL_PENALTY = 0.002
LEARNING_RATE = 4.0


def rollout(controls: list[float]) -> list[float]:
    states = [0.0]
    for control in controls:
        states.append(DECAY * states[-1] + DT * control)
    return states


def objective(controls: list[float]) -> tuple[float, list[float]]:
    states = rollout(controls)
    terminal_cost = (states[-1] - TARGET) ** 2
    control_cost = CONTROL_PENALTY * sum(control * control for control in controls)
    return terminal_cost + control_cost, states


controls = [0.0] * HORIZON
terminal_weights = [
    DT * DECAY ** (HORIZON - 1 - index)
    for index in range(HORIZON)
]
history = []
for iteration in range(81):
    cost, states = objective(controls)
    history.append((iteration, cost, states[-1]))
    if iteration == 80:
        break

    terminal_error = states[-1] - TARGET
    gradient = [
        2.0 * terminal_error * weight + 2.0 * CONTROL_PENALTY * control
        for weight, control in zip(terminal_weights, controls, strict=True)
    ]
    controls = [
        max(-1.0, min(1.0, control - LEARNING_RATE * derivative))
        for control, derivative in zip(controls, gradient, strict=True)
    ]

print(history[0], history[-1])
print(sum(control >= 1.0 - 1e-12 for control in controls))
```

出力では目的関数が `1.0` から `0.034356...` へ下がり、終端状態は `0.950387...` になります。
上限へ達する制御入力は11個です。

この例は単純な動力学と固定一歩の射影勾配を使います。
実務では積分誤差と状態制約を保存します。
単位とソルバー状態区分も分けて記録します。

## 診断値

- 合計費用と終端誤差
- 状態 / 制御入力制約違反
- 前進シミュレーションの安定性
- 勾配ノルムと一歩ノルム
- 計画期間別の感度
- 実行時間と反復数
- 初期制御入力ごとの解

費用の低下、制約違反の許容範囲、前進シミュレーションの安定性は別々に記録します。
実行時間と反復数は、解の良さではなく実時間運用の判定に使います。

## 失敗・切替の兆候

### 追加の診断

- 前進シミュレーションが発散 → 変数の表現、計画期間、安定させる初期制御入力を見直す
- 初期時刻の勾配だけ巨大 → 尺度合わせや多重射撃法を検討
- 経路制約が満たせない → 直接選点法へ
- 計画期間を延ばすと解が急変 → 離散化とモデルを確認
- 実時間の締切を超える → 前回の解からの再開、観測ごとに解き直す運用、専用ソルバーを検討

### コラム: Direct Collocationとの違い

Direct Collocationは状態も決定変数にし、動力学の残差を制約として課します。変数は増えますが、長い計画期間や経路制約で疎構造を使いやすくなります。

[Direct Collocation](#/learn/direct-collocation)とは、変数数だけで比較しません。
前進シミュレーション安定性／整合性の残差／疎構造／前回の解からの再開も確認します。

## 次に読む

[最適制御の定式化](#/formulations/PA042)で、制御列と状態列の役割を整理します。

まず[軌道変数](#/learn/concept.trajectory-variable)で、制御入力列と前進シミュレーションされた状態列を分けて読みます。
次に[時間離散化](#/learn/concept.time-discretization)で、制御入力の保持方法と一歩の大きさを確認します。
経路制約や終端条件が主役なら、[経路・終端制約](#/learn/concept.path-terminal-constraints)へ進みます。
長い計画期間で前進シミュレーション感度が問題なら、[Direct Multiple Shooting](#/learn/multiple-shooting)へ切り替えます。
観測ごとに先頭の制御入力だけを使う運用は、[観測ごとに解き直す運用](#/learn/concept.receding-horizon)で確認します。
