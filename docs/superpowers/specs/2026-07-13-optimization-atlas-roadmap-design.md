# Optimization Atlas ロードマップ統合設計

## 目的

GitHub Issue #1〜#11を、Issue #12のOptimization Atlas構想に沿って一つの製品へ統合する。既存のFastAPI診断、CLI、決定的推薦エンジン、read-only SQLiteは維持し、公開入口としてGitHub Pages上の静的アプリを追加する。

最初の公開版では、地図、診断、教材、アルゴリズム再生、比較、実問題Galleryを相互に移動でき、すべての表示をcanonical ID、source ID、dataset versionへ追跡できる状態を完成条件とする。

## 設計判断

### 1. 実行境界

- `src/optimization_compass/` はcanonicalなPython契約、SQLite読取、推薦、静的データ生成、教育用Trace生成を担当する。
- `site/` はVite + React + TypeScriptの静的クライアントとし、実行時にAPIやSQLiteを必要としない。
- `src/optimization_compass/web.py` の既存FastAPI UIは削除せず、ローカル診断として維持する。
- Python exporterが`site/public/data/`へversion付きJSONを生成し、TypeScript側は生成済みartifactだけを読む。
- GitHub Pagesのサブパスと直リンク404を避けるため、公開ルーティングはHashRouterを使う。画面状態はhash内queryへcanonicalに保存する。

### 2. 契約

次の契約を独立してversion管理する。dataset versionとは別に扱い、互換性のない組合せは読込時に拒否する。

- `ViewSpec 1.0.0`: title/description、意味構造、`root_node_ids`、主分岐、表示順、初期折りたたみ、emphasis、補助edgeと説明、関連method/problem/feature/alternative/source、`answer_bindings`を表す。node IDの文字列解析で診断状態へ変換しない。座標、長文、Trace frameは含めない。
- `SiteData 1.0.0`: 質問、規則、方法、実装、互換性情報をブラウザ推薦器へ渡す。
- `AtlasState 1`: canonical answers、selected node、dataset/view versionをURLへ保存する。未回答、`unknown`、`not_applicable`を別状態とする。
- `AlgorithmTrace 1.0.0`: method/objective/parameters/seed/stop条件と、順序付きframeを表す。推薦の`RuleTrace`とは名前を分ける。各frameは前frameとの差分ではなく単独で完全描画できるsnapshotとし、points、vectors、metrics、event固有payloadを持てる。
- `Content frontmatter 1`: 教材とcaseのID、関連entity/source、status、review日を表す。本文はMarkdown/MDXだけに置く。

### 3. 情報アーキテクチャ

共通レイアウトの主要入口は次の6つとする。

1. `/` — Atlasの入口と現在利用できる探索経路
2. `/map` — 問題構造を3階層以上で段階展開するCompass Map
3. `/diagnose` — 静的推薦器による診断
4. `/methods/:methodId` — 手法・概念教材と可視化への導線
5. `/compare/:comparisonId` — 同一budgetでの比較
6. `/gallery` と `/gallery/:caseId` — 実問題からの逆引き

地図は巨大なnetwork graphにせず、5〜7個の主分岐を持つsemantic treeと詳細panelで構成する。選択ノード、祖先、子、関連entityを明示し、兄弟・未選択枝を弱める。キーボード操作、375px幅、空データ、参照切れ、未知entity typeを最初から契約に含める。

### 4. データ責務

- canonical SQLite: ID、関係、enum、比較preset、可視化対応範囲、学習edge、objective/scenario metadata
- Markdown/MDX frontmatter: 教材/case固有の構造化索引、表示順、review状態
- Markdown/MDX本文: 直感、数式、コード、注意、引用
- Python source: 実行可能なobjectiveとalgorithm更新則。教育用generatorは既存libraryのimplementation IDを名乗らず、独立したgenerator IDを持つ
- 生成済みJSON: ViewSpec、SiteData、Trace、content index。再生成可能なartifactでありcanonicalではない

`unknown`は「未調査または不明」、`not_applicable`は「概念が適用されない」、`unsupported`は「現在の表示・実装が扱わない」と定義する。空文字による代用は禁止する。

決定的exportと`generated_at`を両立するため、生成時刻は実行時刻ではなく、最新`version_history.release_date`のUTC 00:00を使う。同じDB、同じcontract versionからはbyte単位で同じJSONを生成する。

### 5. 実装スライス

#### Slice A — Public Atlas foundation (#1, #2, #3)

静的shell、Pages CI、ViewSpec exporter、problem-structure mapをまとめる。完了時点で公開可能な地図があり、Pythonテストとsite buildが同じCIで通る。

#### Slice B — Diagnosis integration (#4, #5)

Pythonのcanonical推薦データを静的JSON化し、TypeScript evaluatorとのparityを共通fixtureで検証する。地図と診断は一つのAtlasStateを共有し、URL、reload、back/forwardで再現する。

#### Slice C — Trace and learning interactions (#6, #7, #8)

共通AlgorithmTrace contract/playerを先に完成させ、その上へNelder–Mead固有rendererとGD/Momentum/Adam比較を載せる。比較は複数の独立Traceを同じobjective、初期値、停止条件、evaluation budgetで束ね、累積oracle evaluationを同期軸とする。発散時はNaN/InfinityをJSONへ出さず、最後の有限frameと`diverged` stop frameを残す。

#### Slice D — Content, Gallery, metadata (#9, #10, #11)

4本の初期教材、4件のcase、検索と関連導線を追加する。先にauthorityとrelease再生成pipelineを確立し、可視化・比較で実際に必要になったfieldをcanonical SQLiteへ確定してdataset versionを更新する。比較memberは区切り文字列へ詰めず、正規化したbridge tableで管理する。

## 検証

- Python: pytest、ruff、mypy、`optimization-compass verify-data`
- TypeScript: unit tests、Python/TS parity fixtures、production build
- Contracts: JSON schema/Pydantic validation、参照整合性、決定性、version mismatch
- UI: keyboard navigation、375px、reload/deep link/back-forward、未知event/破損参照
- Algorithms:同一入力の同一Trace、evaluation count、Nelder–Mead event coverage、比較budget公平性、発散上限
- Content/data: DBにないIDをCIで拒否し、配布形式と生成indexの一致を確認する

## リリース単位

各Sliceは個別に動作・テスト可能なコミット群にする。Issue #12は個別Issueのチェックリストを追跡するEPICであり、実装固有の重複コードは持たない。PR本文では対応Issueを列挙し、公開URL、dataset version、Python/TypeScript検証結果を記録する。

## 非スコープ

- 任意Pythonコードを実行するbrowser sandbox
- 全手法・全業界caseの網羅
- 単一の総合scoreや恒久的ranking
- SQLiteのブラウザ内更新
- 旧経路と新経路を切り替える互換UI
