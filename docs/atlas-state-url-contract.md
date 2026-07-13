# AtlasState URL contract

AtlasState は、問題構造マップと診断が共有する、URL で再現可能な状態です。公開 URL では HashRouter の query として次の形で使います。

```text
/#/map?state=<token>
```

`token` は UTF-8 JSON を padding なしの base64url にしたものです。圧縮や legacy decoder は使いません。現在サポートする `stateVersion` は `1` だけで、未知の version は明示的に拒否します。

## Canonical state

```ts
interface AtlasStateV1 {
  stateVersion: 1;
  datasetVersion: string;
  viewId: string;
  viewVersion: string;
  selectedNodeId?: string;
  answers: Record<string, AtlasAnswer>;
}
```

回答は次の3状態です。

- `answered`: canonical SQLite answer value を1件以上持つ回答
- `unknown`: 意図して「不明」を選んだ回答。値は必ず `['unknown']`
- `not_applicable`: 意図して「該当なし」を選んだ回答。値は必ず `[]`

未回答は `answers` に質問 ID が存在しないことで表します。`unanswered` status はシリアライズしません。推薦入力には `answered` と `unknown` を渡し、`not_applicable` と未回答は渡しません。

エンコード時は質問 ID と multi-choice の値を辞書順に並べ、入力オブジェクトは変更しません。このため、意味が同じ状態は同じ token になります。

## Compatibility and migration

デコード時は、現在の compatibility catalog と照合します。

- 古い `datasetVersion` は現在の dataset version へ更新し、日本語の警告を返します。
- 同じ `viewId` の古い `viewVersion` は現在の view version へ更新し、日本語の警告を返します。
- 現在の catalog にない質問 ID、回答値、`selectedNodeId` は警告付きで除外します。無効値の除外後に値が残らない質問は未回答として省略します。
- 有効な回答、`unknown`、`not_applicable` は version 更新後も保持します。
- 異なる `viewId` は別の意味構造であり、暗黙に移行せず拒否します。

不正な base64/JSON、必須 metadata の欠落、空 ID、未知の `stateVersion`、single-choice の重複・複数値、status と values の不整合も拒否します。

## Size limit

token の上限は **1800文字**です。`encodeAtlasState` が生成した token が1800文字を超える場合は `AtlasStateUrlTooLongError` を投げます。切り詰めた URL は生成しません。1800文字ちょうどの token は有効です。

## UI-only state

次は操作中だけの UI state であり、AtlasState にはシリアライズしません。

- tree の展開・折りたたみ
- pan / zoom
- 計算済みの推薦結果

推薦結果は canonical answers と現在の dataset から再計算します。
