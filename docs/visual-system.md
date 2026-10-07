# Conceptual Visual System（測量図）

Optimization Compass のすべての画面で、問題・手法・判断・根拠・実行を同じ記号で描くための規則です。button や spacing の design token ではなく、**最適化の概念をどう描くか**を決めます。教材図の画風（`atlas-geometric-v1`、[`content-visual-language.md`](content-visual-language.md)）と explorable の操作規則（[`explorables.md`](explorables.md)）は、この文書の下位規則として残ります。

この文書の規則は、視覚表現より上位の原則（problem-first、alternative-first、exclusion wins、unknown is data、method ≠ implementation、traceable、deterministic、comparison needs context、no universal ranking）を弱めません。図が「この手法が一番」と読める場合、その図は誤りです。

## 1. 出発点：データがすでに一つの座標系を持っている

診断の12問（Q01–Q12）は、Gallery の各 Case が持つ `question_answers` と同じ軸です。手法側にも、同じ特徴量（`mapped_feature_id`）の上に載る `predicates`（前提・非互換）と `rules`（どの回答で候補化・除外されるか）があります。

したがって、

- 問題の性質は「12本の軸のどこに印があるか」として描けます（**Problem Signature**）。
- 手法の前提は「同じ12本の軸のどこを読むか」として描けます（**Method Lens**）。
- 候補・除外は、二つを重ねたときの**一致と不一致**として、どの軸で起きたかまで描けます。
- 「どの条件が変われば候補になるか」は、不一致の軸で別の値を取ったときに働く規則として計算できます。

この座標系を、Diagnose・Gallery・Case・Method・Theater・Compare で共有します。新しい記号を画面ごとに覚え直させないための土台です。

## 2. 3つの visual direction

色違いではなく、概念の比喩そのものを変えた3案を比較しました。

| 観点 | A. 測量図（Survey Atlas） | B. 前提回路（Assumption Circuit） | C. 実験ノート（Lab Ledger） |
|---|---|---|---|
| core metaphor | 問題は未測量の地形、手法は計器を持つ測量者、根拠は測量記録 | 問題の性質は入力信号、手法は前提のゲート、通過したものが候補 | すべての判断と評価は日付つきの記録行、根拠は欄外注 |
| typography | 本文は日本語 sans。座標・ID・評価回数は等幅の tabular 数字。軸名は小さな字間広めのラベル | 等幅中心の schematic。ラベルは端子名のように短い | 表組み中心。行番号・日付・ID が主役 |
| layout | 問い → 主図（地形・署名）→ 次の一手 → 根拠。図が先、記録は後で開く | 左に入力、右に出力の横流れ | 上から時系列に積む縦流れ |
| diagram grammar | 地形（等高線・曲線）、測点、経路、境界帯、未測量の斜線 | 配線、ゲート、遮断、信号の通過 | 行・列、差分のハイライト、注記 |
| motion grammar | インクで描き足す（新しい知識）、斜線が消える（未知が既知に）、印が定まる（判断の確定） | 信号が配線を流れる、ゲートが閉じる | 行が追記される |
| Theater | 各手法の「計器に映った地形」を同じ地形の上に並べる | 各手法を「観測→内部モデル→提案」のループ図として描く | 評価1回を1行とする台帳を手法ごとに並べる |
| Diagnose | 答えるたびに署名の空欄が埋まり、手法の印が定まっていく | 入力を足すとゲートが開閉する | 回答が記録行として積まれる |
| Gallery | 各 Case の署名（地形の凡例）が一目で比べられる | 各 Case は入力パターン | 各 Case は記録の要約行 |
| Compare | 同じ地形・同じ予算に複数手法の測点と経路を重ねる | 複数ループの出力を並べる | 台帳を横に並べて差分を見る |
| narrow width | 署名は4軸×3段に折り返す。舞台は縦に積む | 横流れが破綻しやすい | 表が横スクロールになる |
| strengths | unknown（未測量）、除外（計器が要求する読みを地形が与えない）、探索（地形の上の経路）が一つの比喩で表せる | 前提と除外が最も明確。手法の内部（何を記憶し何を返すか）が描きやすい | 追跡性・決定性・予算の数え方が最も正直 |
| weaknesses | 組合せ問題は「地形」になりにくい。地図の装飾に流れる危険 | 探索の振る舞いと地形が描けない。冷たく密になり、Gallery が弱い | 空間的な直感がなく、表とダッシュボードに寄る |
| scalability | 地形が描けない問題では舞台だけを木・グラフに替え、印と色は共通のまま使える | 新しい手法ごとにゲート図の手作業が増える | 件数が増えると表が長くなるだけで理解は増えない |

### 選んだ方向：A. 測量図

A を骨格にし、B の「手法は特定の軸だけを読む計器である」（Method Lens）と、C の「評価1回を1目盛りで数える」（予算目盛り）を A の中の下位文法として取り込みます。

