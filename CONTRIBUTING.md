# Contributing

ありがとうございます。変更は「推薦ロジック」「データ」「UI」を分けてレビューできる形にしてください。

## Pull request の種類

- **Data correction**: 既存データの誤り、根拠URL、版、ライセンス
- **Knowledge expansion**: 手法、実装、問題類型、失敗モード、ケース
- **Engine**: 決定規則の評価、出力契約、トレース
- **UX/API**: 質問表現、画面、API

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
