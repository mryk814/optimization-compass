---
name: add-content-article
description: Add or improve a method/concept article (method記事・concept記事の追加・修正・充実) in content/**/*.md for an existing canonical entity, validated via optimization-compass validate content / tier-a.
---

# method / concept 記事を追加・充実させる（薄いwrapper）

規則の正はこのスキルではなく次の3つです。編集前に必ず該当箇所を読むこと:

1. `.agents/skills/optimization-compass-maintenance/SKILL.md` — Recipe A（既存記事修正）/ Recipe B（既存entityへの記事追加）
2. `docs/adding-knowledge.md` §6–§7
3. `docs/method-content-density.md` — published method記事の密度floor

## 手順

1. 対象entityがcanonicalに存在することを確認する（記事が無い ≠ entityが無い）。
   `site/public/data/` の生成index（`content.json`、`sources.json`）をReadして
   entity ID・source IDを解決する。無ければ**stop**（canonical追加はRecipe F）。
2. 最も近い既存記事（`content/methods/` / `content/concepts/`）をReadし、
   frontmatterの形をそれに合わせて新規ファイルを書く。関係・sourceが不完全なら `status: draft`。
3. 密度を確認する:
   `uv run python scripts/method_content_density_report.py --output <一時ファイルパス>`
   （デフォルト出力はリポジトリ内の `docs/` を書き換えるため、必ず一時パスへ）
4. 検証する:

   ```
   uv run optimization-compass validate content
   ```

   PRゲートは `uv run optimization-compass validate tier-a`。
   `related_ids` 等で生成index・関係が変わる場合はstaged buildを含む
   `uv run optimization-compass validate tier-b` を推奨（maintenance skill Recipe B参照）。

## Stop条件・PR記載事項

maintenance skillの「Stop conditions」「Completion criteria」と
`docs/knowledge-change-checklist.md` に従う。DCO sign-off必須。
