# Explorable（動かして学ぶ図）

Explorable は、記事の途中に置く対話的な教材図です。読者がスライダーや点を動かし、動きと数式が同時に変わる様子から、文章だけでは伝わりにくい「なぜそうなるか」をつかむために使います。

静的な図（`docs/content-visual-language.md`）、正準の実行記録を再生する Trace / Theater、Comparison とは役割が違います。

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
- `id` は `src/optimization_compass/resources/explorables.json` に登録された kebab-case です。1ページに同じ `id` は1回だけ、トップレベルにだけ置けます。
- 違反はコンテンツのビルドで失敗します（`content_markdown.py`、`tests/test_explorables.py`）。

## 構成

```text
content/**/*.md                       ::: explorable <id>
  └ content_markdown.py               検証し、<figure data-explorable-id> の mount point に変換
      └ resources/explorables.json    id・問い・固定条件・読み取れないこと（authority）
site/src/features/explorable/
  ├ ExplorableMounts.tsx              mount point を見つけ、図を portal で描画
  ├ registry.tsx                      id → React.lazy(図)。図ごとに別chunk
  ├ meta.ts                           JSON の写し。explorable.test.tsx が一致を検査
  ├ ExplorableFrame.tsx               問い / 操作 / 図 / 再生 / 読み取り / 前提、の共通の枠
  ├ controls.tsx                      Slider, Choice, PlayerBar
  ├ useTimeline.ts                    rAF の時計、再生・シーク、reduced motion、変更時の再生
  ├ svg.ts                            座標変換、ドラッグ、幅に追従する viewport
  ├ mathml.tsx                        数値が動く式（live math）のための MathML builder
  ├ math/*.ts                         描画に依存しない数値計算（単体テスト対象）
  └ <Figure>.tsx                      図の本体
```

## 図を追加する手順

1. `resources/explorables.json` に `id`、`question`、`fixed_conditions`、`not_implied` を追加します。`question` と `not_implied` は文末を「。」にします。
2. `meta.ts` に同じ文言を写します（不一致は `explorable.test.tsx` が検出します）。
3. `math/` に、描画に依存しない計算を書き、解析解や既知の値と照らして単体テストします。
4. 図を書き、`registry.tsx` に `lazy` で登録します。
5. 記事に `::: explorable <id>` を置き、`uv run optimization-compass export-site-data --output site/public/data` で公開データを再生成します。
6. 検証します（後述）。

## 設計規則

- **1つの問い**: 図は `question` に答えるためだけに作ります。装飾や別の話題は足しません。
- **式が動く**: 更新式には、いまの数値を代入した形を出します（`LiveMath`）。式の意味を先に日本語で説明する原則は記事側で守ります。
- **色**: 橙は候補・更新、青緑は実行可能・観測、赤は違反だけ、紺は構造線です（`atlas-geometric-v1`）。色だけに意味を預けず、文字も併記します。
- **文字は縮めない**: `useStageViewport` が、図に与えられた幅で 1 SVG 単位 = 1 CSS px になるように座標を再計算します。固定の `viewBox` を縮小すると、スマホで軸ラベルが読めなくなります。
- **動き**: 初回表示は終了状態です。条件を変えたときだけ最初から再生します。再生・一時停止・1つ進む/戻る・シーク・速さを必ず付けます。
- **reduced motion**: `prefers-reduced-motion` では自動再生せず、常に終了状態を表示し、コマ送りで確認できます。
- **操作**: ドラッグできる点は、矢印キーでも動かせます（1次元は `role="slider"`）。図の結果は、動きの各フレームではなく、設定ごとに1回だけ `aria-live` で読み上げます。
- **前提の開示**: 各図の下に「固定している条件」と「読み取れないこと」を開閉できる形で常に置きます。
- **計算は描画から分ける**: `math/` は React に依存しません。解析解（例: 二次関数での誤差の倍率 `1-ηλ`）と一致することをテストで固定します。
- **停止理由**: 非線形最小二乗の図では、表示精度で二乗和の変化が止まった結果、特異な近似や更新不成立による停止、反復予算の打ち切りを区別します。更新できなかった点や予算を使い切った点を、局所最小の谷に着いたとは表示しません。

