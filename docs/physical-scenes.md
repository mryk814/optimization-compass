# 計算結果から読む3D教材

## 目的と境界

材料の配置、ロボットの姿勢、未来の軌道を、実際に解いた数値と対応させて読みます。
この3つは計算済みの教材を再生する画面であり、ブラウザで条件を連続的に変えて解き直すExplorableとは区別します。
掲載先は `/theater/physical/topology`、`/theater/physical/arm`、`/theater/physical/drone` です。
既存記事とTheaterの入口から到達できます。

この追加はrendererと教材用generatorの変更です。
canonicalな問題、手法、推薦、SQLite、dataset releaseのidentityは変更しません。
URLの末尾は教材画面の識別子で、canonical entityの新しいnamespaceではありません。
将来正式なScenarioへ昇格する場合は、正準problem instanceとTraceの登録を別の変更で行います。

## 計算と表示のauthority

- `src/optimization_compass/*_scene.py` が数値計算を所有します。
- `scripts/generate_*_scene.py` が検証済みの結果を `site/src/features/physical-scenes/data/*.json` へ生成します。このJSONを手で編集しません。
- JSONは計算の設定、出典、制約の検査結果、表示する状態列を含みます。検証前の丸め値で制約を判定しません。
- modelのsource、generator、`uv.lock` を順に結合したSHA-256を記録します。計算の入力が変わったとき、再生成していない表示データは検査で失敗します。
- `site/src/features/physical-scenes/` はその状態列を描画します。表示条件の切替は保存済みの別のsolveを選ぶ操作です。
- Three.jsはこの画面だけで遅延読み込みします。WebGLが使えない場合にも同じ数値から作る2D射影と診断値を表示します。

## 各教材で解く問題

| 教材 | 計算 | 確認する境界 |
|---|---|---|
| 構造 | 3D線形弾性の8節点六面体FEM、SIMP、filter、OC | 剛性の対称性、剛体mode、平衡残差、感度、体積制約、目的改善 |
| アーム | 関節角軌道の制約付き最適化 | forward kinematics、全linkの距離、関節制限、速度、区間内の密な検査 |
| ドローン | 3D並進運動のreceding horizon MPC | 状態更新、入力制約、予測の先頭と実行状態の対応、区間内の障害物距離 |

構造の格子は有限の教育用離散化です。メッシュ独立性、応力、座屈、製造性を保証しません。
アームは指定した幾何学モデルで、関節torqueや実機の追従誤差を含みません。
ドローンは質点の並進モデルで、姿勢制御、motor dynamics、視覚状態推定、PAMPCの再現を含みません。

## 見せ方

最初は結果が見える斜め視点を表示します。
構造は終了状態、アームとドローンは障害物付近の途中の状態から読み始めます。
回転、正面と上面のプリセット、視点リセット、再生、コマ送り、シーク、再生速度を付けます。
橙は更新と予測、青緑は構造と実行軌道、紺は参照形状、赤は違反だけです。
3DのラベルはHTMLで表示し、同じframeの2D射影と数値を隣に置きます。
材料の表示thresholdと変形倍率は計算結果の変更ではないことを表示します。
reduced motionでは自動再生しません。

## 再生成と検証

`uv sync --all-extras` の後、各generatorを実行します。
依存の版は `uv.lock` と `site/package-lock.json` で固定します。
数値moduleの単体検査、生成結果の契約検査、siteの型検査とbuild、再生操作と375pxのbrowser検査を行います。
他の教材の生成物は変更しません。