- 「unknown is data」は、地図の**未測量域**（斜線）としてそのまま描けます。空欄ではなく「判断上まだ開いている領域」です。
- 「exclusion wins」は、**計器が必要とする読みを、この地形は与えない**ことです。除外は手法全体を赤くするのではなく、不一致が起きた**軸だけ**を違反色で示します。何を変えれば候補になるかも、同じ軸の上に書けます。
- 探索は、地形の上の**測点と経路**です。アルゴリズムの視点では、地形そのものは見えず、測点と計器の読みだけが見えます。

## 3. 色の意味

色は意味にだけ使います。色だけに意味を預けず、必ず形か文字を併記します。トークンは `site/src/visual-system/tokens.css` にあります。

| トークン | 意味 | 使う場所 |
|---|---|---|
| `--vs-ink` 濃紺 | 構造線・軸・確定した事実 | 署名の枠、地形、軸 |
| `--vs-observed` 青緑 | 観測した・既知・実行可能 | 回答済みの軸、評価点、不確実性帯 |
| `--vs-candidate` 橙 | 候補・次の一手・更新 | 候補の印、次の評価点、更新の矢印 |
| `--vs-violation` 赤 | 違反だけ | 除外を引き起こした軸、制約違反、失敗した評価 |
| `--vs-open` 灰青＋斜線 | 未知・未回答・まだ開いている | 未測量の軸、地形の見えない部分 |
| `--vs-muted` 灰 | 該当なし・文脈 | not applicable、背景の地形（人間だけが見る） |

条件付き候補は橙の**中抜き**、除外は濃紺の輪に斜線（`⊘`）です。除外の印そのものは赤くしません。赤は「どの前提が破れたか」の一点にだけ置きます。

## 4. Visual primitives

一度作った表現を複数の画面で使うことを条件にしています。各 primitive の「使う画面」が3つ未満なら追加しません。

| primitive | 何を描くか | 使う画面 | 実装 |
|---|---|---|---|
| **Problem Signature** | 12軸（形・計算の性質・ほしい結果の3群）それぞれの状態：既知 / 不明 / 未回答 / 該当なし | Gallery カード、Case、Diagnose（回答と同時に埋まる）、Theater の舞台見出し、Compare の文脈 | `ProblemSignature.tsx` |
| **Axis state** | 既知（塗り）、不明＝genuinely uncertain（斜線）、未回答＝missing（点線の空欄）、該当なし＝irrelevant（短い横線） | Signature の各軸、Method Lens | `signature.ts` の `AxisState` |
| **Disposition Mark** | 候補 ●、条件付き ◐、除外 ⊘、判断保留 ◌（根拠不足・未回答） | Case、Diagnose 結果、Method、Theater のレーン見出し | `DispositionMark.tsx` |
| **Method Lens** | 手法が読む軸と、この問題で「支える軸」「破る軸」「まだ開いている軸」、候補に変わる条件 | Case、Diagnose 結果、Method、Theater | `MethodLens.tsx`、`method-lens.ts` |
| **Search Stage** | 地形（人間だけが見る）、評価点、経路、不確実性帯、次の一手、失敗事象、予算目盛り | Theater、Compare（重ね表示）、Case のプレビュー、記事 explorable | `SearchStage.tsx` |
| **Evidence Link** | 主張 → source ID | すべての判断の末尾（既存の `EvidenceLinks` を共通語彙として使う） | `EvidenceLinks.tsx` |
| **Switch Signal** | 「この観測が出たら手法を見直す」印 | Theater の失敗事象、Case の限界、Compare の注記 | `SearchStage.tsx` の `FailureEvent` |

### Search Stage の二つの視点

Theater と Compare では、同じ舞台を二つの視点で見られます。

- **人間の視点**：教材用の真の目的関数（灰色）を表示する。答え合わせ用で、どの手法も参照しません。
- **アルゴリズムの視点**：真の目的関数を消し、その手法が実際に持っている情報だけを描く。勾配法なら測点と差分で得た傾き、集団法なら集団と分布の幅、ベイズ最適化なら観測点・代理モデルの平均・不確実性・獲得関数。

既定は**アルゴリズムの視点**です。「動きが違う」のではなく「見えている世界が違うから動きが違う」ことを先に見せます。

## 5. Motion の意味

動きは、状態の遷移・探索・定式化の変化・比較・不確実性の更新の理解を助けるときだけ使います。画面ごとに別の動きを発明しません。

| 動き | 意味 | 長さ | トークン |
|---|---|---|---|
| ink | 新しい構造・知識が描き足される（署名の軸が埋まる、経路が伸びる） | 320ms | `--vs-motion-ink` |
| settle | 判断が定まる（候補・除外の印が置かれる） | 220ms | `--vs-motion-settle` |
| reveal | 未知が既知になる（斜線が消える） | 280ms | `--vs-motion-reveal` |
| step | 探索の1評価。等間隔で進み、評価1回 = 1拍 | 1拍 | Theater の再生速度 |

