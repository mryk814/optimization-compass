# 記事の見本を別のPCで試す

線形最小二乗と座標降下法で、「触る → 変化を見る → 疑問を持つ → 式で確かめる」流れを試せます。
図の役割、書き手の視点、検収基準は [記事の共通パターン](article-experience-pattern.md) を参照してください。

## 固定するもの

対象repositoryは `mryk814/optimization-compass`、受け渡しbranchは `codex/komori-20261003-article-patterns` です。
基点は `8e91f04b06494cfbda148567d34173d48062594d` です。既存のrelease、DB、推薦、workflowは変更しません。
候補の `b6ca135` と `27a758e` からコードと教材を取り込み、受け渡し用に履歴を構成しています。

| 道具・依存 | 検証環境・固定方法 |
|---|---|
| Python | 3.12。`.python-version` と `pyproject.toml` の範囲に従う |
| uv | 0.12.19で検証。`uv.lock` を変更せず `--frozen` で同期 |
| Node.js / npm | 24.19.0 / 11.9.0で検証 |
| site依存 | `site/package-lock.json` に従って `npm ci`。`npm install` で更新しない |
| ブラウザ検査 | lockfileのPlaywright 1.61.1と、その版のChromium |

lockfileは基点と同じです。生成JSONは正準のMarkdown、registry、生成コマンドから作ります。

## checkoutと生成

以下はWindows PowerShell用です。macOS/Linuxでは `npm.cmd` を `npm` に置き換えます。
既存のrepositoryを起点に、作業中のmainとは別のworktreeを作ります。受け渡しbranchがremoteに存在することを先に確認してください。

```powershell
git fetch origin codex/komori-20261003-article-patterns
git worktree add -b trial/article-patterns ../optimization-compass-article-trial origin/codex/komori-20261003-article-patterns
cd ../optimization-compass-article-trial
git rev-parse HEAD
git status --short
node --version
npm.cmd --version
uv --version
uv lock --check
uv sync --frozen --all-extras --all-groups
npm.cmd --prefix site ci
uv run --frozen optimization-compass export-site-data --output site/public/data
git diff --exit-code -- site/public/data
```

`git rev-parse HEAD` は受け渡された完全SHAと照合します。生成後のdiffが出た場合は、手でJSONを直さず、checkoutと生成条件を確認します。
このbranchは記事とUIを含むため、記事だけを扱う `ready content` にまとめず、exportと検証を分けます。

## 検証とpreview

```powershell
uv run --frozen optimization-compass validate tier-a
uv run --frozen optimization-compass validate content-ready
uv run --frozen pytest tests/test_content_quality.py tests/test_explorables.py tests/test_content_models.py tests/test_content_authoring.py tests/test_branch_and_bound_content_links.py
uv run --frozen ruff check .
uv run --frozen ruff format --check .
npm.cmd --prefix site test -- --run
npm.cmd --prefix site run build
cd site
npx.cmd playwright install chromium
$env:CI = "1"
$env:PLAYWRIGHT_PORT = "4319"
npm.cmd run test:e2e:artifact -- e2e/coordinate-descent-article.spec.ts e2e/least-squares-article.spec.ts e2e/explorable.spec.ts e2e/bayesian-optimization.spec.ts --project=chromium-desktop
Remove-Item Env:CI
Remove-Item Env:PLAYWRIGHT_PORT
npm.cmd exec -- vite preview --host 127.0.0.1 --port 4319 --strictPort
```

buildにはアプリとNode用の型検査が含まれます。検証環境ではsite単体テスト450件が通過し、既存の1件がskip、上記Pythonテスト48件とブラウザ検査30件が通過しています。
この環境のブラウザ検査は、CDN取得の拒否によりインストール済みChromium 151を指定したローカル設定で代替しました。
PCでは上記の標準設定を使い、取得が拒否された場合は結果を未実行として記録してください。

previewは `http://127.0.0.1:4319/optimization-compass/` です。記事への入口は次の2つです。

- `#/learn/concept.linear-least-squares`
- `#/learn/coordinate-descent`

線形最小二乗では点4を上へ動かし、「二乗和が最小の直線」で残差と二乗和を見ます。
座標降下法ではリセット後に「最初から」へ戻り、「1つ進む」で点と式を追います。最小点からの開始、図の切替、キーボード操作も確認できます。
PC 1280pxとスマホ375px、320pxで、主図・補助図の大きさ、近くの本文、目次、操作文字を見ます。
文字200%とタッチイベントはChromiumで確認済みです。Android実機と、この手順を使う別のPCでの実行は未確認です。
320pxの線形最小二乗には、記事外の既存の次の学習カードで約2pxの横はみ出しがあります。

## CIと復旧

現行workflowは、作業branchへのpushだけでは起動しません。Pagesのdeployは `main` へのpushに限ります。
ここに示したローカル検証結果と、GitHub Actionsの実行結果は区別してください。

previewを止めるには `Ctrl+C` を押します。試用worktreeの中で `git switch --detach 8e91f04b06494cfbda148567d34173d48062594d` とすれば基点へ戻れます。
その場合はexportとbuildを再実行してpreviewを作り直します。試用先の変更を保持する必要があるときは、先にcommitまたはstashへ保存してください。
受け渡しcommitを取り消す場合は、その完全SHAを指定した `git revert <SHA>` を使います。
