# 50稿の統合検証

レビュー済み本文 `6ad2ceb` と追加素材 `06503cb` を、現行main `96233f1` の
本文・生成処理・停止表示へ統合しました。dataset versionは0.18.19です。

## 保持と修正

- constrained-nlp、Gauss–Newton、劣勾配法の新しい数式表示を保持。
- 現行mainのSVG生成処理とsineFitの停止表示を保持。
- summary 15件を、レビュー済みの冒頭段落と一致させた。
- 図caption 28件を、隣接するレビュー済み説明から補った。
- 19記事を既存の節順へ配置。見出しを除く全行の内容と出現回数が不変であることを照合した。
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
