# 50稿の統合検証

レビュー済み本文 `6ad2ceb` と追加素材 `06503cb` を、現行main `96233f1` の
本文・生成処理・停止表示へ統合しました。dataset versionは0.18.19です。

## 保持と修正

- constrained-nlp、Gauss–Newton、劣勾配法の新しい数式表示を保持。
- 現行mainのSVG生成処理とsineFitの停止表示を保持。
- summary 15件を、レビュー済みの冒頭段落と一致させた。
- 図caption 28件を、隣接するレビュー済み説明から補った。
- 19記事を既存の節順へ配置。節の移動では見出しを除く全行の内容と出現回数を照合し、数値・code・出典を保持した。
- Trust-region Newton-CGの冒頭には、既存の説明へ「見るもの・動かすもの・前進の判断」のラベルを補った。変数領域の2文は意味と数値を保って短く分けた。
- 既存SVG 9枚を本文と目視照合。8枚を保持し、逆向きの曲線だった `convexity.svg` だけを修正した。
- 凸性図は本文と同じ `f(x)=0.35x²+0.2`。101点の有理数計算でBezier曲線との完全一致を確認。
  端点1.6、中間点0.2、弦との差1.4を表示する。
- 既存の多様体PNGと再現資料137 filesのcanonical LF hashを保持。

## ローカルで通過した検査

| 検査 | 結果 |
|---|---|
| 最終sourceからの公式 `export-site-data` | pass、手動JSON編集なし |
| `validate content-ready` | pass、144教材・36Gallery・29比較・license・公開契約5 tests |
| 今回の50稿すべてのpublish-readyと節構成 | 50/50 pass |
| `tests/test_explorables.py` | 18 pass |
| 先行CIで失敗した記事関連3 tests | 修正後の限定sliceで3 pass |
| 記事表示componentのfocused Vitest | 7 pass |
| 近接勾配・sineFit・registry/mountの先行Vitest | 31 pass、対象実装不変のため再利用 |
| 最終 `npm run build` | pass、TypeScript型検査を含む |
| `ruff check .` / `ruff format --check .` | pass、保存資料の扱いはREADME参照 |
| 公式記事レポートのdrift | 2/2 pass |
| README release facts / repository size | pass |
| 対話図・最小二乗・近接勾配の記事E2E | 35 pass |

## Windows Chromiumの実画面

50稿を1280pxと375pxで表示し、合計100画面を確認しました。画像57 pathsの読込、
非空のalt/caption、目次操作、コード・表のkeyboard focus、ページ全体の横はみ出しを検査し、
最終結果は失敗0、browser error・HTTP error 0です。
概念記事は定式化のcanonical見出しを使う場合があるため、タイトル文字列の同一性ではなく
レビュー済み冒頭段落と目次を確認しています。凸性図は修正後の2画面を再確認しました。

35 E2Eでは、近接勾配の勾配段階とthreshold段階、正則化で0になる条件、keyboard操作、
記事間の往復、最小二乗の再計算・reset・375px・320px・200%文字拡大・touch・axeを確認。
非線形最小二乗の成立しない更新は、局所最小に着いたと判断しない現行mainの表示を確認しました。

previewは専用worktreeのproduction artifactです。mainへのmergeや公開は行っていません。

## 数値検証の範囲

各記事の既存の独立レビュー・計算結果を引き継ぎ、Python64ブロックの構文を確認しました。
今回全code例を再実行したとは主張しません。OR-ToolsのCP-SAT例とOptunaのTPE例の
未実行注記は保持しています。固定帯域のTPE教材計算はOptuna例とは別です。
+
## 近接勾配の最初の一手の表示

初期表示が12回目になり、中間点と更新点が同じ橙色で、二つの図の縮尺も異なっていた。
最初の一手を読む目的に合わせ、次を追加修正した。

- 初期表示とつまみ変更後は、最初の一手で停止。
- 現在の係数（灰）→ 勾配だけの中間点（青緑）→ 0へ縮めた後（橙）を同じ横目盛りの3行で表示。
- 初期値0 → 0.75 → 0.55を点・数値・矢印で示す。λ=3では中間点0.75を保ち、更新後だけが0になる。
- 入出力の曲線、式への代入、診断値を折りたたむ。
- 計算モデル、12回の予算、歩幅の範囲、安定性と性能の限界を保持。
  途中の操作ごとに目的全体が下がるとは主張していない。

[表示意図の文書](../../product-direction/proximal-gradient-first-step.md)を先に保存し、
限定E2Eは変更前の図で失敗した（現在・中間点・更新後を明示する図がない）。
変更後は近接勾配の限定E2E4件とaxe1件が成功。
既存のexplorable読み込み・描画検査は19件成功。数理moduleの先行検証は、sourceが不変のため再利用した。

公式export・2つの記事レポート、content-readyの公開契約5件、ruff check/format、
TypeScriptを含むproduction buildが通過した。buildは別保存先へ出力し、先行7f84140の配信artifactを保持した。

PC1280pxと375pxで初期値とλ=3を表示し、4画面を確認。横overflow・browser errorは0。
49稿の先行表示確認を再利用し、全50稿を再表示したとは主張していない。
GitHubの最終CIとReady状態はPR本文の最新記録を参照。
