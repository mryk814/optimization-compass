# Architecture

## Context

ユーザーの「最適化したい」は、少なくとも次を混同しやすい要求です。

- 数式モデルを作りたい
- 汎用最適化手法を選びたい
- ソルバーやライブラリを選びたい
- ハイパーパラメータを探索したい
- 既存処理の性能を改善したい
- 求根・最小二乗・制約充足など別問題を解きたい

本システムは、最初に問題の種類を明らかにし、汎用最適化より適切な代替解法がないか確認します。

## Components

```text
Browser                         CLI / API client
   |                                  |
   v                                  v
Static Optimization Atlas       Pydantic request validation
   |                                  |
   v                                  v
Versioned exported SiteData     Deterministic rule engine
   |                                  |
   +-------- shared cases ------------+
                                      |
                                      v
                              Read-only repository layer
                                      |
                                      v
                              Versioned SQLite knowledge base
```

Optimization Atlas is the canonical browser experience. FastAPI serves the REST API, OpenAPI, a
health check, and a migration landing page; it does not maintain a fallback diagnosis UI. The
support boundary, feature matrix, and copy authority are fixed in
[`ADR 0002`](adr/0002-canonical-browser-experience.md).

## Why deterministic first

- 同じ回答に同じ結果を返せる
- 推薦変更を差分テストできる
- 規則と source ID を表示できる
- LLMの幻覚やプロンプト差を推薦本体から切り離せる

## LLM boundary

将来の自然文入力は次だけを担当します。

1. ユーザー文から候補回答を抽出
2. 根拠となる原文断片を添える
3. confidence が低い項目を質問へ戻す

LLM がDBに存在しない手法IDを生成したり、確認なしに unknown を埋めたりしてはいけません。

## Recommendation flow

1. 回答を canonical value へ検証
2. `decision_rules` を exact match で発火
3. alternative / method / problem / followup / warning に分配
4. 変数domain・証明要件の互換性ゲートを適用
5. `exclude_method` を優先適用
6. 方法を優先度帯と支持規則数で安定ソート
7. `method_implementation_map` から代表実装を付与
8. トレースと source ID を返す

## Scaling

初期はSQLiteで十分です。書き込み・組織別データ・フィードバック蓄積が必要になった時点で、知識DBはimmutable artifactのまま維持し、ユーザーデータだけをPostgreSQL等へ分離するのが安全です。

## Visualization architecture

可視化は手法ごとの専用画面ではなく、problem definition、problem instance、
scenario、run、artifact、renderer familyを分離します。authority境界、比較可能性、
高次元の扱い、既存Traceからのmigrationは
[`visualization-scenarios.md`](visualization-scenarios.md) と
[`ADR 0001`](adr/0001-visualization-scenarios-and-renderers.md) を参照してください。
