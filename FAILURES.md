# 失敗の記録

このリポジトリで起きた失敗と、同じ失敗を起こさないために残したもの。

## 2026-11-14 補助図の `--check` が Windows でいつも落ちていた

- **したこと**: `uv run python scripts/generate_lesson_figures.py --check`
- **起きたこと**: `trajectory-grid-check.svg` と `inverseProblem.fixture.json` がいつも stale と出た。`--check` を付けずに走らせると、この2つが書き換わった。
- **原因**: コミット済みの版は Linux で作られていた。libm の最後の桁の違いで、(1) 制約が効いて柱の縁にちょうど乗る格子点が内側か外側かが変わり、(2) fixture の17桁の浮動小数の末尾が変わった。
- **直し方**: 縁の判定に 1e-9 の幅を持たせ、fixture の浮動小数を12桁に丸めた（`scripts/lesson_figures/trajectory_optimization.py`、`inverse_problem.py`）。
- **再発防止**: 理由を両方のコードの横にコメントで残した。`docs/writing-articles.md` に、機械精度に近い値は桁で書くと書いた。図の出力で、境界ちょうどの判定や全桁の浮動小数を書くと、同じことが起きる。

## 2026-11-14 並列実行の試験が、起動のしかたで「No module named 'scripts'」になった

- **したこと**: `-n auto`（pytest-xdist）を既定にした全体の試験。
- **起きたこと**: 同じ内容の実行で、ある回だけ `tests/lesson_figures/` の52件が集める段階で失敗した。再実行すると通った。
- **原因**: 補助図の試験は `scripts.lesson_figures` を import する。`python -m pytest` はカレントディレクトリを sys.path に入れるので通るが、ほかの起動のしかたでは入らない。
- **直し方と再発防止**: `pyproject.toml` の pytest 設定に `pythonpath = ["."]` を書いた。`tests/` から起動しても通ることを確かめた。

## 2026-11-14 開発サーバーでだけ、lesson が動かない静的な表示のままになった

- **したこと**: 予想の段の選択肢をボタンに描き直すために、マウント時に元の箇条書き（`<ul data-lesson-choices>`）の中身を消した。
- **起きたこと**: `npm run dev` の画面で lesson が立ち上がらず、図が代替文のままになった。エラーは出ない。
- **原因**: 開発時の React StrictMode は effect を2回走らせる。2回目に同じ HTML を読み直すと、選択肢がもう消えているので「読めない lesson」と判定され、静的な表示に戻していた。
- **直し方**: 元の箇条書きは消さず CSS で隠し、ボタンは隣に足した要素へ描く（`site/src/features/explorable/lessonMarkup.ts`）。同じ HTML を何度読んでも同じ結果になる。
- **再発防止**: `Lesson.test.tsx` の「Reading the same markup again」が、2回読んでも同じ選択肢と同じ描画先になることを確かめる。コンパイル済みの HTML を読む処理は、読んだものを壊さない形で書く。

## 2026-11-14 レビュー用の静止画で、lesson の最初の段だけが掃引の途中で写った

- **したこと**: `npm --prefix site run shots -- concept.hyperparameter-optimization`。段ごとに `window.__ocLessons[...].show(index)` で終了状態を出して撮る。
- **起きたこと**: 375px の1段目だけ、掃引の終わり（log10 λ = 1）ではなく途中（−3.5）の図が写り、段の文章の数値と合わなかった。1280px と、ほかの段は正しかった。
- **原因**: その段の時計が動いている最中に `show` を呼ぶと、React が時計の effect を片付ける前に、予約済みの `requestAnimationFrame` が1回走り、`show` が置いた秒数を時計の秒数で上書きしていた。375px では lesson が最初から画面内にあり、時計が動いていた。
- **直し方**: `show` がその場で立てる ref（`holding`）を時計の各フレームが見て、立っていれば何もしない（`site/src/features/explorable/Lesson.tsx`）。
- **再発防止**: `Lesson.test.tsx` の「keeps a held step where automation put it…」が、`show` の直後に時計のフレームが走っても終了状態のままであることを確かめる。state で止める時計は、止める側が同期で読める印も持たせる。

## 2026-11-14 補助図を書き出すと、Windows で関係のない図が全部「変更あり」になった

- **したこと**: 新しい fixture を足すために `uv run python scripts/generate_lesson_figures.py`（`--check` なし）。
- **起きたこと**: `git status` に `site/public/figures/*.svg` 66個と `inverseProblem.fixture.json` が変更として出た。`git diff --stat` は空だった。
- **原因**: この PC は `core.autocrlf=true` で、作業ツリーのファイルは CRLF。スクリプトは LF で書き出すので、中身が同じでも作業ツリーのバイトが変わる。
- **直し方**: `git checkout -- site/public/figures site/src/features/explorable/math/inverseProblem.fixture.json` で戻し、自分の出力だけを足した。`--check` は文字として比べるので影響を受けない。
- **再発防止**: 記録だけ。コミットに混ざる差分ではない（Git が改行を正規化する）ので、仕組みは足していない。書き出した後に大量の変更が見えたら、まず `git diff --stat` が空かを見る。
