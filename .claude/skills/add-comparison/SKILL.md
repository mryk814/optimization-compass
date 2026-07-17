---
name: add-comparison
description: Add or revise a comparison (比較・Compare定義の追加・修正) in data/seeds/site_comparisons.json reusing existing traces and renderer families, validated via optimization-compass validate comparison / tier-b.
---

# comparisonを追加・改訂する（薄いwrapper）

規則の正はこのスキルではなく次の2つです。編集前に必ず読むこと:

1. `.agents/skills/optimization-compass-maintenance/SKILL.md` — Recipe D
2. `docs/adding-knowledge.md` §9（固定要因・変更要因・budget・同期軸・fairness・
   caveat・ranking eligibilityの明示。failure/感度比較はranking不可）

## 手順

1. 再利用する材料が既存であることを確認する: 対象のtrace/visualization
   （`site/public/data/visualization-scenarios.json`）、problem definition/instance、
   benchmark context、method ID。新しいtraceやrenderer contractが必要なら**stop**
   （それはRecipe G相当の設計作業）。
2. `data/seeds/site_comparisons.json` をReadし、`mode` が最も近い既存comparisonを
   コピーして書き換える。フィールドの正は既存エントリ（検証済みスキーマ）に従う。
3. 検証する:

   ```
   uv run optimization-compass validate comparison
   ```

   PRゲートは `uv run optimization-compass validate tier-b`。
   route・interactionを変える場合はE2Eを含む `validate tier-c`。

## Stop条件・PR記載事項

maintenance skillの「Stop conditions」と `docs/knowledge-change-checklist.md` の
「Comparison」節に従う。ranking_eligibleの判断理由をPRに明記する。DCO sign-off必須。