`prefers-reduced-motion` では全て無効にし、常に終了状態を出します。動きを止めても、静止画だけで主要な構造が読めることを条件にします。

## 6. 画面の情報の順序

すべての画面で、この順序に揃えます。

1. 今見ている問い
2. 判断に必要な主要構造（署名・舞台・判断の印）
3. 次に見るもの
4. 詳細な根拠（source ID、metadata、実装の詳細は消さずに開閉で出す）

## 7. Vertical slice

最初の一周は Case `hyperparameter-search`（高価な実験の設定を探す）で作りました。

```text
Gallery（署名つきカード）
→ Case（署名・Method Lens による候補 / 条件付き / 除外）
→ Method（その手法が読む軸）
→ Theater「アルゴリズムの視点」（勾配・集団・代理モデルの3つの計器を同じ地形と予算で）
→ 重ねて比べる（同じ舞台の上で best-so-far と測点）
→ 限界と切り替えの兆候
→ 根拠
```

この Case では BFGS が除外されています（勾配が得られない black-box）。Theater では勾配の計器を「数値差分で傾きを測る」形で動かし、評価1回ごとに2回分の予算を使うことと、近くの谷に留まることを、除外理由の**観測できる帰結**として見せます。除外を覆すのではなく、除外の理由を目で確かめるための舞台です。

## 8. 完成判定の問い

- Algorithm Theater を削除しても、この visual system は Diagnose・Gallery・Case・Method を良くしているか。
- Diagnose・Gallery・Theater・Compare を行き来したとき、新しい記号体系を学び直す必要がないか。
- 静止画だけで、候補・除外・未知が区別できるか。
- 赤が「違反」以外の意味で使われていないか。

## 9. 実装の場所

| 何を | どこ |
|---|---|
| 色・動きのトークン | `site/src/visual-system/tokens.css` |
| 共通の描画規則 | `site/src/visual-system/visual-system.css` |
| 署名の軸・状態・語彙 | `site/src/visual-system/signature.ts`（軸と選択肢の順序は診断の質問と一致することを `signature.test.ts` が検査） |
| Method Lens の計算 | `site/src/visual-system/method-lens.ts`（規則と predicate だけから作る。Case にない除外を作らないことをテストで固定） |
| 部品 | `ProblemSignature`、`DispositionMark`、`LensBoard`、`MethodReading`、`CaseSignatureStrip`、`SearchStage` |
| アルゴリズムの視点の舞台 | `site/src/features/theater/lenses/`（`/theater/lenses/hyperparameter-search`） |
| e2e | `site/e2e/visual-system.spec.ts`（vertical slice の5画面で axe と375pxの横はみ出し、除外の読み、視点の切り替え） |

画面への配置:

- Gallery カード: 小さな署名、候補 ● と除外 ⊘ の印
- Case: 「この問題の署名を、手法ごとの目で読む」（LensBoard）。旧「手法の役割」節を置き換え
- Diagnose: 回答とともに埋まる署名（中サイズ）、結果の帯の印、各結果カードの小さな Lens
- Method: 「問題のどの軸を読むか」（MethodReading）
- Compare: 「この比較の問題」帯（CaseSignatureStrip）
- Theater: アルゴリズムの視点の舞台と、一覧からの入口
- Home: 候補・選ばない理由の印

## 10. 新しい表現を足すとき

1. まず既存の primitive で描けないかを確かめる。描けるなら新しいものを作らない。
2. 新しい primitive は、使う画面を3つ以上挙げられるときだけ `site/src/visual-system/` に足し、この文書の §4 に行を追加する。
3. 色は §3 のトークンだけを使う。手法の区別には色ではなく形（`MethodShape`）を使う。
4. 動きは §5 の4種類から選ぶ。`prefers-reduced-motion` で終了状態になることを確かめる。

## 11. 分かっている残課題

- 既存の Theater / Compare の正準 renderer（trajectory、surrogate など）は、まだ独自の色と印で描いている。例えば獲得関数を紫の棒で描いている。`SearchStage` の部品へ移すのが次の一歩。
- サイトの外枠（緑）と意味の色（紺・青緑・橙・赤）は分けたが、外枠の配色そのものは変えていない。
- Map・Learn・Search・Sources・Coverage にはまだ署名と印を置いていない。Map の node と Search の結果に小さな署名を付けるのが自然な次の候補。
- データの発見: Case `hyperparameter-search` は「勾配が使えない」ことを理由に BFGS を除外しているが、以前は BFGS に勾配の前提（predicate）がなく、Lens は「規則上の除外軸なし」と表示していた。dataset 0.18.20 で `P_M_BFGS_DERIVATIVE` を追加し、今は「勾配」の軸で外れる理由として描ける。Case の判断と規則・前提の食い違いは、これからも Lens が隠さず表示する。
- Gallery カードのメタ情報の文字（0.65rem）は、この変更の前から14pxの契約を下回っている。
