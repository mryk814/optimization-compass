# 出典台帳

出典IDは文書・JSON・課題票で共通です。機能の存在と本サイトでの統合・学習効果の実証は区別します。個々の追加候補の成立条件・保証・最新版APIは実装着手時に再レビューします。

## R01 — Optimization Compass README

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/README.md

確認日: 2026-10-10 / 種類: repository

支える内容: 公開データセット0.18.20、105手法行、57問題型、65実装、29 canonical事例、78判断規則等。

限界: READMEの生成集計値。今回SQLite全行を再集計していない。

## R02 — Learning Atlas: 2026-09-30の現行方針

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/docs/product-direction/learning-atlas.md

確認日: 2026-10-10 / 種類: repository

支える内容: 引ける辞書・進める道筋・当てはめる、骨格→教材→投影。旧problem-first方針の後継。

限界: 本文中の件数は文書執筆時点の値であり、現在の監査値として流用しない。

## R03 — 生成済みCoverage

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/site/public/data/coverage.md

確認日: 2026-10-10 / 種類: repository

支える内容: 定義済みexpected learning artifactsがavailable11、baselineなし。

限界: 11/11は定義済み期待教材の指標であり、全最適化分野の網羅率ではない。今回検証を再実行していない。

## R04 — Learning paths seed

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/data/seeds/learning_paths.json

確認日: 2026-10-10 / 種類: repository

支える内容: formulation-basics、fit-to-dataの2道筋、合計17ステップ参照。

限界: 道筋の登録数。学習者による完走・理解を示さない。

## R05 — ADR0018: sceneから動き・3D・動画へ

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/docs/adr/0018-motion-3d-and-video.md

確認日: 2026-10-10 / 種類: repository

支える内容: model・beats・viewの分離、同じ場面から複数投影、数値と媒体の鮮度。

限界: proposedのADR。全項目実装済みとは扱わない。TTS固有モデルやCI公開経路の記述は再確認が必要。

## R06 — PR297 記事品質台帳

https://github.com/mryk814/optimization-compass/pull/297

確認日: 2026-10-10 / 種類: repository_pull_request

支える内容: レビューを本文ハッシュと紐付け、変更後stale、品質基準を明示。

限界: 取得時open・未マージ。PR記載のテスト結果は作者申告。head 2810d5aa04dcfabfbc186bee44036dcf4ba969e2。

## R07 — PR298 主単体法の操作図

https://github.com/mryk814/optimization-compass/pull/298

確認日: 2026-10-10 / 種類: repository_pull_request

支える内容: パン屋LPで読者がピボットを選択。PR297への依存。

限界: 取得時open・未マージ。作者申告の動作試験と今回の独立検算を混同しない。head e9ee59c31af7991f170a02d0d24e34ceb3772aca。

## R08 — AGENTS.md

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/AGENTS.md

確認日: 2026-10-10 / 種類: repository

支える内容: 編集可能な入力、生成物直接編集禁止、学習者価値、段階検証。

限界: 実装時は作業先HEADの版を最優先する。本パッケージは置換しない。

## R09 — Architecture

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/docs/architecture.md

確認日: 2026-10-10 / 種類: repository

支える内容: released SQLite、決定論的推薦、静的Atlas、LLM境界。

限界: 設計記述。個別実装の正しさを全検証していない。

## R10 — PR-only CI

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/.github/workflows/ci.yml

確認日: 2026-10-10 / 種類: repository

支える内容: PR単位の検証・ビルド・生成差分・ローカルPages成果物検証。

限界: 自動Pages公開はこのworkflowに含まれない。古いADR記述より現在のworkflowを優先。

## R11 — Agent/MCP境界 ADR0015

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/docs/adr/0015-read-only-agent-and-mcp-boundary.md

確認日: 2026-10-10 / 種類: repository

支える内容: transport非依存のread-only guidance。MCP transportは後続。

限界: MCPの実装済みを意味しない。AIを推薦の第二正本にしない。

## R12 — 推薦用SiteData（部分確認）

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/site/public/data/recommendation/site-data.json

確認日: 2026-10-10 / 種類: repository

支える内容: method / implementation / alternativeの区別、一部の既存IDと対応。

