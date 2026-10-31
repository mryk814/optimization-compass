# 記事の品質台帳（Article quality ledger）

公開している全記事について、どの基準を満たしているか、いつ誰が確かめたか、その後に何が変わったかを一か所で追うための仕組みです。
人もAIも、記事を直す前と直した後に同じコマンドで状態を確かめます。

基準の中身（どう書くか）は [`teaching-article-playbook.md`](teaching-article-playbook.md) が正です。台帳は、その基準を記事ごとにチェックできる形にしたものです。

## 構成

| ファイル | 役割 | 誰が編集するか |
|---|---|---|
| [`data/seeds/article_quality_criteria.json`](../data/seeds/article_quality_criteria.json) | 基準の一覧。`check: auto` はMarkdownから毎回測り、`check: review` は人かAIが読んで判定する | 基準を足す・厳しくするとき |
| [`data/seeds/article_quality_ledger.json`](../data/seeds/article_quality_ledger.json) | 記事ごとのレビュー記録。日付、レビューした人、本文のハッシュ、基準ごとの判定 | `record` コマンドで書く（手で書かない） |
| [`src/optimization_compass/article_quality.py`](../src/optimization_compass/article_quality.py) | 自動判定と、台帳との突き合わせ | |
| [`scripts/article_quality.py`](../scripts/article_quality.py) | 一覧・記事ごとの確認・作業の順番・記録 | |

## 使い方

```bash
uv run python scripts/article_quality.py
```

```bash
uv run python scripts/article_quality.py show adam
```

```bash
uv run python scripts/article_quality.py next --limit 10
```

```bash
uv run python scripts/article_quality.py criteria
```

- 引数なしは全体の集計です。基準ごとの達成数と、全記事の一行要約（学習経路に載る記事が先）を出します。
- `show <ID>` は一つの記事のチェックリストです。content ID、ファイル名（`adam`）、パスのどれでも指定できます。記事を直す前にこれを見て、何が足りないかを確かめます。
- `next` は、学習経路に載る記事 → formulation・method → 失敗の多い順に、作業の候補を出します。
- `--json` を付けると、AIが読みやすいJSONで出します（`--json show adam` など）。

## 状態の読み方

| 記号 | 状態 | 意味 |
|---|---|---|
| ✓ | pass | 基準を満たす |
| ✗ | fail | 満たさない。detailに理由 |
| - | na | この記事には当てはまらない（操作図がない記事の操作図の基準など） |
| w | waived | 自動判定はfailだが、レビューで理由を書いて免除した |
| ? | unreviewed | まだ誰もレビューしていない |
| ~ | stale | レビューの後に本文が変わった。前回の判定を読み直す |
| + | new | レビューの後に基準が追加された、または厳しくなった |

記事の状態は、failが一つでもあれば **要修正**、failはないが ?・~・+ があれば **要レビュー**、すべて ✓・-・w なら **達成** です。

## 更新のヌケモレを見つける仕組み

- **本文が変わったら**: 台帳は、レビューした時点の本文のハッシュを持っています。本文を直すとハッシュが変わり、review基準がすべて `stale` になります。直した人は、読み直して `record` し直します。frontmatterだけの変更では変わりません。
- **基準が増えたら**: 基準の `since` は、追加した日か最後に厳しくした日です。それより前のレビューは、その基準について `new` になります。基準を厳しくしたときは `since` を今日に更新します。そうすると、全記事がその基準だけ確認待ちになります。
- **記事が消えたら・IDが変わったら**: 台帳に存在しない記事が残ると、`scripts/verify_content.py`（`validate content`）が失敗します。

品質の不足（fail や unreviewed）はビルドを止めません。止めるのは台帳の形の誤りだけです。不足は作業の順番として `next` に出ます。

## レビューを記録する

記事を読んで判定したら、`record` で記録します。記録したときの本文のハッシュが一緒に保存されます。

```bash
uv run python scripts/article_quality.py record adam --reviewer claude --pass all --fail "pitfalls.with-example=一般論だけで、例の数値がない" --na explorable.ui-names
```

- `--reviewer` は `owner`・`claude`・`codex`・`human` のどれかです。オーナーが画面で確かめたものだけを `owner` にします。
- `--pass all` は、ほかで指定しなかったreview基準をすべてpassにします。判定のない基準があると記録できません。
- `--fail ID=理由` の理由は `show` にそのまま出ます。次に直す人が読むので、どこがどう足りないかを書きます。
- `--waive AUTO_ID=理由` は、自動判定が記事の型に合わないときの免除です。例：BOは「読者に先に選ばせる」型なので、図の後の番号付きの確かめ項目の代わりに小見出しで観察を追います。免除は理由とともに台帳に残ります。
- auto基準はレビューで判定しません（記録しようとするとエラーになります）。直すか、免除します。

AIがレビューするときは、`show` の出力にあるreview基準を一つずつ、記事の該当箇所を引いて判定します。分からない基準をpassにしません。画面を見ていないときは `screen.three-widths` をfailにせず、`record` の前に画面を確かめるか、その基準だけ別の人に回します。

## 基準を足す・変える

1. `teaching-article-playbook.md` に書き方を足します（台帳だけに基準を書きません）。
2. `article_quality_criteria.json` に基準を足し、`since` を今日にします。`guide` には根拠となる文書の節を書きます。
3. Markdownから測れる基準は `check: auto` にし、`article_quality.py` の `AUTO_CHECKS` にprobeを足します。見本（`concept.linear-least-squares`）が達成のままであることを、`tests/test_article_quality.py` が確かめます。見本がfailになるprobeは、基準ではなくprobeが間違っています。
4. 読まないと判定できない基準は `check: review` にします。

## レビューの流れ

2026-10-04に3記事で試し、次の流れに決めました。

1. **一次レビュー**（Sonnetなどのエージェント、記事ごとに並列）：`show` のreview基準を、行番号つきの根拠とともに判定する。例の数値は計算し直す。台帳には書かず、判定をJSONで返す（並列で同じ台帳を書くと衝突するため）。
2. **照合**（Claude）：一次レビューの主張を本文と照らし、判定を覆すときは理由をメモに残す。`screen.three-widths` は実際の描画を1280px・375px・320pxで見て判定する。Markdownだけを読んで画面の基準をpassにしない。そのうえで `record` する。
3. **最終確認**（オーナー）：実際の画面で記事を読む。オーナーが確かめた記事だけ `--reviewer owner` で記録し直す。

記事を直したら、直した人とは別のエージェントがもう一度一次レビューをします。書いた本人の判定だけで達成にしません。

試行で分かったこと：

- 自動判定が見本でfailになったら、基準かprobeの誤りです。method記事に「つまずきやすい点」の基準を当てていた誤りは、この方法で見つかりました。
- 画面で見て初めて分かる不具合があります（`aligned` の数式が崩れる、320pxで帯がはみ出す）。見つけた不具合のうち、Markdownから判定できるものは自動判定に足します（`math.renders`）。

## 初期状態（2026-10-04）

- 見本の3本（線形最小二乗、Adam、ベイズ最適化）を、オーナーの見本承認として記録しました。基準ごとの判定ではなく、見本として全体を承認したものです。
- 線形計画とGauss–Newton法は、上の流れの2まで済んでいます（要修正）。
