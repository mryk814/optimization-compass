# 編集スコープ（Editorial scope）

Atlasが「どこまで扱うつもりか」（分母）を、既存の正規行・記事との対応づけつきで一か所に記録する仕組みです。
ここに載るIDは計画用のIDです。データベースには書かず、ルートにも使いません。

## 構成

| ファイル | 役割 | 誰が編集するか |
|---|---|---|
| [`data/seeds/editorial_scope.json`](../data/seeds/editorial_scope.json) | スコープの一覧。メンバーごとに採否と、既存の行・記事との対応づけを持つ | メンバーを足す・統合する・層を変えるとき |
| [`src/optimization_compass/editorial_scope.py`](../src/optimization_compass/editorial_scope.py) | 読み込み、整合性の検査、件数の集計 | |
| [`scripts/editorial_scope.py`](../scripts/editorial_scope.py) | 要約と、未処理（pending）の一覧 | |

```bash
uv run python scripts/editorial_scope.py
```

```bash
uv run python scripts/editorial_scope.py --json
```

```bash
uv run python scripts/editorial_scope.py pending
```

`pending` は、`review` が `candidate` のメンバーと、`decision` が `hold` のメンバーを出します。
`uv run python scripts/verify_content.py` は、シードがあれば整合性も検査します（なければ何もしません）。

## 項目の意味

| 項目 | 意味 |
|---|---|
| `scope_id` | 計画用ID。`TOPIC_*`（知識トピック）か `STRUCTURE_*`（問題構造）。一意で、既存の正規ID・記事IDと同じ文字列は使えない |
| `unit` | `knowledge_topic` か `problem_structure`。接頭辞と一致させる |
| `entity_kind` | `knowledge_topic` は `algorithm` / `variant` / `strategy` / `primitive`。`problem_structure` は `problem_archetype` / `modeling_profile` / `neighboring_problem` |
| `tier` | `core` / `applied` / `frontier` |
| `decision` | `include`（採用）/ `merge`（他のメンバーへ統合）/ `hold`（保留）/ `exclude`（除外） |
| `merged_into` | `merge` のときだけ必須。統合先は `include` のメンバー（連鎖は不可） |
| `decision_note_ja` | `merge` / `hold` / `exclude` では理由を必ず書く |
| `mapping.relation` | 既存の行・記事との関係（下表） |
| `mapping.refs` | 対応先。`method` / `problem` / `feature` / `glossary` / `term` / `content` のID。実在するものだけ |
| `mapping.review` | `candidate`（未確認）か `reviewed`（確認済み）。確認済みは `reviewer` と `reviewed_on` が必要 |
| `source_refs` | `sources` に載せた出典の `source_ref` |
| `status` | `proposed` か `approved`。`approved` は `approved_by`（owner か human）と `approved_on` が必要 |

## 関係の語彙

種別ごとに既存のどの表へ写すか、まとめ行をどう扱うかは [`identity-granularity.md`](identity-granularity.md) にあります。

| `relation` | 意味 | `refs` |
|---|---|---|
| `same_entity` | 既存の正規行がそのものである | 必須 |
| `alias_of` | 既存の行の別名にすぎない | 必須 |
| `variant_of` | 独立した行を持たない、名前のある変種 | 必須 |
| `primitive_in` | 既存の方法・記事の内部で使う部品 | 必須 |
| `covered_by_family` | 族（MF_*）か広い問題原型だけが覆っている | 必須 |
| `concept_content` | 記事は説明しているが、専用の正規行はない | 必須 |
| `unrepresented` | 確認したうえで、リポジトリのどこにも表現がない | 空 |
| `unknown` | まだ照合していない。`review` は `candidate` | 空 |

`same_entity` か `alias_of` で同じ参照を指す `include` のメンバーが二つあると、二重計上として検査が失敗します。片方をもう片方へ `merge` してください。

## メンバーの足し方・統合・保留

1. 足す: `scope_id` を決め、`relation` が分からなければ `unknown` と `review: candidate` で入れる。照合したら `relation` と `refs` を埋めて `reviewed` にする。
2. 統合する: 重複するメンバーを `decision: merge`、`merged_into` に残す側の `scope_id`、`decision_note_ja` に理由を書く。
3. 保留する: `decision: hold` と理由。`pending` に出続けるので、決まったら `include` か `exclude` に直す。
4. 検査: `uv run python scripts/verify_content.py` と `uv run pytest tests/test_editorial_scope.py -q`。

## やってはいけないこと

- スコープIDから新しい正規IDを作らない。`TOPIC_*` / `STRUCTURE_*` をデータベースやルートに出さない。正規行が必要なら、通常の追加手順（`docs/adding-knowledge.md`）に従う。
- 「105/160」のような割合や達成率を書かない。ここは件数だけを数える。網羅率は別の仕組みで扱う。
- `unknown`（未照合）を「存在しない」と読まない。存在しないと確かめたものだけが `unrepresented`。
- 出典なしで採否を決めない。Qiita・Zennは出典にしない。

## v1 の作り方と判定の基準（2026-10-10）

`editorial-scope-v1` は、引継ぎパックの初稿 `compass-reference-2026-10-draft1`（知識トピック160、問題構造80）を、既存の行・記事と一件ずつ照合して作りました。層（core / applied / frontier）と採否は、2026-10-10 にオーナーが承認し、`status` を `approved` にしました。以後の追加・統合・層の変更は、この版への変更として記録します。

- パックの問題構造のID `PROBLEM_*` は、既存の `problem_definitions` のID（`PROBLEM_OPTIMAL_CONTROL`、`PROBLEM_ROOT_FINDING` など）と同じ文字列になるものがありました。計画用IDが正規IDを覆わないよう、接頭辞を `STRUCTURE_*` に変えています（`PROBLEM_LP` → `STRUCTURE_LP`）。検査は、正規ID・記事IDと同じ文字列のスコープIDを拒否します。
- `covered_by_family` は、族の行か記事がその名前を出すか説明しているときだけ使います。族の範囲に入りそうでも、名前も説明もリポジトリにないもの（AdaGrad、Frank–Wolfe、Benders分解など）は `unrepresented` とし、収める先の候補を `note_ja` に書いています。
- 一つの行が二つの名前をまとめている場合（Dijkstra / A*、TuRBO / SAASBO、ナップサック / 集合被覆など）は、どちらも `variant_of` にして、同じ行を `same_entity` で二重に数えません。二重計上は、知識トピックと問題構造の単位ごとに検査します。
- 照合の確信が低いものは `review: candidate` のまま残しています。`pending` で一覧できます。
