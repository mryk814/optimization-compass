# 引き継ぎ（2026-10-10 時点）

別の環境の人や AI が、この文書だけで作業を再開できるように書いています。最初に [`AGENTS.md`](../../../AGENTS.md) を読み、続けてこの文書、[進み具合の表](README.md) の順に読んでください。

## 目標

Optimization Compass の発展版（OC-EVOL）では、次の2つを並行して進め、課題の依存順に従います。

- **辞書の幅**: 承認済みの収録範囲 v1（[`data/seeds/editorial_scope.json`](../../../data/seeds/editorial_scope.json)、説明は [`docs/editorial-scope.md`](../../editorial-scope.md)）のうち、`unrepresented` の項目を減らします。
- **理解の体験**: 問題型の記事、操作図、学習経路を厚くします。

候補の一覧は「新しく足すもの」の一覧ではありません。既存の行、別名、変種、部品と照合してから足します（[`docs/identity-granularity.md`](../../identity-granularity.md)）。

オーナーの方針:
- 判断は作業者の推奨に任されています。
- 手法は収録範囲の順にスイープします。順番へのこだわりはありません。
- 文章も報告も日本語で書きます。

役割の分担: 指揮・設計・取りまとめをする AI が、コミット、push、PR、マージを担当します。実装と調査は下位のエージェントに任せてかまいません。どのコミットも DCO sign-off（`git commit -s`）が必須です。コミットや PR にモデル名を書きません。

## 課題の一覧（元の引き継ぎパック `optimization_compass_handoff_2026-10-10` から）

| ID | 題名 | 依存 | 状態 |
|---|---|---|---|
| 001 | 基準監査と既存作業の照合 | – | 完了 |
| 002 | 編集上の収録範囲 v1 | 001 | 完了（オーナー承認） |
| 003 | Coverage へ分母と品質軸を統合 | 002 | 完了 |
| 004 | 同一性と粒度の対応ルール | 002 | 完了 |
| 005 | 条件付き関係の意味契約 | 004 | 未着手 |
| 006 | 俯瞰図と条件レンズ | 005 | 未着手 |
| 007 | 初学者の辞書→一手→次の問い | 004 | 未着手。**persona の順番が未決定** |
| 008 | 高価な評価の利用者 journey | 004 | 未着手。**同上** |
| 009 | 分野ブリッジの最小3件 | 005 | 未着手 |
| 010 | 共有 scene・observable・媒体契約の差分 | 001 | 完了 |
| 011 | 主単体法を証明・感度・動画へ拡張 | 007, 010 | 操作図と本文は完了。動画は未着手 |
| 012 | BO の視界制限・予測・評価費 | 008, 010 | 未着手 |
| 013 | 輸送の対応と正則化を体験 | 009, 010 | 未着手 |
| 014〜018 | 辞書スライス（射影と線形 oracle／分割法・PDHG／分解と列・制約生成／不確実性・多段階／BO の安全・失敗・多忠実度） | 004 / 008 | 手法の**行**は下の PR で入りました。記事はまだです |
| 019 | 問題構造 80 候補の正準対応 | 004 | STRUCTURE_* の10件が `unrepresented` で残っています |
| 020〜032 | 判断規則、実装への橋、persona の入口、評価、a11y、動画、実験室ほか | 上記 | 未着手 |

課題ごとの詳しい受入条件は、元のパックの `backlog/OC-EVOL-0NN.md` にあります。パックが手元になければ、オーナーに頼んでください。

## いま開いている作業（push 済み）

