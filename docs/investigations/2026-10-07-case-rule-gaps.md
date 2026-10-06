# Case の判断と診断規則の食い違いの調査（2026-10-07）

## 結果と範囲

Method Lens（[`docs/visual-system.md`](../visual-system.md)）は、Case の候補・除外を、診断の12軸の上の規則・前提で説明する。Lens を全 Case に当てると、Case の判断と正準の規則・前提・推薦エンジンの間に、次の三種類の食い違いがあった。

1. **推薦エンジンの不具合**: 証明要件（Q10）の判定が部分一致のため、局所法など23手法を「certificate を返す」と誤判定する。
2. **predicate の欠け**: BFGS には「勾配が使える」前提がなく、勾配が使えない Case での除外6件と、確率勾配の Case での除外1件を軸の上で説明できない。
3. **12軸の外の理由**: 残りの除外は「構造を平坦な目的へ隠す」「期限に間に合わない」など、12軸では表せない理由に基づく。

この調査では、正準データ、推薦エンジン、生成物を変更していない。1 と 2 は推薦またはデータセットの変更であり、出典と回帰ケースを用意して別に判断する。

対象は dataset 0.18.19 の公開 Case 36 件、除外 36 件、条件付き候補、候補。

## 1. 証明要件の判定が部分一致になっている

`src/optimization_compass/engine.py` の `_supports_certificate` と、それをブラウザへ写した `site/src/features/diagnose/recommend.ts` の `supportsCertificate` は、`optimality_certificate` に `gap`、`bound`、`dual`、`primal`、`unsat`、`certificate`、`proof` が**文字列として含まれるか**で判定している。

その結果、次のような局所法が certificate を返す扱いになる。

| 一致した語 | 値の例 | 手法の例 |
|---|---|---|
| `dual` | `first_order_resi`**`dual`**`;second_order_optional` | BFGS、L-BFGS、L-BFGS-B、Newton、勾配降下法 |
| `dual`, `primal` | `kkt_residual;`**`primal_dual`**`_residual` | SQP、SLSQP、active-set、内点法 NLP、射影勾配法 |
| `certificate` | `training_gradient_or_loss_not_global_`**`certificate`** | SGD、momentum SGD、AdamW |
| `gap` | `pareto_stationarity_or_`**`gap`**`_method_specific` | NSGA-II、重み付き和、ε制約法 |

`solution_scope` が `global` を含まないのに一致した手法は23件ある。KKT 残差の `primal_dual_residual` は局所の停留性の指標で、大域最適性の上下界ではない。`not_global_certificate` は、certificate を返さないことを明記した値である。

**影響**: Q10 に「大域最適性の証明が必要」と答えても、これらの手法は推薦から除外されない。「最適性 gap がほしい」と答えても、条件付き候補へ下がらない。Python とブラウザの実装はパリティテストで一致させてあるため、両方に同じ挙動がある。

**この調査での扱い**: Lens は Q10 の判定を描かない（`method-lens.ts` に理由をコメントで残した）。誤った判定を、軸の上の根拠として見せないためである。

**修正案（要判断）**: `optimality_certificate` を `;` で区切った語単位で判定し、`not_global_certificate` のような否定形と、`*_residual` のような停留性の指標を certificate として数えないようにする。推薦結果が変わるため、Q10 = `global_proof_required` と `gap_desired` で BFGS・SQP・SGD の除外・降格を確かめる回帰ケースを、Python とブラウザの両方に加える必要がある。

## 2. BFGS に勾配の前提がない

L-BFGS と L-BFGS-B には `F_DERIVATIVE_ACCESS in [analytic_gradient, autodiff, numerical_difference_only]` の前提（assumption predicate）がある。BFGS にはなく、BFGS の predicate は「微分不能」と「大きなノイズ」の非互換だけである。

勾配が使えない（Q05 = `unreliable_or_none`）ことを理由に BFGS を除外している Case は、軸の上で理由を示せない。

- `hyperparameter-search`
- `laser-process-tuning`
- `manufacturing-process-window`
- `battery-operation-tradeoff`
- `traffic-signal-tradeoff`
- `formulation-experiment-tuning`

確率勾配だけが得られる `EC021`（Q05 = `stochastic_gradient`）も同じ前提で説明できる。

**修正案（要判断）**: L-BFGS と同じ出典で、BFGS に同じ前提を追加する。現在の推薦エンジンは predicate を使わないので推薦結果は変わらないが、正準の predicate とデータセットの変更になる。

## 3. 条件付き候補が前提に反している

| Case | 手法 | 反している前提 |
|---|---|---|
| `EC013` | L-BFGS-B | 勾配の前提（Case の Q05 = `jacobian_or_hvp` は前提の値の一覧にない） |
| `EC019` | CP-SAT | 離散変数の前提（Case の Q01 = `structured_or_unknown`） |

どちらも条件付き候補なので、条件の文章では説明されている可能性がある。EC013 は、Jacobian が得られるなら勾配も組める。そのため、前提の値の一覧に `jacobian_or_hvp` を加えるべきかを確かめたい。

## 4. 12軸の外の理由（Case の文章のまま保つ）

変数型のチェックを加えると、`budget-allocation` と `public-infrastructure-selection` の Nelder–Mead（0-1 変数）、`EC027` の BFGS（混合変数）の3件は軸の上で説明できる。上の §2 の7件を除いた残り16件は、次のような理由である。

- 問題の構造を平坦な目的関数へ隠してしまう（軌道最適化、PDE 制約、bilevel、SO(3)）
- 実行の契約に合わない（100Hz の期限、warm start、評価の予算）
- 定式化の別の空間を選んでいる（topology change と fixed topology）

これらは12軸の値からは導けない。Case の除外理由の文章が根拠になるので、Lens は「規則上の除外軸なし」と表示し、Case の理由を出す。この表示は正しい。将来、除外理由に「構造を捨てる」「実行の契約」などの分類を持たせると、Lens でも区別して描ける。

付記: `shape-diffuser` が除外している `M_SIMP_TOPOLOGY` は、推薦用の site data の methods に含まれていない。

## 再現

```bash
# Lens の単体テスト（証明判定を描かないこと、変数型の判定）
npm --prefix site test -- --run src/visual-system
```

集計は、公開データ `site/public/data/gallery.json` と `site/public/data/recommendation/site-data.json` を読み、Case ごとに Lens と同じ規則・predicate・変数型の判定を当てて数えた。
