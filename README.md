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
- Optimization Atlas 静的アプリ: `http://127.0.0.1:5173/optimization-compass/`
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

### Optimization Atlas 静的アプリ

Node.js 24 を使い、静的アプリを別プロセスで起動します。

```bash
cd site
npm ci
npm run dev
```

公開版は GitHub Pages の `/optimization-compass/` 配下に配置し、画面遷移には hash route を使います。ローカルで production artifact を確認する場合は次を実行してください。

```bash
cd site
npm run typecheck
npm test -- --run
npm run build
```

生成物は `site/dist/` に出力されます。

Atlas の主要な hash route は次のとおりです。

- `/theater/nelder-mead`: Nelder–Mead の simplex / 候補点 / イベント再生
- `/compare/gradient-quadratic`: GD / Momentum / Adam の同一条件比較
- `/learn`: 手法・概念の教材一覧と検索
- `/gallery`: 実問題ケースの一覧・診断導線・除外候補

教材と Atlas 用静的インデックスの整合性は次で確認できます。

```bash
uv run python scripts/verify_content.py
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
  rebuild_dataset.py # deterministic stage/publish gate
examples/
tests/
docs/
```

## 開発

Python:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Optimization Atlas:

```bash
cd site
npm run typecheck
npm test -- --run
npm run build
```

## データ更新

まず公開物を変更しないstaged rebuildを実行します:

```bash
uv run python scripts/rebuild_dataset.py --stage
uv run optimization-compass verify-data
uv run pytest
```

stage modeは公開済みv0.2.0をhash固定のbaseとして一時領域へcopyし、atlas metadataの
migration/seed適用、live `CHK001`–`CHK020`、全形式round-trip、2回の同一tree hashまでを
検証します（database-onlyでは`CHK020=not_run`、release tree検証完了時だけ成立）。公開
distribution、runtime DB、`DATASET_VERSION`は変更しません。metadataの
authority境界は [`docs/metadata-responsibilities.md`](docs/metadata-responsibilities.md) に固定しています。

更新PRでは最低限、次を確認します。

- `PRAGMA foreign_key_check` が 0 件
- stored resultではなくliveに再計算した `release_checks` に `fail` がない
- DDL / JSON / JSONL / CSV / ZIP / XLSX / SQLiteが厳密にround-tripする
- manifest schema/version/release dateとJSON/JSONL、SQLite、report、filenameのidentityが一致する
- staged releaseではAtlas contractを明示的に要求し、全Atlas table欠落も検出する
- 2回のstaged rebuildでtree hashが一致する
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

Optimization Compassは権利範囲を分けて公開しています。

- Python / TypeScript / CSS / HTML / build・検証code: [MIT](LICENSE)
- canonical databaseと配布structured data: [CC BY 4.0](DATA_LICENSE)
- 教材Markdown、case説明、生成図、AlgorithmTrace JSON、screenshot:
  [CC BY 4.0](CONTENT_LICENSE)

CC BY 4.0の公式legal codeへの参照は [`CC-BY-4.0`](CC-BY-4.0) にあります。

再配布時の帰属例、第三者source・引用・商標の例外、配布物への同梱方法は
[`docs/licensing.md`](docs/licensing.md) と [`NOTICE`](NOTICE) を参照してください。
`sources`が参照する論文、書籍、公式documentation、repository等そのものは、このprojectの
licenseで再許諾されません。棚卸し結果は
[`THIRD_PARTY_SOURCE_AUDIT.md`](THIRD_PARTY_SOURCE_AUDIT.md) にあります。

## 免責

本ツールは候補選定と前提整理を支援するもので、最適性・安全性・法令適合・商用ライセンス・数値安定性を保証しません。重要な意思決定では、実問題での検証と専門家レビューを行ってください。
