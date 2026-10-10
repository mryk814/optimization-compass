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

- `problem_definition_archetypes` で、`PROBLEM_BILEVEL_REGRESSION` が PA033（非線形最小二乗）、`PROBLEM_FAILED_SIMULATION` が PA054（実験計画）、`PROBLEM_PORTFOLIO_UNCERTAINTY` が PA036（単体）に結ばれていました。`problem_registry.py` の式と照らすと三つとも誤りだったので、dataset 0.18.21 でそれぞれ PA046＋PA005、PA016、PA049＋PA036 に直しました（`problem-suite.json` の `related_problem_ids`）。

## 進み具合（2026-10-10 時点）

| 課題 | 状態 | 記録 |
|---|---|---|
| OC-EVOL-001 基準監査 | 完了 | 上の節 |
| OC-EVOL-002 収録範囲 v1 | 完了（`proposed`。層と採否はオーナーの承認待ち） | [`editorial-scope.md`](../../editorial-scope.md) |
| OC-EVOL-003 Coverage の分母と品質軸 | 完了 | `coverage.py` の scope 節、Coverage 画面 |
| OC-EVOL-004 同一性と粒度 | 完了 | [`identity-granularity.md`](../../identity-granularity.md) |
| OC-EVOL-010 scene・媒体契約の差分 | 完了（提案のみの項目は使う図のPRで足す） | [`explorables.md`](../../explorables.md) の「数値の出どころ」 |
| OC-EVOL-011 主単体法の証明・感度 | 操作図と本文は完了。動画は未着手 | `simplex-shadow-price` |
| 辞書の拡張（問題型の記事） | PA006・PA024・PA031・PA035・PA043・PA055 を追加 | `scripts/formulation_backlog.py` で次を選ぶ |

### 決めることが残っているもの

- 収録範囲で「表現なし」になった手法（Frank–Wolfe、Benders、列生成、AdaGrad、Sinkhorn など）に行を足すのは、dataset のリリースです。AGENTS.md の区分では Red にあたります。どの順番で、どの版に入れるかを決めてから、まとめて追加します。
- OC-EVOL-007（初学者の入口）と OC-EVOL-008（高価な評価の利用者の道筋）は、学習経路の seed を変えます。どの persona を先にするかを決めてから進めます。
