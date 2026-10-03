# 記事体験と検証効率化のPC隔離試用

候補branchは `codex/komori-20261003-integrated-trial`。公開サイトへ反映する前に、記事体験と検証タスクの合流をPCで確認するための保存点です。

## 統合した保存点

| 対象 | 完全SHA |
|---|---|
| 共通base | `8e91f04b06494cfbda148567d34173d48062594d` |
| 記事の共通パターン・線形最小二乗・座標降下法 | `77638a5321e36bf4e5be75d483c5686c3135fc88` |
| build/typecheckの重複削減・同じbuildを使うE2E | `4176d93639d315d09504c48869a04f222f42fccc` |

2候補の変更ファイルは重ならず、履歴を残すmergeで統合しました。通常repoと別のGit保管庫に専用worktreeを置き、通常main・未コミット状態・stashには書き込んでいません。別担当のB&B試用版は、この候補に含めていません。受け渡された完全SHAを確認してから合流対象を決めます。

入力はrepository内の既存Markdown・registry・seed・migration・base SQLiteです。追加の第三者資料は取得していません。既存のMIT、CC BY 4.0、NOTICEと出典を保持しています。両lockfileは共通baseと同一です。

## 今回選んだ確認

既存の記事候補の結果は [article-pattern-trial.md](article-pattern-trial.md) を参照しました。検証効率化候補の受け渡しでは、Python 700件、E2E 117件、生成物222個のhash一致、clean cloneのbuild/preview成功が報告されています。これらを既存証跡として扱い、今回実行した結果と区別します。

統合直後、trackedな公開データ99ファイルとcanonical入力は記事候補と同一でした。合流接点は検証タスクとCIの契約だけなので、各候補のfull build・全Python・全E2E・dataset stageを繰り返さず、以下を選びました。

| 今回の実行 | 結果・範囲 |
|---|---|
| `uv sync --frozen --all-extras --all-groups`、`npm --prefix site ci` | 固定依存を専用環境へ導入。lock変更なし |
| `tests/test_validate_cli.py`、`tests/test_pages_workflow.py` | 49件成功。初回42件成功と、一時フォルダーのアクセス拒否を直した7件の再確認を合算した結果 |
| 変更されたPython 3ファイルのruff check/format | 成功 |
| `npm --prefix site run build` | 成功。typecheckを含む。別のtypecheckを重ねていない |
| 最終buildを使う狭幅E2E | 7件成功。最小二乗・座標降下法の375/320px、最小二乗の再計算/reset/axe、Adam・BOの375px目次操作 |
| PC 1280px、375px、320pxの実ブラウザー表示 | 最小二乗と座標降下法の主要図を確認・画像保存 |

実行環境はWindows、Python 3.12.10、uv 0.12.5、Node 24.4.1、npm 11.4.2、lockfileのPlaywright 1.61.1とChromium 149.0.7827.55です。既存の記事証跡のChromium 151とは区別しています。

### PCで必要になった狭幅修正

初回の対象14件では13件が成功し、最小二乗の320px表示が失敗しました。readoutのgrid子要素が表の最小幅を保持することと、長いinline計算式が行外へ出ることが原因でした。readout子要素へ `min-width: 0` を付け、4点の計算式を既存の数式ブロックへ移しました。数学的な内容とアルゴリズムは同じです。

本文修正のため `optimization-compass validate content concept.linear-least-squares` と `optimization-compass export-site-data --output site/public/data` を実行しました。生成差分は `content.json` と `retrieval-documents.json` のみです。広範な生成差分はありません。

buildは統合時に1回実行し、その後は実際に表示変更を加えた2回に限って更新しました。ブラウザー確認は毎回そのbuildを利用しました。途中のinline数式スクロール案はaxeのキーボード操作検査に失敗したため、最終候補には含めていません。

Windowsではnpm shimを経由する正規表現の `|` がshellに解釈されるため、対象選択は固定PlaywrightのCLIをNodeから直接実行しました。また、最初の自動previewの終了待ちが残ったため、以後は今回専用previewを共有するローカル設定で検証しました。最終7件はrunnerがexit 0で完了しています。

## 再開と試用

受け渡し先のSHAを `git rev-parse HEAD` で照合します。既存のworktree、venv、node_modules、最終distを保存してある場合は、そのままpreviewを再開できます。作り直したcheckoutでは固定依存を導入してbuildします。

```powershell
uv sync --frozen --python 3.12 --all-extras --all-groups
npm.cmd --prefix site ci
npm.cmd --prefix site run build
cd site
node node_modules/vite/bin/vite.js preview --host 127.0.0.1 --port 4338 --strictPort
```

入口は `http://127.0.0.1:4338/optimization-compass/`。記事は `#/learn/concept.linear-least-squares` と `#/learn/coordinate-descent` です。最小二乗は定式化ページへ転送されます。使用中のportを置き換えず、別portを選びます。終了はそのpreviewのterminalで `Ctrl+C`。

## 公開操作の境界

候補branchへの通常pushだけを行います。`ci.yml` のpush対象はmainのみで、source-healthもpush triggerを持ちません。候補pushはPagesを起動しません。PR作成、main merge、公開deploy、通常のTailscale preview差し替えは行っていません。

全Python、全E2E、dataset stage、Android実機確認は今回未実行です。過去の合格件数を今回の全suite成功として扱わないでください。
