# Explorable（動かして学ぶ図）

Explorable は、記事の途中に置く対話的な教材図です。読者がスライダーや点を動かし、動きと数式が同時に変わる様子から、文章だけでは伝わりにくい「なぜそうなるか」をつかむために使います。

静的な図、正準の実行記録を再生する Trace / Theater、Comparison とは役割が違います。静的な図と色の決まり（`atlas-geometric-v1`）、記事での使い方は [`docs/writing-articles.md`](writing-articles.md) にあります。

| 手段 | 読者ができること | 正準データとの関係 |
|---|---|---|
| 静的SVG（`![...]`） | 見る | 固定の generator の出力 |
| Trace / Theater | 記録済みの run を再生する | `traces/**` の正準 Trace |
| Comparison | 固定条件の run を並べる | 比較定義と Trace |
| **Explorable** | **条件を動かして、その場で計算し直す** | **持たない。教材用の小さな厳密モデルで、ブラウザ内で計算する** |

Explorable は正準データを増やしません。手法の性能や順位を主張しない、と各図の `not_implied` に明記します。

## 使うと決める基準

次のすべてを満たすときだけ追加します。

- 記事の理解の核が「条件を変えると挙動が変わる理由」である（learning rate と谷の形、目的の向きと最適頂点、など）。
- 二次関数や2変数LPのように、厳密な解析式で数行のコードにでき、実験ではなく計算そのものを見せられる。
- 静的な図では、条件が変わったときの違いを読者が想像で補うことになる。

1記事につき原則1つです。分類、診断値の一覧、適用条件は、表または文章のままにします。

## 記事への書き方

```markdown
::: explorable gradient-descent-valley
橙の点が軌跡です。η と κ を動かすと…（何を見る図か、何が読み取れないかを一文で）
:::
```

- 直前の文で「何を動かして何を見るか」を書き、図の後で確認手順を示します。
- ブロックの本文は**ちょうど1段落**で、可視の caption と、JavaScript が使えない場合の説明を兼ねます。
- `id` は `site/src/features/explorable/figures/<id>/` のフォルダー名（kebab-case）です。1ページに同じ `id` は1回だけ、トップレベルにだけ置けます。
- 違反はコンテンツのビルドで失敗します（`content_markdown.py`、`tests/test_explorables.py`）。

## 構成

1つの図は1つのフォルダーに閉じます。図を足すときも直すときも、共有のファイルは編集しません。並行して図を作るブランチどうしが衝突しないための形です。

```text
content/**/*.md                    ::: explorable <id>
  └ content_markdown.py            検証し、<figure data-explorable-id> の mount point に変換
      └ explorables.py             figures/*/meta.json を検証して読む（id = フォルダー名）
site/src/features/explorable/
  ├ figures/<id>/                  1図1フォルダー
  │   ├ meta.json                  問い・固定条件・読み取れないこと・beats の正本
  │   ├ Figure.tsx                 図の本体（default export）
  │   ├ math.ts                    この図だけの計算（任意）
  │   ├ style.css                  この図だけの CSS（任意。Figure.tsx が import する）
  │   └ *.test.ts(x)               この図のテスト
  ├ registry.tsx                   figures/*/Figure.tsx を glob で見つける。図ごとに別 chunk（figure-<id>-<hash>.js）
  ├ figureMeta.ts                  figures/*/meta.json を読む。図の共有 chunk だけが読み込む
  ├ ExplorableFrame.tsx ほか       共通の枠、操作部品、時計、SVG・MathML の部品
  ├ Lesson.tsx ほか                lesson（段ごとに図を動かす）の画面。段の読み取りは lessonMarkup.ts
  ├ math/                          2つ以上の図、または図の外（theater など）が使う計算
  └ explorable.css                 2つ以上の図や共通の枠が使う規則だけ
```

コードから読み取りにくい決まりは次のとおりです。`figures.test.ts` が検査します。

- **図の CSS はページ全体に効きます。** `style.css` は図の chunk と一緒に読み込まれ、その後は同じページのほかの図にも当たります。そのため `style.css` の規則には、そのフォルダーの外では使われない class（または `[data-explorable-id="<id>"]`）を必ず含めます。ほかの図と共有する規則は `explorable.css` に置きます。フォルダーを写して新しい図を作るときは、class 名も変えます。
- **ほかの図のフォルダーから import しません。** 2つ目の図が使い始めた計算や部品は `math/` か `explorable/` の直下へ移します。録画の古さの判定は図のフォルダーと共有部分しか見ないので、図どうしの import はその判定をすり抜けます。

