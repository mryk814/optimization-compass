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

## Confidence

現在のMVPは規則の `confidence` を表示用メタデータとして保持し、確率へ変換しません。将来、実ケースの結果から校正する場合も、データ由来の確率と専門家評価を分離します。

## Backward compatibility

API v1ではフィールド追加を許容し、既存フィールドの意味変更・削除はv2で行います。知識DBのschema versionとアプリversionは別々に扱います。
