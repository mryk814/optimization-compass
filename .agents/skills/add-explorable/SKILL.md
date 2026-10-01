---
name: add-explorable
description: "Add an interactive explorable figure (動かして学ぶ図) to a method/concept article using an explorable block, with a registry entry, a tested math core, and a React figure under site/src/features/explorable/."
---

# explorable（動かして学ぶ図）を追加する（薄いwrapper）

規則の正はこのスキルではなく次の3つです。編集前に必ず読むこと:

1. `docs/explorables.md` — 使う基準、構成、設計規則、追加手順、検証コマンド
2. `docs/content-visual-language.md` — 色の言語と、静的図との使い分け
3. `.agents/skills/article-style/SKILL.md` — 記事本文と caption の文体

## 手順

1. 図が答える**1つの問い**を決める。静的な図で足りる場合、または正準の実行記録を再生したい場合は、explorable を使わない（Trace / Theater / Comparison を使う）。
2. `src/optimization_compass/resources/explorables.json` に `id`、`question`、`fixed_conditions`、`not_implied` を追加し、`site/src/features/explorable/meta.ts` に同じ文言を写す。
3. `site/src/features/explorable/math/` に、描画に依存しない厳密な計算を書き、解析解または既知の値でテストする。
4. 図の component を書き、`registry.tsx` に `lazy` で登録する。`ExplorableFrame`、`Slider`、`PlayerBar`、`useTimeline`、`useStageViewport`、`LiveMath` を再利用する。
5. 記事に `::: explorable <id>` を置く（caption は1段落）。直前の文で何を動かして何を見るかを書き、`summary` と本文第1段落の一致を保つ。`last_reviewed` を更新する。
6. 公開データを再生成する: `uv run optimization-compass export-site-data --output site/public/data`
7. 検証する: `uv run optimization-compass validate content`、`npm --prefix site test`、`npm --prefix site run build`、`site/e2e/explorable.spec.ts`（axe と375px を含む）。

## Stop条件

- 手法の性能や順位を示すように読める図になる場合。`not_implied` で否定できないなら作らない。
- 出典のない事実を、図や caption に足す必要がある場合（canonical の追加は別の recipe）。
- 生成済みの公開データを手で編集する必要が出た場合。
