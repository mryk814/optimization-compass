# 最適化コンパス / Optimization Compass

> 「最適化したい。でも、何をどう解けばいい？」を、再現可能な質問・ルール・根拠で整理する診断ツール。

Optimization Compass は、最適化問題の特徴を質問形式で整理し、次の順序で候補を返すオープンソース向けスターターです。

1. **そもそも汎用最適化を使うべきか**を確認する
2. 問題に合う**手法ファミリ**を候補化する
3. 前提違反や避けるべき手法を明示する
4. 利用可能な**実装・ソルバー**を示す
5. 推薦に使った決定ルールと情報源 ID を返す

推薦本体は LLM ではなく、同梱 SQLite の `decision_questions`、`decision_rules`、`methods`、`implementations` などを使う決定的なルールエンジンです。LLM を追加する場合も、自然文を回答候補へ変換する入口に限定し、最終判断は確認済みの構造化回答から行う方針です。

## いま動くもの

- ブラウザ診断画面: `http://127.0.0.1:8000/`
- OpenAPI ドキュメント: `http://127.0.0.1:8000/docs`
- REST API
- JSON 入力対応 CLI
- SQLite の外部キー・リリースチェック検証
- 決定ルールのトレース付き推薦
- 代表実装の提示

## セットアップ

Python 3.12 以上を想定しています。

```bash
uv sync --all-extras
uv run optimization-compass serve
```

`uv` を使わない場合:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
optimization-compass serve
```

## CLI

質問一覧:

```bash
optimization-compass questions
```

サンプル診断:

```bash
optimization-compass recommend examples/binary_linear.json
optimization-compass recommend examples/expensive_blackbox.json
```

データ検証:

```bash
optimization-compass verify-data
```

## API

```bash
curl http://127.0.0.1:8000/v1/questions
```

```bash
curl -X POST http://127.0.0.1:8000/v1/recommendations \
  -H 'content-type: application/json' \
  -d @examples/binary_linear.json
```

主なエンドポイント:

| Endpoint | Purpose |
|---|---|
| `GET /v1/questions` | 診断質問 |
| `POST /v1/recommendations` | 回答から候補・除外・代替解法を生成 |
| `GET /v1/methods/{method_id}` | 手法詳細 |
| `GET /v1/implementations/{implementation_id}` | 実装詳細 |
| `GET /v1/sources/{source_id}` | 根拠情報 |
| `GET /v1/data/verify` | データ整合性 |
| `GET /healthz` | ヘルスチェック |

## 推薦の読み方

結果は「万能ランキング」ではありません。

- `alternatives_first`: 汎用最適化より先に確認すべき解法
- `first_choices`: 複数の強い決定ルールに支持された候補
- `conditional_choices`: 条件を詰めてから比較する候補
- `excluded_methods`: 回答と前提が衝突した候補
- `followups`: 未確定情報として追加確認すべき項目
- `trace`: どの回答がどの規則を発火させたか

内部では候補順を安定させるため優先度を集計しますが、数値スコア自体は意思決定の根拠として公開しません。返すのは、支持した規則数・優先度帯・説明・警告・情報源 ID です。

## 設計原則

- **alternative-first**: 求根、最小二乗、線形方程式、グラフ法、DP などを先に検討
- **exclusion wins**: 前提違反があれば、他の支持より除外を優先
- **unknown is data**: 不明を勝手に yes/no へ補完しない
- **method != implementation**: 理論手法とライブラリ/APIを分離
- **traceable**: 推薦理由を決定ルールと source ID まで追跡可能にする
- **read-only knowledge base**: 実行時に知識DBを書き換えない

## リポジトリ構成

```text
src/optimization_compass/
  api.py          # FastAPI
  cli.py          # Typer CLI
  db.py           # SQLite read-only access
  engine.py       # deterministic recommendation engine
  models.py       # API/domain contracts
  web.py          # dependency-free browser UI
  resources/
    knowledge.sqlite
scripts/
  verify_data.py
  update_dataset.py
examples/
tests/
docs/
```

## 開発

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

## データ更新

新しい SQLite を取り込む場合:

```bash
uv run python scripts/update_dataset.py /path/to/new.sqlite --version 0.3.0
uv run optimization-compass verify-data
uv run pytest
```

更新PRでは最低限、次を確認します。

- `PRAGMA foreign_key_check` が 0 件
- `release_checks` に `fail` がない
- 既存の golden case が意図せず変化していない
- 変更された推薦に evidence/source がある

## ロードマップ

### Phase 1: 信頼できる診断器

- 質問回答 → 代替解法・手法・実装
- 推薦トレース
- golden cases
- データ修正PRの導線

### Phase 2: 自然文入力

- 自然文から質問回答候補を抽出
- 不確実な項目は確認質問へ戻す
- LLM 出力だけで手法を確定しない

### Phase 3: 実問題の検証

- ユーザーが目的関数・制約・予算を記録
- 複数手法の小規模 benchmark plan を生成
- 実測結果を recommendation feedback として保存

## ライセンスについて

このスターターには意図的に LICENSE を確定していません。公開前に、コードとデータを分けて決めてください。候補と注意点は [`docs/licensing.md`](docs/licensing.md) に整理しています。

## 免責

本ツールは候補選定と前提整理を支援するもので、最適性・安全性・法令適合・商用ライセンス・数値安定性を保証しません。重要な意思決定では、実問題での検証と専門家レビューを行ってください。
