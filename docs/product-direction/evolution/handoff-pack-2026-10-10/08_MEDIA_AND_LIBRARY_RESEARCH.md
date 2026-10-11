# 8. 媒体・ライブラリの調査結果と選び方

## 第一選択は既存パイプライン

現行のReact/SVG、Three、math core、scene/derived-media構想を再利用する。未知のライブラリを入れなくても、予測→操作、式との連動、条件切替、他分野の表示は実現できる。新しい依存は“できることが増える”か“制作/保守が測って減る”ときに限る。[R05]

## 比較する候補

|候補|役割|判断|
|---|---|---|
|既存recorder|同じ画面からseek可能な録画|比較の基準。まず不足機能を特定|
|Remotion|Reactによるframe単位の映像編集|既存viewとの相性を小PoCで確認|
|HyperFrames|HTML/CSS/JSからagent編集可能な動画|新しい比較候補。数値viewを再利用できるか確認|
|Manim|式変形・幾何・証明のbuild-time動画|同じobservable入力で作れるときのみ|
|Mafs|Reactの2D数学図|SVG記述の負担削減が測れるときのみ|
|Cytoscape.js|関係の操作・レイアウト|意味は既存データ、描画だけadapter|
|Pyodide/JupyterLite|ブラウザ内実験・notebook|専門家向けの別入口。通常ページの必須依存にしない|
|Idyll|説明と操作の文法|現行authoringの置換でなく参考|
|Motion Canvas|TSアニメーション|保守確認待ちのwatchlist|

[E21,E23,E26,E27,E28,E29,E31,E32,E33,E35]

HyperFramesの公式資料はHTMLベースの編集可能性と動画化を示すが、Optimization Compassとの統合は未検証。公式の競合比較をそのまま性能評価には使わない。RemotionはMIT等と同一に扱わず、使用するpackage版のLICENSE、組織利用、商用提供、render方式と発効時期を確認する。調査時のtermsにはv5 Upcomingとv4置換予定の文言が併存し、将来版を現行条件として確定しなかった。[E23,E24,E25,E26,E27]

## 三方式の同一課題PoC

LP証明sceneの同じ入力・同じobservable・同じ30秒の台本を、既存recorder、Remotion、HyperFramesで出す。数値モデルは一つだけ。外部サービス契約・有料API・追加プラグインの自動導入を不要にした範囲で比較する。

測る項目は、初回制作と小修正に要した作業、render時間、ファイル量、テキスト/字幕の読みやすさ、seekの再現性、入力変更を正しくstale検出できるか、失敗時の修復、dependency/ライセンス負担。性能は同じ端末・同じ入力・同じ出力設定で測る。

合格条件は、正しい動画が1本できるだけでなく、係数や説明を変えたときに同じ正本から再生成できること。改善が小さければ既存方式を選ぶ。

## 音声と3D

TTSはvendor非依存adapterにする。beatsの文言、数式の読み、話者、model版、設定、入力hash、音声の実測長を残す。字幕・文章だけでも理解が完結する。特定のTTSモデルの品質・GA状態・権利は、このパックでは確認済みとしない。声の複製はしない。

3Dは3番目の軸自体に意味があるときに使う。2D断面/射影を併設し、カメラresetと固定視点を用意する。動画/3Dが動かない環境でも式・数表・静止図で同じ主張を取得できる。[R05,E37]

## 配布

数値fixtureとsmall manifestはGit、動画等の大きい派生物はrelease/object storage等の配布先を別判断する。現行CIに自動公開がないため、ADR記載の公開経路を勝手に有効化しない。採用する場合は別の公開権限・保管・再生成・rollback計画を作る。[R10]
