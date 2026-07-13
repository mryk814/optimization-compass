# Recommendation Contract

## Non-goals

- 一つの「最強アルゴリズム」を断定しない
- 理論上対応可能というだけで推奨しない
- ソルバーの商用利用条件を推測しない
- 推薦を実問題でのbenchmarkの代替にしない

## Ordering

候補の並びは次の情報で決めます。

1. `high` priority rule count
2. `medium` priority rule count
3. total supporting rule count
4. stable method ID

数値重みは内部の安定ソートにだけ利用し、APIレスポンスには意思決定スコアとして露出しません。

## Conflict handling

`exclude_method` は `promote_method` より優先します。例として「autodiffがある」と「not differentiable」が同時に与えられた場合、入力矛盾の警告を追加し、除外を優先します。

## Canonical answers

- 質問IDと回答値はSQLiteのcanonical valueへ完全一致させます。
- 回答を送る質問は1件以上の値を持ち、重複を含めません。未回答は質問ID自体を省略します。
- `single_choice` は値をちょうど1件持ちます。
- `unknown` はその質問の `allowed_answers` に存在するときだけデータとして受理し、他の値と同時に選びません。
- 部分回答は有効です。`required` は診断UIの進捗表示に使い、評価器が未回答を推測で補完することはありません。

## Offline parity

静的アプリは `SiteData 1.0.0` を読み、Pythonと同じ評価phase、候補順、除外優先、compatibility gate、source ID、rule traceをTypeScriptで再現します。`SiteData` はSQLiteから決定的に生成され、dataset versionがViewSpecや画面状態と一致しない場合は評価を中止します。

共通fixtureはreal Python engineとreal TypeScript evaluatorの両方で実行し、4つの主要band、問題候補、follow-up、warning、発火rule/source IDをCIで比較します。

## Confidence

現在のMVPは規則の `confidence` を表示用メタデータとして保持し、確率へ変換しません。将来、実ケースの結果から校正する場合も、データ由来の確率と専門家評価を分離します。

## Contract versions

知識DB、`SiteData`、API/appは独立してversion管理します。互換性のない組合せはfallbackせず明示的に拒否します。