`explorable.css` の規則は図の CSS より先に読み込まれます。同じ要素に同じ詳細度の規則が当たる場合は、図の側が勝ちます。

## 図を追加する手順

1. `figures/<id>/meta.json` に `id`（フォルダー名と同じ）、`title_ja`、`question`、`fixed_conditions`、`not_implied` を書きます。`question` と `not_implied` は文末を「。」にします。解説付き再生を付けるなら `beats` も書きます（後述）。
2. 描画に依存しない計算を `math.ts` に書き、解析解や既知の値と照らして `math.test.ts` で確かめます。
3. `Figure.tsx` に図を書き、default export します。`ExplorableFrame` に `id` を渡すと、問い・前提・読み取れないことが `meta.json` から出ます。図だけの CSS は `style.css` に書いて import します。
4. 記事に `::: explorable <id>` を置き、`uv run optimization-compass export-site-data --output site/public/data` で公開データを再生成します。
5. 検証します（後述）。図ごとの操作の e2e は `site/e2e/explorables/<id>.spec.ts` に書きます。

## 設計規則

- **1つの問い**: 図は `question` に答えるためだけに作ります。装飾や別の話題は足しません。
- **式が動く**: 更新式には、いまの数値を代入した形を出します（`LiveMath`）。式の意味を先に日本語で説明する原則は記事側で守ります。
- **色**: 橙は候補・更新、青緑は実行可能・観測、赤は違反だけ、紺は構造線です（`atlas-geometric-v1`）。色だけに意味を預けず、文字も併記します。
- **文字は縮めない**: `useStageViewport` が、図に与えられた幅で 1 SVG 単位 = 1 CSS px になるように座標を再計算します。固定の `viewBox` を縮小すると、スマホで軸ラベルが読めなくなります。
- **動き**: 初回表示は終了状態です。条件を変えたときだけ最初から再生します。再生・一時停止・1つ進む/戻る・シーク・速さを必ず付けます。
- **reduced motion**: `prefers-reduced-motion` では自動再生せず、常に終了状態を表示し、コマ送りで確認できます。
- **操作**: ドラッグできる点は、矢印キーでも動かせます（1次元は `role="slider"`）。図の結果は、動きの各フレームではなく、設定ごとに1回だけ `aria-live` で読み上げます。
- **前提の開示**: 各図の下に「固定している条件」と「読み取れないこと」を開閉できる形で常に置きます。
- **計算は描画から分ける**: `math.ts` と `math/` は React に依存しません。解析解（例: 二次関数での誤差の倍率 `1-ηλ`）と一致することをテストで固定します。
- **停止理由**: 非線形最小二乗の図では、表示精度で二乗和の変化が止まった結果、特異な近似や更新不成立による停止、反復予算の打ち切りを区別します。更新できなかった点や予算を使い切った点を、局所最小の谷に着いたとは表示しません。

## 数値の出どころ（文章・静止図・操作図・動画で同じ値を使う）

一つの例の数値は、一つの計算からだけ出します。記事の表、静止SVG、操作図、録画が別々に計算すると、値がずれても気づけません。

- **操作図の数値は図の `math.ts`（共有なら `math/`）が出します。** 録画（`#/record/<id>`）は同じ部品を scene time `t` で動かすだけで、別に計算しません。
- **記事の例をPythonで作った場合**は、TypeScriptで乱数や行列の組み立てを作り直しません。Python側の生成スクリプトが例の入力（真値、観測、行列など）をJSONのfixtureに書き出し、図の計算はそれを読み込みます。生成スクリプトの `--check` で、fixtureが古くないことを確かめます。例: `inverse-problem-alpha` は `scripts/generate_lesson_figures.py` が書く `math/inverseProblem.fixture.json` を使います。
- **記事・captionが言う数値は、テストで固定します。** 操作図の `math.test.ts` と、静止図の生成スクリプトのテストが、同じ記事の数値を確かめます。

### 共有の契約：今あるものと、まだ提案のもの

