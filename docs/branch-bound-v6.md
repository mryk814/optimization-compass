# 分枝限定法 v6 の試行と引き継ぎ

良い袋を選ぶ操作と、より良い袋がないと証明する操作を分けた教材です。
4品の入門と8品の発展を切り替え、枝の上界と実行可能な最高記録を比べます。
初手の袋が最適でも、証明が終わるまで結果を最適だとは表示しません。

## 保存した範囲

受け入れ済み試用版の基点は `45cdea9`。このdelivery branchは公開mainの
`8e91f04b06494cfbda148567d34173d48062594d` から、B&Bの13ファイルだけを移しました。
両基点の差はドローン教材の4ファイルで、B&B・共有frame・依存lockの変更はありません。
品と袋のSVGはこの教材用の作図です。取得画像、私的ログ、マシン固有のパス、
preview所有情報、認証情報は保存対象に含めていません。

コードとテストはMIT、記事と生成された教材データはCC BY 4.0です。
根拠文献は記事の `source_ids` を参照し、第三者の画像や本文を転載していません。

## 固定依存とPCでの再現

試用時の環境はWindows、Node.js 24.4.1、npm 11.4.2、Python 3.12.5でした。
Python 3.12とNode.js 24を使い、依存を更新せずlockから導入します。

- `uv.lock` SHA-256: `A03E74AC22275086DFFBFF5AEE95EF96A11A2B74CFA139DD01F860B5A793A169`
- `site/package-lock.json` SHA-256: `104D0E2E5C16C79672C995145E7A4BE116DC4CC700E9BFA0C4E1FA3965A7CDE3`

PowerShellで、新しいフォルダへこのbranchを取得します。

```powershell
git clone --single-branch --branch codex/komori-20261003-branch-and-bound https://github.com/mryk814/optimization-compass.git optimization-compass-bnb
Set-Location optimization-compass-bnb
uv sync --frozen --all-extras --all-groups
Set-Location site
npm ci
npm run build
npm exec -- vite preview --host 127.0.0.1 --port 5191 --strictPort
```

`http://127.0.0.1:5191/optimization-compass/#/learn/branch-and-bound` を開きます。
5191が使用中なら別の空きポートを指定し、既存サーバーは停止しません。

必要な関連検証だけを再実行する場合は、`site`で次を使います。

```powershell
npm exec -- vitest run src/features/explorable/branch-bound.test.tsx src/features/explorable/math/branchBound.test.ts
npm exec -- playwright install chromium
$env:PLAYWRIGHT_PORT = '5192'
npm exec -- playwright test e2e/branch-bound.spec.ts --project=chromium-desktop
```

## 再利用した検証結果

移した時点で13ファイルが受け入れ済みv6とSHA-256で一致することを確認しました。
公開用コピーでは、diff checkで検出した `BranchBound.tsx` 末尾の空行1行だけを除いています。
処理・表示、依存lock、B&Bが依存する共有実装は同じため、deliveryのために同じsuiteを再実行していません。

- 関連unit 83件、typecheckとproduction buildが通過。
- 回帰browser 7件、初期4列2行の追加3件、初手最適の結果案内1件が通過。再試行なし。
- 1280/375/390px、keyboard/touch、reduced motion、axe重大違反、overflowを確認。
- 4/8品の全列挙、部分枝の上界と枝刈り、探索順、undo/reset/切替と証明13/18点を確認。
- 容量超過は色と記号・文字、開始不可を確認。初期ADE18から上界18.5を確かめ、18/18へ一致。
- スクロールは通常の分岐と選択で移動0px、主buttonのfocusを維持。
- 記事focused validationと144ページの整合、exportとdiff checkが通過。

旧自動scroll処理との比較は、元のcallbacksを隔離browserへ復元した対照試行です。
v5原本をそのまま測った記録ではありません。全Python suiteは今回再実行していません。
公開データを変更する際は、repository rootで公式exportを行い、生成JSONを手編集しません。

## 試行終了と復旧

このbranchは別checkoutで試すため、終了はそのpreviewの端末でCtrl+Cを押すだけです。
稼働中の別checkoutやmainへの切替・mergeは不要です。稼働環境を切り替える場合は
所有するPID、生成時刻、commandとlistenerを照合し、そのserverだけを対象にします。
ブランチを後から取り消す場合もmainへの変更はありません。既存refの上書きやforce pushは使いません。

## 他の教材候補との接点

B&B固有のarticle、component、CSS、mathとtestsは独立しています。
LSQ・座標降下の教材や検証効率化の候補との接点は、explorableの `registry.tsx`、`meta.ts`、
`resources/explorables.json` と生成されたcontent/search/retrievalデータです。
統合時はcanonical入力を両方保持し、公式exportからJSONを再生成します。
このbranchでは共有frame、依存lock、CI、ドローン修正を変更していません。

既存CIはpush対象をmainに限定し、Pages upload/deployもmainのpushだけです。
この新規branchの通常pushではPagesを更新しません。PR・main統合・本番公開は別の操作です。
