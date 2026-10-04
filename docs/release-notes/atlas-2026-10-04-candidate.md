# Atlas更新候補 — 2026-10-04

状態: 公開前の統合候補。mainへのマージ、PRのclose、tag作成、GitHub Releaseの公開、Pages配信は未実施。

## 更新内容

- レビュー済み50稿と図57 paths、再現資料137 filesを、mainの教材・操作図・スマホ表示の改善と統合。
- 記事のsummary、caption、節順を公開契約へ揃え、公式の検索・取得・本文indexを再生成。
- 近接勾配の図は、灰の現在値0 → 青緑の中間点0.75 → 橙の更新値0.55という最初の一手を同じ目盛りで表示。λ=3では中間点を保ち、更新値だけが0になる。
- 凸性の静止図を本文の関数と一致させ、101点を有理数で照合。
- Actionsの4更新を統合候補で確認。checkoutとdeploy-pagesの修正に加え、setup-uvのcache挙動、setup-pythonの削除inputもレビュー。

既存のmethod/source ID、推薦、schema、runtime SQLite、問題catalogの意味は保持する。
今回全code例を再実行したとは主張しない。OR-ToolsとOptunaの未実行注記を保持する。

## 統合順とPR整理案

基準main: `96233f1b105ffdacdd1cdced03a89def1d950e8e`。公開中のdeploymentもこのcommitとdataset `0.18.19`を識別していた。

| PR | 判断 | 根拠と次の操作 |
|---|---|---|
| [#287](https://github.com/mryk814/optimization-compass/pull/287) | 最初のマージ候補 | head `b323bc966c8571d36b09a4e8bd18ef70a525b54d`。CI #802成功、オーナーの近接勾配レビューを反映済み |
| [#281](https://github.com/mryk814/optimization-compass/pull/281) | 次のマージ候補 | head `926e5855d63065fb21471008fbb2d7d02e699861`。CI #795成功。#287との合成は競合なし。#287マージ後のmainへ更新し、必須CIを確認してからマージ |
| [#285](https://github.com/mryk814/optimization-compass/pull/285) | #287マージ後のclose候補 | 39変更filesの実内容を照合。26 authority filesと最小二乗SVG3枚を同一内容で保持。残る7 authority filesは本文・登録・表示の追加改善で、元の見本・規則を保持 |
| [#258](https://github.com/mryk814/optimization-compass/pull/258) | close候補 | EC021/EC027/EC028はmainに存在。EC027/EC028の本文等は同一で、可視化・比較が追加。EC021は同じAdamW/Momentum SGD/BFGSの判断を保った画像分類の教材へ更新。旧生成物・件数をマージすると現在の拡張を戻す |
| [#283](https://github.com/mryk814/optimization-compass/pull/283) | 保留、依存更新として別途修正 | CI #787はPygments更新後の`content.json`生成driftで失敗。auditは成功。更新後の依存で公式生成し、変更と互換性をレビューする必要がある |
| [#280](https://github.com/mryk814/optimization-compass/pull/280) | 保留、major互換性を別途修正 | CI #786はTypeScript 7のCSS副作用import型宣言エラーで失敗。auditは成功。TypeScript/Vitest/jsdom等のmajor更新を含み、今回の教材公開へ混ぜない |
| [#252](https://github.com/mryk814/optimization-compass/pull/252) | Draftを保持、単純な重複ではない | 6変数の`INSTANCE_SHAPE_DIFFUSER_QUASI1D`とその関数はmainにない。mainは別の3変数`INSTANCE_DIFFUSER_SHAPE_3P`を持つ。旧PRのshape定義とdataset 0.18.7は現行契約へそのままマージできない |

PRのcloseやマージは、この整理案をオーナーが確認してから行う。
追加の統合用mega PRは作らず、既存の小さなマージ順を保つ。

## 版と公開の意味

今回の推奨は **dataset 0.18.19を保持したAtlas更新**。
dataset versionはSQLiteを含む知識データ配布のidentityであり、教材・UIの更新日ではない。
Pythonとsite packageの`0.1.0`、各JSONのcontract versionも独立した値である。
教材更新のために`DATASET_VERSION`、release authority、catalog、CITATIONや既存`v0.18.19`tagを変更しない。

新しいdataset版・配布ZIP・tag・GitHub Releaseを作る場合は、別の公開範囲と版を確定し、公式staging・bundle・catalogの一体検証を行う。
`0.18.7`の再公開や既存版の使い回しはしない。

**mainへのマージはPages公開を起動する。** 現行workflowはmain pushで検証・同一artifactのbrowser/axe検査・deploy・remote smokeを実行する。
PRのCI成功やこのローカル候補は、本番公開完了を意味しない。
公開後は、最終mainのworkflowと公開`deployment.json`が同じcommitとdatasetを識別することを確認する。
`scripts/pages_checkpoint.py --run-id <最終mainのrun-id> --require-published`を最終判定に使う。

## 依存とworkflowの確認

#281の4つのSHAは、upstreamの正確なrelease tagのcommitと一致した。
`contents: read`、main-only deploy、同じvalidated artifactを検査・配信する境界を保持する。

- [setup-uv v9](https://github.com/astral-sh/setup-uv/releases/tag/v9.0.0): cache pruningの既定値がfalseへ変更。
- [setup-uv v10](https://github.com/astral-sh/setup-uv/releases/tag/v10.0.0): `enable-cache: auto`は敏感なeventでcacheを無効化。現行workflowは`enable-cache: true`を明示し、`pull_request_target`や`workflow_run`を使わない。
- [setup-uv v10.2](https://github.com/astral-sh/setup-uv/releases/tag/v10.2.0): merge queueでcache保存を停止。現行workflowはmerge queue eventを使わない。
- [setup-python v7](https://github.com/actions/setup-python/releases/tag/v7.0.0): `pip-install` inputを削除。現行workflowはこのinputを使わず、Python 3.12を明示する。
- [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1)、[deploy-pages v5.0.1](https://github.com/actions/deploy-pages/releases/tag/v5.0.1): pinned修正を使用。

known-vulnerability auditとlicense inventory生成は3つの依存PRで成功していたが、失敗した互換性・生成driftを免除する根拠にはしない。

## 検証の引継ぎ

#287のCI #802: Python705、site unit494（skip1）、critical browser20が成功。
#281のCI #795: 検証・browser/axeが成功。
deploy-pagesとdeploy専用setup-pythonはPRで実行されないため、最終mainのdeploy・smokeで確認する。

合成後のアプリ入力は#287と同一で、差分はworkflow2 files。
50稿の先行表示・数理の確認を再利用し、統合後の新しいproduction buildと、公開を阻止するcritical/axe検査、PC・375pxの代表画面を確認する。
検証結果・候補SHA・artifact hash・個人レビュー経路とrollbackは、作業環境のprivate receiptに記録する。
合成候補そのものにGitHub CIが成功したとは主張しない。最終mainの公開CIを省略しない。

## Licenseと戻し方

codeはMIT、data/contentはCC-BY-4.0。既存NOTICE・帰属・例外を保持する。
個人レビューは既存の経路と旧artifactを保全し、記録した自分のレビューprocessだけを置き換える。
公開後に問題が出た場合は、レビュー済みrevertを同じ公開workflowへ通し、手作りartifactのuploadで迂回しない。