| 項目 | 状態 | 場所 |
|---|---|---|
| 図ごとの問い・固定条件・読み取れないこと | 実装済み | `figures/<id>/meta.json`（`question`、`fixed_conditions`、`not_implied`） |
| 解説の区切り（beats）と一つの時計 | 実装済み | `explorables.py` の Beat、`scene.ts`、`useSceneTour.ts` |
| 録画の入力ハッシュ | 実装済み（CIでは検査しない。録画は git 管理外） | `site/scripts/record-scene.mjs` の `manifest.json` |
| Python の例と操作図で同じ入力を使う fixture と鮮度の検査 | 実装済み（1図） | `generate_lesson_figures.py --check` |
| 段ごとに図を動かす lesson、図の params、読者に先に予想させる段 | 実装済み | `content_markdown.py`、`Lesson.tsx`、`scene.ts` の `resolveSettings`（下の「Lesson」） |
| 学習者が見える情報と最適化側が見える情報の区別の表示 | 提案のみ | 同上 |
| 双対価格・余裕・ギャップなど LP の観測量の共有名 | 一部実装済み（右辺 b を引数にした解、双対値、基底が有効な範囲、見積もりとの差） | `figures/simplex-shadow-price/math.ts`（OC-EVOL-011）。余裕・ギャップの共有名はまだ提案 |
| Python と TypeScript で同じ手法を二度実装している箇所（勾配降下法、Adam） | 既知のずれの危険。同じ例を使う比較のテストはまだない | `math/descent.ts` と `traces/generators.py`、`figures/adam-step-ratio/math.ts` と同 |

提案のものは、使う図ができたときにその図のPRで足します。使い道のない項目を先に契約へ足しません。

## 解説付き再生（beats）と録画

図には、自動で進む解説（guided scene）を付けられます。方針は [ADR 0018](adr/0018-motion-3d-and-video.md) です。

- `meta.json` に `beats` を書きます。各 beat は `settings`（図の設定のうち変えるもの）、`duration_s`（2〜15秒）、`caption_ja`（画面に出す要点）、`narration_ja`（話す文。数式・記号は「イータ」のように読みを書き下す）です。合計は60秒以内です。
- caption が計算について主張することは、テストで固定します（例: 「100回でも収束しない」なら `runDescent` の結果が `unfinished`）。
- 図の側では `useSceneTour(id, beats, onExit)` を使い、`tour.beat` の設定を表示し、`tour.local`（beat 内の秒）から反復の位置を決めます。反復は等速で進めます。終了すると最後の beat の設定が読者の操作に引き継がれます。
- 解説中は操作部品を隠し、caption・進捗・前へ／次へ・終了を出します。reduced motion では各 beat の終了状態を出し、手で進めます。

録画は、scene time `t` を外から与えてフレームごとに撮ります（実時間の再生を録画しません）。

```bash
npm --prefix site run record:scene -- gradient-descent-valley              # 動画一式
npm --prefix site run record:scene -- gradient-descent-valley --still 12.5 # 1フレームだけ（レイアウト確認）
```

出力は `site/.scene-media/<id>/`（git 管理外）に、`scene.mp4`、`scene.webm`、`poster.png`、`captions.vtt`、`transcript.txt`、`manifest.json` です。`manifest.json` の `input_sha256` は、その図のフォルダーと、`figures/` の外にある `site/src/features/explorable/` の共有部分（テストを除く）から計算し、録画が古いかどうかの判定に使います。ほかの図を直しても、この図の録画は古くなりません。ffmpeg が必要です。録画用の画面は `#/record/<id>`（1280×720、サイトの外枠なし）です。

## Lesson（段ごとに図を動かす）と params

Lesson は、文章の段と図の動きを同じ Markdown ブロックに書く形です。段に入ると、その段の設定で図が再生されます。文章と動きが別のファイルにないので、片方だけ直されてずれることがありません。

```markdown
:::: lesson gradient-descent-valley
::: step seconds=8 eta=0.02 iter=0..100
**この段の要点を一文で。** 続く説明。数式や箇条書きも書けます。
:::
::: step predict answer=2 iter=0
どうなるか、先に選んでください。

- 収束する
- 発散する
:::
::: step seconds=7 eta=0.053 iter=0..30@4
**結果を一文で。** 理由の説明。
:::
::::
```

- 外側はコロン4つの `:::: lesson <図のid>`、内側はコロン3つの `::: step`。Lesson はトップレベルに置き、中身は step だけです。図の id は、lesson と `::: explorable` を合わせて1ページに1回です。
- step のキー: `seconds`（2〜15、省くと6）、`predict`（予想の段）、`answer`（正解の番号。1始まり。`predict` のときだけ必須）。ほかのキーは、図の `meta.json` の `params` にある名前だけです。
- 値: 定数（`eta=0.02`、`method=momentum`）、掃引 `a..b`（段の長さから1.5秒を引いた時間で a から b へ等速で動き、残りは b で止まる）、速度 `a..b@r`（a から毎秒 r ずつ動き、b で止まる）。掃引と速度は number / integer の param だけで、両端は min〜max の中です。
- **省いた param は前の段の終わりの値を引き継ぎます**（掃引は b、速度は段の秒数で届いたところ）。最初の段で省いた param は `default` を使い、`default` もなければビルドが失敗します。引き継ぎは Python が解決し、各段の `data-settings` には全部の param が入ります。
- 予想の段は、選択肢の箇条書きをちょうど1つ（2〜4項目）含みます。読者が選ぶと、選んだものと正解に印が付きます。図での種明かしは次の段に書きます。
- 段は2〜12個、秒数の合計は120秒以内です。段の中に見出しは置けません。
- 段の最初の一文（最初の「。」まで）が、その段の caption です（狭い画面で図の下に出る帯、レビュー用の静止画）。数式に頼らず読める一文にします。

