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

## ローカル確認

```bash
uv sync --all-extras
uv run ruff check .
uv run mypy src
uv run pytest
uv run optimization-compass verify-data
```