限界: 全レコード照合は未実施。候補の未収録判定にはローカル監査と人手照合が必要。

## R13 — Site manifest

https://github.com/mryk814/optimization-compass/blob/3099b8821a2317761dab8fb3eacebb20cfe0fbcd/site/public/data/manifest.json

確認日: 2026-10-10 / 種類: repository

支える内容: dataset0.18.20、generated_at 2026-10-07、各projectionの所在・contract版。

限界: 公開URLの実配信内容とmainの一致までは未確認。

## R14 — 今回のmain snapshot

https://github.com/mryk814/optimization-compass/commit/3099b8821a2317761dab8fb3eacebb20cfe0fbcd

確認日: 2026-10-10 / 種類: repository

支える内容: 2026-10-10T00:41:15ZのPR299 mergeを基準に調査。

限界: 実装開始時にHEAD・open PRを再確認。

## E01 — NEOS Optimization Problem Types

https://neos-guide.org/guide/types/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 問題分類には連続/離散、凸性、制約、不確実性など独立した軸がある。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E02 — NEOS Algorithms

https://neos-guide.org/guide/algorithms/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 解法体系・既存手法名を照合する分類の外部基準。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E03 — SciPy optimize

https://docs.scipy.org/doc/scipy/reference/optimize.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 最小化・最小二乗・求根の実務入口。手法とAPIを区別する参照。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E04 — Proximal Algorithms — Parikh & Boyd

https://web.stanford.edu/~boyd/papers/prox_algs.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: proximal operator、分割法、構造を利用する解法の基礎。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E05 — Jaggi 2013: Revisiting Frank-Wolfe

https://proceedings.mlr.press/v28/jaggi13.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 射影ではなく線形最適化oracleを使う凸最適化の教材。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E06 — Optax optimizers

https://optax.readthedocs.io/en/latest/api/optimizers.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 勾配系optimizerの候補を検査する公式API一覧。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E07 — GCG

https://gcg.or.rwth-aachen.de/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: Dantzig–Wolfe、branch-price-and-cut、Benders等の分解構造。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E08 — SCIP Benders cuts

https://www.scipopt.org/doc/html/BENDERSCUT.php

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: Benders cutの実装境界と拡張性。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E09 — SDDP theory introduction

https://sddp.dev/stable/explanation/theory_intro/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 多段階確率計画と価値関数の下界近似。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E10 — Pyomo documentation

https://pyomo.readthedocs.io/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 数理モデル層とsolverを区別する実務接続。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E11 — Python Optimal Transport

https://pythonot.github.io/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 最適輸送・正則化・関連する計算機能。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E12 — BoTorch tutorials

https://botorch.org/docs/tutorials

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: BOの制約、多目的、バッチ、多忠実度等の調査入口。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E13 — CVXPY examples

https://www.cvxpy.org/examples/index.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 凸定式化の分野横断例と実装入口。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E14 — OR-Tools min-cost flow

https://developers.google.com/optimization/flow/mincostflow

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 容量・供給・需要を持つ最小費用流の具体例。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E15 — OR-Tools assignment as min-cost flow

https://developers.google.com/optimization/flow/assignment_min_cost_flow

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 割当とネットワーク流の構造的な接続。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E16 — JuMP power systems

https://jump.dev/JuMP.jl/stable/tutorials/applications/power_systems/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 経済負荷配分からunit commitmentへの定式化の変化。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E17 — JuMP optimal power flow

https://jump.dev/JuMP.jl/stable/tutorials/applications/optimal_power_flow/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 電力潮流と非凸制約・凸緩和を扱う教材。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E18 — NEOS case studies

https://neos-guide.org/case-studies/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 医学、生物、電力、経済、物流等へ分野偏りを点検する外部参照。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E19 — Distill: Why Momentum Really Works

https://distill.pub/2017/momentum/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 連動した図と操作で最適化の振る舞いを説明する表現例。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E20 — Distill: Exploring Bayesian Optimization

https://distill.pub/2020/bayesian-optimization/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: BOの不確実性と獲得関数を見せる表現例。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E21 — Idyll — UIST 2018 research

https://idl.uw.edu/papers/idyll

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: データ駆動の説明と操作を組み合わせるオーサリング研究。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E22 — Deslauriers et al. 2019

