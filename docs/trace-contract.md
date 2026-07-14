# AlgorithmTrace 1.0.0

`AlgorithmTrace`は、最適化アルゴリズムの教育用再生をPython generatorから静的Webアプリへ渡すためのversioned contractです。推薦エンジンが返す`RuleTrace`とは目的もschemaも別であり、相互変換しません。

## Authority and versions

- Pythonの`optimization_compass.trace_models`を生成時のauthorityとし、TypeScriptの`contracts/trace.ts`が同じcore fieldsをexact parseします。
- `contract_version`は`1.0.0`のみを受理します。未知version、未知core field、欠落core fieldはエラーです。legacy decoderやfallback schemaはありません。
- Python/TypeScriptともscalar coercionを行いません。文字列化した整数やbooleanを数値fieldとして受理しません。
- `dataset_version`は参照するcanonical dataset、`data_version`はtrace payload familyの版です。公開indexとtraceは両方が一致しなければ読み込みません。
- `generator_id`/`generator_version`は教育用更新則の実体を示します。教育用generatorは`implementation_mapping_status=not_applicable`かつ`implementation_id=null`です。`supported`だけが非NULLのimplementation IDを要求します。

## Full snapshot frames

各`TraceFrame`は単独で描画できる完全なsnapshotです。前frameとの差分ではありません。

- `frame_index`: 0から始まる連続整数
- `iteration`: algorithm iteration。非負かつ単調非減少
- `oracle_evaluations`: 累積objective/oracle評価回数。非負かつ単調非減少
- `elapsed_steps`: 決定的generator内の論理step。非負かつ単調非減少
- `elapsed_time_ms`: 実時間ではなく、教材用timelineの決定的な経過時間。非負かつ単調非減少
- `event_type`: 未知値を許すlowercase slug。共通playerはalgorithm固有の意味を解釈しません
- `decision`: `accepted`、`rejected`、`not_applicable`のいずれか
- `explanation_key`: 安定した説明文キー
- `event_label_ja`/`event_label_en`: 両方を指定するか、両方をNULLにします。NULLの未知eventは`未定義イベント（event-type）`と表示します
- `keyframe`: downsamplingで必ず残す明示keyframe
- `points`、`vectors`、`metrics`: そのframeを描画する全要素。各list内のIDは一意です
- `payload`: 任意の有限JSON。共通playerは読みません

共通playerのイベント説明は`explanation_key`だけから共有辞書で解決します。未知キーはキーを含む固定fallbackを表示し、algorithm固有の`payload`を説明生成のために解釈しません。

座標、vector、metric、payloadを含む全数値でNaNと正負Infinityを禁止します。`payload`はJSONのnull、boolean、number、string、array、string-key objectだけを許可します。

## Trace and bundle context

`AlgorithmTrace`はtrace/method/profile/objective/scenarioのcanonical ID、objective、preset、parameters、initial state、seed、evaluation budget、stopping、environment、fairness statement、terminal status/summary、source IDsを明示します。wall-clock生成時刻は持ちません。

`TraceBundle`はcomparison IDとmember tracesを束ねます。全memberは次をbundleと完全一致させます。

- dataset/data/objective ID
- objectiveとinitial state
- seedとevaluation budget
- stoppingとenvironment
- fairness statement

同期軸は必ず累積`oracle_evaluations`です。同じframe indexやiterationを同期軸にしてはいけません。指定評価回数以下にある各memberの最新snapshotを表示し、memberの最初の評価より前は`null`として未来のsnapshotを表示しません。

## Determinism and limits

- 1 traceは最大1,000 framesです。
- canonical raw UTF-8 JSONは最大2 MiBです。圧縮後の大きさでは判定しません。
- canonical serializationはUnicodeをそのまま使い、object keyをUnicode code point順にsortし、separatorを`,`と`:`へ固定します。Python/TypeScriptは共有fixtureでbyte lengthも一致させます。
- list順はgeneratorが確定し、同じ入力・contract versionから同じbytesを生成します。
- 公開traceにはwall-clock fieldを含めません。

`downsample_frames`はframeを補間・合成しません。最初、最後、`keyframe=true`、event type区間の先頭を必須とし、残りの枠を元frame列へ等間隔に決定的配分します。選択後は`frame_index`だけを0から連続に振り直し、iteration、評価回数、描画dataは保持します。必須frameだけで上限を超える場合は省略せず失敗します。

## Playback and URL

`usePlayback`だけが再生状態を所有します。共通controlsは再生/一時停止、前後step、frame/evaluation seek、forward/reverse、`0.25`/`0.5`/`1`/`2`/`4`倍速を提供し、先頭・末尾で安全に停止します。

URLへ書けるplayback stateは`trace`、`frame`または`evaluation`、`speed`、`direction`だけです。trace framesやpayloadはURLへ入れません。既存のAtlasStateなど他query parameterは保持します。reload、同一routeのquery遷移、browser back/forwardでは位置・速度・方向を復元しますが、再生は必ずpausedで開始します。player自身の更新はhistoryを増やしません。

## Published contract demo

`optimization-compass export-site-data`は次を決定的に生成します。

- `site/public/data/manifest.json`のversioned `traces` asset（index path、contract/index version、bytes、SHA-256）
- `site/public/data/traces/index.json`
- `site/public/data/traces/dummy-educational.json`

loaderはmanifestからindex pathを発見し、bytesとSHA-256を検証してからexact parseします。hardcoded index fallbackはありません。dummy traceはinitialize、accepted proposal、stopの3つの完全snapshotでcontract、loader、URL-backed playerをend-to-endで検査します。これは手法性能の比較結果ではありません。