## 数値の出どころ（文章・静止図・操作図・動画で同じ値を使う）

一つの例の数値は、一つの計算からだけ出します。記事の表、静止SVG、操作図、録画が別々に計算すると、値がずれても気づけません。

- **操作図の数値は `math/` の関数が出します。** 録画（`#/record/<id>`）は同じ部品を scene time `t` で動かすだけで、別に計算しません。
- **記事の例をPythonで作った場合**は、TypeScriptで乱数や行列の組み立てを作り直しません。Python側の生成スクリプトが例の入力（真値、観測、行列など）をJSONのfixtureに書き出し、`math/` はそれを読み込みます。生成スクリプトの `--check` で、fixtureが古くないことを確かめます。例: `inverse-problem-alpha` は `scripts/generate_lesson_figures.py` が書く `math/inverseProblem.fixture.json` を使います。
- **記事・captionが言う数値は、テストで固定します。** 操作図の `math/` のテストと、静止図の生成スクリプトのテストが、同じ記事の数値を確かめます。

### 共有の契約：今あるものと、まだ提案のもの

| 項目 | 状態 | 場所 |
|---|---|---|
| 図ごとの問い・固定条件・読み取れないこと | 実装済み | `explorables.json`（`question`、`fixed_conditions`、`not_implied`） |
| 解説の区切り（beats）と一つの時計 | 実装済み | `explorables.py` の Beat、`scene.ts`、`useSceneTour.ts` |
| 録画の入力ハッシュ | 実装済み（CIでは検査しない。録画は git 管理外） | `site/scripts/record-scene.mjs` の `manifest.json` |
| Python の例と操作図で同じ入力を使う fixture と鮮度の検査 | 実装済み（1図） | `generate_lesson_figures.py --check` |
| 読者に先に予想させる区切り（予想してから結果を見せる） | 提案のみ | 単体法の証明・BO の場面で必要になったときに beats へ足す |
| 学習者が見える情報と最適化側が見える情報の区別の表示 | 提案のみ | 同上 |
| 双対価格・余裕・ギャップなど LP の観測量の共有名 | 提案のみ | 単体法の証明（OC-EVOL-011）で `simplex.ts` に足す |
| Python と TypeScript で同じ手法を二度実装している箇所（勾配降下法、Adam） | 既知のずれの危険。同じ例を使う比較のテストはまだない | `math/descent.ts` と `traces/generators.py`、`math/adam.ts` と同 |

提案のものは、使う図ができたときにその図のPRで足します。使い道のない項目を先に契約へ足しません。

## 解説付き再生（beats）と録画

図には、自動で進む解説（guided scene）を付けられます。方針は [ADR 0018](adr/0018-motion-3d-and-video.md) です。

- `explorables.json` の entry に `beats` を書きます。各 beat は `settings`（図の設定のうち変えるもの）、`duration_s`（2〜15秒）、`caption_ja`（画面に出す要点）、`narration_ja`（話す文。数式・記号は「イータ」のように読みを書き下す）です。合計は60秒以内です。
- `meta.ts` に同じ内容を写します（不一致は `explorable.test.tsx` が検出します）。
- caption が計算について主張することは、テストで固定します（例: 「100回でも収束しない」なら `runDescent` の結果が `unfinished`）。
- 図の側では `useSceneTour(id, beats, onExit)` を使い、`tour.beat` の設定を表示し、`tour.local`（beat 内の秒）から反復の位置を決めます。反復は等速で進めます。終了すると最後の beat の設定が読者の操作に引き継がれます。
- 解説中は操作部品を隠し、caption・進捗・前へ／次へ・終了を出します。reduced motion では各 beat の終了状態を出し、手で進めます。

録画は、scene time `t` を外から与えてフレームごとに撮ります（実時間の再生を録画しません）。