https://www.pnas.org/doi/10.1073/pnas.1821936116

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 学習した感覚と測定された学習成果を分けて評価する動機。

限界: 大学物理授業の研究。動画・3D・本サイトへの効果を直接証明するものではない。

## E23 — Remotion useCurrentFrame

https://www.remotion.dev/docs/use-current-frame

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: フレーム番号によるReact動画表現。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E24 — Remotion terms（版の注意）

https://www.remotion.dev/docs/terms

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 利用条件・ソフトウェアライセンスの確認入口。

限界: 取得時にv5 Upcoming / v4置換予定という文言が併存。利用する実際のpackage版のLICENSE・発効日・組織条件を再確認。料金や利用許諾を本調査で確定していない。

## E25 — Remotion v4 terms

https://www.remotion.pro/terms-4-0

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: v5公開予定文書と旧/現行文書の版を区別して確認する必要性。

限界: 取得時にv5 Upcoming / v4置換予定という文言が併存。利用する実際のpackage版のLICENSE・発効日・組織条件を再確認。料金や利用許諾を本調査で確定していない。

## E26 — HyperFrames introduction

https://hyperframes.heygen.com/introduction

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: HTML/CSS/JSからフレーム単位の動画を作るagent-orientedな候補。

限界: 公式資料で機能と構成を確認。統合・ライセンス適合・性能は未検証。作者の比較宣伝を独立ベンチマークと扱わない。

## E27 — HyperFrames official repository

https://github.com/heygen-com/hyperframes

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: CLI・engine・studio等の構成と公開ライセンスの確認入口。

限界: 公式資料で機能と構成を確認。統合・ライセンス適合・性能は未検証。作者の比較宣伝を独立ベンチマークと扱わない。

## E28 — Manim Community

https://www.manim.community/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: Pythonで数学アニメーションを作るbuild-time候補。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E29 — Mafs

https://mafs.dev/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: Reactによる操作可能な2D数学図の候補。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E30 — Mafs animation

https://mafs.dev/guides/experimental/animation

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: アニメーション機能がexperimentalであること。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E31 — Motion Canvas documentation

https://motioncanvas.io/docs/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: TypeScriptで解説アニメーションを作る候補。

限界: 公式docsは参照可能だが保守状況について外部記述に不一致がある。最終release・issue応答・npm公開を採用前に確認。

## E32 — Cytoscape.js

https://js.cytoscape.org/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 関係グラフの探索・操作・レイアウト候補。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E33 — Pyodide Web Worker

https://pyodide.org/en/stable/usage/webworker.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: ブラウザでPython計算をUIスレッドから分離する入口。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E34 — Pyodide interrupts

https://pyodide.org/en/stable/usage/keyboard-interrupts.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 割込みとSharedArrayBuffer等の配信条件を確認する必要性。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E35 — JupyterLite

https://jupyterlite.readthedocs.io/en/stable/

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 静的配信でブラウザ内notebookを提供する候補。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E36 — GitHub Pages official

https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 静的HTML/CSS/JS配信という境界。静的配信とブラウザ内計算は両立する。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E37 — W3C animation from interactions

https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 操作由来の動きを無効化できる設計。該当SCはAAA。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。

## E38 — SafeOpt — Sui et al. 2015

https://proceedings.mlr.press/v37/sui15.html

確認日: 2026-10-10 / 種類: primary_research

支える内容: 安全性を課した探索と、仮定下で到達できる最適性を区別。

限界: 実験点の現実安全性を無条件に保証しない。原論文の仮定・初期安全集合・到達可能性をレビューする。

## E39 — CVXPY TV in-painting

https://www.cvxpy.org/version/1.8/examples/applications/tv_inpainting.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 画像欠損補間を全変動最小化として示す公式教材。

限界: 固定版1.8の例。実装時は採用版と検算し、現行ソルバー比較の根拠には流用しない。

## E40 — CVXPY quadratic program

https://www.cvxpy.org/examples/basic/quadratic_program.html

確認日: 2026-10-10 / 種類: primary_documentation

支える内容: 二次計画の標準形と基本例。

限界: 機能の存在・説明を確認した。Optimization Compassでの統合動作・教育効果を実測したものではない。
