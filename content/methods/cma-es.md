---
content_id: cma-es
kind: method
method_id: M_CMA_ES
title_ja: CMA-ES
title_en: Covariance Matrix Adaptation Evolution Strategy
summary: 関数値の順位から探索分布の平均・step size・共分散を更新する連続black-box最適化です。
source_ids: [S032, S058]
prerequisites: [concept.derivative-free]
related_ids: [concept.derivative-free, multi-objective]
visualization_ids: []
comparison_ids: []
aliases: [/learn/cma-es]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-15
---

関数値の順位から探索分布の平均・step size・共分散を更新する連続black-box最適化です。

## 現実の問いを探索分布へ移す

| 項目 | 例 |
|---|---|
| decision variables | simulator parameter、形状parameter、controller gain |
| objective | simulation score、実験loss、設計penalty |
| constraints | bounds、評価失敗、安全領域 |
| problem features | derivative-free、nonconvex、moderate dimension、noise |

現実の問いは「局所的な勾配を信頼できないとき、どの方向とscaleをまとめて試すか」です。populationの良い点から変数間の相関を学習します。

## Alternative-first check

gradientや残差Jacobianを正確に利用できるなら、BFGSやleast-squares法を先に検討します。一評価が極端に高価ならBayesian Optimization、離散・論理変数が中心ならCP-SATなど別familyを検討します。

- candidate: CMA-ES。連続、非凸、black-boxで並列評価が可能な場合。
- conditional: noise handlingやrestart付きCMA-ES。評価noiseやmultimodalityが強い場合。
- excluded: 高次元で一評価が非常に高価な設定。population評価と共分散更新のcostが支配的になります。

## Representative implementationと最小例

Pythonでは`cma`（pycma）が代表的です。initial mean、initial sigma、bounds、seed、evaluation budgetを固定します。

```python
import cma

def sphere(x: list[float]) -> float:
    return sum(value * value for value in x)

result = cma.fmin(sphere, [2.0, -1.0], 0.5, options={"seed": 1, "maxfevals": 200})
print(result[0], result[1])
```

## 実務上の注意

population collapse、step sizeの過小化、boundary handling、restart条件を記録します。単一runのbest valueだけでは探索の安定性を判断できません。複数seedでevaluation budgetを揃え、[Derivative-free教材](#/learn/concept.derivative-free)とMap上の評価情報を併読します。
