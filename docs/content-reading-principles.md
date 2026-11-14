# 画面の読みやすさの原則

サイト全体の画面（記事のページの枠、一覧、ハブ）を作るときの原則です。
記事の中身の書き方は [`writing-articles.md`](writing-articles.md) にあります。

## 1. 最初の視線を本文に置く

ページを開いた直後の主役は、タイトルと、そのページの本題（記事なら書き出しと主図）です。
目次、ID、更新日、根拠、関連リンク、構造化データは消さずに、本文の後か開閉できる場所へ送ります。
同じ意味の説明を、本文、カード、補助パネルで重複させません。

## 2. 文字の契約

ページごとに文字サイズを決めず、`site/src/typography.css` の意味別tokenを使います。

- 本文、summary、カード要約、操作（navigation、button、filter、開閉のsummary）は `1rem` 以上。
- `0.875rem` は日付、ID、件数、短い分類label、captionなどのmetadataだけ。
- `0.75rem`〜`0.8125rem` は、SVG・chartの中の軸、目盛り、短い注記だけ。
- 長い本文は `42rem`、導入文は `48rem` を上限にし、表や図の幅とは分けます。
- 狭い画面では文字を縮めず、一列に戻す、折りたたむ、表や図の内部だけをscrollさせる方法でreflowします。

基準は、[WCAG 2.2 Resize Text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text)、320 CSS px で一方向にreflowさせる [WCAG Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow)、標準文字を16 CSS px以上にする [デジタル庁デザインシステムのタイポグラフィ](https://design.digital.go.jp/dads/foundations/typography/) です。

## 3. 一覧とハブでは「次に選ぶもの」を前に出す

- Home は、製品内部の機能分類より先に、具体的な問いと次の一手を見せます。
- カードは、問い、分野、難易度、学習経路の準備状況を前に出します。
- 一つの面に同じ重さの主行動を並べすぎません。

## 4. 小さな可視化にも問いを持たせる

一覧面の図は、「どこから探せるか」「どこが足りないか」を短時間で判断するために使います。
図の上に問いを置き、対象名と値を直接表示し、色だけで状態を区別しません。

## 5. 実画面で確かめる

変更前後に、PC とスマホ幅の実ブラウザ画面を見て、本文・図・操作のまとまりまで確かめます。
動きは操作の結果や対象の関係を示すために使い、reduced motion でも同じ関係を確かめられるようにします。

## 6. 記事本文の見た目は一つにする

記事本文の見た目は、記事の種類（formulation、method、family、concept）や explorable の有無で変えません。基準は線形最小二乗の記事（`#/learn/concept.linear-least-squares`）です。

- 目次は本文の上に折りたたんで置き、本文は42remの列で読ませます。図だけがこの列より広がれます（`CompiledContent.tsx` の `compiled-content-layout--lesson`）。
- 見出し、段落、リスト、リンク、コード、表、図のキャプションの見た目は、`site/src/styles.css` の `.markdown-body` の共通指定だけで決めます。ページの種類ごとのCSSから `.markdown-body` の中を指定しません。違いが必要なら共通指定を変えます。

この規則は二つのテストが守ります。

- `site/src/features/content/article-style-contract.test.ts`：共通レイアウト以外のclassが `.markdown-body` を指定したら失敗します。
- `site/e2e/typography-contract.spec.ts`：1280pxと375pxで、各種類の記事の計算済みスタイルと本文の列の位置が、線形最小二乗と一致するかを比べます。