```bash
npm --prefix site run record:scene -- gradient-descent-valley              # 動画一式
npm --prefix site run record:scene -- gradient-descent-valley --still 12.5 # 1フレームだけ（レイアウト確認）
```

出力は `site/.scene-media/<id>/`（git 管理外）に、`scene.mp4`、`scene.webm`、`poster.png`、`captions.vtt`、`transcript.txt`、`manifest.json` です。`manifest.json` の `input_sha256` は registry と `site/src/features/explorable/` の内容から計算し、録画が古いかどうかの判定に使います。ffmpeg が必要です。録画用の画面は `#/record/<id>`（1280×720、サイトの外枠なし）です。

## 検証

```bash
uv run optimization-compass validate content
npm --prefix site test -- src/features/explorable
npm --prefix site run build
```

図の見た目と操作は `site/e2e/explorable.spec.ts` が検査します（axe の critical / serious、375px での横はみ出しと文字サイズ、主要な操作）。

```bash
CI=1 PLAYWRIGHT_PORT=4199 npm --prefix site exec playwright test e2e/explorable.spec.ts -- --project=chromium-desktop
```

## 現在の図

| id | 掲載先 | 見せるもの |
|---|---|---|
| `gradient-descent-valley` | `method.gradient-descent` | learning rate と谷の細長さで、方向ごとの誤差の倍率がどう決まるか。安定限界 `2/L` |
| `lp-vertex-walk` | `concept.linear-program` | 目的の向きを回すと、最適解が頂点で切り替わること。内部の点は最良の頂点を超えない |
| `simplex-pivot` | `primal-simplex` | 読者が増やす変数を選び、増やす量 θ を動かして比の最小値を見つける。被約費用を「売値 − 使う資源の値段」で計算し、2回のピボットで最適な頂点に着く |
| `convexity-chord` | `concept.convexity` | 定義の不等式を、2点と混合比で数値として確かめる。局所解と全体の最小の違い |
| `least-squares-bowl` | `concept.linear-least-squares` | 残差の二乗を正方形の面積で見せ、データの平面とパラメータの平面（お椀）をつなぐ。外れ値1点の引っ張り |
| `adam-step-ratio` | `adam` | 座標ごとの比（勾配の平均÷勾配の大きさ）が一歩を決めること。同じηの勾配降下法、ノイズで縮む一歩 |
| `bayes-opt-acquisition` | `bayesian-optimization` | GPの予測平均と不確実性、獲得関数で次の点が決まる様子。β・長さの尺度・EIによる探索と活用の違い |
| `coordinate-descent-walk` | `coordinate-descent` | 一座標の断面の最小と全体の収束の違い。谷の向き・曲率比・座標の結びつきによる軌跡、掃引ごとの停止と予算打ち切り |
| `inverse-problem-alpha` | `concept.inverse-problem` | 罰則の重みαを対数目盛りで動かし、復元した分布・真の分布との誤差・観測とのずれ（雑音の大きさδとの比較）を同じ計算で見る |

## 次の候補

- **曲面の3D表示**: 二変数の目的関数を回転できる曲面として見せ、軌跡を曲面上に重ねる。高さの圧縮などの表現上の加工を必ず開示する。
- **既存の Theater の外枠**: 現在の Theater / Trace ページは、メタデータと操作が図より先に並び、図が画面の下に隠れる。`ExplorableFrame` と同じ「問い → 図 → 再生 → 読み取り」の順へ組み替える。Trace の契約は変えずに、ページの外枠だけを差し替えられる。
- **動画の配信とナレーション**: 録画（上記）を Pages のデプロイで生成して配信する。ナレーションは手元で TTS 生成した音声を置く（ADR 0018 §5a）。
- **手法ごとの図**: 第一候補の一覧は [`docs/teaching-article-playbook.md`](teaching-article-playbook.md) §5.6 にあります。各 method 記事について、第1候補（BFGS の曲率、Newton 法の接線、Nelder–Mead の単体、Adam の座標ごとの step など）を、この基準で選別する。
