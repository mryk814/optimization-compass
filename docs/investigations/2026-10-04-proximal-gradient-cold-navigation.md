# 近接勾配図の初回表示の調査（2026-10-04）

## 結果と範囲

`main` の `b136e78af55c19d55bb5a821d8a18d7998fa3dbd` を取得し、production build を Cloud の Chromium 151.0.7922.173 で確認した。通常の初回遷移では再現しなかった。原因は未確定であり、runtime の修正は行わない。追加するのは初回の実リンク遷移と chunk 待機の回帰テストのみ。

公開サイト、dataset 0.18.19、記事、数式、承認済み UI、workflow は変更しない。

## 先行観測（今回の再現とは区別する）

公開 `https://mryk814.github.io/optimization-compass/` の home → 手法一覧 → 近接勾配の記事へのリンクで、最新の本文は表示されたが、25 秒ほど図に操作 DOM がなく静的代替だけだったとの報告を受けた。reload 1 回で復旧し、その後の一覧からの再入場と browser Back は成功した。失敗時の console、network、代替文の正確な文字列は提供されていない。これだけではリリースの regression と断定できない。

今回の Cloud shell から公開 Pages の root と `deployment.json` を取得すると、proxy の HTTP 403 / CONNECT failure となった。追加の network permission でも解消しない。公開環境の CDN 配信や元の Cloud browser の状態を今回のローカル結果で検証したことにはしない。親 PC は使用していない。

## Source の確認

- `site/src/main.tsx`: `StrictMode` 内で client root を render する。SSR hydration は使っていない。
- `ContentIndexPage`: 生成された entity relation から記事の canonical link を選ぶ。一覧の初期 filter は「動き・比較で学ぶ」。近接勾配を選ぶ際は「手法」filter と検索を使用した。見出し「近接勾配法」を選び、近接勾配を本文で言及する別記事との曖昧さを避ける。
- `CompiledContent`: コンパイル済み HTML を挿入し、その ref と HTML を `ExplorableMounts` に渡す。
- `ExplorableMounts`: layout effect で登録済み ID と mount node を検出して compiler の静的代替を置換し、portal 内の lazy component を描画する。viewport / IntersectionObserver を待つ条件はない。
- `registry.tsx`: `proximal-gradient-threshold` は `ProximalThreshold` の dynamic import。
- import 待機時は `図を読み込んでいます…`、render/import 失敗時は boundary の `図を表示できませんでした。下の説明で内容を確認してください。` を表示する。compiler の元の静的代替とは別の状態である。

## 実行した限定確認

| 確認 | 結果 |
|---|---|
| 既存 `proximal-gradient-article.spec.ts` の 4 tests | 4 pass。直接 URL、最初の一手、キーボード、再生、別記事との往復 |
| 新規 cold home → 一覧 → canonical article link、1280px と 375px、各 2 fresh contexts、retry なし | 4 pass。各 context で操作 DOM、単一 frame、Back → Forward、reload を確認 |
| `ProximalThreshold-*.js` の応答を Promise で保持し、loading を確認してから解放、2 fresh contexts | 2 pass。静的代替や操作 DOM はなく loading を表示し、解放すると reload なしで操作図へ移行 |
| 同 chunk を明示的に abort する一時的な診断 | 1 pass。boundary の失敗文と操作 DOM 不在を確認。abort を解除して reload すると復旧 |

正常な cold tests の browser console / pageerror / requestfailed は空。script response に HTTP 400 以上はなく、proximal figure chunk が実際に request されたことも確認した。desktop / phone の図の screenshot を目視し、slider と再生操作、`0.000 → 0.750 → 0.550` を確認した。λ = 3 で縮めた後が `0.000`、停止理由が「ちょうど0」になる。

一時的な abort 診断では `net::ERR_FAILED` と `TypeError: Failed to fetch dynamically imported module: .../ProximalThreshold-BAFSPmRl.js` が console に出た。失敗図の screenshot も boundary の失敗文と caption のみだった。これは resource failure が「本文は表示、操作なし、reload で回復」を起こせる証拠であり、先行観測の原因の証明ではない。この診断 script は通常の回帰テストに混ぜない。

## 継続するテスト

`site/e2e/proximal-gradient-cold-navigation.spec.ts` に 3 tests を追加する。既存の direct-route tests に欠けていた初回 canonical-link 遷移を、desktop と phone で確認する。3 tests は既存の `@critical` selection に含める。新しい workflow は不要。

既存 browser fixture が console / pageerror / requestfailed を保存して unexpected error を失敗にする。新規 cold tests は script response の URL / status も JSON 添付し、cold 図の screenshot を保存する。chunk の遅延は任意の sleep ではなく、loading DOM を観測して解放する。

Cloud 専用の一時 config で既存 config を継承し、installed `/usr/bin/chromium` を指定した。Playwright の標準 Chromium download も domain forbidden だったためであり、この config は PR に含めない。正式環境では既存 `playwright.config.ts` を使う。

```bash
CI=1 PLAYWRIGHT_PORT=43873 npm --prefix site run test:e2e:artifact -- \
  --config playwright.cloud.config.ts \
  e2e/proximal-gradient-cold-navigation.spec.ts \
  --project=chromium-desktop --retries=0 --repeat-each=2
```

## PR の検証

`UV_CACHE_DIR=/tmp/oc-uv-cache uv run optimization-compass validate pr-fast` は pass。Ruff lint / format、mypy、repository contracts 55 tests、content / licensing checks、site unit 494 pass / 1 skip、typecheck と production build を含む。50 記事を巡回する browser suite は再実行していない。最終の test 添付と `@critical` tag を含む 3 tests も retry なしで 3 pass（10.4 秒）。

## 残る不確実性

元の失敗時の resource / console 記録と正確な代替文がないため、network failure、stale asset、mount の不成立などを区別できない。公開 Pages 上の fresh context 検証も今回の接続制限で未実施。CDN/cache 条件、元の browser version、元の network 条件を網羅してはいない。

再発時は reload 前に図の DOM（compiler fallback / loading / boundary failure）、console、失敗 request と HTTP status、現在の asset URL と deployment identity を保存する。それまでは推測の runtime fix や自動 retry、公開サイト変更を入れない。
