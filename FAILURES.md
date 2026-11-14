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
