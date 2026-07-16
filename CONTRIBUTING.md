# Contributing

ありがとうございます。変更は「推薦ロジック」「データ」「UI」を分けてレビューできる形にしてください。

## まず読むもの

変更内容に応じて、次を先に確認してください。

- [`AGENTS.md`](AGENTS.md) — authority、生成物、変更分類、検証tierの短い入口
- [`docs/adding-knowledge.md`](docs/adding-knowledge.md) — 教材、Gallery、比較、problem、手法、可視化の追加手順
- [`docs/knowledge-change-checklist.md`](docs/knowledge-change-checklist.md) — Knowledge PRの確認項目とPR記載テンプレート
- [`.agents/skills/optimization-compass-maintenance/SKILL.md`](.agents/skills/optimization-compass-maintenance/SKILL.md) — AIエージェント向け作業規約

`src/optimization_compass/resources/knowledge.sqlite`、`site/public/data/**`、公開distribution、生成Traceやmediaは直接修正しません。canonical inputを修正し、documented buildから再生成してください。

## Pull request の種類

- **Data correction**: 既存データの誤り、根拠URL、版、ライセンス
- **Knowledge expansion**: 手法、実装、問題類型、失敗モード、ケース
- **Engine**: 決定規則の評価、出力契約、トレース
- **UX/API**: 質問表現、画面、API

## 言語と公開

公開Atlasは日本語を説明の主言語とし、canonicalな英語用語も見える・検索できる
**Japanese-first, English-term-aware** 方針です。詳細は
[`ADR 0013`](docs/adr/0013-japanese-first-language-strategy.md)に従ってください。

- `published`教材は、`title_ja`、`summary`、本文だけで日本語の説明が完結している必要があります。
- `title_en`、英語alias、略語は正式用語と検索のmetadataです。英語版記事の代わりではありません。
- 手法名、製品/API名、code、数式、source titleは正しい原表記を保ちます。stable ID、URL identifier、
  schema key、API fieldは翻訳しません。
- 未レビューの機械翻訳を、執筆済みの翻訳やlocale fallbackとして追加しません。
- 現在の検索は日本語の語句と英語の正式名・alias・略語を同じ生成indexから探します。これは
  locale切替や英語記事の存在を保証するものではありません。

日本語以外の完全な公開surfaceを作る場合は、URL、翻訳field、review provenance、欠落表示、
言語別Coverageをまとめて設計するi18n projectとして提案してください。

## Data PR に必要なもの

1. 変更対象ID
2. 変更前と変更後
3. 一次情報または原論文
4. 推薦が変化するケース
5. `verify-data` と `pytest` の結果

Qiita / Zenn は根拠として使用しません。公式ドキュメント、公式リポジトリ、原論文、標準規格を優先してください。

## 権利表明とsign-off

このprojectはDeveloper Certificate of Origin 1.1
（[developercertificate.org](https://developercertificate.org/)）を使用し、別途CLAは要求しません。
すべてのcommitに次の形式のsign-offを付けてください。

```text
Signed-off-by: Your Name <your.email@example.com>
```

`git commit -s`で追加できます。sign-offは、自分で作成した変更であるか、適切なlicenseのもとで
提出する権利があり、このprojectのlicenseで配布されることに同意するという表明です。

変更対象ごとのlicenseは次のとおりです。

- code・test・workflow・build/validation script: MIT
- canonical/distributed structured data: CC BY 4.0
- 教材、case text、生成図・Trace・screenshot: CC BY 4.0

第三者の論文、documentation、repository、商標、logo、引用等の権利は移転しません。引用・図・
screenshot・logoを追加する場合は、rights holder、source、適用licenseまたは法的例外、必要な帰属、
対象file/fieldを同じPRで明記してください。詳細は
[`docs/licensing.md`](docs/licensing.md) と [`NOTICE`](NOTICE) を参照してください。

## ローカル確認

```bash
uv sync --all-extras
uv run ruff check .
uv run mypy src
uv run pytest
uv run optimization-compass verify-data
uv run python scripts/verify_content.py
uv run python scripts/verify_licensing.py
```

変更種類ごとの最小確認とdataset stage / site validationは [`docs/adding-knowledge.md`](docs/adding-knowledge.md) を参照してください。
