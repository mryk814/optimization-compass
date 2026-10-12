# 2. 現状監査と既存資産の再利用

## 観測した基準

mainは `3099b8821a2317761dab8fb3eacebb20cfe0fbcd`、datasetは0.18.20。README集計では105手法、57問題型、65実装、110出典、29 canonical事例、78判断規則、4,193 evidence link。これは異なる種類の行数であり、相互に割り算しない。[R01,R13,R14]

`learning_paths.json`には2本、合計17ステップ参照がある。生成Coverageは定義済み期待教材11件をavailableとしており、過去版baselineはない。全記事・全方法・全分野の達成率を示していない。[R03,R04]

## 既にあるもの → 追加の接続先

|目的|既存の中心|今回足すもの|
|---|---|---|
|問題の辞書|formulation_atlas seed / formulation_atlas.py|収録範囲との照合、未収録・別名・profileの区別|
|学習順|learning_paths seed|personaの意図・つまずき・出口を持つ道筋|
|診断|engine.py / predicates.py / decision_rules|判断規則候補のレビューとunknown回帰テスト|
|記事品質|content_skeletons / content quality / PR297|既存品質台帳との統合、レビュー鮮度の集計|
|操作と動画|explorable/math、resources/explorables、ADR0018|一手・oracle・他分野転移、媒体比較adapter|
|根拠付き関係|entity-links / formulation relations|条件付きの型を保持した意味別レンズ|
|成長表示|coverage.py / CoveragePage|分母版と品質軸の追加。第二の正本は作らない|
|AIへの引継ぎ|agent_service / readonly ADR|構造化briefと状態の持ち帰り|

## 重複実装を避ける対象

PR297は記事の品質レビューを本文ハッシュと結び、変更後staleを扱う。新しい“記事品質DB”を別に作らない。PR298はパン屋LPの一手を読者が選ぶ操作図で、297に依存する。新しい同等の単体法図をもう一つ作るのでなく、数式対応・証明・他分野版・動画化へ拡張する。[R06,R07]

取得時どちらもopen。PR本文にある試験成功は作者の申告で、今回の独立実行ではない。実装開始時にmerge状態・ベースSHA・差分を確認する。

## 文書の鮮度

7月のproblem-first文書より9月30日のlearning-atlasが現行方向。ADR0018はproposedであり、動画自動公開や固有TTSモデル名の記述を、そのまま現行の実装事実にしない。現在のCIはPR検証と成果物検証であり、自動Pages公開ではない。[R02,R05,R10]

## 未実施の監査

全SQLiteテーブルの値・全canonical IDと候補リストの対応、publicサイトのルート到達/画面操作、全テスト/ビルド、独立したライブラリ統合試験は未実施。clone失敗を回避して一部connector読み取りで調査した。`tools/audit_repository.py`でローカルの完全データを読み、意味照合を完了することが最初の課題である。

これらが未確認でも、既存方針と構成に接続する準備・候補一覧・検証設計は利用できる。ただし、候補を「現在欠けている」と一括断定してはならない。
