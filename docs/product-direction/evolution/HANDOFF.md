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
| 014〜018 | 辞書スライス（射影と線形 oracle／分割法・PDHG／分解と列・制約生成／不確実性・多段階／BO の安全・失敗・多忠実度） | 004 / 008 | 手法の**行**は 0.18.22 と 0.18.23 で入りました。記事はまだです |
| 019 | 問題構造 80 候補の正準対応 | 004 | STRUCTURE_* の10件が `unrepresented` で残っています |
| 020〜032 | 判断規則、実装への橋、persona の入口、評価、a11y、動画、実験室ほか | 上記 | 未着手 |

課題ごとの詳しい受入条件は、元のパックの `backlog/OC-EVOL-0NN.md` にあります。パックが手元になければ、オーナーに頼んでください。

## いま開いている作業（2026-10-10 時点）

マージ済み: #308（収録範囲 v1 の承認、ロバスト回帰の操作図、この文書）、#309（手法24個、0.18.22）、#311（件数固定をやめるテスト方針）、#312（記事 PA039 ハイパーパラメータ最適化）。

| PR | ブランチ | 中身 | 次にやること |
|---|---|---|---|
| 0.18.23 の PR | `claude/eager-ramanujan-cov8ei-methods-0.18.23` | 手法11個（migration 034、035）と 0.18.23 の公開生成物 | CI が緑ならマージし、メンテナーにタグとバンドルを頼みます |

`site/public/data/**` は複数の PR が同時に触ります。後からマージする側は、main を取り込み、`uv run optimization-compass export-site-data --output site/public/data` と報告2本（`scripts/content_quality_report.py`、`scripts/method_content_density_report.py`）で作り直します。生成物の衝突を手で解いてはいけません。

### メンテナーの作業: タグとバンドル

0.18.22 と 0.18.23 のタグと GitHub Release を作り、バンドル ZIP をアップロードします。ZIP を作った環境は消えるので、次の手順でリポジトリの外に作り直します。`rebuild_dataset.py` は決定的です。

1. 公開の元にしたコミット（版の番号を上げただけで、生成物の公開前の状態）を checkout します。
2. `uv run python scripts/rebuild_dataset.py --stage --output <外の dir>/stage` を実行し、tree の sha256 を確かめます。
3. `uv run python scripts/rebuild_dataset.py --publish --staged-directory <外の dir>/stage --bundle-output <外の dir>/bundle --source-commit <そのコミット> --tag v<版>` を実行します。
4. ZIP の大きさと sha256 が下の表と一致すれば、アップロードします。一致しなければ、アップロードせずに報告してください。publish はリポジトリ内の生成物も書き換えるので、この checkout は捨てます。

| 版 | source commit | tree sha256 | ZIP |
|---|---|---|---|
| 0.18.22 | `08f22fa6dda5fc2f4ba8530ff2e2d66a35fe8a9f` | `9f29ef1a9acb66a26c61e9b6d3272fc4ecfaaeb850c9c352b08a6a190039bd61` | 6,131,838 バイト、sha256 `e77c833b0f355e417e4821b34623dc1b7f47465f7829316461745bbda8163a41` |
| 0.18.23 | `f353246ad11813536b653fc86ef4fb04ae4356d9` | `28976a25a69e579f7c1352e28418441b98f51dd31c8f7841e966cf8cc0a15a73` | 6,306,363 バイト、sha256 `46e7cd81d37f342ae69de393ce352767f73ed2fe60dac33d76cacf8f55328891` |

### 0.18.23 で仮に置いた判断（レビューで変えてよいもの）

- SAA を MF_DISCRETE_EXACT に置きました。合うファミリーがないので、Benders と並べています。
- Submodular greedy を MF_GRAPH_DP に置きました。前例は M_LOCAL_SEARCH_COMBINATORIAL です。
- 非均衡 Sinkhorn は行を作らず、M_SINKHORN の別名と出典にしました。TOPIC は `variant_of` です。
- Sobol 列は部品と判断し、行を作っていません。TOPIC は `unrepresented` のままです。

## 手法を足すリリースの手順

1. 手法を足す migration をコミットします（下の「作業の型」）。
2. `uv run optimization-compass validate manifest` を実行します。
3. 版を上げます（3か所）。
   - `src/optimization_compass/resources/release-authority.json`（`dataset_version` と `release_date`）
   - `tests/test_dataset_formats.py` の `STAGED_TEST_VERSION`
   - `tests/test_release_identity.py` の assert
4. 版上げをコミットします。この commit を `--source-commit` に使います。
5. `rebuild_dataset.py --stage --output <外>` を実行します（2回ビルドして一致を確かめます）。続けて `--publish --staged-directory … --bundle-output <外> --source-commit <4の commit> --tag v<版>` を実行します。
6. 生成物をそろえます。
   - `dataset_publication.py prepare --bundle <zip> --output-directory <存在しない外の dir>` を実行し、出力の CITATION.cff を repo 直下へ、DATASET_CARD.md を `docs/dataset-card.md` へコピーします。そのあと `dataset_publication.py check` を実行します。
   - `recommendation_parity.py --update` を実行し、差分が版の番号だけであることを確かめます。`problem_method_fit` を足していなければ、推薦は変わらないはずです。
   - `generate_article_figures.py`、`export-site-data`、報告2本を作り直します。
   - `pytest`（`test_historical_releases.py` は shallow clone では落ちるので除きます）を実行します。件数は生成元から数えるので（#311）、件数のテストを書き換える必要はありません。
7. PR を出します。マージ後に、上の「メンテナーの作業」の表へ行を足して、タグとバンドルを頼みます。

## この後の作業の候補（推奨順）

1. 0.18.23 の PR を出し切ります。生成物は毎回最新の main から作り直します。
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
