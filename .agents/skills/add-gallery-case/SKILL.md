---
name: add-gallery-case
description: Add a Gallery case (Galleryケース・実例・事例の追加) to data/seeds/site_gallery.json using only existing canonical IDs, validated via optimization-compass validate gallery / tier-b.
---

# Gallery caseを追加する（薄いwrapper）

規則の正はこのスキルではなく次の2つです。編集前に必ず読むこと:

1. `.agents/skills/optimization-compass-maintenance/SKILL.md` — Recipe C
2. `docs/adding-knowledge.md` §8（必須semantics: 3つのmethod集合の非重複、
   conditional/excludedの具体的理由、`map_node_id` の導出可能性、
   compile可能な `python_example`、`limitations` の明示 など）

## 手順

1. 使う予定の全ID（problem archetype、feature、Diagnose質問と回答、method、
   implementation、source、visualization、comparison）が既存であることを、
   `site/public/data/` の生成index（`problems.json`、`sources.json`、
   `recommendation/` 配下）をReadして確認する。無いIDがあれば**stop**して不足を報告する
   （この導線ではIDを新設しない）。
2. `data/seeds/site_gallery.json` をReadし、問題構造が最も近い既存caseをコピーして
   書き換える。コピーした全IDを1つずつ再評価する（プロースだけ変えてIDを流用しない）。
3. 検証する:

   ```
   uv run optimization-compass validate gallery
   ```

   PRゲートは `uv run optimization-compass validate tier-b`。
   GalleryのUIはデータから生成されるため、site側コードは触らない。

## Stop条件・PR記載事項

maintenance skillの「Stop conditions」と `docs/knowledge-change-checklist.md` の
「Gallery case」節に従う。DCO sign-off必須。
