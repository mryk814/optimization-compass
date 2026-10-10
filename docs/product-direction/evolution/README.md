# 発展準備の作業記録（OC-EVOL）

2026-10-10の引継ぎパック（`optimization_compass_handoff_2026-10-10`）にある課題票 OC-EVOL-001〜032 を、このリポジトリの現行方針（[`learning-atlas.md`](../learning-atlas.md)、[`AGENTS.md`](../../../AGENTS.md)）に沿って進めるための記録です。パック本体はリポジトリに取り込みません。課題票のIDだけを、PRと記録の対応づけに使います。

## OC-EVOL-001：基準監査（2026-10-10）

観測値は [`baseline-2026-10-10.json`](baseline-2026-10-10.json) にあります。要点は次のとおりです。

- 監査時の `main` は `d4847aa`（dataset `0.18.20`）でした。パックが基準にした `3099b88` の後に、PR297 の merge commit が乗っています。作業ブランチに未コミットの変更はありませんでした。
- パックの監査ツールは読み取り専用で実行しました。前後で `knowledge.sqlite`、`site/public/data/coverage.json`、`manifest.json`、各seedのハッシュは変わっていません。
- 160の知識トピック候補のうち、名前の正規化一致で候補が出たのは61件、意味レビューが要るのが99件です。これは**照合候補の件数**です。61件を収録済み、99件を未収録とは読みません。

### 既存作業との統合

| 既存作業 | 状態 | この後の課題での扱い |
|---|---|---|
| PR297 記事の品質台帳 | `main` に取り込み済み | OC-EVOL-003 の「説明」軸は、この台帳の記事状態（達成・要修正・要レビュー、本文変更後のstale）をそのまま読みます。品質の正本を別に作りません。 |
| PR298 主単体法の操作図 | open（base `d4847aa`） | OC-EVOL-011 は、この操作図の拡張（証明・感度・動画）として進めます。同じ役割の単体法図は新設しません。OC-EVOL-001〜003 は PR298 が変えるファイルに触れません。生成物 `site/public/data/*` は、それぞれのPRで最新の `main` から再生成します。 |

### 観測していないこと

- PR297/298 の本文にある試験結果は作者の申告です。この監査では再実行していません。
- 画面の確認、リポジトリ全体のテスト、site build は、この票では行っていません。

## OC-EVOL-002：編集上の収録範囲 v1（proposed）

収録範囲は [`data/seeds/editorial_scope.json`](../../../data/seeds/editorial_scope.json)、書き方と判定の基準は [`docs/editorial-scope.md`](../../editorial-scope.md) にあります。件数は `uv run python scripts/editorial_scope.py` で出します。この記録には件数を書き写しません。

照合で分かったことのうち、収録範囲の外で直すものを残します。

- `problem_definition_archetypes` で、`PROBLEM_BILEVEL_REGRESSION` が PA033（非線形最小二乗）、`PROBLEM_FAILED_SIMULATION` が PA054（実験計画）、`PROBLEM_PORTFOLIO_UNCERTAINTY` が PA036（単体）に結ばれています。名前と標準形からは、それぞれ PA046・PA016・確率計画かロバストの行が自然に見えます。結び方の意図を確かめる必要があります（dataset の変更なので別のPRにします）。