| 種類 | ブランチ / PR | 中身 | 次にやること |
|---|---|---|---|
| PR [#308](https://github.com/mryk814/optimization-compass/pull/308) | `claude/eager-ramanujan-cov8ei` | 収録範囲 v1 の承認反映、ロバスト回帰の操作図 `robust-loss-pull`、この引き継ぎ文書 | CI が緑ならマージします。main が進んでいたら、main を取り込み、`export-site-data` と報告2本を作り直してから push します |
| PR [#309](https://github.com/mryk814/optimization-compass/pull/309)（draft） | `claude/eager-ramanujan-cov8ei-rel-0.18.22` | 手法24個（migration 028〜033）、0.18.22 の公開生成物 | 下の「0.18.22 を仕上げる」 |
| PR [#311](https://github.com/mryk814/optimization-compass/pull/311)（draft） | `claude/eager-ramanujan-cov8ei-test-counts` | テストの件数固定をやめ、生成元（DB・seed）と突き合わせる形にする | CI が緑ならマージします。#309 より先が望ましく、#309 は取り込むときに件数の行をこちらに合わせます |
| ブランチ（PR なし） | `claude/eager-ramanujan-cov8ei-pa039` | 記事 PA039 ハイパーパラメータ最適化（数値の照合、3幅の画面確認、台帳の記録まで済み） | 下の「PA039 を出す」 |
| ブランチ（PR なし） | `claude/eager-ramanujan-cov8ei-methods-0.18.23` | 手法11個（migration 034、035） | 下の「0.18.23 を作る」 |

`site/public/data/**` は複数の PR が同時に触ります。後からマージする側は、main を取り込み、`uv run optimization-compass export-site-data --output site/public/data` で作り直します。生成物の衝突を手で解いてはいけません。

### 0.18.22 を仕上げる（#309）

1. 先に #308 がマージされていれば、main を #309 のブランチへ取り込みます。`site/public/data` は `export-site-data` で作り直し、報告2本も作り直します。
   - `uv run python scripts/content_quality_report.py`
   - `uv run python scripts/method_content_density_report.py`
2. 生成物の版が 0.18.22 のままかを確かめます。
   - `uv run python scripts/dataset_publication.py check`
   - `uv run python scripts/verify_content.py`
3. CI（tier-b、約22分）が緑になったら、draft を外してマージします。
4. **メンテナーの作業**: タグと Release `v0.18.22` を作り、バンドル ZIP をアップロードします。
   - ZIP は作った環境と一緒に消えました。`rebuild_dataset.py` は決定的なので、次の手順でリポジトリの外に作り直せます。
     1. 公開の元にしたコミット `08f22fa6dda5fc2f4ba8530ff2e2d66a35fe8a9f` を checkout します（版の番号を上げただけで、生成物の公開前の状態です）。
     2. `uv run python scripts/rebuild_dataset.py --stage --output <外の dir>/stage` を実行します。tree の sha256 は `9f29ef1a9acb66a26c61e9b6d3272fc4ecfaaeb850c9c352b08a6a190039bd61` になるはずです。
     3. `uv run python scripts/rebuild_dataset.py --publish --staged-directory <外の dir>/stage --bundle-output <外の dir>/bundle --source-commit 08f22fa6dda5fc2f4ba8530ff2e2d66a35fe8a9f --tag v0.18.22` を実行します。
   - 期待値は `optimization_method_selection_database_v0.18.22_bundle.zip`、6,131,838 バイト、sha256 `e77c833b0f355e417e4821b34623dc1b7f47465f7829316461745bbda8163a41` です。
   - publish はリポジトリ内の生成物も書き換えます。この checkout は捨ててください。
   - sha が一致しなければ、アップロードせずに報告してください。

### PA039 を出す

ブランチ `claude/eager-ramanujan-cov8ei-pa039` の 6082525 は、古い main の上にあります。
1. 最新の main から新しいブランチを切り、この commit を cherry-pick します。
2. `site/public/data/*` と `docs/content-quality-report.md` で衝突したら、自分の側を捨て、`export-site-data` と報告スクリプトで作り直します。
3. `uv run python scripts/article_quality.py show concept.hyperparameter-optimization` が「達成」のままかを確かめます。記録日より後に本文が変わっていなければ、stale になりません。
4. 次を確認してから PR を出します。
   - `uv run optimization-compass validate content`
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run python scripts/generate_lesson_figures.py --check`
   - `uv run python -m pytest tests/test_lesson_figures.py tests/test_article_quality.py tests/test_content_report_drift.py tests/test_editorial_scope.py -q`

### 0.18.23 を作る（手法11個）

ブランチ `claude/eager-ramanujan-cov8ei-methods-0.18.23` には、2つのコミットがあります。どちらも 0.18.22 の版上げより前の点（57092c1）から分かれています。

| commit | migration | 手法（ファミリー） | 出典 / evidence |
|---|---|---|---|
| b53d8f9 | 034 | M_BOBYQA（MF_DFO_LOCAL）、M_SAFEOPT・M_CONSTRAINED_BO（MF_SURROGATE_HPO）、M_PAREGO（MF_MULTI_OBJECTIVE）、M_SUBMODULAR_GREEDY（MF_GRAPH_DP）、M_LEVELSET_TOPOLOGY（MF_TOPOLOGY_OPTIMIZATION）、実装の対応 MIM_BOBYQA_NLOPT | S145–S152 / EL004256–4264 |
| 2a6da88 | 035 | M_SAA・M_CCG（MF_DISCRETE_EXACT）、M_PROGRESSIVE_HEDGING・M_SINKHORN（MF_LP_QP_CONIC）、M_SDDP（MF_GRAPH_DP） | S160–S167 / EL004280–4289 |

手順:
1. #309 がマージされたら、最新の main から新しいブランチを切り、2つの commit を cherry-pick します。
   - 衝突しやすいのは `data/build-manifest.json`（033 の後ろに 034、035 を並べる）、`tests/test_build_manifest.py`（`range(3, 36)`）、`editorial_scope.json` の3つです。
2. `uv run optimization-compass validate manifest` を実行します。
3. 版を 0.18.23 に上げます（3か所）。
   - `src/optimization_compass/resources/release-authority.json`（`dataset_version` と `release_date`）
   - `tests/test_dataset_formats.py` の `STAGED_TEST_VERSION`
   - `tests/test_release_identity.py` の assert
4. 版上げをコミットします。この commit を `--source-commit` に使います。
5. `rebuild_dataset.py --stage --output <外>` を実行します（2回ビルドして一致を確かめます）。続けて `--publish --staged-directory … --bundle-output <外> --source-commit <4の commit> --tag v0.18.23` を実行します。
6. 生成物をそろえます。
   - `dataset_publication.py prepare --bundle <zip> --output-directory <存在しない外の dir>` を実行し、その出力の CITATION.cff を repo 直下へ、DATASET_CARD.md を `docs/dataset-card.md` へコピーします。そのあと `dataset_publication.py check` を実行します。
   - `recommendation_parity.py --update` を実行します。差分が版の番号だけであることを確かめます。`problem_method_fit` を足していないので、推薦は変わらないはずです。
   - `generate_article_figures.py`、`export-site-data`、報告2本を作り直します。
   - `pytest`（`test_historical_releases.py` は shallow clone では落ちるので除きます）を実行します。
   - #311 がマージ済みなら、この項目は不要です（件数は生成元から数えます）。まだなら、件数を固定したテストを直します。0.18.22 では #309 の 4dd2fb9 で直しました。0.18.23 で増えるのは、手法 +11、出典 +16（S145–S152、S160–S167）、evidence +19 です。
     - `tests/test_coverage.py`: `"method"` を 129→140、`len(report.subjects)` を 196→207
     - `tests/test_evidence.py`: 出典数を 143→159、evidence_targets の合計を 4253→4272
     - `tests/test_site_export.py`: 出典数を 143→159、合計を 4269→4288
     - `tests/test_source_health.py`: 143→159
     - 数は実行して確かめます。増分が migration の行数と合わなければ、テストを合わせずに原因を調べます。
7. 0.18.22 と同じ形の PR を出し、メンテナーにタグとバンドルを頼みます。

この版で仮に置いた判断です。レビューで変えてよいものです。
- SAA を MF_DISCRETE_EXACT に置きました。合うファミリーがないので、Benders と並べています。
- Submodular greedy を MF_GRAPH_DP に置きました。前例は M_LOCAL_SEARCH_COMBINATORIAL です。
- 非均衡 Sinkhorn は行を作らず、M_SINKHORN の別名と出典にしました。TOPIC は `variant_of` です。
- Sobol 列は部品と判断し、行を作っていません。TOPIC は `unrepresented` のままです。

## この後の作業の候補（推奨順）

1. 上の3件（0.18.22、PA039、0.18.23）を順に出します。push 先と PR は1本ずつ、生成物は毎回最新の main から作り直します。
2. **残りの `unrepresented` を片付けます。**
   - 部品の4件（Sobol 列、feasibility restoration、interval bounds、homogeneous embedding）: 手法の行ではなく、用語集の項目にして `primitive_in` で結びます。用語集の置き場所と形式は、既存の glossary の行を見て決めます。
   - 問題構造の10件（幾何計画 GP、signomial、行列補完、レベルセットの形状、bin packing、施設配置、minimax、バンディット、非均衡輸送、劣モジュラ）: 新しい問題型（PA）の行、`data/seeds/formulation_atlas.json` の項目、関係の条件を足します。PA の行は migration なので、リリースが要ります。[`docs/formulation-atlas.md`](../../formulation-atlas.md) の recipe B と、`AGENTS.md` の不変条件（循環なし、関係の `note_ja` に条件を書く）に従います。
3. **問題型の記事**: `uv run python scripts/formulation_backlog.py` で次を選びます。PA039 の次の候補は、PA008、PA016、PA020、PA028、PA037、PA040、PA041、PA057（score 3）です。
4. **手法の記事**: 新しく足した35手法には、まだ記事がありません。OC-EVOL-014〜018 の「辞書スライス」は、行と記事と関係がそろって完了です。
5. **OC-EVOL-007 / 008**: persona の順番をオーナーに聞いてから始めます。

## 作業の型（下位エージェントに渡していた指示の要点）

### 手法を足すバッチ
- **同一性の確認**: methods、aliases、terminology_aliases、content を grep し、既にあればその項目を止めます。
- **置き方**: アルゴリズム、変種、実行できる戦略は methods の行にします（`method_level: variant`、既存の MF_* の下、理由を書く）。部品は行にしません。
- **出典**:
  - 原論文と公式文書を使います。書誌情報は公式の掲載情報（出版社、DOI、PMLR、JMLR、arXiv）で確かめ、ページは公式の掲載で確かめられたときだけ記録します。
  - Qiita と Zenn は使いません。確かめられなかった点は `notes` に書きます。
  - 権威ある一次出典がなければ、その項目を止めます。
- **列の埋め方**:
  - 兄弟の行の水準で埋め、確立していない値は `unknown` にします。
  - `confidence` は medium、`last_verified` は作業日にします。
  - `problem_method_fit` は付けません。
  - 実装の対応は、既存の implementation 行で API を確かめられたものだけにします。
  - `exactness` には schema の CHECK が許す値だけを使います（`exact` は通りません）。
- **付けるもの**: family 行の `child_method_ids`、`is_a` の階層、用語の別名（CHK025 の casefold 一意性に注意）、出典ごとの evidence_links です。
- **ファイル**:
  - `data/migrations/0NN_*.sql` を作り、`data/build-manifest.json` に sha256 付きで登録します。
  - `tests/test_build_manifest.py` の range の上限を、最後の migration 番号 + 1 にします。
  - `editorial_scope.json` の TOPIC を `same_entity` にします。
- **並行作業**: ID の範囲を作業ごとに先に割り当てて、重ならないようにします。
- **確認**:
  - `validate manifest`、`pytest tests/test_build_manifest.py`、`ruff check .` を実行します。
  - 外のディレクトリへ `build_staged_release(BASE_DATABASE, out, target_version=…, release_date=…)` でステージングします。呼び方は `scripts/rebuild_dataset.py` の `BASE_DATABASE` を使います。
  - `tests/test_editorial_scope.py::test_real_seed_validates` と `verify_content.py` は、公開前は新しい手法を知らないので落ちます。公開後に通れば正常です。

### 問題型の記事
- **お手本**: `content/concepts/` の smooth-low-dimensional-unconstrained、inverse-problem、l1-sparse-regularization、model-predictive-control です。
- **骨格**: 7節です（30秒でつかむ／標準形を読む／小さな例／つまずきやすい点／課題から定式化する／困りごとから関連する問題へ／数値計算の方法を選ぶ）。
- **書く前に読むもの**: [`docs/teaching-article-playbook.md`](../../teaching-article-playbook.md)、[`docs/article-style.md`](../../article-style.md)、[`docs/article-quality.md`](../../article-quality.md) です。
- **例と数値**:
  - 1つの題材で記事を通します。
  - 数値はすべてスクリプトで計算し、出力をコメントで貼ります。手で検算できる大きさにします。
  - 順位をつけません。ライブラリの既定は推奨ではないと書きます。
- **図**:
  - 静止図は `scripts/generate_lesson_figures.py` で生成し、`tests/test_lesson_figures.py` で数値を固定します。
  - 色は、橙＝候補・更新、緑（teal）＝実行可能・観測、赤＝違反だけ、紺＝構造です。本文の線や色の説明は、描いたとおりに書きます。
  - 細かい線分でできたパスに `stroke-dasharray` を使いません。
- **収録範囲**: `editorial_scope.json` に、その PA を refs に含む STRUCTURE_* があれば、`{"type":"content","id":…}` を足します。
- **検証**:
  - 数値は書き手と別の者が再実行して照合します。
  - 1280・375・320px の実画面を Chromium で見て、横のはみ出しと図の文字を確かめます。
  - `article_quality.py record --reviewer <名前> --pass all --na <該当しない基準> --note …` で台帳に記録します。

## はまりどころ

- main を取り込んでから生成物を作り直し、それから push します。古い main で作った `site/public/data` は、CI の drift 検査で落ちます。
- 報告2本（`docs/content-quality-report.md`、`docs/method-content-density-report.md`）は、記事を変えたら作り直します。
- `generate_lesson_figures.py` で衝突を解いた後に、末尾の `parts.append("</svg>")` と `return "".join(parts) + "\n"` が消えたことがあります。
- テストの期待値が記事の状態に依存しているものがあります。たとえば `tests/test_formulation_atlas.py` は PA の maturity を固定しています。記事や図を足すと変わります。
- サイトの `DiagnosePage.test.tsx` の結果ページのテストは約3秒かかります。上限を20秒にしてあります（#308 の a27521c）。
- `test_historical_releases.py` の3件は、タグのない shallow clone では必ず落ちます。
- worktree ごとの `.venv` が同期されていないと、ruff の版が違って `format --check` が大量に落ちます。`uv sync --all-extras --dev` を先に実行してください。
- 外のネットワーク（curl）が使えない環境では、書誌の確認は検索の結果で行い、確かめた範囲を `notes` に書きます。