`params` は、beat と step が設定できるものの宣言です。lesson で使う図には必須です。`params` がある図は、既存の `beats[].settings` も同じ宣言で検査します。

```json
"params": {
  "eta":    { "type": "number",  "min": 0.005, "max": 0.3, "default": 0.04 },
  "kappa":  { "type": "integer", "min": 1, "max": 40, "default": 20 },
  "method": { "type": "choice",  "choices": ["gd", "momentum"], "default": "gd" }
}
```

`choice` は、表示する層や場面の切り替え（`layer=plan` など）にも使えます。integer の param は、掃引の途中でも整数で図に届きます。

図の側は `tour.values` を読むだけです。

```tsx
const tour = useSceneTour(id, EXPLORABLE_META[id].beats, onExit);
const shown = tour.active ? fromValues(tour.values, chosen) : chosen;
```

- `tour.values` は、いまの瞬間の設定です（掃引と速度は数値に解決済み。`resolveSettings` in `scene.ts`）。`meta.json` の beats でも lesson でも同じ形なので、図に lesson 専用のコードは要りません。
- Lesson の中では、`useSceneTour` に渡した beats は使われず、段が beats になります。`tour.lesson` が true のあいだ、`ExplorableFrame` は「解説付きで見る」と解説の枠を出さず、操作部品も隠します。読者が最後の段で「自分で動かす」を押すと、`onExit` にそのときの `values` が渡り、操作部品が出ます。
- 画面: 幅 64rem 以上では図を右に固定し、左の段が画面の中央を通るとその段に切り替わります。それより狭い画面では、図の下に現在の段を1つだけ出し、「前へ／次へ」の帯が画面の下に残ります。reduced motion では各段の終了状態を出します。JavaScript がなければ、図の代替文と番号付きの段として読めます。
- 固定した図が画面より高いと、図の中でスクロールすることになります。Lesson で使う図は、段の説明に要る部分が1画面に収まる高さにします。

レビュー用の静止画（`npm --prefix site run shots -- <content-id>`）は、lesson の段ごとに 1280px と 375px で1枚ずつ撮ります。ほかの自動操作には `window.__ocLessons[<図のid>]` を使います。`steps`（各段の `seconds`、`caption`、`predict`）と、`show(index, local?)`（その段を `local` 秒の状態で止めて画面に出し、描画が済んだら解決する Promise。`local` を省くと終了状態）があります。

## 検証

```bash
uv run optimization-compass validate content
npm --prefix site test -- --run src/features/explorable
npm --prefix site run build
```

図の見た目は `site/e2e/explorable.spec.ts` が検査します。図のフォルダーと公開データ（`site/public/data/content.json`）から、図を埋め込んだ記事をすべて見つけ、axe の critical / serious、375px での横はみ出し、図の文字の大きさを確かめます。図を足しても、この spec は編集しません。図ごとの操作は `site/e2e/explorables/<id>.spec.ts` です。

```bash
cd site
CI=1 PLAYWRIGHT_PORT=4199 npx playwright test e2e/explorable.spec.ts e2e/explorables --project=chromium-desktop
```

## 次の候補

- **曲面の3D表示**: 二変数の目的関数を回転できる曲面として見せ、軌跡を曲面上に重ねる。高さの圧縮などの表現上の加工を必ず開示する。
- **既存の Theater の外枠**: 現在の Theater / Trace ページは、メタデータと操作が図より先に並び、図が画面の下に隠れる。`ExplorableFrame` と同じ「問い → 図 → 再生 → 読み取り」の順へ組み替える。Trace の契約は変えずに、ページの外枠だけを差し替えられる。
- **動画の配信とナレーション**: 録画（上記）を Pages のデプロイで生成して配信する。ナレーションは手元で TTS 生成した音声を置く（ADR 0018 §5a）。
- **手法ごとの図**: 各 method 記事について、第1候補（BFGS の曲率、Newton 法の接線、Nelder–Mead の単体、Adam の座標ごとの step など）を、この基準で選別する。記事の書き方は [`docs/writing-articles.md`](writing-articles.md) にあります。
