---
name: add-comparison
description: Add or revise a comparison (比較・Compare定義の追加・修正) in data/seeds/site_comparisons.json reusing existing traces and renderer families, then validate with tier B.
---

# comparisonを追加・改訂する

`data/seeds/site_comparisons.json` に比較定義を追加する導線です。
既存のtrace・artifact・renderer familyを再利用し、検証済みの既存フィールドの範囲内に留まります。
新しいrenderer contractが必要なら、この導線ではなく設計作業（高リスク・Recipe G）です。

## Step 1 — 再利用できる材料を確認する

- 比較対象のtrace/visualizationが既に存在するか（`site/public/data/visualization-scenarios.json`、`site/public/data/traces/`）
- 対象のproblem definition/instance、benchmark context、method IDが既存か
- 近い `mode`（`method_contrast` など）の既存comparisonがどれか

## Step 2 — 最も近い既存comparisonをコピーして書く

実際のスキーマは既存エントリが正です。現在の主要キー:

```text
comparison_id, canonical_url, identity_status, canonical_comparison_id, aliases,
mode, journey_id, case_id, problem_definition_id, problem_instance_id,
benchmark_context_id, title_ja, title_en, comparison_question,
formulation_summary, fixed_factors, changed_factors, seed_policy, budget,
stopping_policy, tuning_policy, synchronization_axis, metrics, comparability,
ranking_eligible, fairness_note, caveat, takeaway, limitations, source_ids,
last_verified, members
```

### 意味的な必須要件

comparisonは以下を必ず説明します:

- 比較の問い（`comparison_question`）
- 何を固定し（`fixed_factors`）、何を変えるか（`changed_factors`）
- 初期条件・seed・budget・停止条件・tuning方針
- 同期軸（`synchronization_axis`: 何を横軸に揃えて比べるか）
- metricsとstatusの読み方、member個別のパラメータ
- fairness note・caveat・comparability

### ranking規律（コア不変条件）

- **failure contrast・感度比較はrankingではない** — `ranking_eligible: false`。
- benchmark contextが不完備な比較を `ranking_eligible: true` にしない。
- 文脈のない総合スコアで手法の優劣を示唆しない。canonical/derived identityを正直に書く。

## Step 3 — 検証する

```bash
make tier-b
```

反復中の先行チェック:

```bash
uv run pytest tests/test_site_export.py tests/test_comparisons.py
npm --prefix site run parity
```

route・interactionを変える場合は `npm --prefix site run test:e2e` も（tier C相当）。

## Stop条件

- 必要なtrace/artifactが存在しない（trace生成はRecipe G相当の別作業）。
- 公平な比較に必要なbenchmark contextを埋められない。
- 新しいrenderer familyやartifact contractが必要になった。

## PRに書くこと

`comparison_id`、mode、参照した全ID、ranking_eligibleの判断理由、
fairness/caveatの根拠、検証コマンドと結果。DCO sign-off必須。
