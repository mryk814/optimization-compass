# 50稿の再現資料

このフォルダは、50稿のレビュー時に使った資料を保存するためのものです。
公開される記事の正本は `content/`、図の正本は `site/public/media/` にあります。
`reproduction-map.json` は記事と資料の対応、`reproduction-manifest.json` は
`reproduce/` 内137 filesのSHA-256を記録しています。WindowsのCRLF改行はLFへ戻して照合します。

`reproduce/` のPython filesはレビュー時点の計算記録です。本文からcodeを取り込む
`exec`、当時の作業フォルダ、隣接するMarkdownなどを前提にするものもあります。
通常のアプリ実行・build・testからは読み込まれず、repository内の汎用entrypointとしては扱いません。
元の計算記録とhashを保つため、この保存領域だけをRuffのlint・format対象から除外しています。
`src/`、`scripts/`、`tests/` などの検査範囲は従来どおりです。

記事の数値は既存の独立レビューと再現結果を引き継いでいます。今回の統合で全例を
再実行したという意味ではありません。OR-Toolsを使うCP-SAT例とOptunaを使うTPE例の
未実行注記は本文に残しています。TPEの固定帯域密度の教材計算は、このOptuna例とは別です。
